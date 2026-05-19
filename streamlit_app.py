from __future__ import annotations

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="World Cup Dashboard",
    page_icon=":soccer:",
    layout="wide",
)


st.title("World Cup Dashboard")
st.caption("Upload match data to explore teams, goals, and tournament notes.")

uploaded_file = st.sidebar.file_uploader("Upload match CSV", type=["csv"])
tournament_year = st.sidebar.selectbox(
    "Tournament year",
    [2026, 2022, 2018, 2014, 2010, 2006, 2002, 1998],
)


def load_matches() -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()
    return pd.read_csv(uploaded_file)


matches = load_matches()

overview_tab, data_tab, notes_tab = st.tabs(["Overview", "Data", "Notes"])

with overview_tab:
    st.subheader(f"{tournament_year} overview")

    if matches.empty:
        st.info("Upload a CSV from the sidebar to populate the dashboard.")
        st.markdown(
            "Suggested columns: `date`, `home_team`, `away_team`, "
            "`home_score`, `away_score`, `stage`, `venue`."
        )
    else:
        metric_cols = st.columns(3)
        metric_cols[0].metric("Matches", len(matches))

        if {"home_score", "away_score"}.issubset(matches.columns):
            goals = matches["home_score"].sum() + matches["away_score"].sum()
            metric_cols[1].metric("Goals", int(goals))
            metric_cols[2].metric("Goals per match", f"{goals / len(matches):.2f}")
        else:
            metric_cols[1].metric("Columns", len(matches.columns))
            metric_cols[2].metric("Rows", len(matches.index))

with data_tab:
    st.subheader("Match data")

    if matches.empty:
        st.write("No data loaded yet.")
    else:
        st.dataframe(matches, use_container_width=True)

with notes_tab:
    st.subheader("Tournament notes")
    notes = st.text_area(
        "Notes",
        placeholder="Track assumptions, data sources, or match observations here.",
        height=180,
    )

    if notes:
        st.success("Notes captured for this session.")
