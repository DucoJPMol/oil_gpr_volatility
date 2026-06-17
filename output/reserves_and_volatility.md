# Oil reserves and volatility — what happens when the buffer runs low

*Extension D. Supporting depth for the discussion. The honest finding is more
nuanced than "low reserves → high volatility", and that nuance is itself useful.*

## The headline, stated honestly
Inventories alone **do not** predict oil volatility. Across 1990–2026 the
correlation between reserve adequacy (commercial crude stocks vs their trailing
5-year mean) and Brent realized vol is a weak **+0.11**, and average vol is
actually *lower* when reserves are low (31.6%) than when they are ample (37.2%).
The reason is that the biggest volatility events were **demand collapses**
(2008–09, 2020), during which inventories *built to records* even as vol
exploded. So a simple "empty tanks → panic" story does not survive the data
(Figure 13).

## Where reserves *do* matter: the buffer is deployed in disruptions
The reserves story for *geopolitical* episodes is about the **SPR buffer being
actively used**, not the inventory level on the day (Table 10, Figure 14):

| Episode | Commercial stock (mb) | Reserve adequacy | SPR draw over window (mb) |
|---|---|---|---|
| Gulf War 1990 | 365 | +2.7 (ample) | +3 |
| Iran sanctions 2018 | 432 | +0.1 | −2 |
| Russia–Ukraine 2022 | 413 | **−1.2 (low)** | **−48** |
| Twelve-Day War 2025 | 421 | −0.9 | +3 |
| 2026 Iran campaign | 439 | +0.2 | **−50** |
| 2026 Strait closure | 443 | +0.4 | **−58** |

Two patterns stand out:
- **2022** is the one episode that began with reserves *already* dangerously low
  (−1.2 SD), and it coincided with the largest emergency **SPR release** in
  history (the −48 mb here is just the 60-trading-day window; the full 2022
  drawdown was ~180 mb).
- The **2026** episodes show the buffer being drawn down hard (SPR −50 to −58 mb)
  *while volatility stays elevated* (both are still-elevated / censored). That is
  consistent with the "second spike" idea: when a disruption runs long and the
  buffer is being depleted to contain it, volatility does not settle.

## The "second spike" reading
The mechanism the presentation asked about — *if reserves run out, a second spike
could come* — is **suggestive but not proven** here. What the data support is
weaker and more defensible: in the persistent disruption episodes (2022, 2026)
the authorities deploy the buffer (large SPR draws), and volatility stays high
while that is happening. Whether a *second* spike follows full depletion is not
something the current sample can establish (no episode fully exhausts the SPR),
so frame it as a hypothesis, not a result.

## Caveats
- US-centric: commercial stocks and the SPR are US series; OECD inventories and
  OPEC spare capacity (the global buffer) are in EIA's STEO dataset and are not
  yet included — a natural next step.
- Weekly inventory data aligned to daily vol by nearest week.
- The reserve–vol relationship is confounded by demand shocks; do not overclaim.

## Reproduce
`python code/10_reserves.py` (needs `EIA_API_KEY`) → `table10_reserves_context`,
`fig13_reserves_vs_vol`, `fig14_buffer_drawdown`. Raw stocks cached at
`data/raw/raw_eia_stocks_*.csv`.
