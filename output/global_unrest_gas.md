# Global unrest and the energy complex — the gas dimension

*Context document (extension C). This is supporting depth for the discussion, not
a core result. It uses natural gas to make the point that a geopolitical conflict
is rarely an "oil-only" event — it propagates across the whole energy complex, and
sometimes lands hardest somewhere other than crude.*

## The point in one paragraph
Geopolitical conflict raises *global* energy-market unrest, not just oil
volatility. Geopolitical risk (GPR) measures attention to the conflict as a whole;
that attention shows up across crude, natural gas, power and freight at once.
Looking only at oil can therefore understate — or misattribute — the disruption.
Natural gas is the clearest example: in several of our episodes the gas-volatility
response is larger than the oil response.

## What the data show (Henry Hub, EIA)
Peak 21-day realized volatility in the −10/+60 window, gas vs oil (`table8_gas_vs_oil`):

| Episode | Oil peak vol | Gas peak vol | Gas ÷ Oil |
|---|---|---|---|
| Iran sanctions 2018 | 38% | 36% | 0.97 |
| Russia–Ukraine 2022 | 91% | 165% | **1.82** |
| Twelve-Day War 2025 | 53% | 132% | 2.52 |
| 2026 Iran campaign | 114% | 662% | 5.79 |
| 2026 Strait closure | 114% | 662% | 5.79 |

Gas volatility exceeds oil volatility in every conflict-driven episode, often by a
wide margin. (Gulf War 1990 is excluded — Henry Hub data begin in 1997.)

## Russia–Ukraine 2022: a gas shock first, an oil shock second
This is the key case for the discussion. The 2022 episode is commonly framed as an
oil event, but Russia is a far larger player in *gas*, and the shock landed hardest
there. Figure 9 (`fig9_oil_vs_gas_russia`) shows gas volatility already elevated
*going into* the invasion — the European gas crisis had been building since late
2021 — while oil volatility rose afterward. The implication for the paper: Russia
belongs in the sample as a major-exporter sanctions shock, but its primary
transmission was through gas, and our oil-only persistence number for 2022 (61
days) should be read with that caveat.

## Important caveat — Henry Hub understates it
Henry Hub is the **US** benchmark, and the US is relatively insulated (a net
exporter with its own production). The 2022 Russian shock actually hit hardest in
**European TTF** gas, which spiked far more than Henry Hub. TTF is **not available
on the EIA API**, so we proxy with Henry Hub and flag that it *understates* the
true European gas disruption. If the group wants the full picture, TTF would need
a separate data source (ICE / Refinitiv / a manual download). Gas markets are
regional, so this regional caveat matters.

## How to use this in the paper
- A discussion paragraph supporting the "global unrest" framing: conflicts raise
  volatility across the correlated energy complex (oil, gas, power, freight), which
  is consistent with GPR being an *attention* measure spanning the whole event.
- A qualification on the Russia 2022 episode: include it, but note the gas-first
  transmission and that Henry Hub understates the European shock.
- A limitation line: European TTF gas is the more relevant benchmark for Russia and
  is a known data gap.

## Reproduce
`python code/08_gas_context.py` (needs `EIA_API_KEY`) → `table8_gas_vs_oil`,
`fig9_oil_vs_gas_russia`. Raw gas cached at `data/raw/raw_eia_gas.csv`.
