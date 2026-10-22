import pandas as pd
import pytest

from src.data import SOURCES, change_table, countries, mix


@pytest.fixture
def toy():
    rows = []
    for country, iso, gen, fossil, low in [("A", "AAA", (100, 150), (80, 100), (20, 50)),
                                           ("B", "BBB", (200, 180), (150, 90), (50, 90)),
                                           ("Small", "SML", (10, 12), (9, 10), (1, 2)),
                                           ("World", "OWID_WRL", (310, 342), (239, 200), (71, 142))]:
        for year, g, f, lc in zip((2014, 2024), gen, fossil, low):
            row = {"country": country, "iso_code": iso, "year": year, "electricity_generation": g,
                   "fossil_electricity": f, "low_carbon_electricity": lc, "solar_share_elec": lc / g * 50,
                   "wind_share_elec": lc / g * 50, "low_carbon_share_elec": lc / g * 100}
            row.update({f"{s}_electricity": g / len(SOURCES) for s in SOURCES})
            rows.append(row)
    return pd.DataFrame(rows)


def test_countries_drops_aggregates(toy):
    assert "World" not in set(countries(toy)["country"])


def test_change_table_filters_small_countries(toy):
    t = change_table(toy, 2014, 2024, min_twh=100)
    assert set(t.index) == {"A", "B"}


def test_change_table_math(toy):
    t = change_table(toy, 2014, 2024, min_twh=100)
    assert t.loc["A", "demand_growth_pct"] == pytest.approx(50)
    assert t.loc["A", "fossil_change_pct"] == pytest.approx(25)
    # A needed 50 TWh more and got 30 TWh more low-carbon power -> 60% of growth was clean
    assert t.loc["A", "clean_share_of_growth_pct"] == pytest.approx(60)
    # B's demand fell, so "share of growth" is undefined rather than a misleading number
    assert pd.isna(t.loc["B", "clean_share_of_growth_pct"])
    assert t.index[0] == "B"  # sorted by fossil change, biggest cut first


def test_mix_has_all_sources_in_order(toy):
    m = mix(toy, "A")
    assert list(m.columns) == list(SOURCES.values())
    assert m.loc[2024].sum() == pytest.approx(150)
