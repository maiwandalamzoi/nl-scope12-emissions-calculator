# Netherlands Scope 1+2 Emissions Calculator

Enter real company activity data — fuel used, electricity purchased — and get a Scope 1+2 GHG
emissions estimate in kg CO2e, using real Dutch government-referenced emission factors. Every
number is your input multiplied by an official published factor, fully traceable to its source.

Author: **Maiwand Jan Alamzoi** — [m.alamzoi123@gmail.com](mailto:m.alamzoi123@gmail.com) · [github.com/maiwandalamzoi](https://github.com/maiwandalamzoi)

---

## Problem statement

The EU's CSRD (Corporate Sustainability Reporting Directive) is making GHG Protocol Scope 1-2-3
emissions reporting mandatory for a growing number of companies — and it cascades down the
supply chain, so even SMEs get asked for their numbers by bigger clients. Scope 1 (fuel you
burn directly) and Scope 2 (electricity/heat you purchase) are the most tractable place to
start: unlike Scope 3, the activity data (litres of diesel, kWh of electricity) is usually
something a company already has, and the official conversion factors are public.

**What this is**: a calculator that turns real activity data into a real Scope 1+2 emissions
estimate, using the same official factors Dutch companies use for CO2-Prestatieladder/CSRD
reporting. **What this is not**: a full Scope 1-2-3 audit or CSRD compliance tool — Scope 3
(supplier emissions, business travel, product use — often 70%+ of a company's real footprint)
is deliberately not included, because it needs supplier/activity data no public-data tool can
get. That limitation is stated in the app itself, not hidden.

## Data source

[co2emissiefactoren.nl](https://co2emissiefactoren.nl/) — an initiative of Milieu Centraal,
Stichting Stimular, SKAO (the body behind the Dutch CO2-Prestatieladder scheme), Connekt and
the Dutch government. This is the standard reference list Dutch companies already use for
CO2-Prestatieladder and CSRD emissions reporting — not a generic international factor set
retrofitted onto the Netherlands (UK DEFRA factors, the other major free public source, use a
UK-specific electricity grid mix that would give the wrong answer for a Dutch company).

63 factors covering:

| Scope | Category | Examples |
|---|---|---|
| 1 | Fossil fuels | Petrol, diesel, LPG, hydrogen (grey), kerosene, methanol |
| 1 | Fuels with bio-blend | E10 petrol, B7 diesel, HVO30 |
| 1 | Renewable fuels | Green hydrogen, biodiesel (HVO/FAME), bio-CNG/LNG, SAF |
| 1 | Gaseous fuels | Natural gas, biogas (4 production routes), propane |
| 1 | Liquid & solid fuels | Crude oil derivatives, coal, coke, peat |
| 2 | Electricity | Grey power (0.483 kg CO2e/kWh), grid-mix average (0.244), wind/solar/hydro (~0), biomass |
| 2 | District heating | Average heat networks, waste-heat-only networks |

Both WTW (well-to-wheel, includes upstream production emissions) and TTW (tank-to-wheel,
combustion only) values are used depending on what the source reports for each category —
labeled explicitly per row, never silently conflated.

## Method

1. **`src/extract_factors.py`** — downloads the current year's official factor list and parses
   it into a clean table. The source file's layout is genuinely inconsistent between sections
   (confirmed by direct inspection, not assumed): fuel subsections combine their name and unit
   label on one row, while electricity/heat split that across two rows, and some fuel
   categories only report a TTW value with no WTW total. The parser was iterated against the
   real downloaded file until every category appeared with correct values — this caught two
   real bugs along the way (documented in the script and the commit history), including one
   classic pandas gotcha: `float(nan)` succeeds in Python and returns `nan`, not `None`, so a
   bare `try/except` never catches it — an explicit `pd.isna()` check was required.
2. **`app_streamlit.py`** — pick fuel/energy types and enter real quantities, get a Scope 1+2
   breakdown and total, with the full source factor table available for inspection.

## Verified real calculation

1,000 litres of petrol (Fossiele brandstoffen — Benzine E0, 3.059 kg CO2e/litre) + 500 kWh of
grey electricity (0.483 kg CO2e/kWh) = **3,300.5 kg CO2e** (3,059 Scope 1 + 241.5 Scope 2) —
checked by hand against the app's output before considering this "working."

## Reproduce it

```bash
git clone https://github.com/maiwandalamzoi/nl-scope12-emissions-calculator.git
cd nl-scope12-emissions-calculator
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt

python src/extract_factors.py   # re-downloads and re-parses the current year's factors
streamlit run app_streamlit.py
```

The parsed factor table (`data/processed/emission_factors.csv`) is committed, so
`streamlit run app_streamlit.py` alone works immediately without re-running extraction.

## License

MIT for the code — see [LICENSE](LICENSE). Underlying emission factors: co2emissiefactoren.nl,
please credit them directly if you reuse the factor values elsewhere.
