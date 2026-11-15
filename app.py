"""JIE42403 Scientific Visualisation - Streamlit dashboard
Household income, schools and marriages in Malaysia (2019-2023). Source: data.gov.my."""
import html
import json
import urllib.request

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import data_prep as dp

st.set_page_config(page_title="Malaysia Income, Schools & Marriages", layout="wide")

STUDENT_NAME = "Tayaalini Devarajan"          # <- change to your name
MATRIC_NO = "S23A0164"    # <- change to your matric number

GEOJSON_URL = ("https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
               "master/public/data/malaysia.geojson")
TYPE_LABELS = {"Sekolah Rendah Kerajaan": "Primary (government)",
               "Sekolah Menengah Kerajaan": "Secondary (government)",
               "IPTA": "Public universities (IPTA)"}
INCOME_SCALE = [(0.00, "#ffffcc"), (0.15, "#c7e9b4"), (0.30, "#7fcdbb"), (0.50, "#41b6c4"),
                (0.70, "#1d91c0"), (0.85, "#225ea8"), (1.00, "#0c2c84")]
DIVERGING = [[0.0, "#b2182b"], [0.25, "#f4a582"], [0.5, "#f7f7f7"], [0.75, "#80cdc1"], [1.0, "#01665e"]]


# ------------------------------------------------------------------ data
@st.cache_data
def load_data():
    schools, income, marriages = dp.load_raw(".")
    merged = dp.build_merged(schools, income, marriages)
    districts = dp.school_districts(schools)
    districts["type_label"] = districts["type"].map(TYPE_LABELS)
    return merged, districts


@st.cache_data
def load_geojson():
    try:
        with urllib.request.urlopen(GEOJSON_URL, timeout=15) as r:
            gj = json.load(r)
        for f in gj["features"]:
            f["properties"]["canon"] = dp.canon(f["properties"].get("name", ""))
        return gj
    except Exception:
        return None


merged, districts = load_data()
merged["canon"] = merged["state"].map(dp.canon)


def pct(new, old):
    return (new / old - 1) * 100


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Sora:wght@500;600;700&display=swap');
:root {
  --ink:#17324d; --teal:#0e7c86; --saffron:#f4b400; --paper:#f6f8fb; --rule:#dde5ec; --soft:#5d7284;
  --shadow: 0 1px 2px rgba(23,50,77,.06), 0 10px 28px rgba(23,50,77,.07);
  --pattern: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='16' viewBox='0 0 24 16'%3E%3Cpolygon points='0,16 12,1 24,16' fill='%230e7c86'/%3E%3Cpolygon points='6,16 12,7 18,16' fill='%23f4b400'/%3E%3C/svg%3E");
}
[data-testid="stAppViewContainer"] { background: var(--paper); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; max-width: 1200px; }
h1, h2, h3, h4 { font-family: 'Sora', sans-serif; color: var(--ink); letter-spacing: -0.01em; }
h3 { font-size: 1.2rem; margin-top: 1.6rem; padding-bottom: 6px; border-bottom: 1px solid var(--rule); }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { font-family: 'DM Sans', sans-serif; }

[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--rule); }
.side-title { font-family: 'Sora', sans-serif; font-size: 1.2rem; font-weight: 700; line-height: 1.3; color: var(--ink); margin: 6px 0 10px; }
.side-me { font-family: 'DM Sans', sans-serif; font-size: .85rem; line-height: 1.55; color: var(--soft);
           border-top: 1px solid var(--rule); padding-top: 12px; margin-top: 18px; }

.pattern { height: 16px; background-image: var(--pattern); background-repeat: repeat-x; background-size: 24px 16px;
           border-bottom: 3px solid var(--teal); margin-bottom: 22px; }
