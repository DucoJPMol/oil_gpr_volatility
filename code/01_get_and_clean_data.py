"""
01_get_and_clean_data.py
Phase 1 (get the data) and Phase 2 (clean and build the core series).

What it does, in order:
  1. Pulls the FRED oil and volatility series (Brent, WTI, OVX, VIX) straight
     from FRED's CSV endpoint and saves each raw pull to data/raw.
  2. Loads the hand-downloaded GPR monthly and daily files from data/raw.
  3. Parses every date to a proper datetime index, merges on a common daily
     index (outer join), and keeps only real observations (no gap filling).
  4. Computes daily log returns and the 21-day annualised realized volatility
     for Brent and WTI.
  5. Standardises the daily GPR (GPRD) to z-scores for later regressions.
  6. Saves the cleaned daily panel and the monthly GPR to data/processed,
     and prints sanity checks.

Why FRED is pulled with `requests` and not pandas-datareader: the installed
pandas is 3.x, which pandas-datareader 0.10 is not compatible with. FRED's
public CSV endpoint needs no API key and is more robust, so we use it directly.

Usage, from the project root:
    python code/01_get_and_clean_data.py
"""

import io
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# make config.py (in the same folder) importable however this is launched
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
START = "1985-01-01"   # well before the 1990 Gulf War; FRED trims to each series' real start
# FRED sits behind a WAF that blocks the default python-requests user-agent on
# larger queries, so we present a browser one.
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


# ----------------------------------------------------------------------
# Phase 1: pull the FRED series
# ----------------------------------------------------------------------
def _parse_fred_csv(text: str, series_id: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text), na_values=".")
    df.columns = ["date", series_id]           # observation_date, <series id>
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[series_id].dropna()


def _fetch_chunk(series_id: str, start: str, end: str, retries: int = 4) -> pd.Series:
    """One FRED CSV request for a date range, with retries on timeout/WAF."""
    params = {"id": series_id, "cosd": start, "coed": end}
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(FRED_CSV, params=params, headers=HEADERS, timeout=120)
            r.raise_for_status()
            if r.text.lstrip().startswith("<"):      # WAF/HTML challenge, not CSV
                raise ValueError("non-CSV response (WAF challenge / rate limit)")
            return _parse_fred_csv(r.text, series_id)
        except Exception as e:                       # noqa: BLE001 - retry on anything
            last = e
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"FRED fetch failed for {series_id} {start}..{end}: {last}")


def fetch_fred(series_id: str, start: str = START, end: str | None = None) -> pd.Series:
    """Download one FRED series as a dated pandas Series. Fetched in ~5-year
    chunks because FRED's gateway times out generating very long daily ranges;
    smaller windows return quickly and are concatenated. Missing days are '.'
    in the CSV and are dropped (we keep only real trading-day observations)."""
    end = end or date.today().isoformat()
    edges = pd.date_range(start=start, end=end, freq="5YS").union(
        pd.DatetimeIndex([start, end]))
    parts = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        parts.append(_fetch_chunk(series_id, lo.date().isoformat(), hi.date().isoformat()))
    s = pd.concat(parts)
    return s[~s.index.duplicated(keep="last")].sort_index()


def get_oil_and_vol(refresh: bool = False) -> dict[str, pd.Series]:
    """Return every FRED series in the config. Loads a cached raw pull from
    data/raw if present (so a flaky network does not block a re-run); pass
    refresh=True (or `--refresh` on the command line) to force a fresh download."""
    out = {}
    print("Phase 1: FRED series")
    for name, series_id in config.FRED_SERIES.items():
        raw_path = config.DATA_RAW / f"raw_fred_{name}.csv"
        if raw_path.exists() and not refresh:
            s = _parse_fred_csv(raw_path.read_text(), series_id)
            src = "cached"
        else:
            s = fetch_fred(series_id, end=config.DATA_CUTOFF)
            s.to_csv(raw_path, header=[series_id])
            src = f"downloaded {date.today().isoformat()}"
        print(f"  {name:6s} {series_id:14s} {len(s):>6d} obs  "
              f"{s.index.min().date()} to {s.index.max().date()}  ({src})")
        out[name] = s.rename(name)
    print()
    return out


