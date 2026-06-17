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
4. Get a free EIA API key (instant) at <https://www.eia.gov/opendata/register.php> and export it: `export EIA_API_KEY=your_key_here`
5. Run the setup check: `python code/00_check_setup.py`

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
| Brent spot (daily) | EIA `RBRTE` | pulled by the code (needs a free EIA key) | (auto) |
| WTI spot (daily) | EIA `RWTC` | pulled by the code | (auto) |
| OVX, oil volatility | FRED `OVXCLS` | pulled by the code (best-effort; skipped if FRED is unreachable) | (auto) |
| VIX (optional) | FRED `VIXCLS` | pulled by the code (best-effort) | (auto) |

Oil prices come from **EIA**, not FRED: FRED's Brent series `DCOILBRENTEU` is itself EIA series `RBRTE`, so the data is identical, and EIA stays reachable on networks that block FRED. Get a free key (instant) at <https://www.eia.gov/opendata/register.php> and export it before running the pipeline:

```bash
export EIA_API_KEY=your_key_here
```

OVX and VIX are CBOE indices available only on FRED; they are a secondary cross-check, so the pipeline still runs (without them) if FRED is blocked.
| GPR monthly | Caldara and Iacoviello | download by hand from matteoiacoviello.com/gpr.htm into `data/raw` | __fill in__ |
| GPR daily (GPRD) | Caldara and Iacoviello | download by hand from the same page into `data/raw` | __fill in__ |
| OPEC spare capacity | EIA Short-Term Energy Outlook | download by hand | __fill in__ |
| US crude production | EIA | download by hand | __fill in__ |

After downloading the GPR files, write their exact filenames into `code/config.py` (the `GPR_MONTHLY_FILE` and `GPR_DAILY_FILE` lines).

**Country indices and Iran.** The Caldara–Iacoviello country set covers 44 countries and does **not** include Iran (there is no `GPRC_IRN`, and the daily file has no country breakdown). The Iran-centric episodes (2018 JCPOA, 2025 Twelve-Day War, 2026 campaign) therefore use **Israel (`GPRC_ISR`)** as the closest covered proxy, alongside the overall daily `GPRD`. The country indices carried through the pipeline are set in `config.GPR_COUNTRIES` (`ISR, SAU, RUS, EGY, TUR`) and the Iran proxy in `config.GPR_IRAN_PROXY`.

## Run order
Set `EIA_API_KEY` first (see Setup), then run in order:
1. `code/00_check_setup.py` — checks the environment, folders, and the EIA key.
2. `code/01_get_and_clean_data.py` — pulls Brent/WTI from the EIA API, loads the GPR files, builds returns and the 21-day annualised volatility, and saves to `data/processed`. OVX/VIX are a best-effort FRED pull (skipped if FRED is unreachable). Re-runs use the cached pulls in `data/raw`; pass `--refresh` to force a fresh download.
3. `code/02_event_windows.py` — builds the event panel and pre-event baselines.
4. `code/03_persistence.py` — days-to-revert and GARCH(1,1) (writes working data to `data/processed`; the paper-ready Tables 2–3 are built by `06_tables.py`).
5. `code/04_regressions.py` — correlations, the pooled event-window regression, and the local projection (Table 4).
6. `code/05_figures.py` — Figures 1–7. `code/06_tables.py` — Tables 1–3.
7. `code/07_robustness.py` — days-to-revert across Brent/WTI and 10/21/30-day vol windows (Table 5).

A plain-language summary of the results for the write-up is in `output/results_summary.md`.

## File-naming convention
- Raw: `raw_<source>_<series>.csv`, for example `raw_fred_brent.csv`
- Processed: `processed_<series>.csv`, for example `processed_brent_vol.csv`
- Figures: `fig<N>_<short_name>.png` and `.pdf`, for example `fig4_2025_vs_2026.png`
- Tables: `table<N>_<short_name>.csv`, for example `table2_event_summary.csv`

## Reproducibility
All locked parameters (window lengths, the volatility window, trigger dates, the data cutoff) live in `code/config.py`. Change them there, never inside a script. After your first successful run, pin exact package versions with `pip freeze > requirements.txt`.
