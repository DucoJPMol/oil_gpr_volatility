"""
03_persistence.py
Phase 4: the two persistence metrics.

Metric 1 (days to revert): for each episode, the threshold is the pre-event
baseline mean + 1 SD of Brent realized vol. We find the first trading day after
day zero where realized vol drops below the threshold and *stays* below for
REVERT_CONSECUTIVE_DAYS trading days in a row, and report that day's offset.
For an episode still elevated at the data cutoff, we report it as censored
("at least N days").

Metric 2 (GARCH persistence): GARCH(1,1) on daily Brent log returns. We report
omega, alpha, beta and the sum alpha+beta (the persistence number), confirm
alpha+beta < 1, save the conditional volatility series, and run Ljung-Box
diagnostics on the standardised residuals and their squares.

Output:
  tables/table2_days_to_revert.csv
  tables/table3_garch.csv
  data/processed/processed_garch_condvol.csv

Usage, from the project root:
    python code/03_persistence.py   (run 01 and 02 first)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


def load_inputs():
    panel_path = config.DATA_PROCESSED / "processed_daily_panel.csv"
    base_path = config.DATA_PROCESSED / "processed_baselines.csv"
    if not panel_path.exists() or not base_path.exists():
        sys.exit("Missing processed inputs. Run 01_get_and_clean_data.py and "
                 "02_event_windows.py first.")
    panel = pd.read_csv(panel_path, parse_dates=["date"]).set_index("date").sort_index()
    baselines = pd.read_csv(base_path, parse_dates=["trigger_date", "day_zero"])
    return panel, baselines


# ----------------------------------------------------------------------
# Metric 1: days to revert
# ----------------------------------------------------------------------
def days_to_revert(vol_after: pd.Series, threshold: float,
                   consec: int) -> tuple[int | None, bool]:
    """vol_after is Brent realized vol on trading days from day zero (offset 0)
    onward. Return (offset of the first day that begins a run of `consec`
    consecutive days below threshold, censored_flag). If no such run exists,
    return (last available offset, True) to mark it as still elevated."""
    below = (vol_after < threshold).to_numpy()
    n = len(below)
    for i in range(n - consec + 1):
        if below[i:i + consec].all():
            return i, False          # offset i (trading days after day zero)
    return n - 1, True               # never reverted within the available data


def metric1(panel: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    cal = panel.index[panel["brent"].notna()]
    rows = []
    print("Metric 1: days to revert "
          f"(threshold = baseline mean + {config.PERSISTENCE_SD_MULTIPLE} SD, "
          f"stay below {config.REVERT_CONSECUTIVE_DAYS} days)")
    for _, b in baselines.iterrows():
        d0 = pd.Timestamp(b["day_zero"])
        if d0 not in cal:
            continue
        z = cal.get_loc(d0)
        vol_after = panel.loc[cal[z:], "brent_vol"].dropna()
        offset, censored = days_to_revert(
            vol_after, b["revert_threshold"], config.REVERT_CONSECUTIVE_DAYS)
        rows.append({
            "episode": b["episode"],
            "label": b["label"],
            "day_zero": d0.date().isoformat(),
            "threshold_vol": round(b["revert_threshold"], 2),
            "days_to_revert": offset,
            "censored": censored,
        })
        tag = f">= {offset} (still elevated at cutoff)" if censored else f"{offset}"
        print(f"  {b['episode']:22s} days_to_revert = {tag}")
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Metric 2: GARCH(1,1) persistence
# ----------------------------------------------------------------------
def metric2(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    from arch import arch_model
    from statsmodels.stats.diagnostic import acorr_ljungbox

    # arch fits best on percent returns; this only rescales omega, not alpha/beta.
    r = (panel["brent_ret"].dropna() * 100.0)
    res = arch_model(r, mean="Constant", vol="Garch", p=1, q=1, dist="normal").fit(disp="off")

    omega = res.params["omega"]
    alpha = res.params["alpha[1]"]
    beta = res.params["beta[1]"]
    persistence = alpha + beta

    std_resid = res.resid / res.conditional_volatility
    lb = acorr_ljungbox(std_resid.dropna(), lags=[10], return_df=True)
    lb2 = acorr_ljungbox((std_resid.dropna() ** 2), lags=[10], return_df=True)

    print()
    print("Metric 2: GARCH(1,1) on daily Brent log returns")
    print(f"  omega={omega:.5f}  alpha={alpha:.4f}  beta={beta:.4f}  "
          f"alpha+beta={persistence:.4f}  ({'stationary' if persistence < 1 else 'NON-stationary'})")
    print(f"  Ljung-Box(10) std resid p={lb['lb_pvalue'].iloc[0]:.3f}  "
          f"squared p={lb2['lb_pvalue'].iloc[0]:.3f}")

    table = pd.DataFrame({
        "parameter": ["omega", "alpha", "beta", "alpha+beta",
                      "loglik", "n_obs", "lb10_resid_p", "lb10_sq_resid_p"],
        "value": [omega, alpha, beta, persistence,
                  res.loglikelihood, int(res.nobs),
                  lb["lb_pvalue"].iloc[0], lb2["lb_pvalue"].iloc[0]],
    })
    # Conditional vol back to a daily-decimal, annualised % scale to match realized vol.
    condvol = (res.conditional_volatility / 100.0) * np.sqrt(config.TRADING_DAYS_PER_YEAR) * 100.0
    condvol.name = "garch_condvol_ann_pct"
    return table, condvol


def main() -> None:
    config.TABLES.mkdir(parents=True, exist_ok=True)
    panel, baselines = load_inputs()

    revert = metric1(panel, baselines)
    garch_table, condvol = metric2(panel)

    revert_path = config.TABLES / "table2_days_to_revert.csv"
    garch_path = config.TABLES / "table3_garch.csv"
    condvol_path = config.DATA_PROCESSED / "processed_garch_condvol.csv"
    revert.to_csv(revert_path, index=False)
    garch_table.to_csv(garch_path, index=False)
    condvol.to_csv(condvol_path)
    print()
    print(f"Saved {revert_path.relative_to(config.PROJECT_ROOT)}")
    print(f"Saved {garch_path.relative_to(config.PROJECT_ROOT)}")
    print(f"Saved {condvol_path.relative_to(config.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
