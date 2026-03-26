import pandas as pd

from src.enrichment import enrich_issue_text
from src.similarity import find_similar_groups


def run_all_detectors(df):
    results = []

    # Volume spike detection
    daily = df.groupby("opened_date").size().reset_index(name="count")
    avg = daily["count"].mean() if not daily.empty else 0

    spikes = daily[daily["count"] > avg * 2] if avg > 0 else pd.DataFrame()

    for _, row in spikes.iterrows():
        title = f"Spike on {row['opened_date']}"
        description = f"{row['count']} tickets vs average {round(avg, 1)}"
        enrichment = enrich_issue_text(title, description)

        if enrichment["possible_system"] == "Unknown":
            enrichment["interpretation"] = (
                "A sharp rise in daily ticket volume may indicate a shared outage, "
                "failed rollout, or service degradation."
            )

        results.append({
            "anomaly_type": "volume_spike",
            "title": title,
            "description": description,
            "count": int(row["count"]),
            "severity": "high",
            "impact_score": 90,
            **enrichment,
        })

    # Category concentration detection
    cat_counts = df["category"].value_counts()

    for cat, count in cat_counts.items():
        if count > len(df) * 0.3:
            title = f"High volume in category: {cat}"
            description = f"{count} tickets were opened in this category"
            enrichment = enrich_issue_text(cat, description)

            results.append({
                "anomaly_type": "category",
                "title": title,
                "description": description,
                "count": int(count),
                "severity": "medium",
                "impact_score": 65,
                **enrichment,
            })

    # Repeated similar issue detection
    groups = find_similar_groups(df)

    for group in groups:
        sample_text = df.iloc[group[0]]["short_description"]
        count = len(group)
        title = "Repeated similar issue detected"
        description = f"{count} similar tickets: '{sample_text}'"
        enrichment = enrich_issue_text(title, sample_text)

        results.append({
            "anomaly_type": "repeated_similar_issue",
            "title": title,
            "description": description,
            "count": count,
            "severity": "high",
            "impact_score": min(100, 50 + count * 5),
            **enrichment,
        })

    if not results:
        return pd.DataFrame(columns=[
            "anomaly_type",
            "title",
            "description",
            "count",
            "severity",
            "impact_score",
            "possible_system",
            "recommended_check",
            "interpretation",
            "confidence",
        ])

    anomalies_df = pd.DataFrame(results)
    anomalies_df = anomalies_df.sort_values(
        by=["impact_score", "count", "title"],
        ascending=[False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return anomalies_df


def group_systemic_incidents(anomalies_df):
    columns = [
        "possible_system",
        "total_impact_score",
        "count",
        "top_issue",
        "interpretation",
    ]

    if anomalies_df is None or anomalies_df.empty:
        return pd.DataFrame(columns=columns)

    grouped_rows = []

    for possible_system, group in anomalies_df.groupby("possible_system", dropna=False):
        sorted_group = group.sort_values(
            by=["impact_score", "count", "title"],
            ascending=[False, False, True],
            kind="mergesort",
        )
        top_row = sorted_group.iloc[0]

        grouped_rows.append({
            "possible_system": possible_system,
            "total_impact_score": int(group["impact_score"].sum()),
            "count": int(len(group)),
            "top_issue": top_row["title"],
            "interpretation": top_row["interpretation"],
        })

    grouped_df = pd.DataFrame(grouped_rows)
    grouped_df = grouped_df.sort_values(
        by=["total_impact_score", "count", "possible_system"],
        ascending=[False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return grouped_df
