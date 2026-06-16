# Results summary for Part 4 (interpretation)

Plain-language summary of what the numbers show, for writing the results and
discussion without reading the code. All figures are in `figures/`, tables in
`tables/`. Data cutoff for the ongoing 2026 episode: **2026-06-12**.

## The headline finding
Volatility from **real supply disruption persists; volatility from headlines
fades**. The two 2026 episodes (Iran campaign and the declared Strait of Hormuz
closure) are **still elevated at the data cutoff**, the 1990 Gulf War (real
barrels lost) took **178 trading days** to settle, while the 2018 JCPOA
withdrawal — a pure headline with the Strait open — reverted in **2 days**.

## Persistence: days-to-revert (Table 2, Figure 3)
Trading days until 21-day realized Brent vol falls back below the pre-event
baseline mean + 1 SD and stays there for 5 days, measured from the spike onset.

| Episode | Peak vol | Days to revert |
|---|---|---|
| Gulf War 1990 | 103% | 178 |
| Iran sanctions 2018 (JCPOA) | 38% | 2 |
| Russia–Ukraine 2022 | 91% | 61 |
| Twelve-Day War 2025 | 53% | 27 |
| 2026 Iran campaign | 114% | ≥66 (ongoing) |
| 2026 Strait closure | 114% | ≥64 (ongoing) |

## GARCH(1,1) persistence (Table 3, Figure 6)
On daily Brent log returns: alpha+beta = **0.993** (highly persistent but
stationary). Diagnostics are fine (Ljung-Box on squared standardised residuals
p = 0.53, i.e. no leftover ARCH).

## Geopolitical risk and volatility (Table 4, Figures 5 and 7)
- Contemporaneous correlation of GPRD with realized vol: **0.19** full sample,
  **0.44** pooled within event windows — the link is much tighter around events.
- Pooled event-window regression (vol on standardised GPRD + episode fixed
  effects, Newey-West SEs): GPRD coefficient **+3.5** but **not significant**
  (p = 0.20). Read: most of the GPRD–vol link is *between* episodes, not in the
  day-to-day wiggle *within* an episode.
- Local projection: a 1-SD GPRD shock raises realized vol by up to **+1.6
  points**, peaking about **19 trading days** out, then decaying (Figure 7).

## Robustness (Table 5)
The episode ranking holds for WTI as well as Brent and across 10/21/30-day vol
windows. **One honest caveat:** the 2018 days-to-revert is window-sensitive
(2 days at 21-day vol, ~80 at 30-day) because vol barely crossed the threshold —
worth a sentence in the discussion.

## Things to flag in the write-up
1. **Iran has no GPR country index.** Caldara–Iacoviello's 44-country set does
   not include Iran, so the Iran-centric episodes use **Saudi Arabia (GPRC_SAU)**
   as the country proxy (Israel was rejected: as Iran's adversary it spikes far
   harder — z = 6.3/10.0 in 2025/2026 vs 0.6/5.8 for Saudi — and would confound
   the signal; Table 6). The headline results use the overall daily GPRD, so this
   choice does not move the main numbers. State this.
2. **Days-to-revert metric.** Because 21-day realized vol is backward-looking,
   the search for reversion starts at the spike onset (the first day vol crosses
   the threshold), not at day zero. This is a deliberate, documented choice on a
   group-locked metric — confirm with the group.
3. **OVX cross-check is pending.** OVX (post-2007 implied-vol comparator) is on
   FRED, which was unreachable on our network; it fills in automatically when
   `01` is run somewhere FRED is reachable. Oil prices come from EIA (identical
   to FRED's Brent series).
4. **2026 is truncated/ongoing.** Both 2026 episodes are censored at the cutoff.

## Figure guide
- Fig 1: GPR and Brent price, 1990–2026 (scene-setter).
- Fig 2: long-run Brent realized vol with episodes marked.
- Fig 3: event-study panel — vol around all six triggers (the key comparison).
- **Fig 4: 2025 vs 2026 — the headline visual for the progress meeting.**
- Fig 5: small multiples, vol vs GPRD per episode.
- Fig 6: GARCH conditional vol over the sample.
- Fig 7: local-projection impulse response with 95% bands.
