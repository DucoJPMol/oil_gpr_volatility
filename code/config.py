"""
config.py
Single source of truth for the project's locked parameters.
Every script imports from here. Do not hardcode these values anywhere else.

Project: Headlines or Disruption? Geopolitical Risk and the Persistence
of Oil Price Volatility, 1990 to 2026.
"""

import os
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
# The last full trading week before the final draft (Mon 8 - Fri 12 Jun 2026).
# Group-locked: change only after telling the group. The 2026 episode is ongoing,
# so its event window is truncated at this date (handled in 02_event_windows.py).
DATA_CUTOFF = "2026-06-12"

# ----------------------------------------------------------------------
# Oil prices: EIA is the primary source. FRED's Brent (DCOILBRENTEU) is itself
# EIA series RBRTE, so this is the same data, and EIA stays reachable on networks
# that block FRED. Get a free key in seconds at
#   https://www.eia.gov/opendata/register.php
# then export it before running the pipeline:
#   export EIA_API_KEY=your_key_here
# ----------------------------------------------------------------------
EIA_API_KEY = os.environ.get("EIA_API_KEY", "")
EIA_SERIES = {
    "brent": "RBRTE",   # Europe Brent Spot Price FOB, daily, from 1987
    "wti":   "RWTC",    # Cushing WTI Spot Price FOB, daily, from 1986
}

# Volatility indices come from FRED (CBOE indices, not on EIA). These are a
# secondary cross-check, so the pipeline still runs if FRED is unreachable.
FRED_SERIES = {
    "ovx":   "OVXCLS",         # crude oil volatility index, daily, from 2007
    "vix":   "VIXCLS",         # equity volatility index (optional comparator)
}

# ----------------------------------------------------------------------
# GPR data (download by hand from the page below, save into data/raw)
# ----------------------------------------------------------------------
GPR_PAGE = "https://www.matteoiacoviello.com/gpr.htm"
# Download both the monthly file and the daily file from that page, save them
# into data/raw, then write the exact filenames and the download date here.
GPR_MONTHLY_FILE = "data_gpr_export.xls"
GPR_DAILY_FILE = "data_gpr_daily_recent.xls"
GPR_DOWNLOAD_DATE = "2026-06-11"   # version of the GPR files in data/raw (updates monthly)

# ----------------------------------------------------------------------
# GPR country indices (monthly column GPRC_<code> in the file).
#
# Important: the Caldara-Iacoviello country set covers 44 countries and does
# NOT include Iran (there is no GPRC_IRN), so there is no Iran series to load.
# For the Iran-centric episodes (2018 JCPOA, 2025 Twelve Day War, 2026 campaign)
# we use Israel as the closest covered proxy; Russia covers the 2022 episode and
# Saudi Arabia is the Gulf proxy. The overall daily GPRD is used regardless.
# ----------------------------------------------------------------------
GPR_COUNTRIES = ["ISR", "SAU", "RUS", "EGY", "TUR"]   # carried through to the processed panel
# Saudi Arabia proxies the Iran episodes: there is no GPRC_IRN, and Israel
# (Iran's adversary) carries Israel-specific risk that would confound the Iran
# signal, so we use Saudi Arabia (an oil-exporting Gulf neighbour). Israel is
# kept in GPR_COUNTRIES as a robustness comparison (see the proxy table).
GPR_IRAN_PROXY = "SAU"

# ----------------------------------------------------------------------
# The five episodes. Dates are calendar dates; the code maps day zero to the
# first trading day on or after the date.
#
# "country" is the GPR country index used as the episode's country-level signal
# (see GPR_COUNTRIES above; Israel proxies the Iran episodes since no GPRC_IRN
# exists).
#
# The mechanism coding (spine of the headline-versus-disruption argument):
#   strait_disrupted   was the Strait of Hormuz physically closed/disrupted?
#   supply_disruption  were barrels actually lost / was physical supply hit?
# Both are yes / partial / no. Values below are a historically grounded best
# estimate -- ATTACH A SOURCE FOR EACH (grading + replicability). The 2026 rows
# are recent/scenario-specific and must be verified before the final draft.
# ----------------------------------------------------------------------
TRIGGERS = {
    "gulf_war_1990": {
        "date": "1990-08-02",
        "label": "Gulf War (Iraq invades Kuwait)",
        "country": "SAU",
        "strait_disrupted": "no",      # Strait stayed open
        "supply_disruption": "yes",    # ~4 Mb/d Iraqi+Kuwaiti exports removed
    },
    "iran_sanctions_2018": {
        "date": "2018-05-08",
        "label": "US withdrawal from the JCPOA",
        "country": GPR_IRAN_PROXY,
        "strait_disrupted": "no",      # the "Strait open" contrast
        "supply_disruption": "no",     # gradual sanctions only; no in-window loss
    },
    "russia_ukraine_2022": {
        "date": "2022-02-24",
        "label": "Russia invades Ukraine",
        "country": "RUS",
        "strait_disrupted": "no",       # not a Hormuz event
        "supply_disruption": "partial", # Russian flows sanctioned, largely redirected
    },
    "twelve_day_war_2025": {
        "date": "2025-06-13",   # Israel's opening strikes, 13 Jun 2025
        "label": "Twelve Day War (Israel and Iran)",
        "country": GPR_IRAN_PROXY,
        "strait_disrupted": "no",      # threatened but stayed open
        "supply_disruption": "no",     # no sustained physical loss (the headline)
    },
    "iran_2026_campaign": {
        "date": "2026-02-28",   # first strikes, late February 2026
        "label": "2026 Iran campaign begins",
        "country": GPR_IRAN_PROXY,
        "strait_disrupted": "partial",  # escalating strikes; VERIFY
        "supply_disruption": "partial", # escalating disruption; VERIFY
    },
    "iran_2026_closure": {
        "date": "2026-03-04",   # Strait of Hormuz declared closed
        "label": "Strait of Hormuz closure declared",
        "country": GPR_IRAN_PROXY,
        "strait_disrupted": "yes",     # closure declared; VERIFY
        "supply_disruption": "yes",    # ~20% of seaborne oil blocked; VERIFY
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
    print(f"GPR files dated {GPR_DOWNLOAD_DATE}; country indices {GPR_COUNTRIES} "
          f"(Iran proxy: {GPR_IRAN_PROXY}, no GPRC_IRN exists)")
    print()
    print(f"Episodes ({len(TRIGGERS)})")
    for key, t in TRIGGERS.items():
        print(f"  {t['date']}  {t['label']:42s} country={t['country']}")


if __name__ == "__main__":
    summary()
