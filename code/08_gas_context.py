"""
08_gas_context.py
Extension C: the gas dimension of conflict-driven volatility.

The 2022 Russia-Ukraine shock was primarily a *gas* event, so this script adds a
gas view for context: it pulls Henry Hub natural-gas spot from EIA, builds gas
realized volatility with the same 21-day method, and compares the oil and gas
volatility response around each episode (especially Russia 2022). It feeds the
write-up in output/global_unrest_gas.md.

Data note: Henry Hub is the US benchmark and is what EIA serves; the European TTF
benchmark — where the 2022 Russian gas shock actually landed hardest — is not on
EIA, so Henry Hub understates the European gas disruption. This is a documented
gap, not a result.

Output:
  data/raw/raw_eia_gas.csv
  tables/table8_gas_vs_oil.csv / .txt
  figures/fig9_oil_vs_gas_russia.png / .pdf

Usage, from the project root (needs EIA_API_KEY):
    python code/08_gas_context.py   (run 01 first for the oil panel)
"""

import io
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

GAS_SERIES = "RNGWHHD"   # Henry Hub Natural Gas Spot Price ($/MMBtu), daily
GAS_ROUTE = "natural-gas/pri/fut"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


def fetch_gas(refresh: bool = False) -> pd.Series:
    raw = config.DATA_RAW / "raw_eia_gas.csv"
    if raw.exists() and not refresh:
        s = pd.read_csv(raw, index_col=0).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        return s
    if not config.EIA_API_KEY:
        sys.exit("EIA_API_KEY is not set (needed to download Henry Hub gas).")
    url = f"https://api.eia.gov/v2/{GAS_ROUTE}/data/"
    rows, offset = [], 0
    while True:
        params = {"api_key": config.EIA_API_KEY, "frequency": "daily",
                  "data[0]": "value", "facets[series][]": GAS_SERIES,
                  "start": "1997-01-01", "end": config.DATA_CUTOFF,
                  "sort[0][column]": "period", "sort[0][direction]": "asc",
                  "offset": offset, "length": 5000}
        r = requests.get(url, params=params, headers=HEADERS, timeout=60)
        r.raise_for_status()
        page = r.json()["response"]["data"]
        rows.extend(page)
        if len(page) < 5000:
            break
        offset += 5000
    s = pd.Series({pd.Timestamp(d["period"]): d["value"] for d in rows}, dtype="float64")
    s = pd.to_numeric(s, errors="coerce").dropna().sort_index()
    s.to_csv(raw, header=[GAS_SERIES])
    print(f"  gas {GAS_SERIES} {len(s)} obs {s.index.min().date()} to {s.index.max().date()} "
          f"(downloaded {date.today().isoformat()})")
    return s


def realized_vol(price: pd.Series) -> pd.Series:
    p = price.where(price > 0)
    ret = np.log(p / p.shift(1))
    return ret.rolling(config.VOL_WINDOW, min_periods=config.VOL_WINDOW).std() \
        * np.sqrt(config.TRADING_DAYS_PER_YEAR) * 100.0


def load_ttf() -> pd.Series | None:
    """European TTF gas, hand-downloaded from investing.com (Dutch TTF Natural
    Gas Futures) to data/raw/raw_ttf.csv. None if not present."""
    path = config.DATA_RAW / "raw_ttf.csv"
    if not path.exists():
        return None
    m = pd.read_csv(path, encoding="utf-8-sig")
    m.columns = [c.strip().lstrip("﻿").lower() for c in m.columns]
    dcol = next(c for c in m.columns if c in ("date", "period"))
    ccol = next(c for c in m.columns if c in ("price", "close", "adj close", "value"))
    vals = pd.to_numeric(m[ccol].astype(str).str.replace(",", ""), errors="coerce")
    return pd.Series(vals.values, index=pd.to_datetime(m[dcol], errors="coerce")).dropna().sort_index()


