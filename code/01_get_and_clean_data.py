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
EIA_DATA_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
START = "1985-01-01"   # well before the 1990 Gulf War; the source trims to each series' real start
# Present a browser user-agent; FRED's WAF blocks the default python-requests one.
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


# ----------------------------------------------------------------------
# Phase 1: pull the oil prices from the EIA v2 API
# ----------------------------------------------------------------------
def fetch_eia(series_id: str, start: str = START, end: str | None = None) -> pd.Series:
    """Download one EIA daily spot-price series (e.g. RBRTE, RWTC) as a dated
    pandas Series. The v2 API returns at most 5000 rows per call, so we page
    through with offset until a short page comes back."""
    if not config.EIA_API_KEY:
        sys.exit("EIA_API_KEY is not set. Get a free key at "
                 "https://www.eia.gov/opendata/register.php, then run:\n"
                 "    export EIA_API_KEY=your_key_here")
    end = end or date.today().isoformat()
    rows, offset, length = [], 0, 5000
    while True:
        params = {
            "api_key": config.EIA_API_KEY,
            "frequency": "daily",
            "data[0]": "value",
            "facets[series][]": series_id,
            "start": start, "end": end,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset, "length": length,
        }
        r = requests.get(EIA_DATA_URL, params=params, headers=HEADERS, timeout=60)
        if r.status_code == 403:
            sys.exit("EIA returned 403 (invalid or missing API key). Check $EIA_API_KEY.")
        r.raise_for_status()
        page = r.json()["response"]["data"]
        rows.extend(page)
        if len(page) < length:
            break
        offset += length
    s = pd.Series(
        {pd.Timestamp(d["period"]): d["value"] for d in rows},
        dtype="float64", name=series_id,
    )
    return pd.to_numeric(s, errors="coerce").dropna().sort_index()


# ----------------------------------------------------------------------
# Phase 1: pull the FRED series
# ----------------------------------------------------------------------
def _parse_fred_csv(text: str, series_id: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text), na_values=".")
    df.columns = ["date", series_id]           # observation_date, <series id>
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[series_id].dropna()


def _fetch_chunk(series_id: str, start: str, end: str,
                 retries: int = 4, timeout: int = 120) -> pd.Series:
    """One FRED CSV request for a date range, with retries on timeout/WAF."""
    params = {"id": series_id, "cosd": start, "coed": end}
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(FRED_CSV, params=params, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            if r.text.lstrip().startswith("<"):      # WAF/HTML challenge, not CSV
                raise ValueError("non-CSV response (WAF challenge / rate limit)")
            return _parse_fred_csv(r.text, series_id)
        except Exception as e:                       # noqa: BLE001 - retry on anything
            last = e
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"FRED fetch failed for {series_id} {start}..{end}: {last}")


def fetch_fred(series_id: str, start: str = START, end: str | None = None,
               retries: int = 4, timeout: int = 120) -> pd.Series:
    """Download one FRED series as a dated pandas Series. Fetched in ~5-year
    chunks because FRED's gateway times out generating very long daily ranges;
    smaller windows return quickly and are concatenated. The first failing chunk
    aborts the whole fetch (so a blocked FRED gives up fast with low retries).
    Missing days are '.' in the CSV and are dropped (real trading days only)."""
    end = end or date.today().isoformat()
    edges = pd.date_range(start=start, end=end, freq="5YS").union(
        pd.DatetimeIndex([start, end]))
    parts = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        parts.append(_fetch_chunk(series_id, lo.date().isoformat(), hi.date().isoformat(),
                                  retries=retries, timeout=timeout))
    s = pd.concat(parts)
    return s[~s.index.duplicated(keep="last")].sort_index()


def _report(name: str, series_id: str, s: pd.Series, src: str) -> None:
    print(f"  {name:6s} {series_id:14s} {len(s):>6d} obs  "
          f"{s.index.min().date()} to {s.index.max().date()}  ({src})")


