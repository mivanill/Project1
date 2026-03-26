from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.loader import load_table, normalize_column_names, validate_columns
from src.cleaner import clean_tickets
from src.detectors import run_all_detectors, group_systemic_incidents
from src.summarizer import (
    build_executive_summary,
    build_overview_stats,
    generate_systemic_issue_notes,
    generate_systemic_incident_explanations,
)

st.set_page_config(page_title="Ticket Anomaly Agent", layout="wide")

st.title("Ticket Anomaly Agent")
st.caption("V1 demo: detect repeated issues and possible systemic anomalies from ticket exports.")

uploaded_file = st.file_uploader("Upload ticket file", type=["xlsx", "csv"])

if uploaded_file is None:
    st.info("Upload an Excel or CSV file to begin.")
    st.stop()

try:
    raw_df = load_table(uploaded_file)
    raw_df = normalize_column_names(raw_df)

    is_valid, missing_columns = validate_columns(raw_df)
    if not is_valid:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        st.stop()

    df = clean_tickets(raw_df)
    anomalies_df = run_all_detectors(df)
    stats = build_overview_stats(df, anomalies_df)
    executive_summary = build_executive_summary(stats, anomalies_df)
    notes = generate_systemic_issue_notes(anomalies_df)
    # New: group and explain likely systemic incidents
    grouped_incidents = group_systemic_incidents(anomalies_df, system_col="assignment_group")
    systemic_explanations = generate_systemic_incident_explanations(grouped_incidents)

except Exception as exc:
    st.exception(exc)
    st.stop()

st.subheader("Overview")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Tickets", stats["total_tickets"])
col2.metric("Unique Categories", stats["unique_categories"])
col3.metric("Top Category", stats["top_category"])
col4.metric("Busiest Day", str(stats["busiest_day"]))
col5.metric("Anomalies Detected", stats["anomalies_detected"])

st.markdown("### Executive Summary")
st.write(executive_summary)

st.subheader("Daily Ticket Volume")
daily_counts = df.groupby("opened_date").size().reset_index(name="count")
fig = px.bar(daily_counts, x="opened_date", y="count", title="Tickets Opened Per Day")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Detected Anomalies")
if anomalies_df.empty:
    st.success("No anomalies detected under the current V1 rules.")
else:
    st.dataframe(anomalies_df, use_container_width=True)

    high_severity = anomalies_df[anomalies_df["severity"] == "high"]

    st.subheader("High Severity Findings")
    if high_severity.empty:
        st.write("No high severity findings.")
    else:
        for _, row in high_severity.iterrows():
            st.warning(
                f"**{row['title']}**  \n"
                f"{row['description']}  \n"
                f"Impact Score: {row['impact_score']} | Confidence: {row['confidence']}"
            )


# New section: Likely Systemic Incidents
st.subheader("Likely Systemic Incidents")
if grouped_incidents is not None and not grouped_incidents.empty:
    for idx, row in grouped_incidents.iterrows():
        st.markdown(f"**System:** {row['possible_system']}  ")
        st.markdown(f"Impact Score: {row['total_impact_score']} | Anomaly Count: {row['count']}")
        st.markdown(f"_Example:_ {row['sample_title']} — {row['sample_description']}")
        st.info(systemic_explanations[idx])
else:
    st.write("No likely systemic incidents detected.")

# Keep previous notes section for context
st.subheader("Possible Systemic Problem Indicators")
for note in notes:
    st.write(f"- {note}")

with st.expander("Preview Cleaned Data"):
    st.dataframe(df.head(50), use_container_width=True)