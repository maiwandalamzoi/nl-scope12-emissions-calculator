"""
Netherlands Scope 1+2 Emissions Calculator.

Real Dutch government-referenced emission factors (co2emissiefactoren.nl --
Milieu Centraal, Stichting Stimular, SKAO, Connekt, Dutch government).
Enter your company's real activity data (fuel used, electricity purchased)
and get a Scope 1+2 emissions estimate in kg CO2e, with every factor traced
back to its official source.

Scope 3 is NOT covered -- see the "About" tab for why.

Run:
    streamlit run app_streamlit.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
FACTORS_PATH = ROOT / "data" / "processed" / "emission_factors.csv"

st.set_page_config(page_title="NL Scope 1+2 Emissions Calculator", layout="wide")


@st.cache_data
def load_factors():
    df = pd.read_csv(FACTORS_PATH)
    df = df.dropna(subset=["value_kg_co2e_per_unit"])
    return df


def main():
    st.title("🇳🇱 Netherlands Scope 1+2 Emissions Calculator")
    st.caption(
        "Real emission factors from [co2emissiefactoren.nl](https://co2emissiefactoren.nl/) -- "
        "an initiative of Milieu Centraal, Stichting Stimular, SKAO (the CO2-Prestatieladder "
        "body), Connekt and the Dutch government. No estimation beyond what you enter -- every "
        "number below is your input multiplied by an official published factor."
    )

    factors = load_factors()
    scope1 = factors[factors["scope"] == 1]
    scope2 = factors[factors["scope"] == 2]

    tab_calc, tab_about = st.tabs(["🧮 Calculator", "ℹ️ About the data & scope"])

    with tab_calc:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Scope 1 — fuel you burn directly")
            st.caption("Company vehicles, on-site heating, owned generators/machinery.")
            n1 = st.number_input("How many Scope 1 fuel entries?", min_value=0, max_value=10, value=1, key="n1")
            scope1_rows = []
            for i in range(n1):
                c1, c2 = st.columns([2, 1])
                options = (scope1["subsection"] + " — " + scope1["name"] + " (" + scope1["unit"] + ")").tolist()
                choice = c1.selectbox(f"Fuel #{i+1}", options, key=f"s1_choice_{i}")
                idx = options.index(choice)
                row = scope1.iloc[idx]
                qty = c2.number_input(f"Quantity ({row['unit']})", min_value=0.0, value=0.0, key=f"s1_qty_{i}")
                scope1_rows.append((row, qty))

        with col2:
            st.subheader("Scope 2 — purchased energy")
            st.caption("Electricity and district heating you buy, not generate yourself.")
            n2 = st.number_input("How many Scope 2 entries?", min_value=0, max_value=10, value=1, key="n2")
            scope2_rows = []
            for i in range(n2):
                c1, c2 = st.columns([2, 1])
                options = (scope2["subsection"] + " — " + scope2["name"] + " (" + scope2["unit"] + ")").tolist()
                choice = c1.selectbox(f"Energy #{i+1}", options, key=f"s2_choice_{i}")
                idx = options.index(choice)
                row = scope2.iloc[idx]
                qty = c2.number_input(f"Quantity ({row['unit']})", min_value=0.0, value=0.0, key=f"s2_qty_{i}")
                scope2_rows.append((row, qty))

        st.divider()

        breakdown = []
        for row, qty in scope1_rows + scope2_rows:
            if qty <= 0:
                continue
            emissions_kg = qty * row["value_kg_co2e_per_unit"]
            breakdown.append({
                "Scope": f"Scope {int(row['scope'])}",
                "Item": row["name"],
                "Quantity": qty,
                "Unit": row["unit"],
                "Factor (kg CO2e/unit)": row["value_kg_co2e_per_unit"],
                "Basis": row["value_basis"],
                "Emissions (kg CO2e)": round(emissions_kg, 1),
            })

        if breakdown:
            df_breakdown = pd.DataFrame(breakdown)
            total = df_breakdown["Emissions (kg CO2e)"].sum()
            s1_total = df_breakdown[df_breakdown["Scope"] == "Scope 1"]["Emissions (kg CO2e)"].sum()
            s2_total = df_breakdown[df_breakdown["Scope"] == "Scope 2"]["Emissions (kg CO2e)"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Total (Scope 1+2)", f"{total:,.0f} kg CO2e", f"{total/1000:,.2f} tonnes")
            c2.metric("Scope 1 subtotal", f"{s1_total:,.0f} kg CO2e")
            c3.metric("Scope 2 subtotal", f"{s2_total:,.0f} kg CO2e")

            st.dataframe(df_breakdown, width="stretch")
        else:
            st.info("Enter a quantity above (>0) for at least one item to see a calculation.")

    with tab_about:
        st.subheader("Where this data comes from")
        st.markdown(
            "All factors come from the official Dutch reference list at "
            "[co2emissiefactoren.nl](https://co2emissiefactoren.nl/) -- used as the standard "
            "basis for CO2-Prestatieladder and CSRD emissions reporting in the Netherlands. "
            "**WTW** (well-to-wheel) factors, where available, include both the emissions from "
            "burning the fuel and the emissions from producing/transporting it. A few fuel "
            "categories in the source only report a **TTW** (tank-to-wheel, combustion-only) "
            "value -- those are labeled as such in the 'Basis' column above, not silently "
            "treated as equivalent to WTW."
        )
        st.subheader("What this tool does NOT cover — read this before using it for real reporting")
        st.markdown(
            "- **Scope 3 is not included at all.** Purchased goods and services, upstream "
            "transport, business travel, employee commuting, use of sold products -- none of "
            "that is here. For most companies Scope 3 is the *majority* of total emissions, "
            "often 70%+. This tool alone is not a CSRD-compliant full emissions inventory.\n"
            "- Only fuels and electricity/heat categories are included -- not refrigerant "
            "leakage, business travel, or other Scope 1/2 edge cases also covered by the "
            "source list.\n"
            "- This is a calculator over real official factors, not an audit or verification "
            "service -- the accuracy of the result depends entirely on the accuracy of the "
            "activity data you enter."
        )
        st.caption("Raw factor table, for transparency:")
        st.dataframe(factors, width="stretch")


if __name__ == "__main__":
    main()
