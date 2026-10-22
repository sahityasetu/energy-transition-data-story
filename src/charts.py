"""Plotly figures for the data story. One function per chart; all share one visual style.

Colors: source colors were checked for colour-blind separation (adjacent pairs in stack order).
Three of them are light on a white background, so every stacked chart also carries direct labels.
"""
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
