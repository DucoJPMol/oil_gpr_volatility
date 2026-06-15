# Handoff message to the group (paste into Teams / email)

---

Hi all,

Part 3 (data + methodology) is done and in the shared repo:
**https://github.com/DucoJPMol/oil_gpr_volatility**

**What's there**
- Full pipeline, `code/00`–`07`, runs end to end and reproduces every number.
- 8 figures (PNG + PDF, 300 dpi) in `figures/`, 9 tables (CSV + paper-ready TXT) in `tables/`.
- `output/results_summary.md` — one-page plain-language summary of the findings (for Elia / Part 4).
- `output/methodology.md` — the replicable Data & Methodology section.

**Headline result.** Volatility from real supply disruption persists; volatility from headlines fades. Days until 21-day Brent realized vol settles back: Gulf War 1990 = 178 trading days, 2018 JCPOA = 2, Russia–Ukraine 2022 = 61, Twelve-Day War 2025 = 27, and both 2026 episodes still elevated at the cutoff. GARCH(1,1) persistence α+β = 0.993. The 2025-vs-2026 contrast (Figure 4) is the strongest visual.

**Two methodology decisions I need you to sign off (both touch locked parameters):**
1. **Days-to-revert** is measured from the volatility spike onset, not from day zero. Without this the 2022 and 2025 episodes return a spurious "0" (21-day realized vol is backward-looking, so at the trigger it still reflects the calm pre-event window).
2. **Iran proxy = Israel (GPRC_ISR).** Caldara–Iacoviello's country set has 44 countries and no Iran index, so the Iran-centric episodes use Israel as the nearest covered proxy, alongside the overall daily GPRD.

**Two things I need from the group:**
- The **2026 Strait/supply codings** are provisional (mine are best-estimate) — whoever owns the mechanism sheet, please verify and add a source per episode.
- **Maxim (Part 1):** what format do you want the figures/tables in for the document? You currently have PNG + PDF + CSV.

**One caveat:** oil prices come from EIA (identical to FRED's Brent series — FRED was blocked on my network). OVX (the secondary implied-vol cross-check) isn't populated yet; it fills in automatically when the data script runs somewhere FRED is reachable. Not blocking.

Persistence numbers and the 2025-vs-2026 figure are ready for the 16 June progress meeting.

Duco

---
