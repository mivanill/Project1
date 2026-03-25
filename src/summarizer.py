def build_overview_stats(df, anomalies):
    return {
        "total_tickets": len(df),
        "unique_categories": df["category"].nunique(),
        "top_category": df["category"].value_counts().idxmax(),
        "busiest_day": df.groupby("opened_date").size().idxmax(),
        "anomalies_detected": len(anomalies),
    }


def build_executive_summary(stats, anomalies):
    return (
        f"Detected {stats['anomalies_detected']} anomalies "
        f"out of {stats['total_tickets']} tickets."
    )


def generate_systemic_issue_notes(anomalies):
    if anomalies.empty:
        return ["No major issues detected."]

    return [
        "Potential recurring issues were detected based on volume and category patterns."
    ]