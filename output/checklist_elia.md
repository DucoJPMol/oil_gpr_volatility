# Checklist — Elia (Part 4: Results and Discussion)

Your job: turn the numbers and figures into the Results and Discussion sections.
Everything you need is already produced — you should not have to run any code.
Tick each box as you go.

## 0. Before you write (read these first)
- [ ] `output/results_summary.md` — the one-page plain-language summary.
- [ ] `output/presentation_notes.md` — every key number and the story arc.
- [ ] `output/methodology.md` — definitions (so you can *cite* them, not redefine).
- [ ] Open all figures in `figures/` and all tables in `tables/` once, so you know
      what exists.
- [ ] Agree section numbering and figure/table numbers with Maxim (Part 1) before
      drafting, so your in-text references are final.

## 1. Results section — structure to follow
Write it in this order; each bullet maps to an artifact.

### 1.1 Descriptive / sample
- [ ] Report the sample: Brent 1987–2026 (9,908 days), WTI from 1986; GPR daily
      1985–2026. Cite Table 1 (`table1_summary_stats`): Brent daily return mean ≈ 0,
      SD ≈ 2.5%; realized vol averages ~34%.
- [ ] Introduce Figures 1 and 2 (long-run GPR+price, long-run realized vol) to set
      the scene — note the vol spikes visually line up with the episodes.

### 1.2 Event-study results (per episode)
- [ ] Use Figure 3 (event-study panel) and Table 2 (`table2_event_summary`).
- [ ] For each episode state: peak vol, the day it peaks, and the baseline. Numbers:
      Gulf War peak 103% (day +60), 2018 38% (+48), 2022 91% (+22), 2025 53% (+13),
      2026 114% (+30/+32).
- [ ] Contrast the shapes: 2018 stays flat (headline), disruption episodes spike hard.

### 1.3 Persistence — the core result
- [ ] **Days-to-revert** (Table 2): Gulf War 178, 2018 = 2, 2022 = 61, 2025 = 27,
      both 2026 episodes still elevated (≥66/≥64). This is the headline.
- [ ] **GARCH(1,1)** (Table 3): α+β = 0.993 — volatility is highly persistent but
      stationary; diagnostics clean (Ljung-Box squared-resid p = 0.53). Reference
      Figure 6 (conditional vol).

### 1.4 Geopolitical risk and volatility
- [ ] Correlations (Table 4 `table4_correlations`): 0.19 full sample, **0.44 within
      event windows** — tighter around events.
- [ ] Pooled regression: GPR coefficient +3.5 but **not significant (p = 0.20)**
      with episode fixed effects. Interpret: the GPR–vol link is *between* episodes,
      not in the day-to-day variation *within* one. (Important nuance — don't
      overclaim a within-episode causal effect.)
- [ ] Local projection (Figure 7): a 1-SD GPR shock raises vol up to +1.6 points,
      peaking ~19 trading days out, then decaying.

### 1.5 Robustness
- [ ] Table 5 (`table5_robustness`): ranking stable across Brent/WTI and 10/21/30-day
      windows. **Flag honestly:** 2018 days-to-revert is window-sensitive (2 at 21d,
      ~80 at 30d) because vol barely crossed the threshold.
- [ ] Table 6 (`table6_iran_proxy_comparison`): justify Saudi Arabia over Israel as
      the Iran proxy (Israel spikes z = 6.3/10.0 vs Saudi 0.6/5.8).

## 2. Discussion section — the argument
- [ ] **State the central finding:** real supply disruption → persistent volatility;
      headlines without lost barrels → volatility fades. Anchor on Figure 8
      (days-to-revert coloured by supply disruption) and Figure 4 (2025 vs 2026).
- [ ] **Walk the mechanism per episode** using the `supply_disruption` /
      `strait_disrupted` coding in Table 2: Gulf War (barrels lost → 178 days),
      2018 (Strait open, no loss → 2 days), 2022 (partial → 61), 2025 (threatened,
      stayed open → 27), 2026 (closure → still elevated).
- [ ] **The headline figure:** explain Figure 4 — same region, same kind of trigger,
      opposite persistence, because in 2026 the Strait actually closed.
- [ ] **Spot vs futures** (Fig 11, Table 9): in 2026 disruption episodes WTI spot
      trades $2.5–8 above front-month futures (backwardation) — the market prices
      near-term scarcity the longer the conflict runs.
- [ ] **Reserves / spare-capacity angle** (Figs 13–15, Tables 10–11,
      `reserves_and_volatility.md`): inventories don't predict vol unconditionally;
      the story is the buffer — 2022's record SPR release and the 2026 Strait
      closure with ~zero OPEC spare capacity. Frame the "second spike" as a
      hypothesis, not a result. The mechanism is disruption × thin buffer.
- [ ] **Gas vs oil for Russia** (Fig 9, Table 8, `output/global_unrest_gas.md`):
      the 2022 shock was largely a gas event; gas vol exceeds oil vol in every
      conflict episode (Russia 1.8×).

## 3. Limitations (write these explicitly — graded)
- [ ] OVX implied-vol cross-check is pending (FRED was unreachable on our network).
- [ ] The 2026 episode is ongoing; its window is truncated and days-to-revert is a
      lower bound (censored at the 12 June 2026 cutoff).
- [ ] No Iran GPR index exists; Saudi Arabia is a proxy.
- [ ] 2018 result is sensitive to the volatility-window length.
- [ ] Days-to-revert is measured from the spike onset (state this; it is a
      deliberate, documented choice).

## 4. Numbers you will cite most (quick reference)
| Episode | Peak vol | Days-to-revert | Supply disruption |
|---|---|---|---|
| Gulf War 1990 | 103% | 178 | yes |
| Iran sanctions 2018 | 38% | 2 | no |
| Russia–Ukraine 2022 | 91% | 61 | partial |
| Twelve-Day War 2025 | 53% | 27 | no |
| 2026 Iran campaign | 114% | ≥66 | partial |
| 2026 Strait closure | 114% | ≥64 | yes |

GARCH α+β = 0.993 · GPR–vol corr 0.19 (full) / 0.44 (events) · LP peak +1.6 at ~19d.

## 5. Hand-off back
- [ ] Give Maxim a list of which figures/tables you cite and where, with final
      numbers, so integration matches your text.
- [ ] Flag anything you want Duco to re-run or recompute (e.g. a different threshold).
