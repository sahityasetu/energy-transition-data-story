"""Build the data story: docs/index.html (GitHub Pages) plus PNG previews and a summary table in reports/.

Run from the project root:  python -m src.build_story
Every number in the text is computed here from the data, so the story updates when OWID updates the file.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.io as pio

from src import charts
from src.data import LAST_YEAR, change_table, countries, load, mix, world_kpis

ROOT = Path(__file__).resolve().parents[1]
DOCS, FIG, REPORTS = ROOT / "docs", ROOT / "reports" / "figures", ROOT / "reports"
START = 2014
SPOTLIGHT = "India"
SCATTER_LABELS = ["China", "India", "United States", "Germany", "United Kingdom", "Vietnam", "Brazil",
                  "Japan", "Indonesia", "Saudi Arabia", "Spain", "Netherlands"]


def pct(x, digits=0):
    return f"{x:.{digits}f}%"


def compute_facts(df, t):
    k = world_kpis(df, START, LAST_YEAR)
    fell = t[t["fossil_change_pct"] < 0]
    rose = t[t["fossil_change_pct"] >= 0]
    sp = t.loc[SPOTLIGHT]
    sp_mix = mix(df, SPOTLIGHT)
    sp_share = sp_mix.div(sp_mix.sum(axis=1), axis=0) * 100
    world_growth = k["generation"][1] - k["generation"][0]
    return {
        "world": k,
        "world_clean_share_of_growth": (1 - (k["fossil"][1] - k["fossil"][0]) / world_growth) * 100,
        "n_countries": len(t), "n_fell": len(fell), "n_rose": len(rose),
        "fell_median_demand": fell["demand_growth_pct"].median(),
        "rose_median_demand": rose["demand_growth_pct"].median(),
        "corr_demand_fossil": t["demand_growth_pct"].corr(t["fossil_change_pct"]),
        "biggest_cut": fell["fossil_change_pct"].idxmin(), "biggest_cut_pct": fell["fossil_change_pct"].min(),
        "top_solar_wind": t["solar_wind_gain_pts"].idxmax(), "top_solar_wind_gain": t["solar_wind_gain_pts"].max(),
        "spot": {
            "demand_growth": sp["demand_growth_pct"], "fossil_change": sp["fossil_change_pct"],
            "clean_share_of_growth": sp["clean_share_of_growth_pct"],
            "coal_share_start": sp_share.loc[START, "Coal"], "coal_share_end": sp_share.loc[LAST_YEAR, "Coal"],
            "solar_share_start": sp_share.loc[START, "Solar"], "solar_share_end": sp_share.loc[LAST_YEAR, "Solar"],
            "solar_twh_start": sp_mix.loc[START, "Solar"], "solar_twh_end": sp_mix.loc[LAST_YEAR, "Solar"],
        },
    }


def build_figures(df, t, f):
    c = countries(df)
    big = t.sort_values("generation_end", ascending=False).index.tolist()
    figs = {
        "world_mix": charts.world_mix(mix(df, "World")),
        "fossil_change": charts.fossil_change(t, START, LAST_YEAR),
        "demand_vs_fossil": charts.demand_vs_fossil(t, SCATTER_LABELS, START, LAST_YEAR),
        "solar_wind": charts.solar_wind_dumbbell(t, START, LAST_YEAR),
        "map": charts.low_carbon_map(c, LAST_YEAR),
        "spotlight": charts.country_mix_share(mix(df, SPOTLIGHT), SPOTLIGHT),
        "explore": charts.explore_mix({name: mix(df, name) for name in big}),
    }
    # titles that state a finding are set here, from the computed facts
    figs["fossil_change"].update_layout(title_text=(
        f"<b>{f['n_fell']} of {f['n_countries']} large power systems burn less fossil fuel than in {START}</b>"
        f"<br><span style='font-size:13px;color:{charts.INK_2}'>Countries generating 100+ TWh in {LAST_YEAR}. "
        "Blue = fossil generation fell, red = rose.</span>"))
    return figs


def tile(value, label, note):
    return f'<div class="tile"><div class="v">{value}</div><div class="l">{label}</div><div class="n">{note}</div></div>'


def page(figs, f):
    w, s = f["world"], f["spot"]
    div = {name: pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"displaylogo": False,
                                                                                   "responsive": True})
           for name, fig in figs.items()}
    tiles = "".join([
        tile(pct(w["low_carbon_share"][1], 1), f"of world electricity was low-carbon in {LAST_YEAR}",
             f"up from {pct(w['low_carbon_share'][0], 1)} in {START}"),
        tile(pct(w["solar_wind_share"][1], 1), "came from solar + wind", f"up from {pct(w['solar_wind_share'][0], 1)}"),
        tile(f"{(w['carbon_intensity'][1] / w['carbon_intensity'][0] - 1) * 100:+.0f}%", "CO₂ per kWh generated",
             f"{w['carbon_intensity'][0]:.0f} → {w['carbon_intensity'][1]:.0f} g/kWh"),
        tile(f"{(w['fossil'][1] / w['fossil'][0] - 1) * 100:+.0f}%", "fossil-fuel electricity",
             "still rising in absolute terms"),
    ])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Energy Transition Story</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@4.1.1/plotly.min.js"></script>
<style>
:root {{ color-scheme: light; --surface:#fcfcfb; --page:#f9f9f7; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
        --line:#e1e0d9; --blue:#2a78d6; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--page); color:var(--ink); font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width: 980px; margin: 0 auto; padding: 32px 16px 64px; }}
h1 {{ font-size: 2rem; line-height: 1.2; margin: 0 0 8px; }}
h2 {{ font-size: 1.3rem; margin: 48px 0 8px; }}
p {{ color: var(--ink2); max-width: 70ch; }}
.lede {{ font-size: 1.1rem; }}
.tiles {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin: 24px 0; }}
.tile {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:16px; }}
.tile .v {{ font-size: 2rem; font-weight: 700; }} .tile .l {{ color: var(--ink2); }} .tile .n {{ color: var(--muted); font-size:.85rem; }}
.chart {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:8px; margin: 16px 0; overflow:hidden; }}
.note {{ font-size: .85rem; color: var(--muted); }}
a {{ color: var(--blue); }}
</style></head>
<body><main>
<p class="note">Data story · Our World in Data energy dataset · {START}-{LAST_YEAR}</p>
<h1>The world's electricity is getting cleaner. Why isn't fossil power falling?</h1>
<p class="lede">Solar and wind went from a rounding error to {pct(w['solar_wind_share'][1])} of global electricity in ten
years. Yet fossil-fuel generation is still <b>higher</b> than in {START}. This page follows the numbers to explain both
facts at once: clean power is growing fast, but in fast-growing economies demand grows faster.</p>
<div class="tiles">{tiles}</div>

<h2>1. The global picture</h2>
<p>World generation grew from {w['generation'][0]:,.0f} to {w['generation'][1]:,.0f} TWh. Low-carbon sources covered
about {f['world_clean_share_of_growth']:.0f}% of that growth; the rest still came from fossil fuels, mostly coal and gas.</p>
<div class="chart">{div['world_mix']}</div>

<h2>2. Two groups of countries</h2>
<p>Among the {f['n_countries']} countries that generate at least 100 TWh a year, {f['n_fell']} now burn less fossil fuel for
power than in {START}. {f['biggest_cut']} cut it the most ({f['biggest_cut_pct']:.0f}%). The other {f['n_rose']} burn more.</p>
<div class="chart">{div['fossil_change']}</div>

<h2>3. The difference is demand growth</h2>
<p>Countries that cut fossil power grew their total generation by a median of {f['fell_median_demand']:.0f}%.
Countries where fossil power rose grew by a median of {f['rose_median_demand']:.0f}%. Across all {f['n_countries']}
countries, the correlation between demand growth and fossil change is {f['corr_demand_fossil']:.2f}.
Building clean power is not enough on its own: it must also outpace new demand.</p>
<div class="chart">{div['demand_vs_fossil']}</div>

<h2>4. Solar and wind took off almost everywhere</h2>
<p>This is the good news, and it is broad. {f['top_solar_wind']} gained the most:
+{f['top_solar_wind_gain']:.0f} percentage points of its electricity from solar and wind.</p>
<div class="chart">{div['solar_wind']}</div>

<h2>5. Where the grid is cleanest today</h2>
<p>Countries with large hydro or nuclear fleets (Norway, Sweden, France, Brazil) lead. Most of Asia, the Middle East
and North Africa still run mainly on fossil fuels.</p>
<div class="chart">{div['map']}</div>

<h2>6. Spotlight: {SPOTLIGHT}</h2>
<p>{SPOTLIGHT}'s generation grew {s['demand_growth']:.0f}% in ten years. Solar output rose from
{s['solar_twh_start']:.0f} to {s['solar_twh_end']:.0f} TWh, and coal's share slipped from
{pct(s['coal_share_start'])} to {pct(s['coal_share_end'])}. But low-carbon sources met only about
{s['clean_share_of_growth']:.0f}% of the new demand, so fossil generation still rose {s['fossil_change']:.0f}%.</p>
<div class="chart">{div['spotlight']}</div>

<h2>7. Explore any large country</h2>
<div class="chart">{div['explore']}</div>

<h2>Method and caveats</h2>
<p class="note">Source: <a href="https://github.com/owid/energy-data">Our World in Data energy dataset</a> (Ember and
Energy Institute data). Low-carbon = nuclear + renewables. Country comparisons use the {f['n_countries']} countries with at
least 100 TWh of generation in {LAST_YEAR} and compare {START} with {LAST_YEAR}; 2025 is left out because many
countries have not reported it yet. Correlation is not causation: weather, hydro years and fuel prices also move
these numbers. Code: <a href="https://github.com/sahityasetu/energy-transition-data-story">GitHub</a>.</p>
</main></body></html>"""


def main():
    df = load()
    t = change_table(df, START, LAST_YEAR)
    f = compute_facts(df, t)
    figs = build_figures(df, t, f)

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page(figs, f), encoding="utf-8")

    FIG.mkdir(parents=True, exist_ok=True)
    for name in ["world_mix", "fossil_change", "demand_vs_fossil", "solar_wind", "map", "spotlight"]:
        figs[name].write_image(FIG / f"{name}.png", width=1000, height=figs[name].layout.height, scale=2)

    t.round(2).to_csv(REPORTS / f"country_change_{START}_{LAST_YEAR}.csv")
    (REPORTS / "facts.json").write_text(json.dumps(f, indent=2, default=lambda x: round(float(x), 2)))
    print(json.dumps(f, indent=2, default=lambda x: round(float(x), 2)))


if __name__ == "__main__":
    main()