.page-head { margin-bottom: 22px; }
.page-title { font-family: 'Sora', sans-serif; font-size: 2.1rem; font-weight: 700; color: var(--ink); line-height: 1.2; }
.page-obj { font-family: 'DM Sans', sans-serif; color: var(--soft); font-size: 1.05rem; max-width: 72ch; margin: .5rem 0 0; }

.strip-title { font-family: 'Sora', sans-serif; font-weight: 600; color: var(--ink); margin: 4px 0 8px; }
.strip { display: grid; grid-template-columns: repeat(4, 1fr); background: #fff; border: 1px solid var(--rule);
         border-top: 4px solid var(--teal); border-radius: 12px; margin-bottom: 24px; box-shadow: var(--shadow); }
.cell { padding: 18px 22px; border-right: 1px solid var(--rule); }
.cell:last-child { border-right: none; }
.cell-label { font-family: 'DM Sans', sans-serif; font-size: .88rem; color: var(--soft); font-weight: 500; }
.cell-value { font-family: 'Sora', sans-serif; font-size: 1.7rem; font-weight: 600; color: var(--ink); margin: 3px 0; }
.cell-note { font-family: 'DM Sans', sans-serif; font-size: .86rem; font-weight: 700; }
.up { color: #1a7f5a; } .down { color: #c0392b; } .flat { color: var(--soft); }

.finds { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 8px 0 22px; }
.find { background: #fff; border: 1px solid var(--rule); border-radius: 12px; padding: 20px 22px; box-shadow: var(--shadow); }
.find-num { font-family: 'Sora', sans-serif; font-size: 2.4rem; font-weight: 700; line-height: 1.1; }
.find-text { font-family: 'DM Sans', sans-serif; color: #33495a; font-size: .98rem; margin-top: 8px; line-height: 1.5; }
.find-tag { font-family: 'DM Sans', sans-serif; color: var(--soft); font-size: .86rem; font-weight: 500; margin-top: 10px; }

.objs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 6px 0 20px; }
.obj { background: #fff; border: 1px solid var(--rule); border-left: 5px solid var(--saffron); border-radius: 12px; padding: 18px 20px; }
.obj h4 { margin: 0 0 6px; font-size: 1.05rem; }
.obj p { margin: 0 0 8px; font-size: .95rem; color: #33495a; font-family: 'DM Sans', sans-serif; }
.obj .src { font-size: .86rem; color: var(--soft); font-weight: 500; }

[data-testid="stPlotlyChart"] { background: #fff; border: 1px solid var(--rule); border-radius: 12px; padding: 10px 12px;
                                box-shadow: var(--shadow); }
[data-testid="stExpander"] { background: #fff; border: 1px solid var(--rule); border-radius: 12px; }
@media (max-width: 900px) {
  .strip { grid-template-columns: repeat(2, 1fr); } .cell { border-bottom: 1px solid var(--rule); }
  .objs, .finds { grid-template-columns: 1fr; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def page_head(title, text):
    st.markdown(f'<div class="pattern"></div><div class="page-head"><div class="page-title">{html.escape(title)}</div>'
                f'<p class="page-obj">{html.escape(text)}</p></div>', unsafe_allow_html=True)


def summary_box(items, title="Summary box"):
    cells = ""
    for label, value, note in items:
        cls = "up" if str(note).startswith("+") else ("down" if str(note).startswith("-") else "flat")
        cells += (f'<div class="cell"><div class="cell-label">{html.escape(str(label))}</div>'
                  f'<div class="cell-value">{html.escape(str(value))}</div>'
                  f'<div class="cell-note {cls}">{html.escape(str(note))}</div></div>')
    if title:
        st.markdown(f'<div class="strip-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="strip">{cells}</div>', unsafe_allow_html=True)


def show(fig):
    fig.update_layout(font=dict(family="DM Sans, Arial, sans-serif", color="#12263a"),
                      title_font=dict(family="Sora, Arial, sans-serif", size=16))
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------ sidebar
st.sidebar.markdown('<div class="pattern" style="margin-bottom:14px"></div>'
                    '<div class="side-title">Malaysia income, schools and marriages</div>', unsafe_allow_html=True)
page = st.sidebar.radio("Go to", ["Home", "Objective 1: Income", "Objective 2: Schools",
                                  "Objective 3: Marriages", "Merged data"])
st.sidebar.markdown(f'<div class="side-me">{html.escape(STUDENT_NAME)}<br>{html.escape(MATRIC_NO)}<br>'
                    'JIE42403 Scientific Visualisation<br>Data: data.gov.my, 2019 to 2023</div>',
                    unsafe_allow_html=True)

# ================================================================== HOME
if page == "Home":
    page_head("Household income, schools and marriages in Malaysia",
              "Three open datasets for 16 states and federal territories, merged by state and year, 2019 to 2023.")
    summary_box([("States and territories", "16", "all of Malaysia"),
                 ("Years covered", "2019-2023", "income: 2019, 2020, 2022"),
                 ("Merged table", "80 rows", "14 columns"),
                 ("Datasets", "3", "income, schools, marriages")], title="")
    _inc = merged.dropna(subset=["income_mean"]).groupby("year")["income_mean"].mean()
    _sch = merged.groupby("year")["schools_total"].sum()
    _mar = merged.groupby("year")["marriage_abs_avg"].sum()
    st.markdown(f"""
<div class="finds">
  <div class="find"><div class="find-num" style="color:#c0392b">{pct(_inc[2020], _inc[2019]):+.1f}%</div>
  <div class="find-text">Average household income fell in 2020 and was back above its 2019 level by 2022 ({pct(_inc[2022], _inc[2019]):+.1f}%).</div>
  <div class="find-tag">Objective 1: income</div></div>
  <div class="find"><div class="find-num" style="color:#0e7c86">{pct(_sch[2023], _sch[2019]):+.2f}%</div>
  <div class="find-text">The number of schools hardly changed between 2019 and 2023 ({int(_sch[2023] - _sch[2019]):+d} schools).</div>
  <div class="find-tag">Objective 2: schools</div></div>
  <div class="find"><div class="find-num" style="color:#c0392b">{pct(_mar[2023], _mar[2019]):+.1f}%</div>
  <div class="find-text">Marriages in 2023 were below 2019, after a dip in 2020 and a rebound in 2021.</div>
  <div class="find-tag">Objective 3: marriages</div></div>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class="objs">
  <div class="obj"><h4>Objective 1: Household income trends</h4>
  <p>Show how household income changed across states between 2019, 2020 and 2022, and where it is highest and lowest.</p>
  <div class="src">Data: income</div></div>
  <div class="obj"><h4>Objective 2: School distribution</h4>
  <p>Examine the number and distribution of schools across states, districts and school types from 2019 to 2023.</p>
  <div class="src">Data: schools</div></div>
  <div class="obj"><h4>Objective 3: Marriage trends</h4>
  <p>Explore how marriages changed by state and sex from 2019 to 2023, and how they relate to household income.</p>
  <div class="src">Data: marriages and income</div></div>
</div>
""", unsafe_allow_html=True)
    st.info("Open an objective from the menu on the left. Household income is only published for 2019, 2020 and 2022, "
            "so income charts use those years. Schools and marriages have all five years.")

# ================================================================== OBJECTIVE 1
elif page == "Objective 1: Income":
    page_head("Objective 1: Household income trends",
              "To show how household income changed across Malaysian states between 2019, 2020 and 2022, "
              "and where it is highest and lowest.")
    inc = merged.dropna(subset=["income_mean"]).copy()
    avg = inc.groupby("year")[["income_mean", "income_median"]].mean()
    w = inc.pivot(index="state", columns="year", values="income_mean")
    i19, i20, i22 = w[2019], w[2020], w[2022]

    summary_box([
        ("Avg mean income (2022)", f"RM {avg.loc[2022, 'income_mean']:,.0f}",
         f"{pct(avg.loc[2022, 'income_mean'], avg.loc[2019, 'income_mean']):+.1f}% vs 2019"),
        ("Avg median income (2022)", f"RM {avg.loc[2022, 'income_median']:,.0f}",
         f"{pct(avg.loc[2022, 'income_median'], avg.loc[2019, 'income_median']):+.1f}% vs 2019"),
        ("Highest state (2022)", i22.idxmax(), f"RM {i22.max():,.0f}"),
        ("Lowest state (2022)", i22.idxmin(), f"RM {i22.min():,.0f}"),
    ])

    # ---- Visualization 1: line plot
    st.subheader("Visualization 1: Line plot of mean income by state")
    states = sorted(inc["state"].unique())
    sel = st.multiselect("Filter states", states, default=states)
    fig = px.line(inc[inc["state"].isin(sel)], x="year", y="income_mean", color="state", markers=True,
                  color_discrete_sequence=px.colors.qualitative.Alphabet,
                  labels={"income_mean": "Mean monthly household income (RM)", "year": "Year"})
    fig.update_traces(line=dict(width=1.5))
    al = inc.groupby("year")["income_mean"].mean().reset_index()
    fig.add_scatter(x=al["year"], y=al["income_mean"], mode="lines+markers+text",
                    name="Average of all states", line=dict(color="black", width=4, dash="dash"),
                    marker=dict(color="black", size=9),
                    text=[f"RM {v:,.0f}" for v in al["income_mean"]], textposition="top center")
    fig.update_xaxes(tickvals=[2019, 2020, 2022])
    fig.update_layout(template="plotly_white", title="Mean monthly household income by state",
                      legend_title_text="States & averages", hovermode="x unified", height=550)
    show(fig)

    # ---- Visualization 2: map
    st.subheader("Visualization 2: Geospatial map")
    yr = st.selectbox("Year", [2019, 2020, 2022], index=2)
    dm = inc[inc["year"] == yr]
    gj = load_geojson()
    if gj is None:
        st.warning("Could not load the map boundaries (no internet). Showing a bar chart instead.")
        fig = px.bar(dm.sort_values("income_mean"), x="income_mean", y="state", orientation="h")
    else:
        fig = px.choropleth(dm, geojson=gj, locations="canon", featureidkey="properties.canon",
                            color="income_mean", hover_name="state", color_continuous_scale=INCOME_SCALE,
                            range_color=(4500, 13500), labels={"income_mean": "Mean income (RM)"})
        fig.update_geos(fitbounds="locations", visible=False, bgcolor="#f7f8fa")
        fig.update_traces(marker_line_color="white", marker_line_width=1)
        fig.update_layout(coloraxis_colorbar=dict(
            title="Mean Income (RM)", tickvals=list(range(5000, 14000, 1000)),
            ticktext=[f"{v // 1000}k" for v in range(5000, 14000, 1000)], thickness=15, len=0.75),
            title=f"Mean household income by state, {yr}", height=550, margin=dict(r=0, t=50, l=0, b=0))
        gj_names = {f["properties"]["canon"] for f in gj["features"]}
        missing = sorted(dm.loc[~dm["canon"].isin(gj_names), "state"].unique())
        if missing:
            st.caption("Not shown on the map (no boundary in the GeoJSON): " + ", ".join(missing))
    show(fig)

    # ---- Visualization 3: scatter 2019 vs 2022
    st.subheader("Visualization 3: Scatter plot, income 2019 vs 2022")
    sc = pd.DataFrame({"income_2019": i19, "income_2022": i22}).dropna()
    sc["pct_change"] = pct(sc["income_2022"], sc["income_2019"])
    sc = sc.reset_index()
    r1 = np.corrcoef(sc["income_2019"], sc["income_2022"])[0, 1]
    POS = {"W.P. Putrajaya": "top center", "W.P. Kuala Lumpur": "middle right", "Selangor": "top center",
           "W.P. Labuan": "bottom right", "Johor": "top left", "Kelantan": "middle right"}
    sc["label"] = sc["state"].where(sc["state"].isin(POS), "")
    fig = px.scatter(sc, x="income_2019", y="income_2022", color="pct_change", text="label",
                     hover_name="state", color_continuous_scale="YlGnBu",
                     labels={"income_2019": "Mean income 2019 (RM)", "income_2022": "Mean income 2022 (RM)",
                             "pct_change": "% change"})
    fig.update_traces(textposition=[POS.get(s, "top center") for s in sc["state"]],
                      marker=dict(size=13, line=dict(width=1.5, color="#444")))
    fig.add_scatter(x=[3500, 15500], y=[3500, 15500], mode="lines", name="No change (y = x)",
                    line=dict(dash="dash", color="grey"))
    fig.add_annotation(x=14200, y=4500, text=f"r = {r1:.3f}", showarrow=False, bordercolor="#999",
                       bgcolor="white")
    ticks = list(range(5000, 16000, 2000))
    fig.update_xaxes(range=[3500, 15500], tickvals=ticks, ticktext=[f"{t // 1000}k" for t in ticks])
    fig.update_yaxes(range=[3500, 15500], tickvals=ticks, ticktext=[f"{t // 1000}k" for t in ticks])
    fig.update_layout(template="plotly_white", title="Mean household income: 2019 vs 2022", height=650,
                      coloraxis_colorbar=dict(title="% change", thickness=15, len=0.7),
                      legend=dict(orientation="h", y=-0.15))
    show(fig)

    with st.expander("Interpretation / Discussion", expanded=True):
        chg = pct(i22, i19).sort_values()
        drop20 = pct(i20, i19)
        st.markdown(f"""
- **Trend:** average mean income went from RM {avg.loc[2019, 'income_mean']:,.0f} (2019) to
  RM {avg.loc[2020, 'income_mean']:,.0f} (2020) and RM {avg.loc[2022, 'income_mean']:,.0f} (2022).
  In 2020, {int((drop20 < 0).sum())} of {len(drop20)} states had lower income than in 2019 (COVID-19 period).
- **Highest and lowest:** {i22.idxmax()} is highest in 2022 (RM {i22.max():,.0f}) and {i22.idxmin()} is lowest
  (RM {i22.min():,.0f}), about {i22.max() / i22.min():.2f} times higher.
- **Change 2019 to 2022:** biggest rise {chg.idxmax()} ({chg.max():+.2f}%); {int((chg < 0).sum())} state(s) below the
  2019 level ({chg.idxmin()}, {chg.min():+.2f}%). Correlation 2019 vs 2022: r = {r1:.3f}.
- **Link to objective:** income recovered in most states, but the ranking of states hardly changed, so the gap
  between rich and poor states did not close. The data only shows income values, so reasons are our interpretation.
""")

# ================================================================== OBJECTIVE 2
elif page == "Objective 2: Schools":
    page_head("Objective 2: School distribution",
              "To examine the number and distribution of schools across states, districts and school types "
              "from 2019 to 2023.")
    tot = merged.groupby("year")[["schools_primary", "schools_secondary", "schools_tertiary",
                                  "schools_total"]].sum()
    top23 = merged[merged["year"] == 2023].set_index("state")["schools_total"]

    def d(col):
        return f"{int(tot.loc[2023, col] - tot.loc[2019, col]):+,} vs 2019"

    summary_box([
        ("Total schools (2023)", f"{int(tot.loc[2023, 'schools_total']):,}", d("schools_total")),
        ("Primary (2023)", f"{int(tot.loc[2023, 'schools_primary']):,}", d("schools_primary")),
        ("Secondary (2023)", f"{int(tot.loc[2023, 'schools_secondary']):,}", d("schools_secondary")),
        ("Most schools (2023)", top23.idxmax(), f"{int(top23.max()):,} schools"),
    ])
    st.caption("State-level data covers government primary, secondary and public universities (IPTA) only.")

    # ---- Visualization 1: zoomed line plot
    st.subheader("Visualization 1: Line plot of schools over time")
    opts = ["All states"] + sorted(merged["state"].unique())
    sst = st.selectbox("State", opts)
    base = merged if sst == "All states" else merged[merged["state"] == sst]
    tt = base.groupby("year")[["schools_primary", "schools_secondary"]].sum()
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Primary (government)", "Secondary (government)"))
    for i, (col, colour) in enumerate([("schools_primary", "#1f77b4"), ("schools_secondary", "#ff7f0e")], start=1):
        fig.add_trace(go.Scatter(x=list(tt.index), y=list(tt[col]), mode="lines+markers+text",
                                 text=[f"{int(v):,}" for v in tt[col]], textposition="top center",
                                 line=dict(color=colour, width=3), showlegend=False), row=1, col=i)
        fig.update_xaxes(tickvals=list(tt.index), title_text="Year", row=1, col=i)
        fig.update_yaxes(title_text="Number of schools", row=1, col=i)
    fig.update_layout(template="plotly_white", height=450,
                      title="Change in number of schools, 2019-2023 (y-axes zoomed to show small changes)")
    show(fig)

    # ---- Visualization 2: treemap
    st.subheader("Visualization 2: Treemap (state > district)")
    c1, c2 = st.columns(2)
    ty = c1.selectbox("School type", list(TYPE_LABELS.values()))
    yr = c2.selectbox("Year", sorted(districts["year"].unique()), index=4)
    dt = districts[(districts["type_label"] == ty) & (districts["year"] == yr) & (districts["schools"] > 0)]
    fig = px.treemap(dt, path=["state", "district"], values="schools", color="schools",
                     color_continuous_scale="Blues", range_color=(0, 190))
    try:  # make the state (parent) boxes neutral so only districts carry the colour
        tr = fig.data[0]
        cols = list(tr.marker.colors)
        for i, par in enumerate(tr.parents):
            if par == "":
                cols[i] = 0
        tr.marker.colors = cols
    except Exception:
        pass
    fig.update_layout(title=f"{ty} schools by state and district, {yr}", height=700,
                      coloraxis_colorbar=dict(title="Schools per district"))
    show(fig)

    # ---- Visualization 3: heatmap of change vs 2019
    st.subheader("Visualization 3: Heatmap of change in schools vs 2019")
    p = merged.pivot(index="state", columns="year", values="schools_total")
    chg = p.sub(p[2019], axis=0).drop(columns=2019).round().astype(int)
    chg = chg.sort_values(2023, ascending=False)
    chg.columns = [str(c) for c in chg.columns]
    fig = px.imshow(chg, text_auto="+d", aspect="auto", color_continuous_scale="RdBu", zmin=-4, zmax=4,
                    labels={"color": "Change in schools", "x": "Year", "y": "State"})
    fig.update_xaxes(type="category")
    fig.update_layout(title="Change in total schools compared with 2019, by state", height=600)
    show(fig)

    with st.expander("Interpretation / Discussion", expanded=True):
        chg23 = chg["2023"]
        share = top23.sort_values(ascending=False)
        st.markdown(f"""
- **Stability:** total schools went from {int(tot.loc[2019, 'schools_total']):,} (2019) to
  {int(tot.loc[2023, 'schools_total']):,} (2023), a change of only
  {pct(tot.loc[2023, 'schools_total'], tot.loc[2019, 'schools_total']):+.2f}%. Primary
  {int(tot.loc[2023, 'schools_primary'] - tot.loc[2019, 'schools_primary']):+d}, secondary
  {int(tot.loc[2023, 'schools_secondary'] - tot.loc[2019, 'schools_secondary']):+d}.
- **Distribution:** {share.index[0]} ({int(share.iloc[0]):,}), {share.index[1]} ({int(share.iloc[1]):,}) and
  {share.index[2]} ({int(share.iloc[2]):,}) have the most schools; {share.index[-1]} ({int(share.iloc[-1]):,}) has the fewest.
- **Change by state (heatmap):** {int((chg23 > 0).sum())} states gained schools, {int((chg23 == 0).sum())} stayed the same
  and {int((chg23 < 0).sum())} lost schools ({', '.join(chg23[chg23 < 0].index)}).
- **Link to objective:** school provision stayed stable, and differences between states mostly follow state size and
  number of districts. The data counts schools, not students.
""")

# ================================================================== OBJECTIVE 3
elif page == "Objective 3: Marriages":
    page_head("Objective 3: Marriage trends",
              "To explore how marriages changed across states and by sex from 2019 to 2023, and how they relate "
              "to household income.")
    p = merged.pivot(index="state", columns="year", values="marriage_abs_avg")
    nat = merged.groupby("year").agg(f=("marriage_rate_female", "mean"), m=("marriage_rate_male", "mean"),
                                     cnt=("marriage_abs_avg", "sum"))
    ch23 = pct(p[2023], p[2019])
    ch22 = pct(p[2022], p[2019])
    ip = merged.pivot(index="state", columns="year", values="income_mean")
    sc = pd.DataFrame({"income_change": pct(ip[2022], ip[2019]), "marriage_change": ch22,
                       "marriages_2019": p[2019]}).dropna().reset_index()
    r = np.corrcoef(sc["income_change"], sc["marriage_change"])[0, 1]

    summary_box([
        ("Marriages (2023)", f"{nat.loc[2023, 'cnt']:,.0f}", f"{pct(nat.loc[2023, 'cnt'], nat.loc[2019, 'cnt']):+.2f}% vs 2019"),
        ("Peak year", str(int(nat["cnt"].idxmax())), f"{nat['cnt'].max():,.0f} marriages"),
        ("Biggest drop (2019-23)", ch23.idxmin(), f"{ch23.min():+.2f}%"),
        ("Income vs marriage (r)", f"{r:.4f}", "Pearson r, 2019-2022"),
    ])
    st.caption("Marriages per state = average of the male and female records.")

    # ---- Visualization 1: line plot by sex
    st.subheader("Visualization 1: Marriage rate by sex")
    dd = nat[["f", "m"]].rename(columns={"f": "Female", "m": "Male"}).reset_index()
    dd = dd.melt("year", var_name="Sex", value_name="rate")
    dd["label"] = dd["rate"].round(1).astype(str)
    fig = px.line(dd, x="year", y="rate", color="Sex", markers=True, text="label",
                  color_discrete_map={"Female": "#e4503f", "Male": "#4c6ef5"},
                  labels={"rate": "Marriage rate", "year": "Year"})
    fig.update_traces(mode="lines+markers+text")
    fig.for_each_trace(lambda t: t.update(textposition="top center" if t.name == "Female" else "bottom center"))
    fig.update_xaxes(dtick=1)
    fig.update_layout(template="plotly_white", title="Average marriage rate by sex, 2019-2023 (y-axis zoomed)",
                      height=480)
    show(fig)

    # ---- Visualization 2: diverging bar
    st.subheader("Visualization 2: Change in marriages by state")
    yb = st.radio("Compare 2019 with", [2020, 2021, 2022, 2023], index=3, horizontal=True)
    cb = pct(p[yb], p[2019]).sort_values().reset_index()
    cb.columns = ["state", "change"]
    fig = px.bar(cb, x="change", y="state", orientation="h", color="change",
                 color_continuous_scale=DIVERGING, range_color=(-21, 21), labels={"change": "% change"})
    fig.update_traces(texttemplate="%{x:+.1f}%", textposition="outside",
                      marker_line_color="white", marker_line_width=1)
    fig.add_vline(x=0, line_color="#bbb")
    fig.update_xaxes(range=[-27, 20], title="% change")
    fig.update_layout(template="plotly_white", title=f"Change in marriages by state, 2019 to {yb} (%)",
                      height=650, coloraxis_colorbar=dict(title="% change", thickness=15, len=0.6))
    show(fig)

    # ---- Visualization 3: scatter income vs marriage change
    st.subheader("Visualization 3: Income change vs marriage change")
    POS = {"W.P. Putrajaya": "top center", "Kelantan": "bottom right", "Pahang": "bottom center",
           "Perak": "middle left", "Johor": "bottom right", "Selangor": "top center"}
    sc["label"] = sc["state"].where(sc["state"].isin(POS), "")
    fig = px.scatter(sc, x="income_change", y="marriage_change", size="marriages_2019", size_max=40,
                     color="marriage_change", color_continuous_scale=DIVERGING, range_color=(-30, 30),
                     text="label", hover_name="state",
                     labels={"income_change": "Income change, 2019 to 2022 (%)",
                             "marriage_change": "Marriage change, 2019 to 2022 (%)"})
    fig.update_traces(textposition=[POS.get(s, "top center") for s in sc["state"]],
                      marker=dict(line=dict(width=1, color="#888")))
    k, b = np.polyfit(sc["income_change"], sc["marriage_change"], 1)
    xs = np.linspace(sc["income_change"].min(), sc["income_change"].max(), 20)
    fig.add_scatter(x=xs, y=k * xs + b, mode="lines", name="Trend line",
                    line=dict(dash="dash", color="grey"))
    fig.add_hline(y=0, line_color="#ccc")
    fig.add_annotation(x=12, y=-9, text=f"r = {r:.3f}", showarrow=False, bordercolor="#999", bgcolor="white")
    fig.update_layout(template="plotly_white", height=650, margin=dict(r=100),
                      title="Income change vs marriage change by state, 2019 to 2022",
                      coloraxis_colorbar=dict(title="Marriage change (%)", thickness=15, len=0.7))
    show(fig)

    with st.expander("Interpretation / Discussion", expanded=True):
        strength = "no clear" if abs(r) < 0.2 else ("weak" if abs(r) < 0.4 else "moderate or strong")
        st.markdown(f"""
- **Trend:** marriages were {nat.loc[2019, 'cnt']:,.0f} (2019), {nat.loc[2020, 'cnt']:,.0f} (2020),
  {nat.loc[2021, 'cnt']:,.0f} (2021), {nat.loc[2022, 'cnt']:,.0f} (2022) and {nat.loc[2023, 'cnt']:,.0f} (2023): a fall in 2020
  (COVID-19 period), a rebound in 2021, and a fall again in 2023.
- **By sex:** the female rate is higher than the male rate in every year (2023: {nat.loc[2023, 'f']:.2f} vs {nat.loc[2023, 'm']:.2f}).
- **By state:** marriages fell in {int((ch23 < 0).sum())} of {len(ch23)} states between 2019 and 2023. Biggest fall:
  {ch23.idxmin()} ({ch23.min():+.2f}%); biggest rise: {ch23.idxmax()} ({ch23.max():+.2f}%).
- **Link to income:** r = {r:.3f}, so there is {strength} relationship across 16 states. This shows association only,
  not cause, and small states such as Putrajaya can show large % changes from small numbers.
""")

# ================================================================== MERGED DATA
else:
    page_head("Merged dataset (state by year)",
              "Three data.gov.my files merged on state and year: schools (state totals from the 'All Districts' rows), "
              "marriages (male and female) and household income.")
    out = merged.drop(columns=["canon"])
    st.dataframe(out, use_container_width=True)
    st.caption("Income is empty for 2021 and 2023 because the source file has no data for those years.")
    st.download_button("Download merged CSV", out.to_csv(index=False), "merged_dataset.csv", "text/csv")
