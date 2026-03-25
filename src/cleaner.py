import pandas as pd


def clean_tickets(df):
    df = df.copy()

    df["opened_at"] = pd.to_datetime(df["opened_at"], errors="coerce")
    df = df.dropna(subset=["opened_at"])

    df["category"] = df["category"].fillna("unknown").str.lower()
    df["assignment_group"] = df["assignment_group"].fillna("unknown").str.lower()
    df["short_description"] = df["short_description"].fillna("")

    df["opened_date"] = df["opened_at"].dt.date

    return df