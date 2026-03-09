"""
COVID-19 Global Dashboard
Data source: Johns Hopkins University CSSE COVID-19 Dataset
https://github.com/CSSEGISandData/COVID-19
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from io import StringIO

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="COVID-19 Global Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data loading ──────────────────────────────────────────────────────────────
BASE_URL = (
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
    "csse_covid_19_data/csse_covid_19_time_series/"
)

DATASETS = {
    "Confirmed Cases": "time_series_covid19_confirmed_global.csv",
    "Deaths":          "time_series_covid19_deaths_global.csv",
}


@st.cache_data(ttl=3600, show_spinner="Fetching latest COVID-19 data…")
def load_dataset(filename: str) -> pd.DataFrame:
    """Download a CSSE time-series CSV and return it tidy (long format)."""
    url = BASE_URL + filename
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))

    # Aggregate by country (Province/State rows → sum)
    df = df.drop(columns=["Province/State", "Lat", "Long"], errors="ignore")
    df = df.groupby("Country/Region", as_index=False).sum()

    # Melt to long format
    df = df.melt(id_vars="Country/Region", var_name="Date", value_name="Cumulative")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Country/Region", "Date"])

    # Daily new cases (diff within each country)
    df["Daily"] = (
        df.groupby("Country/Region")["Cumulative"]
        .diff()
        .clip(lower=0)  # remove negative corrections
    )

    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_all_data() -> dict[str, pd.DataFrame]:
    return {label: load_dataset(fname) for label, fname in DATASETS.items()}


# ── Load data ─────────────────────────────────────────────────────────────────
data = get_all_data()
all_countries = sorted(data["Confirmed Cases"]["Country/Region"].unique())

# ── Sidebar controls ──────────────────────────────────────────────────────────
st.sidebar.title("🦠 COVID-19 Dashboard")
st.sidebar.markdown("Data: [JHU CSSE](https://github.com/CSSEGISandData/COVID-19)")
st.sidebar.divider()

# Country selection
st.sidebar.subheader("Select Countries")
default_countries = ["US", "India", "Brazil", "United Kingdom", "Germany"]
default_countries = [c for c in default_countries if c in all_countries]

selected_countries = st.sidebar.multiselect(
    "Add / remove countries",
    options=all_countries,
    default=default_countries,
    placeholder="Type or scroll to add a country…",
)

if not selected_countries:
    st.warning("Please select at least one country from the sidebar.")
    st.stop()

st.sidebar.divider()

# Metric selection
st.sidebar.subheader("Metric")
metric = st.sidebar.radio(
    "Show",
    options=["Confirmed Cases", "Deaths"],
    index=0,
)

# Count type
st.sidebar.subheader("Count Type")
count_type = st.sidebar.radio(
    "Display",
    options=["Daily New", "Cumulative"],
    index=0,
)
col_name = "Daily" if count_type == "Daily New" else "Cumulative"

# Date range
st.sidebar.divider()
st.sidebar.subheader("Date Range")
df_full = data[metric]
min_date = df_full["Date"].min().date()
max_date = df_full["Date"].max().date()

date_range = st.sidebar.date_input(
    "From / To",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Chart type
st.sidebar.divider()
chart_type = st.sidebar.selectbox(
    "Chart type",
    ["Line", "Bar", "Area"],
    index=0,
)

# Rolling average
smooth = st.sidebar.checkbox("7-day rolling average", value=True)

# ── Main content ──────────────────────────────────────────────────────────────
st.title("🌍 COVID-19 Global Dashboard")
st.markdown(
    f"**Metric:** {metric} &nbsp;|&nbsp; "
    f"**Display:** {count_type} &nbsp;|&nbsp; "
    f"**Period:** {start_date} → {end_date}"
)

# Filter data
df = df_full[
    (df_full["Country/Region"].isin(selected_countries))
    & (df_full["Date"] >= pd.Timestamp(start_date))
    & (df_full["Date"] <= pd.Timestamp(end_date))
].copy()

if smooth and count_type == "Daily New":
    df[col_name] = (
        df.groupby("Country/Region")[col_name]
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )

# ── Chart ─────────────────────────────────────────────────────────────────────
fig = go.Figure()

for country in selected_countries:
    cdf = df[df["Country/Region"] == country]
    if cdf.empty:
        continue

    kwargs = dict(
        x=cdf["Date"],
        y=cdf[col_name],
        name=country,
        hovertemplate=f"<b>{country}</b><br>%{{x|%b %d, %Y}}<br>{col_name}: %{{y:,.0f}}<extra></extra>",
    )

    if chart_type == "Line":
        fig.add_trace(go.Scatter(mode="lines", **kwargs))
    elif chart_type == "Bar":
        fig.add_trace(go.Bar(**kwargs))
    else:  # Area
        fig.add_trace(go.Scatter(fill="tozeroy", mode="lines", **kwargs))

title_suffix = " (7-day avg)" if smooth and count_type == "Daily New" else ""
fig.update_layout(
    title=f"{count_type} {metric}{title_suffix}",
    xaxis_title="Date",
    yaxis_title="Count",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=520,
    template="plotly_white",
)
fig.update_yaxes(tickformat=",")

st.plotly_chart(fig, use_container_width=True)

# ── Summary table ─────────────────────────────────────────────────────────────
st.subheader("Summary Statistics")

latest_date = df["Date"].max()
summary_rows = []
for country in selected_countries:
    cdf = df_full[df_full["Country/Region"] == country]
    if cdf.empty:
        continue
    latest = cdf[cdf["Date"] == cdf["Date"].max()].iloc[0]
    summary_rows.append({
        "Country": country,
        "Total Confirmed": int(
            data["Confirmed Cases"][
                (data["Confirmed Cases"]["Country/Region"] == country)
                & (data["Confirmed Cases"]["Date"] == data["Confirmed Cases"]["Date"].max())
            ]["Cumulative"].values[0]
        ) if country in data["Confirmed Cases"]["Country/Region"].values else 0,
        "Total Deaths": int(
            data["Deaths"][
                (data["Deaths"]["Country/Region"] == country)
                & (data["Deaths"]["Date"] == data["Deaths"]["Date"].max())
            ]["Cumulative"].values[0]
        ) if country in data["Deaths"]["Country/Region"].values else 0,
    })

if summary_rows:
    summary_df = pd.DataFrame(summary_rows).set_index("Country")
    summary_df["Case Fatality Rate"] = (
        summary_df["Total Deaths"] / summary_df["Total Confirmed"] * 100
    ).round(2).astype(str) + "%"
    summary_df["Total Confirmed"] = summary_df["Total Confirmed"].map("{:,}".format)
    summary_df["Total Deaths"] = summary_df["Total Deaths"].map("{:,}".format)
    st.dataframe(summary_df, use_container_width=True)

# ── Data last updated ─────────────────────────────────────────────────────────
st.caption(
    f"Data last updated through: **{max_date}** · "
    "Source: Johns Hopkins University CSSE COVID-19 Dataset"
)
