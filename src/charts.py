"""Plotly figures for the data story. One function per chart; all share one visual style.

Colors: source colors were checked for colour-blind separation (adjacent pairs in stack order).
Three of them are light on a white background, so every stacked chart also carries direct labels.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

SURFACE, GRID, AXIS = "#fcfcfb", "#e1e0d9", "#c3c2b7"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
BLUE, RED = "#2a78d6", "#e34948"
FONT = "system-ui, -apple-system, Segoe UI, sans-serif"

SOURCE_COLORS = {
    "Coal": "#eb6834", "Oil": "#6250d6", "Gas": "#e34948", "Nuclear": "#008300",
    "Hydro": "#2a78d6", "Wind": "#1baf7a", "Solar": "#eda100", "Bioenergy & other": "#e87ba4",
}
STACK_ORDER = list(SOURCE_COLORS)  # fossil at the bottom, then low-carbon
# label offsets in pixels (dx, dy) so neighbouring names do not collide
LABEL_OFFSET = {"United Kingdom": (75, 5), "Germany": (-10, -35), "Netherlands": (40, 30), "Brazil": (50, 0),
                "Japan": (-40, 35), "Spain": (45, -30), "United States": (-75, -45), "Saudi Arabia": (-60, -25),
                "Indonesia": (-50, -25), "India": (0, -45), "China": (0, -60), "Vietnam": (-60, 0)}
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def style(fig: go.Figure, title: str, subtitle: str, height: int = 460) -> go.Figure:
    has_legend = sum(1 for tr in fig.data if tr.showlegend is not False and tr.name) > 1
    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><span style='font-size:13px;color:{INK_2}'>{subtitle}</span>",
                   x=0, xanchor="left", y=1, yanchor="top", yref="container", pad=dict(t=16), font=dict(size=18, color=INK)),
        font=dict(family=FONT, size=12, color=INK_2), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        height=height, margin=dict(l=10, r=10, t=115 if has_legend else 90, b=40), hoverlabel=dict(bgcolor="white", font_family=FONT),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title=None, traceorder="normal"),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED))
    return fig


def _mix_traces(m: pd.DataFrame, visible: bool = True):
    total = m.sum(axis=1)
    for src in STACK_ORDER:
        share = (m[src] / total * 100).round(1)
        yield go.Scatter(
            x=m.index, y=m[src], name=src, stackgroup="one", mode="lines", visible=visible,
            line=dict(width=0.5, color=SURFACE), fillcolor=SOURCE_COLORS[src],
            customdata=share, hovertemplate=f"<b>{src}</b> %{{x}}: %{{y:,.0f}} TWh (%{{customdata}}%)<extra></extra>",
        )


def world_mix(m: pd.DataFrame) -> go.Figure:
    fig = go.Figure(list(_mix_traces(m)))
    # direct labels at the right edge for the larger sources (identity is never colour alone)
    last, cum = m.iloc[-1], 0.0
    for src in STACK_ORDER:
        mid = cum + last[src] / 2
        cum += last[src]
        if last[src] / last.sum() > 0.04:
            fig.add_annotation(x=m.index[-1], y=mid, text=f"{src} {last[src] / last.sum():.0%}", xanchor="left",
                               showarrow=False, xshift=6, font=dict(size=11, color=INK_2))
    fig.update_yaxes(title="TWh", ticksuffix="")
    fig.update_xaxes(range=[m.index[0], m.index[-1] + 4.5], tickvals=list(range(m.index[0], m.index[-1], 5)) + [m.index[-1]])
    return style(fig, "Clean sources grew, but so did coal",
                 "World electricity generation by source, TWh, 2000-2024", height=500)


def explore_mix(mixes: dict) -> go.Figure:
    """Stacked area with a country dropdown. Every country's traces are built once; the menu toggles visibility."""
    names = list(mixes)
    fig = go.Figure()
    for i, name in enumerate(names):
        for t in _mix_traces(mixes[name], visible=(i == 0)):
            t.showlegend = i == 0
            t.legendgroup = t.name
            fig.add_trace(t)
    n = len(STACK_ORDER)
    buttons = [dict(label=name, method="update",
                    args=[{"visible": [j // n == i for j in range(n * len(names))]}])
               for i, name in enumerate(names)]
    fig.update_layout(updatemenus=[dict(buttons=buttons, x=1, xanchor="right", y=1.18, yanchor="bottom",
                                        bgcolor="white", bordercolor=AXIS, font=dict(color=INK))])
    fig.update_yaxes(title="TWh")
    return style(fig, "Explore any large country", "Electricity generation by source, TWh. Pick a country from the menu.",
                 height=520)


def fossil_change(t: pd.DataFrame, start: int, end: int) -> go.Figure:
    t = t.sort_values("fossil_change_pct")
    colors = [BLUE if v < 0 else RED for v in t["fossil_change_pct"]]
    fig = go.Figure(go.Bar(
        x=t["fossil_change_pct"], y=t.index, orientation="h", marker=dict(color=colors, line=dict(width=0)),
        customdata=t[["fossil_start", "fossil_end", "demand_growth_pct"]].round(0),
        hovertemplate=("<b>%{y}</b><br>Fossil generation: %{customdata[0]:,.0f} -> %{customdata[1]:,.0f} TWh "
                       "(%{x:+.0f}%)<br>Total demand: %{customdata[2]:+.0f}%<extra></extra>"),
    ))
    fig.add_vline(x=0, line=dict(color=AXIS, width=1))
    fig.update_xaxes(ticksuffix="%", title=f"Change in fossil-fuel electricity, {start}-{end}")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=INK_2))
    fig.add_annotation(x=t["fossil_change_pct"].min(), y=1.02, yref="paper", text="<b>Fell</b>", showarrow=False,
                       xanchor="left", font=dict(color=BLUE))
    fig.add_annotation(x=t["fossil_change_pct"].max(), y=1.02, yref="paper", text="<b>Rose</b>", showarrow=False,
                       xanchor="right", font=dict(color=RED))
    return style(fig, "Half the big power systems burn less fossil fuel than ten years ago",
                 f"Countries generating 100+ TWh in {end}. Blue = fossil generation fell, red = rose.",
                 height=max(520, 22 * len(t) + 140))


def demand_vs_fossil(t: pd.DataFrame, labels: list, start: int, end: int) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=t["demand_growth_pct"], y=t["fossil_change_pct"], mode="markers",
        marker=dict(size=(t["generation_end"] ** 0.5) / 2.2 + 6, color=BLUE, opacity=0.75,
                    line=dict(width=2, color=SURFACE)),
        customdata=t[["clean_share_of_growth_pct", "generation_end"]].round(0),
        hovertemplate=("<b>%{hovertext}</b><br>Demand growth: %{x:+.0f}%<br>Fossil change: %{y:+.0f}%"
                       "<br>Generation " + str(end) + ": %{customdata[1]:,.0f} TWh<extra></extra>"),
        hovertext=t.index,
    ))
    for c in labels:
        if c in t.index:
            dx, dy = LABEL_OFFSET.get(c, (0, -30))
            fig.add_annotation(x=t.loc[c, "demand_growth_pct"], y=t.loc[c, "fossil_change_pct"], text=c, ax=dx, ay=dy,
                               showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=MUTED,
                               font=dict(size=11, color=INK_2), bgcolor="rgba(252,252,251,0.8)")
    fig.add_hline(y=0, line=dict(color=AXIS, width=1))
    fig.add_vline(x=0, line=dict(color=AXIS, width=1))
    fig.update_xaxes(ticksuffix="%", title=f"Growth in total electricity generation, {start}-{end}")
    fig.update_yaxes(ticksuffix="%", title="Change in fossil generation")
    return style(fig, "Where demand grows fast, fossil power still grows",
                 "Each bubble is a country (size = generation). Above the line: more fossil power than in "
                 f"{start}.", height=520)


