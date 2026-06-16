# Checklist — Maxim (Part 1: Integration)

Your job: assemble the four parts into one coherent, correctly formatted paper,
with consistent figures, tables, references, and notation. Tick as you go.

## 0. Before you integrate
- [ ] Clone/pull the repo: `github.com/DucoJPMol/oil_gpr_volatility`.
- [ ] Read `output/methodology.md` (Duco) and `output/results_summary.md` (the
      findings) so you know the content you are assembling.
- [ ] Confirm the target format with the group: journal style / course template,
      word or page limit, citation style (e.g. APA / Chicago / author-year), and
      whether figures go inline or in an appendix.
- [ ] Lock the **section numbering** and a single **figure/table numbering scheme**
      and circulate it, so Elia's and Duco's in-text references are final.

## 1. Document skeleton (assemble in this order)
- [ ] Title page: paper title, authors, course, date.
- [ ] Abstract (~150–200 words) — write last; synthesise question, data, method,
      headline result (disruption persists, headlines fade; Gulf War 178d vs 2018 2d;
      GARCH α+β = 0.993).
- [ ] 1. Introduction (Part 2 owner) — research question, contribution.
- [ ] 2. Literature review (Part 2 owner) — GPR (Caldara & Iacoviello), oil-vol,
      Kilian-style oil shocks.
- [ ] 3. Data and Methodology (Duco) — paste from `output/methodology.md`.
- [ ] 4. Results (Elia).
- [ ] 5. Discussion (Elia).
- [ ] 6. Conclusion (Part 2/4) — restate finding, limitations, policy.
- [ ] References.
- [ ] Appendix (optional) — extra figures/tables, robustness.

## 2. Figures — pull from `figures/` (use the PDF for print quality)
Place each with a number, caption, and the source note already on the figure.
- [ ] Fig 1 `fig1_gpr_and_brent` — GPR and Brent price, 1990–2026 (scene-setter).
- [ ] Fig 2 `fig2_realized_vol_long_run` — long-run realized vol.
- [ ] Fig 3 `fig3_event_study_panel` — event-study panel (key comparison).
- [ ] **Fig 4 `fig4_2025_vs_2026` — the headline; feature it prominently.**
- [ ] Fig 5 `fig5_small_multiples_vol_gprd` — small multiples.
- [ ] Fig 6 `fig6_garch_conditional_vol` — GARCH conditional vol.
- [ ] Fig 7 `fig7_local_projection_irf` — impulse response.
- [ ] Fig 8 `fig8_days_to_revert_by_disruption` — the mechanism chart.
- [ ] Check every figure: 300 dpi, consistent font, axis labels with units, one
      colour per episode (consistent across all figures), source note present.

## 3. Tables — pull from `tables/` (the `.txt` versions drop in cleanly)
- [ ] Table 1 `table1_summary_stats` — summary statistics.
- [ ] Table 2 `table2_event_summary` — trigger, peak vol, days-to-revert, disruption.
- [ ] Table 3 `table3_garch_formatted` — GARCH estimates.
- [ ] Table 4 `table4_correlations`, `table4_event_regression`,
      `table4_local_projection` — regression/correlation results.
- [ ] Table 5 `table5_robustness_days_to_revert` — robustness.
- [ ] Table 6 `table6_iran_proxy_comparison` — Saudi-vs-Israel proxy justification.
- [ ] Reformat each into the document's table style; keep numbers identical to source.

## 4. Cross-referencing and consistency pass
- [ ] Every "Figure N"/"Table N" in the text matches the actual artifact.
- [ ] Episode names are identical everywhere (Gulf War 1990; Iran sanctions 2018;
      Russia–Ukraine 2022; Twelve-Day War 2025; 2026 Iran campaign; 2026 Strait
      closure) and the per-episode colours match across all figures.
- [ ] Notation is consistent (realized vol in %, annualised; event time in trading
      days; GPRD vs GPR monthly used correctly).
- [ ] Key numbers agree across sections (peak vols, days-to-revert, α+β = 0.993).
      Spot-check against `output/results_summary.md`.
- [ ] Define each acronym once (GPR, GPRD, OVX, JCPOA, EIA, GARCH, HAC).

## 5. References / citations
- [ ] Caldara, D. and Iacoviello, M. (2022), "Measuring Geopolitical Risk",
      *American Economic Review*.
- [ ] U.S. Energy Information Administration (EIA) — Brent (RBRTE), WTI (RWTC),
      data accessed June 2026.
- [ ] Kilian (oil supply/demand shocks) and any GARCH reference (Bollerslev 1986)
      cited in methods.
- [ ] Source notes on figures read "Source: EIA, Caldara and Iacoviello (2022),
      authors' calculations" — keep consistent with the reference list.

## 6. Reproducibility / data availability statement
- [ ] Add a short statement pointing to the repo
      (`github.com/DucoJPMol/oil_gpr_volatility`) and noting the EIA key requirement
      and the run order (`code/00`–`07`).

## 7. Final pass before submission
- [ ] Word/page count within limit.
- [ ] Abstract written and consistent with the conclusion.
- [ ] All figures/tables referenced in text and numbered in order of appearance.
- [ ] One read-through for flow across the four authors' sections (smooth handoffs,
      no repeated definitions, consistent tense and voice).
- [ ] Export to the required submission format (PDF) and check figures render at
      full resolution.

## 8. Open items to chase
- [ ] OVX cross-check and the reserves/gas extensions are pending (Duco) — decide
      whether they make this draft or the final.
- [ ] Confirm the 2026 mechanism codings have sources attached before submission.
