"""
config.py
Single source of truth for the project's locked parameters.
Every script imports from here. Do not hardcode these values anywhere else.

Project: Headlines or Disruption? Geopolitical Risk and the Persistence
of Oil Price Volatility, 1990 to 2026.
"""

from pathlib import Path

# ----------------------------------------------------------------------
# Paths, resolved relative to the project root, so the code runs the same
# on all four laptops without editing absolute paths.
# (config.py lives in code/, so the root is one level up.)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES = PROJECT_ROOT / "figures"
TABLES = PROJECT_ROOT / "tables"
OUTPUT = PROJECT_ROOT / "output"

# ----------------------------------------------------------------------
# Volatility construction
# ----------------------------------------------------------------------
VOL_WINDOW = 21               # trading days for the rolling realized volatility
TRADING_DAYS_PER_YEAR = 252   # annualise by multiplying the daily std by sqrt(252)

# ----------------------------------------------------------------------
# Event study design
# ----------------------------------------------------------------------
WINDOW_PRE = 10        # trading days before the trigger (for plotting)
WINDOW_POST = 60       # trading days after the trigger
BASELINE_WINDOW = 60   # trading days before the trigger used for the baseline mean and SD

# ----------------------------------------------------------------------
# Persistence metric 1: days to revert
# ----------------------------------------------------------------------
PERSISTENCE_SD_MULTIPLE = 1.0   # threshold = baseline mean + this many SDs
REVERT_CONSECUTIVE_DAYS = 5     # vol must stay below the threshold this many days in a row to count as reverted

# ----------------------------------------------------------------------
# Data cutoff for the still-running 2026 episode
# ----------------------------------------------------------------------
# TODO confirm with the group: set to the last trading day before the final draft.
DATA_CUTOFF = "2026-06-12"

# ----------------------------------------------------------------------
# FRED series IDs (used with pandas-datareader, which needs no API key)
# ----------------------------------------------------------------------
FRED_SERIES = {
    "brent": "DCOILBRENTEU",   # Brent spot, daily, from 1987
    "wti":   "DCOILWTICO",     # WTI spot, daily, from 1986
    "ovx":   "OVXCLS",         # crude oil volatility index, daily, from 2007
    "vix":   "VIXCLS",         # equity volatility index (optional comparator)
}

# ----------------------------------------------------------------------
# GPR data (download by hand from the page below, save into data/raw)
# ----------------------------------------------------------------------
GPR_PAGE = "https://www.matteoiacoviello.com/gpr.htm"
# Download both the monthly file and the daily file from that page, save them
# into data/raw, then write the exact filenames and the download date here.
GPR_MONTHLY_FILE = ""   # e.g. "data_gpr_export.xls"        (fill in once downloaded)
GPR_DAILY_FILE = ""     # e.g. "data_gpr_daily_recent.xls"  (fill in once downloaded)

# ----------------------------------------------------------------------
# The five episodes. Dates are calendar dates; the code maps day zero to the
# first trading day on or after the date.
#
# supply_disruption is left blank on purpose. Fill it from your Phase 1
# coding sheet (yes / no / partial) with a source for each, because it is the
# spine of the headline-versus-disruption argument.
# ----------------------------------------------------------------------
TRIGGERS = {
    "gulf_war_1990": {
        "date": "1990-08-02",
        "label": "Gulf War (Iraq invades Kuwait)",
        "supply_disruption": None,
    },
    "iran_sanctions_2018": {
        "date": "2018-05-08",
        "label": "US withdrawal from the JCPOA",
        "supply_disruption": None,
    },
    "russia_ukraine_2022": {
        "date": "2022-02-24",
        "label": "Russia invades Ukraine",
        "supply_disruption": None,
    },
    "twelve_day_war_2025": {
        "date": "2025-06-13",   # TODO confirm the exact start date
        "label": "Twelve Day War (Israel and Iran)",
        "supply_disruption": None,
    },
    "iran_2026_campaign": {
        "date": "2026-02-28",   # first strikes, late February 2026
        "label": "2026 Iran campaign begins",
        "supply_disruption": None,
    },
    "iran_2026_closure": {
        "date": "2026-03-04",   # Strait of Hormuz declared closed
        "label": "Strait of Hormuz closure declared",
        "supply_disruption": None,
    },
}


def summary():
    """Print every locked parameter. Run `python code/config.py` to confirm it loads."""
    print("Project paths")
    for name, p in [("root", PROJECT_ROOT), ("raw", DATA_RAW),
                    ("processed", DATA_PROCESSED), ("figures", FIGURES),
                    ("tables", TABLES), ("output", OUTPUT)]:
        print(f"  {name:10s} {p}")
    print()
    print("Volatility")
    print(f"  window {VOL_WINDOW} days, annualised with sqrt({TRADING_DAYS_PER_YEAR})")
    print()
    print("Event study")
    print(f"  window: {WINDOW_PRE} before to {WINDOW_POST} after; baseline {BASELINE_WINDOW} days")
    print()
    print("Persistence")
    print(f"  threshold: baseline mean + {PERSISTENCE_SD_MULTIPLE} SD")
    print(f"  revert rule: below threshold for {REVERT_CONSECUTIVE_DAYS} days in a row")
    print()
    print(f"Data cutoff (2026): {DATA_CUTOFF}")
    print()
    print(f"Episodes ({len(TRIGGERS)})")
    for key, t in TRIGGERS.items():
        print(f"  {t['date']}  {t['label']}")


if __name__ == "__main__":
    summary()