def solar_wind_dumbbell(t: pd.DataFrame, start: int, end: int, top: int = 15) -> go.Figure:
    t = t.nlargest(top, "solar_wind_gain_pts").sort_values("solar_wind_gain_pts")
    fig = go.Figure()
    for _, (c, r) in enumerate(t.iterrows()):
        fig.add_trace(go.Scatter(x=[r.solar_wind_share_start, r.solar_wind_share_end], y=[c, c], mode="lines",
                                 line=dict(color=AXIS, width=2), showlegend=False, hoverinfo="skip"))
    for col, year, color in [("solar_wind_share_start", start, MUTED), ("solar_wind_share_end", end, BLUE)]:
        fig.add_trace(go.Scatter(
            x=t[col], y=t.index, mode="markers", name=str(year),
            marker=dict(size=11, color=color, line=dict(width=2, color=SURFACE)),
            hovertemplate=f"<b>%{{y}}</b> {year}: %{{x:.1f}}% of electricity<extra></extra>"))
    fig.update_xaxes(ticksuffix="%", title="Solar + wind share of electricity")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=INK_2))
    return style(fig, f"Solar and wind: from niche to mainstream in {end - start} years",
                 f"The {top} large countries with the biggest gain in solar + wind share, {start} (grey) vs {end} (blue)",
                 height=560)


