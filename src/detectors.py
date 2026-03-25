import pandas as pd


def run_all_detectors(df):
    results = []

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