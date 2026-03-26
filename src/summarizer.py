def build_overview_stats(df, anomalies):
    top_category = df["category"].value_counts().idxmax() if not df.empty else "n/a"
    busiest_day = df.groupby("opened_date").size().idxmax() if not df.empty else "n/a"

    return {
        "total_tickets": len(df),
        "unique_categories": df["category"].nunique(),
        "top_category": top_category,
        "busiest_day": busiest_day,
        "anomalies_detected": len(anomalies),
    }


def build_executive_summary(stats, anomalies):
    if anomalies.empty:
        return (
            f"Reviewed {stats['total_tickets']} tickets and detected no major anomalies "
            "under the current analysis rules."
        )

    top_finding = anomalies.sort_values(
        by=["impact_score", "count", "title"],
        ascending=[False, False, True],
        kind="mergesort",
    ).iloc[0]

    return (
        f"Reviewed {stats['total_tickets']} tickets and flagged "
        f"{stats['anomalies_detected']} anomalies. "
        f"The highest-impact finding is '{top_finding['title']}', and the likely affected "
        f"system is {top_finding['possible_system']}."
    )


def generate_systemic_issue_notes(anomalies):
    if anomalies.empty:
        return ["No major issues detected."]

    notes = []
    anomaly_types = set(anomalies["anomaly_type"].tolist())

    if "repeated_similar_issue" in anomaly_types:
        notes.append(
            "Repeated similar issue clusters suggest users may be experiencing the same underlying service disruption."
        )

    if "volume_spike" in anomaly_types:
        notes.append(
            "Daily volume spikes may reflect a shared outage, a failed change, or broader service degradation."
        )

    if "category" in anomaly_types:
        notes.append(
            "Category concentration indicates one support domain is driving a disproportionate share of tickets."
        )

    if not notes:
        notes.append("Anomalies were detected, but they do not yet point to a clear systemic pattern.")

    return notes