def low_carbon_map(c: pd.DataFrame, year: int) -> go.Figure:
    d = c[c["year"] == year].dropna(subset=["low_carbon_share_elec"])
    fig = go.Figure(go.Choropleth(
        locations=d["iso_code"], z=d["low_carbon_share_elec"], text=d["country"], zmin=0, zmax=100,
        colorscale=[[i / (len(BLUES) - 1), b] for i, b in enumerate(BLUES)],
        marker_line=dict(color="white", width=0.4),
        colorbar=dict(title="Low-carbon<br>share", ticksuffix="%", thickness=12, len=0.7),
        hovertemplate="<b>%{text}</b><br>Low-carbon share: %{z:.0f}%<extra></extra>",
    ))
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor=SURFACE,
                    showland=True, landcolor="#f0efec")
    return style(fig, f"Low-carbon share of electricity, {year}",
                 "Nuclear + hydro + wind + solar + bioenergy. Darker = cleaner grid.", height=520)


def country_mix_share(m: pd.DataFrame, country: str) -> go.Figure:
    share = m.div(m.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for src in STACK_ORDER:
        fig.add_trace(go.Scatter(x=share.index, y=share[src].round(1), name=src, stackgroup="one", mode="lines",
                                 line=dict(width=0.5, color=SURFACE), fillcolor=SOURCE_COLORS[src],
                                 customdata=m[src].round(0),
                                 hovertemplate=f"<b>{src}</b> %{{x}}: %{{y:.1f}}% (%{{customdata:,.0f}} TWh)<extra></extra>"))
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    return style(fig, f"{country}: coal still supplies most of the power",
                 f"Share of {country}'s electricity by source, %", height=460)


def solar_wind_growth(w: pd.DataFrame, start: int) -> go.Figure:
    """World solar and wind generation, TWh. w: World rows indexed by year."""
    fig = go.Figure()
    for col, name in [("wind_electricity", "Wind"), ("solar_electricity", "Solar")]:
        s = w[col].loc[2005:]
        fig.add_trace(go.Scatter(x=s.index, y=s, name=name, mode="lines", line=dict(color=SOURCE_COLORS[name], width=2.5),
                                 hovertemplate=f"<b>{name}</b> %{{x}}: %{{y:,.0f}} TWh<extra></extra>"))
        end = s.index[-1]
        fig.add_annotation(x=end, y=s.iloc[-1], text=f"{name} x{s.iloc[-1] / s.loc[start]:.0f} since {start}",
                           xanchor="left", xshift=6, showarrow=False, font=dict(size=11, color=INK_2))
    fig.update_yaxes(title="TWh")
    fig.update_xaxes(range=[2005, w.index[-1] + 6])
    return style(fig, "Solar output grew more than tenfold in ten years",
                 "World generation from solar and wind, TWh", height=440)


def coal_concentration(df: pd.DataFrame, top: list) -> go.Figure:
    """Coal generation stacked by the largest coal users + rest of world. df: pivot year x country (incl. 'World')."""
    colors = [BLUE, "#eb6834", "#1baf7a", "#eda100"]
    rest = df["World"] - df[top].sum(axis=1)
    fig = go.Figure()
    for name, series, color in [*zip(top, [df[c] for c in top], colors), ("Rest of world", rest, colors[len(top)])]:
        fig.add_trace(go.Scatter(x=series.index, y=series, name=name, stackgroup="one", mode="lines",
                                 line=dict(width=0.5, color=SURFACE), fillcolor=color,
                                 hovertemplate=f"<b>{name}</b> %{{x}}: %{{y:,.0f}} TWh<extra></extra>"))
    fig.update_yaxes(title="TWh")
    return style(fig, "Coal power is now mostly a China and India story",
                 "Electricity from coal by country, TWh, 2000-2024", height=460)


def carbon_intensity_grid(series: dict, world: pd.Series) -> go.Figure:
    """Small multiples: one panel per country, country in blue, world average in grey for reference."""
    from plotly.subplots import make_subplots
    names = list(series)
    cols = 4
    rows = (len(names) + cols - 1) // cols
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=names, shared_yaxes=True,
                        horizontal_spacing=0.03, vertical_spacing=0.14)
    for i, name in enumerate(names):
        r, c = i // cols + 1, i % cols + 1
        fig.add_trace(go.Scatter(x=world.index, y=world, mode="lines", line=dict(color=AXIS, width=1.5, dash="dot"),
                                 name="World", showlegend=i == 0, hovertemplate="World %{x}: %{y:.0f} g<extra></extra>"),
                      row=r, col=c)
        s = series[name]
        fig.add_trace(go.Scatter(x=s.index, y=s, mode="lines", line=dict(color=BLUE, width=2.5), name=name,
                                 showlegend=False, hovertemplate=f"<b>{name}</b> %{{x}}: %{{y:.0f}} gCO₂/kWh<extra></extra>"),
                      row=r, col=c)
    fig.update_annotations(font=dict(size=12, color=INK))
    fig.update_yaxes(range=[0, 900])
    fig.update_layout(legend=dict(x=1, xanchor="right", y=1.06))
    fig.update_xaxes(dtick=10)
    return style(fig, "How dirty is each kWh? Carbon intensity of electricity",
                 "Grams of CO₂ per kWh generated, 2000-2024. Blue = country, dotted grey = world average.",
                 height=560)


