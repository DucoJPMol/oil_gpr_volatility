"""
07_robustness.py
Phase 6: robustness checks.

Re-runs the headline persistence result (days-to-revert per episode) for:
  - Brent and WTI, and
  - 10-, 21-, and 30-day realized-volatility windows,
so the reader can see the ranking of episodes is not an artifact of the price
series or the volatility window. (The days-to-revert metric searches the full
post-event series, so it does not depend on the +60 event-window length.)

The logic mirrors 01-03: log returns on each price's own trading days, a
60-day pre-event baseline, threshold = baseline mean + 1 SD, and reversion
measured from the spike onset.

Output: tables/table5_robustness_days_to_revert.csv / .txt

Usage, from the project root:
    python code/07_robustness.py   (run 01 first)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


def log_returns(price: pd.Series) -> pd.Series:
    p = price.where(price > 0)
    return np.log(p / p.shift(1))


def realized_vol(returns: pd.Series, window: int) -> pd.Series:
    rstd = returns.rolling(window, min_periods=window).std()
    return rstd * np.sqrt(config.TRADING_DAYS_PER_YEAR) * 100.0


def days_to_revert(vol_after: pd.Series, threshold: float, consec: int):
    """Spike-onset version, mirroring 03_persistence.py."""
    above = (vol_after >= threshold).to_numpy()
    below = ~above
    n = len(below)
    if not above.any():
        return 0, False
    onset = int(above.argmax())
    for i in range(onset, n - consec + 1):
        if below[i:i + consec].all():
            return i, False
    return n - 1, True


def revert_for(price: pd.Series, vol_window: int) -> dict:
    """days-to-revert per episode for one price series and one vol window."""
    cal = price.index                       # this series' own trading days
    vol = realized_vol(log_returns(price), vol_window)
    out = {}
    for key, trig in config.TRIGGERS.items():
        after = cal[cal >= pd.Timestamp(trig["date"])]
        if not len(after):
            out[key] = None
            continue
        d0 = after[0]
        z = cal.get_loc(d0)
        baseline = vol.loc[cal[max(z - config.BASELINE_WINDOW, 0):z]].dropna()
        threshold = baseline.mean() + config.PERSISTENCE_SD_MULTIPLE * baseline.std()
        vol_after = vol.loc[cal[z:]].dropna()
        offset, censored = days_to_revert(vol_after, threshold,
                                          config.REVERT_CONSECUTIVE_DAYS)
        out[key] = f">={offset}" if censored else offset
    return out


def main():
    config.TABLES.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(config.DATA_PROCESSED / "processed_daily_panel.csv",
                        parse_dates=["date"]).set_index("date")
    prices = {"brent": panel["brent"].dropna(), "wti": panel["wti"].dropna()}

    print("Phase 6: robustness — days-to-revert by price series and vol window")
    cols = {}
    for series in ["brent", "wti"]:
        for w in [10, 21, 30]:
            cols[f"{series}_{w}d"] = revert_for(prices[series], w)

    table = pd.DataFrame(cols)
    table.index.name = "episode"
    table = table.reset_index()
    # mark the locked baseline column (Brent, 21-day) for the reader
    table = table.rename(columns={"brent_21d": "brent_21d (main)"})

    print(table.to_string(index=False))
    table.to_csv(config.TABLES / "table5_robustness_days_to_revert.csv", index=False)
    (config.TABLES / "table5_robustness_days_to_revert.txt").write_text(
        table.to_string(index=False))
    print()
    print("Saved table5_robustness_days_to_revert.csv / .txt")


if __name__ == "__main__":
    main()
