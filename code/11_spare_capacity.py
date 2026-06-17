"""
11_spare_capacity.py
Extension D (global buffer): OPEC spare capacity and oil volatility.

OPEC spare capacity is the world's shock absorber for oil supply disruptions: if
it is ample, OPEC can replace lost barrels and a scare fades; if it is thin, a
disruption cannot be offset and volatility persists. This is the cleaner buffer
measure for geopolitical episodes than US inventories (which are confounded by
demand shocks, see 10_reserves.py).

Series (EIA STEO, monthly):
  COPS_OPEC  OPEC Total Spare Crude Oil Production Capacity (million bbl/day)
  COPS_SA    Saudi Arabia Spare Crude Oil Production Capacity

Output:
  data/raw/raw_steo_spare.csv
  tables/table11_spare_capacity.csv / .txt
  figures/fig15_spare_capacity_vs_vol.png / .pdf

Usage (needs EIA_API_KEY):
    python code/11_spare_capacity.py   (run 01 first)
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


def fetch_steo(series_id: str) -> pd.Series:
    raw = config.DATA_RAW / "raw_steo_spare.csv"
    if raw.exists():
        s = pd.read_csv(raw, index_col=0).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        return s
    if not config.EIA_API_KEY:
        sys.exit("EIA_API_KEY is not set (needed for STEO spare capacity).")
    url = "https://api.eia.gov/v2/steo/data/"
    rows, offset = [], 0
    while True:
        params = {"api_key": config.EIA_API_KEY, "frequency": "monthly", "data[0]": "value",
                  "facets[seriesId][]": series_id, "sort[0][column]": "period",
                  "sort[0][direction]": "asc", "offset": offset, "length": 5000}
        page = requests.get(url, params=params, headers=HEADERS, timeout=60).json()["response"]["data"]
        rows.extend(page)
        if len(page) < 5000:
            break
        offset += 5000
    s = pd.to_numeric(pd.Series({pd.Timestamp(d["period"]): d["value"] for d in rows},
                                dtype="float64"), errors="coerce").dropna().sort_index()
    s.to_csv(raw, header=[series_id])
    print(f"  {series_id} {len(s)} obs {s.index.min().date()} to {s.index.max().date()}")
    return s


def main():
    print("Extension D (global buffer): OPEC spare capacity")
    spare = fetch_steo("COPS_OPEC")          # million bbl/day, monthly

    panel = pd.read_csv(config.DATA_PROCESSED / "processed_daily_panel.csv",
                        parse_dates=["date"]).set_index("date")
    vol_m = panel["brent_vol"].resample("MS").mean()     # monthly mean realized vol
    df = pd.concat([spare.rename("spare"), vol_m.rename("vol")], axis=1).dropna()
    r = df["spare"].corr(df["vol"])
    print(f"  corr(OPEC spare capacity, realized vol) = {r:.3f}  "
          f"(negative => thin spare capacity goes with high vol), n={len(df)}")
    lo, hi = spare.quantile(1/3), spare.quantile(2/3)
    print(f"  mean vol when spare thin (<{lo:.1f} mb/d) = "
          f"{df.loc[df.spare < lo, 'vol'].mean():.1f}%  vs ample (>{hi:.1f}) = "
          f"{df.loc[df.spare > hi, 'vol'].mean():.1f}%")

    # Per-episode spare capacity at the trigger month.
    rows = []
    revert = pd.read_csv(config.TABLES / "table2_days_to_revert.csv").set_index("episode") \
        if (config.TABLES / "table2_days_to_revert.csv").exists() else None
    for key, trig in config.TRIGGERS.items():
        mo = pd.Timestamp(trig["date"]).to_period("M").to_timestamp()
        if mo < spare.index.min() or mo > spare.index.max():
            continue
        i = spare.index.get_indexer([mo], method="nearest")[0]
        sc = spare.iloc[i]
        pct = round((spare < sc).mean() * 100)        # percentile vs history
        dtr = ""
        if revert is not None and key in revert.index:
            d = revert.loc[key]
            dtr = f">={int(d['days_to_revert'])}" if d["censored"] else int(d["days_to_revert"])
        rows.append({"episode": key, "trigger_month": mo.date().isoformat(),
                     "opec_spare_mbd": round(sc, 2), "spare_percentile": pct,
                     "days_to_revert": dtr})
    table = pd.DataFrame(rows)
    config.TABLES.mkdir(parents=True, exist_ok=True)
    table.to_csv(config.TABLES / "table11_spare_capacity.csv", index=False)
    (config.TABLES / "table11_spare_capacity.txt").write_text(table.to_string(index=False))
    print(table.to_string(index=False))

    # Figure 15: OPEC spare capacity vs realized vol, episodes marked.
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    s = spare.loc["1995":]
    ax1.fill_between(s.index, 0, s, color="#2ca02c", alpha=0.25)
    ax1.plot(s.index, s, color="#2ca02c", lw=1.2, label="OPEC spare capacity (mb/d)")
    ax1.set_ylabel("OPEC spare capacity (million bbl/day)", color="#2ca02c")
    ax1.tick_params(axis="y", labelcolor="#2ca02c")
    ax1.set_xlabel("Year")
    ax2 = ax1.twinx(); ax2.grid(False)
    v = panel["brent_vol"].loc["1995":].dropna()
    ax2.plot(v.index, v, color="#ff7f0e", lw=0.6, alpha=0.8, label="Brent realized vol")
    ax2.set_ylabel("Brent realized vol (%, annualised)", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")
    for key, trig in config.TRIGGERS.items():
        t = pd.Timestamp(trig["date"])
        if t >= pd.Timestamp("1995-01-01"):
            ax1.axvline(t, color="0.5", lw=0.8, ls="--")
    ax1.set_title("OPEC spare capacity and Brent realized volatility, 1995–2026")
    ax1.legend(loc="upper right", fontsize=8)
    fig.text(0.01, 0.01, "Source: EIA STEO (COPS_OPEC), Brent realized vol. Dashed lines = "
             "episode triggers. Authors' calculations.", fontsize=7.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig15_spare_capacity_vs_vol.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Saved table11_spare_capacity and fig15_spare_capacity_vs_vol")


if __name__ == "__main__":
    main()