def low_carbon_heatmap(h: pd.DataFrame) -> go.Figure:
    """h: countries (rows, sorted) x years, low-carbon share %."""
    fig = go.Figure(go.Heatmap(
        z=h.values, x=h.columns, y=h.index, zmin=0, zmax=100, xgap=1, ygap=1,
        colorscale=[[i / (len(BLUES) - 1), b] for i, b in enumerate(BLUES)],
        colorbar=dict(title="Low-carbon<br>share", ticksuffix="%", thickness=12, len=0.6),
        hovertemplate="<b>%{y}</b> %{x}: %{z:.0f}% low-carbon<extra></extra>"))
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", tickfont=dict(color=INK_2))
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)", dtick=4)
    return style(fig, "25 years of change at a glance",
                 "Low-carbon share of electricity for the 20 largest power systems, sorted by 2024 value",
                 height=620)


def per_capita_scatter(t: pd.DataFrame, labels: list, year: int) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=t["per_capita_kwh"], y=t["low_carbon_share_end"], mode="markers", hovertext=t.index,
        marker=dict(size=(t["generation_end"] ** 0.5) / 2.2 + 6, color=BLUE, opacity=0.75,
                    line=dict(width=2, color=SURFACE)),
        hovertemplate="<b>%{hovertext}</b><br>%{x:,.0f} kWh per person<br>%{y:.0f}% low-carbon<extra></extra>"))
    for c in labels:
        if c in t.index:
            fig.add_annotation(x=np.log10(t.loc[c, "per_capita_kwh"]), y=t.loc[c, "low_carbon_share_end"], text=c,
                               ax=0, ay=-28, showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=MUTED,
                               font=dict(size=11, color=INK_2), bgcolor="rgba(252,252,251,0.8)")
    ticks = [500, 1000, 2000, 5000, 10000, 20000, 30000]
    fig.update_xaxes(type="log", tickvals=ticks, ticktext=[f"{v:,}" for v in ticks],
                     title=f"Electricity generated per person, kWh, {year} (log scale)")
    fig.update_yaxes(ticksuffix="%", title="Low-carbon share", range=[0, 105])
    return style(fig, "Low-carbon shares vary at every level of consumption",
                 f"Countries generating 100+ TWh, {year}. Bubble size = total generation.", height=520)


def solar_leaders(t: pd.DataFrame, highlight: str, top: int = 15) -> go.Figure:
    s = t.nlargest(top, "solar_share")
    if highlight not in s.index:
        s = pd.concat([s.iloc[:top - 1], t.loc[[highlight]]])
    s = s.sort_values("solar_share")
    colors = [BLUE if c == highlight else "#9ec5f4" for c in s.index]
    fig = go.Figure(go.Bar(x=s["solar_share"], y=s.index, orientation="h", marker=dict(color=colors),
                           text=[f"{v:.1f}%" for v in s["solar_share"]], textposition="outside",
                           textfont=dict(color=INK_2, size=11),
                           hovertemplate="<b>%{y}</b>: %{x:.1f}% of electricity from solar<extra></extra>"))
    fig.update_xaxes(ticksuffix="%", title="Solar share of electricity")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=INK_2))
    return style(fig, "Who gets the most power from the sun?",
                 f"Solar share of electricity, large power systems (100+ TWh), {highlight} highlighted", height=520)
