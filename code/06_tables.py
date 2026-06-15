"""
06_tables.py
Phase 8: the tables.

  Table 1  summary statistics: mean, sd, min, max of returns and realized vol
           for Brent and WTI over the full sample.
  Table 2  event summary: trigger date, day zero, baseline vol, peak vol (and
           the day it peaks), days-to-revert, and whether the Strait was
           disrupted (from config; fill the coding sheet to populate it).
  Table 3  GARCH(1,1) estimates, formatted for the paper.

Each table is written as a csv plus a plain-text version that drops into the
paper. Regression/correlation results (Table 4) are produced by 04_regressions.py.

Usage, from the project root:
    python code/06_tables.py   (run 01-03 first; Table 3 needs 03)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


def load():
    p = config.DATA_PROCESSED
    panel = pd.read_csv(p / "processed_daily_panel.csv", parse_dates=["date"]).set_index("date")
    event = pd.read_csv(p / "processed_event_panel.csv", parse_dates=["date"])
    base = pd.read_csv(p / "processed_baselines.csv", parse_dates=["trigger_date", "day_zero"])
    return panel, event, base


def write(df: pd.DataFrame, n: int, name: str, index: bool = False) -> None:
    csv = config.TABLES / f"table{n}_{name}.csv"
    txt = config.TABLES / f"table{n}_{name}.txt"
    df.to_csv(csv, index=index)
    txt.write_text(df.to_string(index=index))
    print(f"  saved table{n}_{name}.csv / .txt")


# ----------------------------------------------------------------------
def table1_summary_stats(panel: pd.DataFrame) -> pd.DataFrame:
    spec = [("brent_ret", "Brent log return"), ("wti_ret", "WTI log return"),
            ("brent_vol", "Brent realized vol (%)"), ("wti_vol", "WTI realized vol (%)")]
    rows = []
    for col, label in spec:
        s = panel[col].dropna()
        rows.append({
            "series": label, "n": len(s),
            "mean": round(s.mean(), 5), "sd": round(s.std(), 5),
            "min": round(s.min(), 4), "max": round(s.max(), 4),
        })
    return pd.DataFrame(rows)


def table2_event_summary(event: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    revert = pd.read_csv(config.TABLES / "table2_days_to_revert.csv")
    rbykey = revert.set_index("episode")
    rows = []
    for _, b in base.iterrows():
        key = b["episode"]
        g = event[event["episode"] == key]
        ipk = g["brent_vol"].idxmax()
        peak_vol = g.loc[ipk, "brent_vol"]
        peak_day = int(g.loc[ipk, "event_day"])
        dr = rbykey.loc[key] if key in rbykey.index else {}
        days = dr.get("days_to_revert", np.nan)
        censored = bool(dr.get("censored", False))
        rows.append({
            "episode": key,
            "label": b["label"],
            "trigger_date": b["trigger_date"].date().isoformat(),
            "day_zero": b["day_zero"].date().isoformat(),
            "baseline_vol_%": round(b["baseline_mean_vol"], 1),
            "peak_vol_%": round(peak_vol, 1),
            "peak_day": peak_day,
            "days_to_revert": (f">={int(days)}" if censored else int(days)),
            "strait_disrupted": config.TRIGGERS[key]["strait_disrupted"],
            "supply_disruption": config.TRIGGERS[key]["supply_disruption"],
            "country_index": config.TRIGGERS[key]["country"],
        })
    return pd.DataFrame(rows)


def table3_garch_formatted() -> pd.DataFrame:
    raw = pd.read_csv(config.TABLES / "table3_garch.csv")
    val = dict(zip(raw["parameter"], raw["value"]))
    order = [("omega", "omega (constant)"), ("alpha", "alpha (ARCH)"),
             ("beta", "beta (GARCH)"), ("alpha+beta", "alpha+beta (persistence)"),
             ("loglik", "log-likelihood"), ("n_obs", "observations"),
             ("lb10_resid_p", "Ljung-Box(10) resid p"),
             ("lb10_sq_resid_p", "Ljung-Box(10) sq resid p")]
    rows = [{"parameter": label, "estimate": round(val[k], 4)} for k, label in order]
    return pd.DataFrame(rows)


def main():
    config.TABLES.mkdir(parents=True, exist_ok=True)
    panel, event, base = load()
    print("Phase 8: tables")

    t1 = table1_summary_stats(panel)
    print(t1.to_string(index=False))
    write(t1, 1, "summary_stats")

    t2 = table2_event_summary(event, base)
    print()
    print(t2.to_string(index=False))
    write(t2, 2, "event_summary")

    if (config.TABLES / "table3_garch.csv").exists():
        t3 = table3_garch_formatted()
        write(t3, 3, "garch_formatted")


if __name__ == "__main__":
    main()
