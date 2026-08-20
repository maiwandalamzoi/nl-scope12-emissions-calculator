"""
Download and parse the official Dutch emission factors list from
co2emissiefactoren.nl -- an initiative of Milieu Centraal, Stichting
Stimular, SKAO (the body behind the CO2-Prestatieladder scheme), Connekt
and the Dutch government. This is the standard reference Dutch companies
use for CO2-Prestatieladder / CSRD emissions reporting.

The file is a real, structured, government-affiliated Excel export -- not
scraped or guessed. Its layout is genuinely inconsistent between sections
(confirmed by direct inspection, not assumed): fuel subsections combine
their name and unit label on one row ("Fossiele brandstoffen  Kg CO2-eq /
eenheid"), while Elektriciteit/Warmtelevering split those across two rows.
Some fuel categories (liquid/solid fuels) only report a TTW (combustion)
value with no WTW (well-to-wheel) total. This parser was iterated against
the real downloaded file until every row category actually appeared in the
output -- not written from assumption alone.

Usage:
    python src/extract_factors.py
"""
from pathlib import Path

import pandas as pd
import requests

YEAR = 2026
DOWNLOAD_URL = f"https://co2emissiefactoren.nl/factoren/{YEAR}/download/"
RAW_XLSX = Path(__file__).resolve().parent.parent / "data" / "raw" / f"nl_emission_factors_{YEAR}.xlsx"
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "emission_factors.csv"

# Sections relevant to Scope 1 (fuels burned on-site / in owned vehicles,
# refrigerant leakage) and Scope 2 (purchased electricity, heat). Business
# travel (air/rail/bus/car-as-passenger) and most refrigerant blends are
# deliberately left out of THIS tool -- see README for the honest scope
# statement (this is not a full Scope 1-3 audit).
IN_SCOPE_SUBSECTIONS = {
    "Fossiele brandstoffen", "Fossiele brandstoffen met bio-bijmenging",
    "Hernieuwbare brandstoffen", "Gasvormige brandstoffen",
    "Vloeibare brandstoffen", "Vaste Brandstoffen",
    "Elektriciteit", "Warmtelevering",
}
SCOPE_MAP = {
    "Fossiele brandstoffen": "1", "Fossiele brandstoffen met bio-bijmenging": "1",
    "Hernieuwbare brandstoffen": "1", "Gasvormige brandstoffen": "1",
    "Vloeibare brandstoffen": "1", "Vaste Brandstoffen": "1",
    "Elektriciteit": "2", "Warmtelevering": "2",
}


def download():
    RAW_XLSX.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(DOWNLOAD_URL, timeout=30)
    resp.raise_for_status()
    RAW_XLSX.write_bytes(resp.content)
    print(f"Downloaded {len(resp.content):,} bytes to {RAW_XLSX}")


def safe_float(v):
    # float(nan) succeeds and returns nan (it IS a valid float) -- pandas'
    # own NaN sentinel passes straight through a bare try/except here, so
    # an explicit pd.isna() check is required or every "is not None"
    # fallback check downstream silently never fires. Confirmed by hitting
    # exactly this bug once already in this file.
    if pd.isna(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def is_blank_row(row):
    return all(pd.isna(row[c]) for c in ["c1", "c2", "c3", "c4", "unit", "mj"])


def parse():
    df = pd.read_excel(RAW_XLSX, header=None)
    df = df.iloc[:, :7]
    df.columns = ["name", "c1", "c2", "c3", "c4", "unit", "mj"]

    rows = []
    current_subsection = None

    for _, row in df.iterrows():
        name = row["name"]
        name_str = str(name).strip() if pd.notna(name) else None

        # Combined "name + CO2-eq unit label" row (fuel-style subsections):
        # e.g. name="Fossiele brandstoffen", c1="Kg CO2-eq / eenheid".
        if name_str and isinstance(row["c1"], str) and "CO" in row["c1"] and pd.isna(row["c2"]):
            current_subsection = name_str
            continue

        # Pure section-name row, everything else blank: could be a top
        # section ("Brandstoffen voertuigen en schepen") OR a subsection
        # that has no separate combined-header row (Elektriciteit,
        # Warmtelevering). Only treat it as the active subsection if it's
        # one of ours -- otherwise a real fuel-subsection header row will
        # follow and set current_subsection correctly.
        if name_str and is_blank_row(row):
            if name_str in IN_SCOPE_SUBSECTIONS:
                current_subsection = name_str
            else:
                current_subsection = None
            continue

        # Column-meaning header row (name is blank, c1 starts a "Totaal.../
        # GWP100/..." label) -- not needed for parsing, values are always
        # in the same column positions; skip.
        if name_str is None and pd.notna(row["c1"]):
            continue

        # Actual data row.
        if name_str is None or current_subsection not in IN_SCOPE_SUBSECTIONS:
            continue
        if str(row["c1"]).strip() == "Vervallen":
            continue

        wtw = safe_float(row["c1"])
        ttw = safe_float(row["c2"])
        # Some categories (liquid/solid fuels) only report a TTW combustion
        # value with no separate WTW total -- fall back to it rather than
        # dropping the row, and say so explicitly in the output.
        value = wtw if wtw is not None else ttw
        if value is None:
            continue

        rows.append({
            "scope": SCOPE_MAP[current_subsection],
            "subsection": current_subsection,
            "name": name_str,
            "value_kg_co2e_per_unit": value,
            "value_basis": "WTW (well-to-wheel)" if wtw is not None else "TTW (combustion only, no WTW reported)",
            "wtt_kg_co2e_per_unit": safe_float(row["c3"]),
            "biogenic_kg_co2e_per_unit": safe_float(row["c4"]),
            "unit": row["unit"],
        })

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"Parsed {len(out)} emission factor rows -> {OUT_CSV}")
    print(out.groupby(["scope", "subsection"]).size())
    return out


if __name__ == "__main__":
    download()
    parse()
