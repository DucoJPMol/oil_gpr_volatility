"""
04_regressions.py
Phase 5: supporting regressions and correlations.

  1. Contemporaneous correlation between GPRD and realized vol (and OVX if
     present), full sample and within each event window.
  2. Pooled event-window regression: Brent realized vol on standardised GPRD
     plus episode fixed effects, with Newey-West (HAC) standard errors.
  3. Local projections: regress Brent realized vol at horizon h on a GPRD shock
     at day zero (with lag controls and HAC SEs) for h = 0..60, to trace the
     impulse response and read off the half-life. (Figure 7 plots this.)

Output:
  tables/table4_correlations.csv
  tables/table4_event_regression.csv  (+ .txt with the full HAC summary)
  tables/table4_local_projection.csv

Usage, from the project root:
    python code/04_regressions.py   (run 01 and 02 first)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

HAC_LAGS = 10        # Newey-West lags for the pooled event regression
LP_HMAX = 60         # local-projection horizon (trading days)
LP_LAGS = 5          # lag controls in the local projection


def load():
    p = config.DATA_PROCESSED
    panel = pd.read_csv(p / "processed_daily_panel.csv", parse_dates=["date"]).set_index("date")
    event = pd.read_csv(p / "processed_event_panel.csv", parse_dates=["date"])
    return panel, event


# ----------------------------------------------------------------------
def correlations(panel: pd.DataFrame, event: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(sample, pair, a, b, frame):
        d = frame[[a, b]].dropna()
        if len(d) > 2:
            rows.append({"sample": sample, "pair": pair,
                         "correlation": round(d[a].corr(d[b]), 4), "n": len(d)})

    add("full_sample", "gprd~brent_vol", "gprd", "brent_vol", panel)
    add("full_sample", "gprd~wti_vol", "gprd", "wti_vol", panel)
    if panel["ovx"].notna().any():
        add("full_sample", "gprd~ovx", "gprd", "ovx", panel)
    add("event_windows_pooled", "gprd~brent_vol", "gprd", "brent_vol", event)
    for key, g in event.groupby("episode", sort=False):
        add(key, "gprd~brent_vol", "gprd", "brent_vol", g)

    out = pd.DataFrame(rows)
    print("Contemporaneous correlations (GPRD vs realized vol)")
    print(out.to_string(index=False))
    return out


def event_regression(event: pd.DataFrame):
    ev = event.dropna(subset=["brent_vol", "gprd"]).copy()
    ev["gprd_z"] = (ev["gprd"] - ev["gprd"].mean()) / ev["gprd"].std()
    model = smf.ols("brent_vol ~ gprd_z + C(episode)", data=ev).fit(
        cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    tidy = pd.DataFrame({
        "coef": model.params, "se": model.bse,
        "t": model.tvalues, "p": model.pvalues,
    }).round(4)
    print()
    print("Pooled event-window regression: brent_vol ~ gprd_z + episode FE "
          f"(HAC, {HAC_LAGS} lags)")
    print(f"  gprd_z coef = {model.params['gprd_z']:.3f} "
          f"(se {model.bse['gprd_z']:.3f}, p {model.pvalues['gprd_z']:.3g}), "
          f"n={int(model.nobs)}, R2={model.rsquared:.3f}")
    return model, tidy


def local_projection(panel: pd.DataFrame) -> pd.DataFrame:
    """y_{t+h} = a + b_h * gprd_z_t + lags of y and gprd_z + e, HAC SEs.
    b_h is the impulse response of realized vol to a 1-SD GPRD shock."""
    df = panel[["brent_vol", "gprd_z"]].dropna().copy()
    y, x = df["brent_vol"], df["gprd_z"]
    lagcols = {}
    for L in range(1, LP_LAGS + 1):
        lagcols[f"ylag{L}"] = y.shift(L)
        lagcols[f"xlag{L}"] = x.shift(L)
    base = pd.DataFrame({"x": x, **lagcols})
    regressors = ["x"] + list(lagcols.keys())

    rows = []
    for h in range(LP_HMAX + 1):
        d = base.copy()
        d["y"] = y.shift(-h)
        d = d.dropna()
        res = sm.OLS(d["y"], sm.add_constant(d[regressors])).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 5})
        rows.append({"horizon": h, "beta": res.params["x"], "se": res.bse["x"]})
    lp = pd.DataFrame(rows)
    lp["ci_low"] = lp["beta"] - 1.96 * lp["se"]
    lp["ci_high"] = lp["beta"] + 1.96 * lp["se"]
    peak = lp.loc[lp["beta"].idxmax()]
    print()
    print(f"Local projection: peak vol response {peak['beta']:.3f} at horizon "
          f"{int(peak['horizon'])} days (per 1-SD GPRD shock)")
    return lp.round(4)


def main():
    config.TABLES.mkdir(parents=True, exist_ok=True)
    panel, event = load()

    corr = correlations(panel, event)
    model, tidy = event_regression(event)
    lp = local_projection(panel)

    corr.to_csv(config.TABLES / "table4_correlations.csv", index=False)
    tidy.to_csv(config.TABLES / "table4_event_regression.csv")
    (config.TABLES / "table4_event_regression.txt").write_text(str(model.summary()))
    lp.to_csv(config.TABLES / "table4_local_projection.csv", index=False)
    print()
    print("Saved table4_correlations.csv, table4_event_regression.csv (+.txt), "
          "table4_local_projection.csv")


if __name__ == "__main__":
    main()