def window(vol: pd.Series, trigger: str) -> pd.DataFrame:
    cal = vol.dropna().index
    trig = pd.Timestamp(trigger)
    after = cal[cal >= trig]
    # No coverage if the series starts well after the trigger (e.g. gas pre-1997).
    if not len(after) or (after[0] - trig).days > 7:
        return pd.DataFrame()
    z = cal.get_loc(after[0])
    lo, hi = max(z - config.WINDOW_PRE, 0), min(z + config.WINDOW_POST, len(cal) - 1)
    days = np.arange(lo - z, hi - z + 1)
    return pd.DataFrame({"event_day": days, "vol": vol.loc[cal[lo:hi + 1]].values})


def main():
    gas = fetch_gas()
    gas_vol = realized_vol(gas)
    ttf = load_ttf()
    ttf_vol = realized_vol(ttf) if ttf is not None else None
    if ttf is not None:
        print(f"  TTF (European gas) loaded: {len(ttf)} obs to {ttf.index.max().date()}")
    panel = pd.read_csv(config.DATA_PROCESSED / "processed_daily_panel.csv",
                        parse_dates=["date"]).set_index("date")
    oil_vol = panel["brent_vol"]

    # Peak oil vs gas vol per episode (gas only covers episodes from 1997 on).
    rows = []
    for key, trig in config.TRIGGERS.items():
        ow, gw = window(oil_vol, trig["date"]), window(gas_vol, trig["date"])
        if ow.empty or gw.empty:
            continue
        row = {"episode": key,
               "oil_peak_vol_%": round(ow["vol"].max(), 1),
               "gas_peak_vol_%": round(gw["vol"].max(), 1),
               "gas_over_oil": round(gw["vol"].max() / ow["vol"].max(), 2)}
        if ttf_vol is not None:
            tw = window(ttf_vol, trig["date"])
            if not tw.empty:
                row["ttf_peak_vol_%"] = round(tw["vol"].max(), 1)
                row["ttf_over_oil"] = round(tw["vol"].max() / ow["vol"].max(), 2)
        rows.append(row)
    table = pd.DataFrame(rows)
    config.TABLES.mkdir(parents=True, exist_ok=True)
    table.to_csv(config.TABLES / "table8_gas_vs_oil.csv", index=False)
    (config.TABLES / "table8_gas_vs_oil.txt").write_text(table.to_string(index=False))
    print("Extension C: oil vs gas volatility around each episode")
    print(table.to_string(index=False))

    # Figure: oil vs gas realized vol around Russia 2022.
    ow = window(oil_vol, config.TRIGGERS["russia_ukraine_2022"]["date"])
    gw = window(gas_vol, config.TRIGGERS["russia_ukraine_2022"]["date"])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ow["event_day"], ow["vol"], color="#9467bd", lw=2.0, label="Brent oil vol")
    ax.plot(gw["event_day"], gw["vol"], color="#d62728", lw=2.0, label="Henry Hub gas vol (US)")
    if ttf_vol is not None:
        tw = window(ttf_vol, config.TRIGGERS["russia_ukraine_2022"]["date"])
        if not tw.empty:
            ax.plot(tw["event_day"], tw["vol"], color="#8c1a11", lw=2.0, ls="--",
                    label="TTF gas vol (Europe)")
    ax.axvline(0, color="0.4", lw=1.0, ls=":")
    ax.set_xlabel("Event time (trading days; 0 = 24 Feb 2022)")
    ax.set_ylabel("21-day realized volatility (%, annualised)")
    ax.set_title("Russia–Ukraine 2022: oil vs natural-gas volatility")
    ax.legend(loc="upper left", fontsize=9)
    note = ("Source: EIA (Brent RBRTE, Henry Hub RNGWHHD)"
            + (", investing.com (Dutch TTF)" if ttf_vol is not None else "")
            + ", authors' calculations."
            + ("" if ttf_vol is not None else " Henry Hub (US) understates the European TTF shock."))
    fig.text(0.01, 0.01, note, fontsize=7.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig9_oil_vs_gas_russia.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Saved table8_gas_vs_oil and fig9_oil_vs_gas_russia")


if __name__ == "__main__":
    main()
