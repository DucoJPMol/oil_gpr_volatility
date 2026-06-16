# Extension plan — post-presentation feedback (16 June 2026)

Four pointers from the mock presentation, turned into a step-by-step plan.
Ordered quickest-win first. Each workstream lists: goal, data, code, outputs,
and the decisions/risks to settle before starting.

## Decisions confirmed + data findings (16 June 2026)
- **A — Saudi proxy: CONFIRMED and DONE.** Proxy switched to `GPRC_SAU`; Table 6
  added documenting why (Israel spikes z=6.3/10.0 vs Saudi 0.6/5.8 in 2025/2026).
- **B — futures: CONFIRMED WTI-only.** EIA key still valid, but the WTI futures
  series IDs need discovery (the petroleum/pri/fut route returned empty for the
  guessed IDs) — first task of B.
- **C — gas: go ahead, but as a STANDALONE context document**
  (`output/global_unrest_gas.md`) framing global unrest during conflicts. Henry
  Hub gas (`RNGWHHD`) is confirmed reachable on EIA; European TTF is not on EIA.
- **D — reserves: focus on what happened when reserves ran dangerously low** and
  how that fed oil prices and global volatility. **Add OVX** — but OVX (FRED
  `OVXCLS`) is still blocked on this network (FRED and Yahoo both walled off), so
  OVX needs a **manual browser download** (CBOE/Yahoo/investing.com) into
  `data/raw`, like the GPR files. Build the loader to read that file.

## Shared prerequisite (do once, enables A/B/C)
The EIA fetcher (`fetch_eia` in `01_get_and_clean_data.py`) is hardcoded to one
route (`petroleum/pri/spt`). Generalise it to take a dataset route so we can pull
futures, gas, and stocks from EIA with the same code and caching.
- [ ] Refactor `fetch_eia(series_id, route=..., facet="series")`; keep spot as default.
- [ ] Add a small registry in `config.py` mapping each new series to its route.
- Effort: S. Risk: low.

---

## A. Iran proxy: Israel → Saudi Arabia  (pointer 4) — START HERE
**Goal.** Israel is Iran's adversary, so `GPRC_ISR` may load Israel-specific risk
into the Iran episodes and confound the signal. Switch the proxy to Saudi Arabia
(an oil-exporting neighbour, less of an adversary confound), and show the result
is not driven by the proxy choice.

**Steps.**
- [ ] `config.py`: set `GPR_IRAN_PROXY = "SAU"` (SAU is already in `GPR_COUNTRIES`;
      keep `ISR` in the list for the comparison). This auto-retags the 2018/2025/
      2026 episodes.
- [ ] Add a robustness comparison: for each Iran episode, correlate realized vol
      with GPRD, `GPRC_SAU`, and `GPRC_ISR` side by side (new small table).
- [ ] Re-run `01`–`07`; regenerate figures/tables that reference the country index.
- [ ] Update `methodology.md` and `results_summary.md` (state SAU as main proxy,
      ISR as a robustness check).
- **Outputs.** Updated Table 2; new `table6_iran_proxy_comparison.csv`; updated docs.
- **Decision needed.** Confirm SAU (vs EGY/TUR or GPRD-only) as the main proxy.
- Effort: S. Risk: low. Note: this is a locked-parameter change — but the group
  asked for it, so it's sanctioned; record it in the methodology.

---

## B. Spot vs futures term structure  (pointer 1)
**Goal.** Long conflicts show up in the futures curve: a persistent disruption
pushes the front into backwardation and widens the spot–deferred spread. Compare
spot to futures and track the basis across each episode to read how the market
prices conflict *duration*.

**Steps.**
- [ ] Add WTI futures contracts 1–4 from EIA (`RCLC1`–`RCLC4`, route
      `petroleum/pri/fut`) — same source/key, full history. (Brent ICE futures are
      not on EIA; see risk.)
- [ ] Build the term structure: spot−C1 basis and the C1−C4 spread (backwardation
      indicator); add to the daily panel and the event panel.
- [ ] New figure: spot, C1, C4 and the C1−C4 spread around each episode (esp. the
      long ones: 1990, 2022, 2026), showing the curve shifting as the conflict drags.
- [ ] New table: average basis / backwardation per episode window.
- **Outputs.** New figure(s), `table7_term_structure.csv`, doc paragraph.
- **Risk / decision.** EIA has the WTI curve but not ICE Brent futures. Options:
  (i) do the futures analysis on WTI (clean, all-EIA); (ii) source Brent futures
  (BZ=F) elsewhere. Recommend starting with WTI and noting Brent as a possible add.
- Effort: M.

---

## C. Gas price shock — reframing Russia  (pointer 3)
**Goal.** The 2022 Russia–Ukraine shock was primarily a *gas* event. Add a gas
view to (a) justify/qualify Russia's place in an oil-vol study and (b) show the
gas-vol response dwarfs the oil-vol response there.

**Steps.**
- [ ] Add Henry Hub natural-gas daily spot from EIA (`RNGWHHD`, route
      `natural-gas/pri/fut` or the NG spot route) and build gas realized vol with
      the same 21-day method.
- [ ] Compare oil vs gas realized vol around the Russia episode (and others) —
      new overlay figure; quantify peak and days-to-revert for gas vs oil.
- [ ] Add a short reframing paragraph: Russia is included as a major-exporter
      sanctions shock; the gas panel shows where the bigger disruption actually was.
- **Outputs.** New figure (oil vs gas vol, Russia), `table8_gas_vs_oil.csv`, doc text.
- **Risk / decision.** Henry Hub (US) is on EIA; European **TTF** (more relevant to
  the Russia gas shock) is not on EIA and needs another source. Recommend Henry Hub
  first, flag TTF as a known gap, decide with the group whether to source TTF.
- Effort: M.

---

## D. Oil reserves / inventories and the "second spike"  (pointer 2)
**Goal.** Inventories and spare capacity buffer the price; the depth of the buffer
may explain *how long* vol persists, and a depleting buffer could trigger a second
spike. Bring inventories into the story.

**Steps.**
- [ ] Pull from EIA: US crude stocks excl. SPR (weekly, verify `WCESTUS1`), SPR
      stocks (`WCSSTUS1`), US crude production (shale buffer), and OPEC spare
      capacity / OECD inventories from the STEO dataset (verify series IDs).
- [ ] Overlay inventory levels/draws on price and vol within each episode; test
      whether low spare capacity / falling stocks line up with longer persistence.
- [ ] "Second-spike" check: within the long episodes, look for a second vol peak
      and relate it to inventory depletion (descriptive; flag any case found).
- **Outputs.** New figures (inventory vs vol per episode; spare capacity vs
      days-to-revert), `table9_inventory_context.csv`, doc text.
- **Risk / decision.** STEO series IDs need verifying; weekly stocks vs daily
  vol need an alignment rule (document it). This is the most exploratory pointer —
  partly descriptive rather than a clean test.
- Effort: L.

---

## Suggested order and rough effort
1. **A — Saudi proxy** (S) — quick, high-value, settles a methodology question.
2. **B — spot vs futures** (M) — clean, all-EIA (WTI).
3. **C — gas shock** (M) — Henry Hub from EIA; TTF a known gap.
4. **D — inventories / second spike** (L) — biggest, most exploratory.

Open decisions to raise with the group: (1) SAU vs another Iran proxy; (2) WTI-only
vs source Brent futures; (3) whether to source European TTF gas; (4) how exploratory
to make the inventory/second-spike analysis.
