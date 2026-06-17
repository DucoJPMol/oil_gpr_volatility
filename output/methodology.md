# Data and Methodology

This section documents every data source, variable, and method so the results
can be reproduced from this text alone. All parameters live in `code/config.py`;
the scripts that implement each step are noted in brackets.

## Data

**Oil prices.** Daily Brent and WTI spot prices come from the US Energy
Information Administration (EIA): Europe Brent Spot Price FOB (series `RBRTE`,
from 20 May 1987) and Cushing WTI Spot Price FOB (`RWTC`, from 2 January 1986),
pulled via the EIA v2 API (accessed June 2026) [`01_get_and_clean_data.py`].
We use EIA rather than FRED because FRED's Brent series `DCOILBRENTEU` *is* EIA
`RBRTE`; the data are identical, and EIA was reachable on our network when FRED
was not. Brent is the main series; WTI is used for robustness. Brent from 1987
covers the 1990 Gulf War.

**Geopolitical risk.** The Geopolitical Risk index of Caldara and Iacoviello
(2022): the monthly index (`GPR`) and the daily index (`GPRD`), downloaded by
hand from matteoiacoviello.com/gpr.htm (file version dated 11 June 2026; the file
updates monthly). The country-specific monthly indices are also used. The C&I
country set covers 44 countries and does **not** include Iran (there is no
`GPRC_IRN`, and the daily file has no country breakdown). The Iran-centric
episodes use **Saudi Arabia (`GPRC_SAU`)** as the country proxy: Israel
(`GPRC_ISR`) is Iran's adversary and spikes far harder around these episodes
(trigger-month z-scores of 6.3 in 2025 and 10.0 in 2026 vs 0.6 and 5.8 for Saudi
Arabia; Table 6), which would confound an "Iran geopolitical risk" measure, so
Saudi Arabia is the cleaner oil-exporting-Gulf signal (Israel kept as a
robustness comparison). Russia (`GPRC_RUS`) covers the 2022 episode. The headline
results use the overall daily `GPRD`, not the country index, so the proxy choice
does not move the main numbers.

**Implied volatility (cross-check).** OVX, the CBOE Crude Oil Volatility Index
(FRED `OVXCLS`, from 2007), is a secondary cross-check for the post-2007
episodes. It is forward-looking implied volatility, whereas our main measure is
backward-looking realized volatility, so the two are not expected to coincide.
OVX covers only the 2018, 2022, 2025 and 2026 episodes; the 1990 Gulf War is
outside its sample.

**Missing values and calendar.** Series are merged on an outer join over a
common date index. Returns and volatility are computed on each price's own
trading-day index (weekday observations with a real price); we do not fill gaps
before computing returns. WTI's negative print on 20 April 2020 is genuine, not
an error, and lies outside every event window; we flag it and leave it in, but
the log return is undefined on that day and is treated as missing.

## Variable construction

**Log returns** [`01`]. For price $P_t$, $r_t = \ln(P_t / P_{t-1})$, computed on
trading days only.

**Realized volatility** [`01`]. The 21-day rolling standard deviation of daily
log returns, annualised and expressed in percent:
$\mathrm{RV}_t = \mathrm{sd}(r_{t-20},\dots,r_t) \times \sqrt{252} \times 100$.
This is the main volatility measure (`VOL_WINDOW = 21`,
`TRADING_DAYS_PER_YEAR = 252`).

**Geopolitical risk** [`01`]. `GPRD` is the daily GPR index; for the regressions
it is standardised to z-scores over the full sample (`gprd_z`). For event-window
work the daily index is aligned to the trading-day calendar (carried forward).

## Event-study design

We study six triggers (`config.TRIGGERS`):

| Episode | Trigger date |
|---|---|
| Gulf War (Iraq invades Kuwait) | 2 Aug 1990 |
| US withdrawal from the JCPOA | 8 May 2018 |
| Russia invades Ukraine | 24 Feb 2022 |
| Twelve-Day War (Israel–Iran) | 13 Jun 2025 |
| 2026 Iran campaign begins | 28 Feb 2026 |
| Strait of Hormuz closure declared | 4 Mar 2026 |

