# Oil price volatility and geopolitical risk

Code and data for the paper *Headlines or Disruption? Geopolitical Risk and the Persistence of Oil Price Volatility, 1990 to 2026.*

## What this repo does
It pulls oil prices and a geopolitical risk index, builds a daily volatility series, studies five geopolitical episodes in an event window, measures how long each volatility spike lasts, and produces the figures and tables for the paper.

## Setup
1. Install Python 3.10 or newer (built and tested on 3.12).
2. From the project root, create and activate a virtual environment:
   - macOS or Linux: `python -m venv .venv && source .venv/bin/activate`
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
3. Install the packages: `pip install -r requirements.txt`
4. Run the setup check: `python code/00_check_setup.py`

## Folder structure
- `code/` all scripts and `config.py`
- `data/raw/` files exactly as downloaded, never edited by hand
- `data/processed/` cleaned series produced by the code
- `figures/` exported figures (PNG and PDF)
- `tables/` exported tables (CSV)
- `output/` anything else for the paper

## Data sources
Record the download date next to each, since some of these update over time.

| Series | Source | How to get it | Downloaded on |
|---|---|---|---|
| Brent spot (daily) | FRED `DCOILBRENTEU` | pulled by the code, no API key | (auto) |
| WTI spot (daily) | FRED `DCOILWTICO` | pulled by the code | (auto) |
| OVX, oil volatility | FRED `OVXCLS` | pulled by the code | (auto) |
| VIX (optional) | FRED `VIXCLS` | pulled by the code | (auto) |
| GPR monthly | Caldara and Iacoviello | download by hand from matteoiacoviello.com/gpr.htm into `data/raw` | __fill in__ |
| GPR daily (GPRD) | Caldara and Iacoviello | download by hand from the same page into `data/raw` | __fill in__ |
| OPEC spare capacity | EIA Short-Term Energy Outlook | download by hand | __fill in__ |
| US crude production | EIA | download by hand | __fill in__ |

After downloading the GPR files, write their exact filenames into `code/config.py` (the `GPR_MONTHLY_FILE` and `GPR_DAILY_FILE` lines).

## Run order
1. `code/00_check_setup.py` checks the environment and folders.
2. `code/01_get_and_clean_data.py` pulls the FRED data (straight from FRED's CSV endpoint, no API key), loads the GPR files, builds returns and the 21-day annualised volatility, and saves to `data/processed`. Re-runs use the cached pulls in `data/raw`; pass `--refresh` to force a fresh download.
3. `code/02_event_windows.py` builds the event panel and pre-event baselines for the episodes.
4. `code/03_persistence.py` computes days-to-revert and fits the GARCH model.
5. `code/04_regressions.py` runs the supporting regressions.
6. `code/05_figures.py` and `code/06_tables.py` export the figures and tables.

## File-naming convention
- Raw: `raw_<source>_<series>.csv`, for example `raw_fred_brent.csv`
- Processed: `processed_<series>.csv`, for example `processed_brent_vol.csv`
- Figures: `fig<N>_<short_name>.png` and `.pdf`, for example `fig4_2025_vs_2026.png`
- Tables: `table<N>_<short_name>.csv`, for example `table2_event_summary.csv`

## Reproducibility
All locked parameters (window lengths, the volatility window, trigger dates, the data cutoff) live in `code/config.py`. Change them there, never inside a script. After your first successful run, pin exact package versions with `pip freeze > requirements.txt`.