def get_oil_and_vol(refresh: bool = False) -> dict[str, pd.Series]:
    """Oil prices (Brent, WTI) from EIA; volatility indices (OVX, VIX) from FRED.
    Cached raw pulls in data/raw are reused unless refresh=True (`--refresh`).
    OVX/VIX are best-effort: if FRED is unreachable, they are skipped with a
    warning and the realized-vol pipeline runs without them."""
    out = {}

    print("Phase 1: EIA oil prices")
    for name, series_id in config.EIA_SERIES.items():
        raw_path = config.DATA_RAW / f"raw_eia_{name}.csv"
        if raw_path.exists() and not refresh:
            s = pd.read_csv(raw_path, index_col=0).iloc[:, 0]
            s.index = pd.to_datetime(s.index)
            src = "cached"
        else:
            s = fetch_eia(series_id, end=config.DATA_CUTOFF)
            s.to_csv(raw_path, header=[series_id])
            src = f"downloaded {date.today().isoformat()}"
        _report(name, series_id, s, src)
        out[name] = s.rename(name)

    print("FRED volatility indices (cross-check; skipped if FRED is unreachable)")
    for name, series_id in config.FRED_SERIES.items():
        raw_path = config.DATA_RAW / f"raw_fred_{name}.csv"
        if raw_path.exists() and not refresh:
            s = _parse_fred_csv(raw_path.read_text(), series_id)
            _report(name, series_id, s, "cached")
            out[name] = s.rename(name)
            continue
        try:
            # Quick-fail (short timeout, one try) so a blocked FRED skips fast.
            s = fetch_fred(series_id, end=config.DATA_CUTOFF, retries=1, timeout=15)
            s.to_csv(raw_path, header=[series_id])
            _report(name, series_id, s, f"downloaded {date.today().isoformat()}")
            out[name] = s.rename(name)
        except Exception as e:                       # noqa: BLE001
            print(f"  {name:6s} {series_id:14s} skipped (FRED unreachable: {type(e).__name__})")
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
    """Monthly GPR plus the country indices listed in config.GPR_COUNTRIES.
    Note: the Caldara-Iacoviello country set has no Iran index (no GPRC_IRN);
    Israel proxies the Iran episodes (see config.GPR_IRAN_PROXY)."""
    path = config.DATA_RAW / config.GPR_MONTHLY_FILE
    df = pd.read_excel(path)
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = df.dropna(subset=["month"]).set_index("month")
    country_cols = [f"GPRC_{c}" for c in config.GPR_COUNTRIES]
    keep = [c for c in ["GPR", "GPRT", "GPRA", *country_cols] if c in df.columns]
    missing = [c for c in country_cols if c not in df.columns]
    if missing:
        print(f"  note: country columns not in file and skipped: {missing}")
    out = df[keep].dropna(how="all").sort_index()
    out.columns = [c.lower() for c in out.columns]
    return out


# ----------------------------------------------------------------------
# Phase 2: returns and realized volatility
# ----------------------------------------------------------------------
def log_returns(price: pd.Series) -> pd.Series:
    """Daily log returns r = ln(P_t / P_{t-1}) on actual trading days only.
    Must be passed a price series indexed by its own trading days (not the
    merged calendar), so shift(1) is the previous trading day. Non-positive
    prices (WTI on 2020-04-20) make the log undefined and yield NaN there."""
    p = price.where(price > 0)
    return np.log(p / p.shift(1))


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

    # Compute returns and realized vol on each price's OWN trading-day index,
    # so shift(1) is the previous trading day (not the previous calendar day,
    # which would lose every Monday across the weekend gap once GPRD's
    # every-calendar-day index is merged in).
    cols = {
        "brent": fred["brent"],
        "wti": fred["wti"],
        "brent_ret": log_returns(fred["brent"]),
        "wti_ret": log_returns(fred["wti"]),
        "brent_vol": realized_vol(log_returns(fred["brent"])),
        "wti_vol": realized_vol(log_returns(fred["wti"])),
    }
    for opt in ["ovx", "vix"]:
        if opt in fred:
            cols[opt] = fred[opt]
    cols["gprd"] = gprd

    # Outer join keeps every date any series has data, so we can see coverage.
    panel = pd.concat(cols, axis=1)
    panel.index = pd.to_datetime(panel.index)
    panel = panel.sort_index()
    for opt in ["ovx", "vix"]:
        if opt not in panel.columns:   # FRED unreachable: keep the column, all NaN
            panel[opt] = np.nan

    # Standardise GPRD over the full sample for the regressions.
    panel["gprd_z"] = zscore(panel["gprd"])

    # Respect the agreed data cutoff for the still-running 2026 episode.
    panel = panel.loc[:pd.Timestamp(config.DATA_CUTOFF)]
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

    # Hand-verify the last realized-vol value: std of the final 21 trading-day
    # returns (use the trading-day series, not the merged calendar, so weekends
    # are not counted as rows).
    v = panel["brent_vol"].dropna()
    if len(v):
        ts = v.index[-1]
        ret_td = panel["brent_ret"].dropna()
        window = ret_td.loc[:ts].iloc[-config.VOL_WINDOW:]
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
