"""
10_reserves.py
Extension D: oil reserves and volatility — what happens when buffers run low.

The idea: oil inventories and the SPR are the shock absorber. When they are
ample, a geopolitical scare can fade; when they are drawn dangerously low, the
market has no cushion and volatility stays high (and can re-spike). This script
pulls US crude inventories from EIA, builds a "reserve adequacy" measure
(deviation from the trailing 5-year average), flags dangerously-low periods, and
relates them to Brent realized volatility, plus a per-episode reserves context.

Series (EIA, weekly, route petroleum/stoc/wstk):
  WCESTUS1  commercial crude stocks excluding the SPR
  WCSSTUS1  SPR crude stocks
  WCRSTUS1  total crude stocks (commercial + SPR)

Output:
  data/raw/raw_eia_stocks_*.csv
  tables/table10_reserves_context.csv / .txt
  figures/fig13_reserves_vs_vol.png / .pdf
  figures/fig14_buffer_drawdown.png / .pdf

Usage (needs EIA_API_KEY):
    python code/10_reserves.py   (run 01 first)
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

STOCKS = {"commercial": "WCESTUS1", "spr": "WCSSTUS1", "total": "WCRSTUS1"}
ROUTE = "petroleum/stoc/wstk"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
LOW_SD = 1.0   # "dangerously low" = this many SD below the trailing 5-year mean


def fetch_stock(name: str, series_id: str) -> pd.Series:
    raw = config.DATA_RAW / f"raw_eia_stocks_{name}.csv"
    if raw.exists():
        s = pd.read_csv(raw, index_col=0).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        return s
    if not config.EIA_API_KEY:
        sys.exit("EIA_API_KEY is not set (needed for inventory data).")
    url = f"https://api.eia.gov/v2/{ROUTE}/data/"
    rows, offset = [], 0
    while True:
        params = {"api_key": config.EIA_API_KEY, "frequency": "weekly", "data[0]": "value",
                  "facets[series][]": series_id, "sort[0][column]": "period",
                  "sort[0][direction]": "asc", "offset": offset, "length": 5000}
        page = requests.get(url, params=params, headers=HEADERS, timeout=60).json()["response"]["data"]
        rows.extend(page)
        if len(page) < 5000:
            break
        offset += 5000
    s = pd.to_numeric(pd.Series({pd.Timestamp(d["period"]): d["value"] for d in rows},
                                dtype="float64"), errors="coerce").dropna().sort_index()
    s.to_csv(raw, header=[series_id])
    print(f"  {name:11s} {series_id} {len(s)} obs {s.index.min().date()} to {s.index.max().date()}")
    return s / 1000.0   # thousand barrels -> million barrels


def main():
    print("Extension D: oil reserves and volatility")
    com = fetch_stock("commercial", STOCKS["commercial"])
    spr = fetch_stock("spr", STOCKS["spr"])

    # Reserve adequacy: deviation of commercial stocks from a trailing 5-year
    # (260-week) mean, in SD units. "Dangerously low" when far below the band.
    roll = com.rolling(260, min_periods=104)
    adequacy = (com - roll.mean()) / roll.std()
    low = adequacy < -LOW_SD

    panel = pd.read_csv(config.DATA_PROCESSED / "processed_daily_panel.csv",
                        parse_dates=["date"]).set_index("date")
    vol = panel["brent_vol"]
    # Weekly realized vol (align to the stock weeks) for the correlation.
    vol_w = vol.reindex(com.index, method="nearest", tolerance=pd.Timedelta("4D"))
    corr = pd.concat([adequacy.rename("adeq"), vol_w.rename("vol")], axis=1).dropna()
    r = corr["adeq"].corr(corr["vol"])
    print(f"  corr(reserve adequacy, realized vol) = {r:.3f}  "
          f"(negative => low reserves go with high vol), n={len(corr)}")
    print(f"  mean vol when reserves low = {corr.loc[corr.adeq < -LOW_SD, 'vol'].mean():.1f}% "
          f"vs ample = {corr.loc[corr.adeq > LOW_SD, 'vol'].mean():.1f}%")

    # Per-episode reserves context.
    rows = []
    for key, trig in config.TRIGGERS.items():
        t = pd.Timestamp(trig["date"])
        if t < com.index.min() or t > com.index.max():
            continue
        i = com.index.get_indexer([t], method="nearest")[0]
        end = min(i + 12, len(com) - 1)        # ~12 weeks ~ 60 trading days
        rows.append({
            "episode": key,
            "commercial_mb": round(com.iloc[i], 1),
            "adequacy_sd": round(adequacy.iloc[i], 2),
            "dangerously_low": bool(adequacy.iloc[i] < -LOW_SD),
            "commercial_draw_mb": round(com.iloc[end] - com.iloc[i], 1),
            "spr_draw_mb": round(spr.iloc[min(spr.index.get_indexer([t], method='nearest')[0] + 12,
                                  len(spr) - 1)] - spr.iloc[spr.index.get_indexer([t], method='nearest')[0]], 1),
        })
    table = pd.DataFrame(rows)
    config.TABLES.mkdir(parents=True, exist_ok=True)
    table.to_csv(config.TABLES / "table10_reserves_context.csv", index=False)
    (config.TABLES / "table10_reserves_context.txt").write_text(table.to_string(index=False))
    print(table.to_string(index=False))

    config.FIGURES.mkdir(parents=True, exist_ok=True)
    # Figure 13: commercial stocks + 5yr mean, low-reserve shading, vs realized vol.
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    c = com.loc["1990":]
    ax1.plot(c.index, c, color="#1b5e9b", lw=1.0, label="Commercial crude stocks")
    ax1.plot(c.index, roll.mean().loc["1990":], color="0.5", lw=1.0, ls="--",
             label="Trailing 5-yr mean")
    lo = low.loc["1990":]
    ax1.fill_between(c.index, c.min(), c.max(), where=lo.reindex(c.index, fill_value=False),
                     color="#d62728", alpha=0.12, label="Dangerously low (<-1 SD)")
    ax1.set_ylabel("US commercial crude stocks (million bbl)")
    ax1.set_xlabel("Year")
    ax2 = ax1.twinx(); ax2.grid(False)
    ax2.plot(vol.loc["1990":].dropna().index, vol.loc["1990":].dropna(),
             color="#ff7f0e", lw=0.6, alpha=0.8, label="Brent realized vol")
    ax2.set_ylabel("Brent realized vol (%, annualised)", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")
    ax1.set_title("US oil inventories (red = dangerously low) and Brent realized volatility")
    h1, l1 = ax1.get_legend_handles_labels()
    ax1.legend(h1, l1, loc="upper left", fontsize=8)
    fig.text(0.01, 0.01, "Source: EIA (WCESTUS1), Brent realized vol. Authors' calculations.",
             fontsize=7.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig13_reserves_vs_vol.{ext}", bbox_inches="tight")
    plt.close(fig)

    # Figure 14: the total buffer (commercial + SPR) over time.
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(com.loc["1990":].index, com.loc["1990":], color="#1b5e9b", lw=1.0, label="Commercial")
    ax.plot(spr.loc["1990":].index, spr.loc["1990":], color="#2ca02c", lw=1.0, label="SPR")
    ax.plot(com.loc["1990":].index, (com + spr).loc["1990":], color="0.2", lw=1.2, label="Total buffer")
    ax.set_ylabel("Crude stocks (million bbl)")
    ax.set_xlabel("Year")
    ax.set_title("The US oil buffer: commercial inventories and the SPR")
    ax.legend(loc="upper left", fontsize=8)
    fig.text(0.01, 0.01, "Source: EIA (WCESTUS1, WCSSTUS1). Authors' calculations.",
             fontsize=7.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig14_buffer_drawdown.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Saved table10_reserves_context, fig13_reserves_vs_vol, fig14_buffer_drawdown")


if __name__ == "__main__":
    main()
