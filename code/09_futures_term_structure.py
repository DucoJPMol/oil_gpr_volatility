"""
09_futures_term_structure.py
Extension B: spot vs futures and the term structure across conflicts.

A long, persistent disruption should pull the futures curve into backwardation
(near-month above deferred) and keep it there, whereas a headline event should
not. This script pulls the WTI futures curve from EIA (front-month RCLC1 and the
4th contract RCLC4), builds the spot-C1 basis and the C1-C4 spread (the
backwardation indicator), and looks at them around each episode.

Data note: EIA's NYMEX futures series end on 2024-04-05, so they cover the 1990,
2018 and 2022 episodes but NOT 2025/2026. The two long disruption episodes (1990,
2022) are the showcase. For 2025/2026, front-month futures (BZ=F/CL=F) would need
a manual download (Yahoo/ICE), as those sources are walled off from this network.

Output:
  data/raw/raw_eia_fut_c1.csv, raw_eia_fut_c4.csv
  tables/table9_term_structure.csv / .txt
  figures/fig10_term_structure.png / .pdf

Usage (needs EIA_API_KEY):
    python code/09_futures_term_structure.py   (run 01 first)
"""

import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

FUT_ROUTE = "petroleum/pri/fut"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
# Episodes EIA futures actually cover (data end 2024-04-05).
COVERED = ["gulf_war_1990", "iran_sanctions_2018", "russia_ukraine_2022"]


def fetch_fut(series_id: str, name: str, refresh: bool = False) -> pd.Series:
    raw = config.DATA_RAW / f"raw_eia_fut_{name}.csv"
    if raw.exists() and not refresh:
        s = pd.read_csv(raw, index_col=0).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        return s
    if not config.EIA_API_KEY:
        sys.exit("EIA_API_KEY is not set (needed to download futures).")
    url = f"https://api.eia.gov/v2/{FUT_ROUTE}/data/"
    rows, offset = [], 0
    while True:
        params = {"api_key": config.EIA_API_KEY, "frequency": "daily", "data[0]": "value",
                  "facets[series][]": series_id, "start": "1985-01-01",
                  "sort[0][column]": "period", "sort[0][direction]": "asc",
                  "offset": offset, "length": 5000}
        r = requests.get(url, params=params, headers=HEADERS, timeout=60)
        r.raise_for_status()
        page = r.json()["response"]["data"]
        rows.extend(page)
        if len(page) < 5000:
            break
        offset += 5000
    s = pd.to_numeric(pd.Series({pd.Timestamp(d["period"]): d["value"] for d in rows},
                                dtype="float64"), errors="coerce").dropna().sort_index()
    s.to_csv(raw, header=[series_id])
    print(f"  {name} {series_id} {len(s)} obs {s.index.min().date()} to {s.index.max().date()}")
    return s


def load_front_month(eia_c1: pd.Series) -> tuple[pd.Series, str]:
    """Front-month WTI futures across the full sample. EIA's RCLC1 ends 2024-04,
    so if a manual Yahoo CL=F download is present (data/raw/raw_cl_futures.csv)
    we splice its later observations on, extending coverage through 2026."""
    manual_path = config.DATA_RAW / "raw_cl_futures.csv"
    if not manual_path.exists():
        return eia_c1, "EIA RCLC1 only (ends 2024-04; add data/raw/raw_cl_futures.csv for 2025/2026)"
    # utf-8-sig strips the BOM that investing.com / Excel prepend.
    m = pd.read_csv(manual_path, encoding="utf-8-sig")
    m.columns = [c.strip().lstrip("﻿").lower() for c in m.columns]
    # Tolerant of Yahoo (Date, Close/Adj Close) and investing.com (Date, Price).
    date_col = next(c for c in m.columns if c in ("date", "period"))
    close_col = next(c for c in m.columns if c in ("close", "adj close", "close*", "price", "value"))
    vals = pd.to_numeric(m[close_col].astype(str).str.replace(",", ""), errors="coerce")
    man = pd.Series(vals.values,
                    index=pd.to_datetime(m[date_col], errors="coerce")).dropna().sort_index()
    # Use EIA up to its end, then the manual series afterwards.
    cutoff = eia_c1.index.max()
    spliced = pd.concat([eia_c1, man[man.index > cutoff]]).sort_index()
    spliced = spliced[~spliced.index.duplicated(keep="first")]
    return spliced, f"EIA RCLC1 to {cutoff.date()} + manual CL=F to {spliced.index.max().date()}"


def event_window(s: pd.Series, trigger: str) -> pd.DataFrame:
    cal = s.dropna().index
    trig = pd.Timestamp(trigger)
    after = cal[cal >= trig]
    if not len(after) or (after[0] - trig).days > 10:
        return pd.DataFrame()
    z = cal.get_loc(after[0])
    lo, hi = max(z - config.WINDOW_PRE, 0), min(z + config.WINDOW_POST, len(cal) - 1)
    return pd.DataFrame({"event_day": np.arange(lo - z, hi - z + 1),
                         "val": s.loc[cal[lo:hi + 1]].values})


