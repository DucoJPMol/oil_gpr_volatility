# Handoff message to the group (paste into Teams / email)

---

Hi all,

Part 3 (data + methodology) is done and in the shared repo:
**https://github.com/DucoJPMol/oil_gpr_volatility**

**What's there**
- Full pipeline, `code/00`–`11`, runs end to end and reproduces every number.
- 15 figures (PNG + PDF, 300 dpi) in `figures/`, 12 paper tables (CSV + paper-ready TXT) in `tables/`.
- `output/results_summary.md` — plain-language summary of all findings (for Elia / Part 4).
- `output/methodology.md` — the replicable Data & Methodology section.
- **Detailed checklists for each of you:** `output/checklist_elia.md` (Results & Discussion) and `output/checklist_maxim.md` (Integration).

**Headline result.** Volatility from real supply disruption persists; volatility from headlines fades. Days until 21-day Brent realized vol settles back: Gulf War 1990 = 178 trading days, 2018 JCPOA = 2, Russia–Ukraine 2022 = 61, Twelve-Day War 2025 = 27, both 2026 episodes still elevated at the cutoff. GARCH(1,1) persistence α+β = 0.993. The 2025-vs-2026 contrast (Figure 4) is the strongest visual.

**Extensions done (post-presentation feedback).**
- *Spot vs futures (Fig 11):* in the 2026 disruption episodes WTI spot trades $2.5–8 above front-month futures — the longer a real disruption runs, the bigger the premium.
- *Gas / global unrest (Fig 9, `global_unrest_gas.md`):* European TTF gas vol hit 301% in 2022 = 3.3× the oil response — Russia was a gas-first shock.
- *Reserves & OPEC spare capacity (Figs 13–15, `reserves_and_volatility.md`):* the 2026 Strait closure had ~zero spare capacity (when the Strait closes, OPEC's Gulf buffer is trapped). Inventories don't predict vol unconditionally — it's the buffer × disruption interaction.
- *OVX + VIX* implied-vol cross-checks now included (Fig 12).
- *Iran proxy switched to Saudi Arabia* (Israel, Iran's adversary, was confounding — Table 6).

**Two methodology decisions I need you to sign off (both touch locked parameters):**
1. **Days-to-revert** is measured from the volatility spike onset, not from day zero. Without this the 2022 and 2025 episodes return a spurious "0" (21-day realized vol is backward-looking, so at the trigger it still reflects the calm pre-event window).
2. **Iran proxy = Saudi Arabia (GPRC_SAU).** No Iran index exists; Israel spiked far harder (z=6.3/10.0 vs 0.6/5.8) and would confound the signal. Headline results use the overall daily GPRD, so this doesn't move the main numbers.

**Two things I need from the group:**
- The **2026 Strait/supply codings** are provisional (mine are best-estimate) — whoever owns the mechanism sheet, please verify and add a source per episode.
- **Maxim (Part 1):** what format do you want the figures/tables in for the document? You currently have PNG + PDF + CSV (the `.txt` tables drop in cleanly).

**One caveat:** oil prices come from EIA (identical to FRED's Brent series — FRED was blocked on my network); OVX/VIX/TTF/CL futures were hand-downloaded. Everything reproduces with a free EIA key.

Persistence numbers and the 2025-vs-2026 figure are ready for the 16 June progress meeting.

Duco

---
