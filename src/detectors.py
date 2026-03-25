import pandas as pd


def run_all_detectors(df):
    results = []

    # 🔹 Volume spike
    daily = df.groupby("opened_date").size().reset_index(name="count")
    avg = daily["count"].mean()

    spikes = daily[daily["count"] > avg * 2]

    for _, row in spikes.iterrows():
        results.append({
            "anomaly_type": "volume_spike",
            "title": f"Spike on {row['opened_date']}",
            "description": f"{row['count']} tickets vs avg {round(avg,1)}",
            "count": int(row["count"]),
            "severity": "high"
        })

    # 🔹 Repeated categories
    cat_counts = df["category"].value_counts()

    for cat, count in cat_counts.items():
        if count > len(df) * 0.3:
            results.append({
                "anomaly_type": "category",
                "title": f"High volume in {cat}",
                "description": f"{count} tickets in this category",
                "count": int(count),
                "severity": "medium"
            })

    return pd.DataFrame(results)