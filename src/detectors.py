import pandas as pd
from src.similarity import find_similar_groups


def run_all_detectors(df):
    results = []

    # Volume spike detection
    daily = df.groupby("opened_date").size().reset_index(name="count")
    avg = daily["count"].mean() if not daily.empty else 0

    spikes = daily[daily["count"] > avg * 2] if avg > 0 else pd.DataFrame()

    for _, row in spikes.iterrows():
        results.append({
            "anomaly_type": "volume_spike",
            "title": f"Spike on {row['opened_date']}",
            "description": f"{row['count']} tickets vs average {round(avg, 1)}",
            "count": int(row["count"]),
            "severity": "high",
            "impact_score": 90,
            "confidence": "high",
        })

    # Category concentration detection
    cat_counts = df["category"].value_counts()

    for cat, count in cat_counts.items():
        if count > len(df) * 0.3:
            results.append({
                "anomaly_type": "category",
                "title": f"High volume in category: {cat}",
                "description": f"{count} tickets were opened in this category",
                "count": int(count),
                "severity": "medium",
                "impact_score": 65,
                "confidence": "medium",
            })

    # Repeated similar issue detection
    groups = find_similar_groups(df)

    for group in groups:
        sample_text = df.iloc[group[0]]["short_description"]
        count = len(group)

        results.append({
            "anomaly_type": "repeated_similar_issue",
            "title": "Repeated similar issue detected",
            "description": f"{count} similar tickets: '{sample_text}'",
            "count": count,
            "severity": "high",
            "impact_score": min(100, 50 + count * 5),
            "confidence": "high",
        })

    if not results:
        return pd.DataFrame(columns=[
            "anomaly_type",
            "title",
            "description",
            "count",
            "severity",
            "impact_score",
            "confidence",
        ])

    return pd.DataFrame(results)