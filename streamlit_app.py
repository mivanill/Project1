from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.cleaner import clean_tickets
from src.detectors import correlate_incidents, group_systemic_incidents, run_all_detectors
from src.loader import load_table, normalize_column_names, validate_columns
from src.summarizer import (
    build_executive_summary,
    build_overview_stats,
    generate_systemic_issue_notes,
)

st.set_page_config(page_title="Ticket Anomaly Agent", layout="wide")

st.title("Ticket Anomaly Agent")
st.caption("Analyze ticket exports for anomaly patterns, likely affected systems, and follow-up checks.")

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
    grouped_incidents = group_systemic_incidents(anomalies_df)
    correlated_incidents = correlate_incidents(anomalies_df)
    stats = build_overview_stats(df, anomalies_df)
    executive_summary = build_executive_summary(stats, anomalies_df)
    notes = generate_systemic_issue_notes(anomalies_df)

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
    st.success("No anomalies detected under the current analysis rules.")
else:
    display_columns = [
        "anomaly_type",
        "title",
        "description",
        "possible_system",
        "recommended_check",
        "interpretation",
        "confidence",
        "count",
        "impact_score",
        "severity",
    ]
    st.dataframe(anomalies_df[display_columns], use_container_width=True)

    st.subheader("High Severity Findings")
    high_severity = anomalies_df[anomalies_df["severity"] == "high"]
    if high_severity.empty:
        st.write("No high severity findings.")
    else:
        for _, row in high_severity.iterrows():
            st.warning(
                f"**{row['title']}**  \n"
                f"{row['description']}  \n"
                f"System: {row['possible_system']}  \n"
                f"Recommended Check: {row['recommended_check']}  \n"
                f"Interpretation: {row['interpretation']}  \n"
                f"Impact Score: {row['impact_score']} | Confidence: {row['confidence']}"
            )

st.subheader("Likely Systemic Incidents")
if grouped_incidents.empty:
    st.write("No likely systemic incidents detected.")
else:
    for _, row in grouped_incidents.iterrows():
        st.markdown(f"**System:** {row['possible_system']}")
        st.write(
            f"Total Impact: {row['total_impact_score']} | Occurrence Count: {row['count']}"
        )
        st.write(f"Top Issue: {row['top_issue']}")
        st.caption(row["interpretation"])

st.subheader("Correlated Incidents")
if correlated_incidents.empty:
    st.write("No correlated incidents inferred from the current anomaly signals.")
else:
    display_incidents = correlated_incidents.copy()
    display_incidents["signals"] = display_incidents["signals"].apply(
        lambda values: ", ".join(values) if isinstance(values, list) else str(values)
    )

    st.dataframe(
        display_incidents[["system", "confidence", "signals", "summary"]],
        use_container_width=True,
    )

    for _, row in correlated_incidents.iterrows():
        st.markdown(f"**System:** {row['system']}")
        st.write(f"Confidence: {row['confidence']}")
        st.write(f"Signals: {', '.join(row['signals']) if row['signals'] else 'limited signal'}")
        st.caption(row["summary"])

st.subheader("Recommended Checks")
if anomalies_df.empty:
    st.write("No recommended checks to display.")
else:
    recommended_checks = (
        anomalies_df[["possible_system", "recommended_check"]]
        .drop_duplicates()
        .sort_values(by=["possible_system", "recommended_check"], kind="mergesort")
    )
    for _, row in recommended_checks.iterrows():
        st.markdown(f"**{row['possible_system']}**")
        st.write(row["recommended_check"])

st.subheader("Possible Systemic Problem Indicators")
for note in notes:
    st.write(f"- {note}")

with st.expander("Preview Cleaned Data"):
    st.dataframe(df.head(50), use_container_width=True)