EPISODE_STYLE = {
    "gulf_war_1990": ("#1f77b4", "Gulf War 1990"),
    "iran_sanctions_2018": ("#2ca02c", "Iran sanctions 2018"),
    "russia_ukraine_2022": ("#9467bd", "Russia–Ukraine 2022"),
    "twelve_day_war_2025": ("#ff7f0e", "Twelve-Day War 2025"),
    "iran_2026_campaign": ("#d62728", "2026 campaign"),
    "iran_2026_closure": ("#8c564b", "2026 Strait closure"),
}


def main():
    print("Extension B: futures term structure")
    c1 = fetch_fut("RCLC1", "c1")
    c4 = fetch_fut("RCLC4", "c4")
    wti = pd.read_csv(config.DATA_RAW / "raw_eia_wti.csv", index_col=0).iloc[:, 0]
    wti.index = pd.to_datetime(wti.index)

    front, front_src = load_front_month(c1)
    print(f"  front-month: {front_src}")
    spread = (c1 - c4).dropna()                 # >0 = backwardation (EIA, to 2024)
    basis = (wti - front).dropna()              # spot - front-month futures (full)

    # Per-episode: C1-C4 term spread (EIA, covered) and spot-futures basis (full).
    rows = []
    for key, trig in config.TRIGGERS.items():
        w = event_window(spread, trig["date"])
        b = event_window(basis, trig["date"])
        if w.empty and b.empty:
            continue
        rows.append({
            "episode": key,
            "spread_pre": round(w.loc[w.event_day <= 0, "val"].mean(), 2) if not w.empty else np.nan,
            "spread_post": round(w.loc[w.event_day > 0, "val"].mean(), 2) if not w.empty else np.nan,
            "basis_pre": round(b.loc[b.event_day <= 0, "val"].mean(), 2) if not b.empty else np.nan,
            "basis_post": round(b.loc[b.event_day > 0, "val"].mean(), 2) if not b.empty else np.nan,
        })
    table = pd.DataFrame(rows)
    config.TABLES.mkdir(parents=True, exist_ok=True)
    table.to_csv(config.TABLES / "table9_term_structure.csv", index=False)
    (config.TABLES / "table9_term_structure.txt").write_text(table.to_string(index=False))
    print(table.to_string(index=False))

    config.FIGURES.mkdir(parents=True, exist_ok=True)

    # Figure 10: C1-C4 term-structure spread (EIA-covered episodes).
    fig, ax = plt.subplots(figsize=(10, 6))
    for key in COVERED:
        w = event_window(spread, config.TRIGGERS[key]["date"])
        if not w.empty:
            ax.plot(w.event_day, w.val, color=EPISODE_STYLE[key][0], lw=1.8,
                    label=EPISODE_STYLE[key][1])
    ax.axhline(0, color="0.4", lw=1.0); ax.axvline(0, color="0.5", lw=0.9, ls=":")
    ax.set_xlabel("Event time (trading days; 0 = trigger)")
    ax.set_ylabel("WTI C1 − C4 spread ($/bbl)   ▲ backwardation / ▼ contango")
    ax.set_title("Futures term structure around conflicts (WTI front − 4th contract)")
    ax.legend(loc="upper left", fontsize=9)
    fig.text(0.01, 0.01, "Source: EIA (WTI futures RCLC1/RCLC4). EIA futures end "
             "2024-04; 2025/2026 not covered.", fontsize=7.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig10_term_structure.{ext}", bbox_inches="tight")
    plt.close(fig)

    # Figure 11: spot - front-month futures basis (all covered episodes).
    fig, ax = plt.subplots(figsize=(10, 6))
    for key, (color, label) in EPISODE_STYLE.items():
        b = event_window(basis, config.TRIGGERS[key]["date"])
        if not b.empty:
            ax.plot(b.event_day, b.val, color=color, lw=1.8, label=label)
    ax.axhline(0, color="0.4", lw=1.0); ax.axvline(0, color="0.5", lw=0.9, ls=":")
    ax.set_xlabel("Event time (trading days; 0 = trigger)")
    ax.set_ylabel("WTI spot − front-month futures ($/bbl)   ▲ backwardation")
    ax.set_title("Spot vs futures around conflicts (WTI spot − front-month)")
    ax.legend(loc="upper left", fontsize=9)
    fig.text(0.01, 0.01, f"Source: EIA spot RWTC; futures {front_src}. Authors' "
             "calculations.", fontsize=7.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig11_spot_vs_futures.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Saved table9_term_structure, fig10_term_structure, fig11_spot_vs_futures")


if __name__ == "__main__":
    main()