# ----------------------------------------------------------------------
# Phase 1: load the hand-downloaded GPR files
# ----------------------------------------------------------------------
def load_gpr_daily() -> pd.Series:
    """Daily GPR (GPRD) from the Caldara-Iacoviello daily file."""
    path = config.DATA_RAW / config.GPR_DAILY_FILE
    df = pd.read_excel(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    s = df.dropna(subset=["date"]).set_index("date")["GPRD"].dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.rename("gprd")


def load_gpr_monthly() -> pd.DataFrame:
    """Monthly GPR plus the Russia country index (Iran is not in this export)."""
    path = config.DATA_RAW / config.GPR_MONTHLY_FILE
    df = pd.read_excel(path)
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = df.dropna(subset=["month"]).set_index("month")
    keep = [c for c in ["GPR", "GPRT", "GPRA", "GPRC_RUS"] if c in df.columns]
    out = df[keep].dropna(how="all").sort_index()
    out.columns = [c.lower() for c in out.columns]
    return out


# ----------------------------------------------------------------------
# Phase 2: returns and realized volatility
# ----------------------------------------------------------------------
def log_returns(price: pd.Series) -> pd.Series:
    """Daily log returns r = ln(P_t / P_{t-1}) on actual trading days only."""
    return np.log(price / price.shift(1))


def realized_vol(returns: pd.Series) -> pd.Series:
    """21-day rolling realized volatility, annualised and in percent:
    rolling std of daily log returns * sqrt(252) * 100."""
    rstd = returns.rolling(config.VOL_WINDOW, min_periods=config.VOL_WINDOW).std()
    return rstd * np.sqrt(config.TRADING_DAYS_PER_YEAR) * 100.0


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


# ----------------------------------------------------------------------
# Build the merged daily panel
# ----------------------------------------------------------------------
def build_panel(fred: dict[str, pd.Series], gprd: pd.Series) -> pd.DataFrame:
    """Merge all daily series on an outer join, then add returns and vol."""
    print("Phase 2: building the core daily series")

    # Outer join keeps every date any series has data, so we can see coverage.
    panel = pd.concat([fred["brent"], fred["wti"], fred["ovx"], fred["vix"], gprd],
                      axis=1).sort_index()

    # Returns and realized vol are computed on each price's own trading days.
    panel["brent_ret"] = log_returns(panel["brent"])
    panel["wti_ret"] = log_returns(panel["wti"])
    panel["brent_vol"] = realized_vol(panel["brent_ret"])
    panel["wti_vol"] = realized_vol(panel["wti_ret"])

    # Standardise GPRD over the full sample for the regressions.
    panel["gprd_z"] = zscore(panel["gprd"])

    # Respect the agreed data cutoff for the still-running 2026 episode.
    panel = panel.loc[:config.DATA_CUTOFF]
    panel.index.name = "date"
    return panel


def sanity_checks(panel: pd.DataFrame) -> None:
    print()
    print("Sanity checks")
    for col in ["brent_ret", "wti_ret"]:
        r = panel[col].dropna()
        print(f"  {col:9s} n={len(r):>6d}  mean={r.mean():+.5f}  std={r.std():.5f}  "
              f"min={r.min():+.3f}  max={r.max():+.3f}")
    for col in ["brent_vol", "wti_vol"]:
        v = panel[col].dropna()
        print(f"  {col:9s} n={len(v):>6d}  mean={v.mean():6.2f}%  "
              f"min={v.min():5.2f}%  max={v.max():6.2f}%")

    # Hand-verify one realized-vol value against a direct numpy computation.
    v = panel["brent_vol"].dropna()
    if len(v):
        ts = v.index[-1]
        loc = panel.index.get_loc(ts)
        window = panel["brent_ret"].iloc[loc - config.VOL_WINDOW + 1: loc + 1]
        manual = window.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR) * 100.0
        print(f"  hand-check brent_vol on {ts.date()}: "
              f"code={v.iloc[-1]:.4f}  manual={manual:.4f}  "
              f"{'MATCH' if np.isclose(v.iloc[-1], manual) else 'MISMATCH'}")

    # Flag the real (not erroneous) negative WTI print on 2020-04-20.
    neg = panel.loc[panel["wti"] < 0, "wti"]
    if len(neg):
        print(f"  note: WTI negative on {[d.date().isoformat() for d in neg.index]} "
              f"(real, outside all event windows; left in)")


def main() -> None:
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    refresh = "--refresh" in sys.argv   # force a fresh FRED download, ignoring the cache

    fred = get_oil_and_vol(refresh=refresh)
    gprd = load_gpr_daily()
    gpr_monthly = load_gpr_monthly()
    print(f"GPR daily   {len(gprd):>6d} obs  {gprd.index.min().date()} to {gprd.index.max().date()}")
    print(f"GPR monthly {len(gpr_monthly):>6d} obs  {gpr_monthly.index.min().date()} to {gpr_monthly.index.max().date()}")
    print()

    panel = build_panel(fred, gprd)
    sanity_checks(panel)

    daily_path = config.DATA_PROCESSED / "processed_daily_panel.csv"
    monthly_path = config.DATA_PROCESSED / "processed_gpr_monthly.csv"
    panel.to_csv(daily_path)
    gpr_monthly.to_csv(monthly_path)
    print()
    print(f"Saved {daily_path.relative_to(config.PROJECT_ROOT)}  "
          f"({len(panel)} rows, {panel.index.min().date()} to {panel.index.max().date()})")
    print(f"Saved {monthly_path.relative_to(config.PROJECT_ROOT)}  ({len(gpr_monthly)} rows)")


if __name__ == "__main__":
    main()
