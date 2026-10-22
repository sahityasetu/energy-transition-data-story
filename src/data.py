"""Load the Our World in Data energy dataset and build the tables behind each chart.

All electricity values are in TWh. 2025 is excluded because only about half of the countries have reported it.
"""
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "owid-energy-data.csv"
URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
LAST_YEAR = 2024

# Display order: fossil sources at the bottom of stacks, then low-carbon
SOURCES = {
    "coal": "Coal", "gas": "Gas", "oil": "Oil", "nuclear": "Nuclear",
    "hydro": "Hydro", "wind": "Wind", "solar": "Solar", "other_renewable": "Bioenergy & other",
}


def load() -> pd.DataFrame:
    if not CSV.exists():
        CSV.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, CSV)
    df = pd.read_csv(CSV)
    return df[df["year"] <= LAST_YEAR]


def countries(df: pd.DataFrame) -> pd.DataFrame:
    """Real countries only: OWID aggregates (World, continents, income groups) have no ISO code or an OWID_ code."""
    iso = df["iso_code"].fillna("")
    return df[(iso != "") & ~iso.str.startswith("OWID")]


def mix(df: pd.DataFrame, country: str, start: int = 2000) -> pd.DataFrame:
    """Generation by source (TWh), one row per year, columns in SOURCES order."""
    part = df[(df["country"] == country) & (df["year"] >= start)].set_index("year")
    out = part[[f"{s}_electricity" for s in SOURCES]].copy()
    out.columns = list(SOURCES.values())
    return out.dropna(how="all").fillna(0)


def change_table(df: pd.DataFrame, start: int = 2014, end: int = LAST_YEAR, min_twh: float = 100) -> pd.DataFrame:
    """Country-level change between two years, for countries generating at least `min_twh` in the end year."""
    c = countries(df)
    a = c[c["year"] == start].set_index("country")
    b = c[c["year"] == end].set_index("country")
    keep = b.index[b["electricity_generation"] >= min_twh].intersection(a.index)
    a, b = a.loc[keep], b.loc[keep]
    t = pd.DataFrame({
        "iso_code": b["iso_code"],
        "generation_start": a["electricity_generation"],
        "generation_end": b["electricity_generation"],
        "fossil_start": a["fossil_electricity"],
        "fossil_end": b["fossil_electricity"],
        "low_carbon_start": a["low_carbon_electricity"],
        "low_carbon_end": b["low_carbon_electricity"],
        "solar_wind_share_start": a["solar_share_elec"] + a["wind_share_elec"],
        "solar_wind_share_end": b["solar_share_elec"] + b["wind_share_elec"],
        "low_carbon_share_end": b["low_carbon_share_elec"],
    }).dropna()
    t["demand_growth_pct"] = (t["generation_end"] / t["generation_start"] - 1) * 100
    t["fossil_change_pct"] = (t["fossil_end"] / t["fossil_start"] - 1) * 100
    t["solar_wind_gain_pts"] = t["solar_wind_share_end"] - t["solar_wind_share_start"]
    # Of the extra electricity a country needed, how much came from low-carbon sources?
    growth = t["generation_end"] - t["generation_start"]
    t["clean_share_of_growth_pct"] = ((t["low_carbon_end"] - t["low_carbon_start"]) / growth * 100).where(growth > 0)
    return t.sort_values("fossil_change_pct")


def world_kpis(df: pd.DataFrame, start: int = 2014, end: int = LAST_YEAR) -> dict:
    w = df[df["country"] == "World"].set_index("year")
    get = lambda col, y: float(w.loc[y, col])  # noqa: E731
    return {
        "low_carbon_share": (get("low_carbon_share_elec", start), get("low_carbon_share_elec", end)),
        "solar_wind_share": (get("solar_share_elec", start) + get("wind_share_elec", start),
                             get("solar_share_elec", end) + get("wind_share_elec", end)),
        "coal_share": (get("coal_share_elec", start), get("coal_share_elec", end)),
        "carbon_intensity": (get("carbon_intensity_elec", start), get("carbon_intensity_elec", end)),
        "generation": (get("electricity_generation", start), get("electricity_generation", end)),
        "fossil": (get("fossil_electricity", start), get("fossil_electricity", end)),
    }
