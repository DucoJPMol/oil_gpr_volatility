"""
02_event_windows.py
Phase 3: build the event windows for the five (here six, two 2026 variants)
geopolitical triggers.

For each trigger it:
  - finds day zero: the first Brent trading day on or after the trigger date;
  - extracts event time from -WINDOW_PRE to +WINDOW_POST trading days, carrying
    Brent and WTI realized vol, OVX, GPRD (aligned to the trading calendar),
    and log returns;
  - computes the pre-event baseline (mean and SD of Brent realized vol over the
    BASELINE_WINDOW trading days before day zero);
  - flags the 2026 episode as truncated if it lacks a full post window.

Output:
  data/processed/processed_event_panel.csv   one tidy row per episode-and-event-day
  data/processed/processed_baselines.csv      per-episode baseline mean / SD / threshold

Usage, from the project root:
    python code/02_event_windows.py   (run 01_get_and_clean_data.py first)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


def load_panel() -> pd.DataFrame:
    path = config.DATA_PROCESSED / "processed_daily_panel.csv"
    if not path.exists():
        sys.exit("processed_daily_panel.csv not found. Run 01_get_and_clean_data.py first.")
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def trading_calendar(panel: pd.DataFrame) -> pd.DatetimeIndex:
    """The Brent trading-day calendar: dates Brent actually has a price. Event
    time is counted in these days, and GPRD is aligned onto them."""
    return panel.index[panel["brent"].notna()]


def day_zero(cal: pd.DatetimeIndex, trigger_date: str) -> pd.Timestamp | None:
    """First trading day on or after the trigger's calendar date."""
    trig = pd.Timestamp(trigger_date)
    after = cal[cal >= trig]
    return after[0] if len(after) else None


def build_episode(key: str, trig: dict, panel: pd.DataFrame,
                  cal: pd.DatetimeIndex, gprd_on_cal: pd.Series) -> tuple[pd.DataFrame, dict]:
    """Return the event-window rows and the baseline summary for one episode."""
    d0 = day_zero(cal, trig["date"])
    if d0 is None:
        print(f"  {key:22s} no trading day on/after {trig['date']} (skipped)")
        return pd.DataFrame(), {}

    z = cal.get_loc(d0)                       # integer position of day zero on the calendar
    lo = max(z - config.WINDOW_PRE, 0)
    hi = min(z + config.WINDOW_POST, len(cal) - 1)
    win_dates = cal[lo: hi + 1]
    event_days = np.arange(lo - z, hi - z + 1)

    rows = panel.loc[win_dates, ["brent", "wti", "ovx", "brent_ret", "wti_ret",
                                 "brent_vol", "wti_vol"]].copy()
    rows.insert(0, "event_day", event_days)
    rows.insert(0, "episode", key)
    rows["gprd"] = gprd_on_cal.reindex(win_dates).values

    # Pre-event baseline on Brent realized vol over BASELINE_WINDOW days before day zero.
    base_lo = max(z - config.BASELINE_WINDOW, 0)
    baseline_vol = panel.loc[cal[base_lo: z], "brent_vol"].dropna()
    base_mean = baseline_vol.mean()
    base_sd = baseline_vol.std()
    threshold = base_mean + config.PERSISTENCE_SD_MULTIPLE * base_sd

    post_available = int(event_days.max())
    truncated = post_available < config.WINDOW_POST

    summary = {
        "episode": key,
        "label": trig["label"],
        "trigger_date": trig["date"],
        "day_zero": d0.date().isoformat(),
        "baseline_mean_vol": base_mean,
        "baseline_sd_vol": base_sd,
        "revert_threshold": threshold,
        "post_days_available": post_available,
        "truncated": truncated,
    }
    flag = "  [TRUNCATED]" if truncated else ""
    print(f"  {key:22s} day0 {d0.date()}  baseline {base_mean:5.1f}% (+1SD={threshold:5.1f}%)  "
          f"post {post_available}/{config.WINDOW_POST}{flag}")
    return rows, summary


def main() -> None:
    panel = load_panel()
    cal = trading_calendar(panel)
    # GPRD is daily on every calendar day; carry the last value onto trading days.
    gprd_on_cal = panel["gprd"].reindex(cal).ffill()

    print(f"Phase 3: event windows ({config.WINDOW_PRE} before to {config.WINDOW_POST} after)")
    print(f"Trading calendar: {len(cal)} days, {cal.min().date()} to {cal.max().date()}")

    all_rows, summaries = [], []
    for key, trig in config.TRIGGERS.items():
        rows, summary = build_episode(key, trig, panel, cal, gprd_on_cal)
        if len(rows):
            all_rows.append(rows)
            summaries.append(summary)

    event_panel = pd.concat(all_rows).reset_index().rename(columns={"index": "date"})
    baselines = pd.DataFrame(summaries)

    ep_path = config.DATA_PROCESSED / "processed_event_panel.csv"
    bl_path = config.DATA_PROCESSED / "processed_baselines.csv"
    event_panel.to_csv(ep_path, index=False)
    baselines.to_csv(bl_path, index=False)
    print()
    print(f"Saved {ep_path.relative_to(config.PROJECT_ROOT)}  ({len(event_panel)} rows, "
          f"{event_panel['episode'].nunique()} episodes)")
    print(f"Saved {bl_path.relative_to(config.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