The two 2026 variants are both run, per the design note. Event time is measured
in trading days relative to day zero, the first trading day on or after the
trigger date. For each episode we extract the window from 10 trading days before
to 60 after (`WINDOW_PRE = 10`, `WINDOW_POST = 60`) for returns, realized vol,
OVX where available, and GPRD [`02`]. The pre-event baseline is the mean and
standard deviation of Brent realized vol over the 60 trading days before day
zero (`BASELINE_WINDOW = 60`). The two 2026 episodes are ongoing and their
windows are truncated at the data cutoff.

## Persistence

**Metric 1 — days to revert** [`03`]. The threshold is the pre-event baseline
mean plus one standard deviation (`PERSISTENCE_SD_MULTIPLE = 1.0`). We record the
number of trading days from the trigger until realized vol first drops below the
threshold and stays below for five consecutive trading days
(`REVERT_CONSECUTIVE_DAYS = 5`). Because 21-day realized vol is backward-looking,
at the trigger day it still reflects the calm pre-event window and can lie below
the threshold; we therefore begin the reversion search at the spike onset (the
first day vol crosses above the threshold), so the metric measures persistence of
the actual spike rather than registering a spurious zero. Episodes still elevated
at the cutoff are reported as censored ("at least *n* days").

**Metric 2 — GARCH(1,1) persistence** [`03`]. A GARCH(1,1) model is fit to daily
Brent log returns (constant mean, normal errors), using the `arch` package. We
report $\omega$, $\alpha$, $\beta$ and the persistence $\alpha + \beta$, confirm
$\alpha + \beta < 1$ (stationarity), save the conditional-volatility series, and
run Ljung-Box tests on the standardised residuals and their squares to check for
misspecification.

## Supporting regressions

Implemented in [`04`]: (i) contemporaneous correlations between GPRD and realized
vol, full sample and within event windows; (ii) a pooled event-window regression
of Brent realized vol on standardised GPRD plus episode fixed effects, with
Newey-West (HAC) standard errors (10 lags); and (iii) local projections — Brent
realized vol at horizon $h$ regressed on the day-zero GPRD shock with lagged
controls and HAC errors, for $h = 0,\dots,60$, tracing the impulse response of
volatility to a one-standard-deviation geopolitical-risk shock.

## Robustness

We re-run days-to-revert for WTI as well as Brent and for 10-, 21- and 30-day
volatility windows [`07`]. The episode ranking is stable; any specification that
changes a conclusion is noted in the results.

## Data cutoff and the ongoing 2026 episode

The data cutoff is **12 June 2026** (`DATA_CUTOFF`), the last full trading week
before the draft. The 2026 episode is still running: its event window is
truncated and its days-to-revert is censored at the cutoff, reported as a lower
bound.

## Mechanism coding

For each episode we hand-code whether the Strait of Hormuz was disrupted and
whether barrels were actually lost (`strait_disrupted`, `supply_disruption` in
`config.TRIGGERS`), the spine of the headline-versus-disruption argument. Each
value requires a cited source; the 2026 codings are provisional pending
verification.

## Extensions (post-presentation)

Additional data and measures, each in its own script (`code/08`–`11`):

- **Futures term structure [`09`].** WTI futures from EIA (`RCLC1`–`RCLC4`, daily,
  to 2024-04) spliced with a hand-downloaded front-month CL=F (investing.com,
  `data/raw/raw_cl_futures.csv`) to extend through 2026. We build the C1−C4
  spread (backwardation indicator) and the spot−front-month basis.
- **Natural gas [`08`].** Henry Hub spot from EIA (`RNGWHHD`); European TTF
  optional via a manual investing.com download (`raw_ttf.csv`). Gas realized vol
  uses the same 21-day method.
- **Inventories [`10`].** US commercial crude stocks excl. SPR (EIA `WCESTUS1`),
  SPR (`WCSSTUS1`), total (`WCRSTUS1`), weekly. Reserve adequacy = deviation of
  commercial stocks from their trailing 5-year mean, in SD units.
- **OPEC spare capacity [`11`].** EIA STEO `COPS_OPEC` (monthly), the global
  supply buffer.
- **Implied volatility.** OVX (`OVXCLS`) and VIX (`VIXCLS`) are hand-downloaded
  from FRED into `data/raw/raw_ovx.csv` / `raw_vix.csv` (FRED is blocked on our
  network) and loaded with priority over the API pull.
