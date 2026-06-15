# Presentation cheat-sheet — everything in one place

Study aid for the mock presentation. Paper: *Headlines or Disruption?
Geopolitical Risk and the Persistence of Oil Price Volatility, 1990–2026.*
My part: data, methodology, all code, volatility and persistence, every figure.

## 1. The one-sentence story
**Oil-price volatility from real supply disruption persists for months; volatility
from geopolitical headlines without lost barrels fades within days.** The
2025-vs-2026 contrast is the proof: same region, same kind of trigger, opposite
persistence — because in 2026 the Strait of Hormuz was actually closed.

## 2. Research question and framing
Does geopolitical risk move oil volatility, and — more importantly — does the
volatility *persist*? We separate two channels: **headlines/attention** (GPR
spikes, no barrels lost) versus **physical disruption** (barrels actually
removed, Strait of Hormuz closed). Five-plus episodes from 1990 to 2026.

## 3. Data (what, where, how much)
| Series | Source | Coverage |
|---|---|---|
| Brent spot (main) | EIA `RBRTE` | 9,908 days, 1987–2026 |
| WTI spot (robustness) | EIA `RWTC` | 10,181 days, 1986–2026 |
| Geopolitical risk, daily `GPRD` | Caldara & Iacoviello | 1985–2026 |
| GPR monthly + 44 country indices | Caldara & Iacoviello | through 2026-05 |
| OVX implied vol (cross-check) | FRED `OVXCLS` | 2007+ (pending) |

- **Why EIA not FRED:** FRED's Brent (`DCOILBRENTEU`) *is* EIA `RBRTE` — identical
  data — and FRED was blocked on our network. Methodology unchanged.
- **No Iran index exists** in C&I (44-country set excludes Iran) → use **Israel
  (GPRC_ISR)** as the proxy for Iran episodes, plus overall GPRD.
- Cutoff **12 June 2026** (last full trading week); 2026 episode is ongoing/truncated.

## 4. Methods (be ready to explain each)
- **Log returns:** r = ln(P_t / P_{t-1}), trading days only.
- **Main volatility:** 21-day rolling SD of log returns × √252 × 100 (annualised %).
- **Event study:** day 0 = first trading day on/after the trigger; window −10 to
  +60 trading days; baseline = 60 days before day 0.
- **Persistence metric 1 (days to revert):** trading days until vol falls below
  (baseline mean + 1 SD) and stays below 5 days straight — measured **from the
  spike onset** (key fix, see §8).
- **Persistence metric 2 (GARCH(1,1)):** on daily Brent returns; persistence =
  α + β.
- **Regressions:** GPRD–vol correlations; pooled event regression with episode
  fixed effects + Newey-West SEs; local projections (impulse response, h=0–60).
- **Robustness:** WTI vs Brent; 10/21/30-day vol windows.

## 5. THE NUMBERS (memorise these)
**Days to revert / peak vol per episode**
| Episode | Peak vol | Days to revert | Disruption |
|---|---|---|---|
| Gulf War 1990 | 103% | **178** | barrels lost (yes) |
| Iran sanctions 2018 (JCPOA) | 38% | **2** | none (Strait open) |
| Russia–Ukraine 2022 | 91% | **61** | partial (redirected) |
| Twelve-Day War 2025 | 53% | **27** | none (Strait threatened, open) |
| 2026 Iran campaign | 114% | **≥66, ongoing** | partial |
| 2026 Strait closure | 114% | **≥64, ongoing** | yes (Strait closed) |

**GARCH(1,1):** ω=0.06, α=0.09, β=0.90, **α+β = 0.993** (very persistent,
stationary). Diagnostics clean (Ljung-Box squared-resid p = 0.53).

**GPR ↔ volatility:** correlation 0.19 full sample, **0.44 within event windows**.
Pooled regression coef on GPR = +3.5 but **not significant (p = 0.20)** once
episode fixed effects are in → the link is *between* episodes, not day-to-day
within one. Local projection: a 1-SD GPR shock lifts vol up to **+1.6 points,
peaking ~19 trading days out**, then decays.

**Summary stats:** Brent daily return mean ≈ 0, SD 2.5%; Brent realized vol
averages ~34% (min 6%, max 344% in 2020).

## 6. The figures — what each shows (one-liner takeaways)
- **Fig 1** GPR + Brent price, 1990–2026 — scene-setter; spikes line up with events.
- **Fig 2** Long-run Brent realized vol — the volatility spikes at each episode.
- **Fig 3** Event-study panel (all episodes, event time) — 2018 stays flat, the
  disruption episodes spike highest.
- **Fig 4 (HEADLINE)** 2025 vs 2026 — 2026 (closure) climbs and *stays* ~60%;
  2025 (headline) peaks ~52% and fades. The paper's strongest visual.
- **Fig 5** Small multiples — vol vs GPR per episode.
- **Fig 6** GARCH conditional vol over the sample — illustrates persistence.
- **Fig 7** Local-projection impulse response with 95% bands — vol response to a
  GPR shock, peak ~day 19.
- **Fig 8 (MECHANISM)** Days-to-revert per episode, coloured by supply disruption
  (green→orange→red) — the central argument in one bar chart.

## 7. The story arc for the talk (4 beats)
1. Geopolitical risk spikes oil volatility — but by how much, and for how long?
2. Headlines vs disruption: GPR attention vs barrels actually lost.
3. Persistence is the discriminator — 2018 reverts in 2 days, the Gulf War took
   178, and 2026 (real closure) is still elevated.
4. Fig 4 + Fig 8 make it visible; GARCH α+β=0.993 confirms volatility is sticky.

## 8. Decisions / caveats to defend (likely questions)
- **Why measure days-to-revert from the spike onset?** 21-day realized vol is
  backward-looking; at day 0 it still reflects the calm pre-event window and sits
  below the threshold, so searching from day 0 falsely reports "0 days" for 2022
  and 2025. Starting at the onset measures persistence of the actual spike.
- **Why Israel for Iran?** No GPRC_IRN exists; Israel is the nearest covered
  country and the Iran episodes are Israel-driven. Overall GPRD used too.
- **EIA vs FRED?** Same Brent series; EIA is the original source.
- **2018 robustness flip:** days-to-revert is 2 at 21-day vol but ~80 at 30-day —
  it barely crossed the threshold. Honest caveat; ranking otherwise stable.
- **2026 mechanism codings are provisional** (still being verified/sourced).
- **OVX cross-check** not yet populated (FRED was blocked); secondary only.

## 9. Where everything lives
- Code `code/00`–`07`; figures `figures/`; tables `tables/`; processed data
  `data/processed/`; write-ups `output/`. Repo:
  github.com/DucoJPMol/oil_gpr_volatility
- Re-run: `export EIA_API_KEY=...` then run `code/00`…`07` in order.
