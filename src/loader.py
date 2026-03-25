import pandas as pd


def load_table(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def normalize_column_names(df):
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    return df


def validate_columns(df):
    required = [
        "ticket_id",
        "opened_at",
        "category",
        "subcategory",
        "priority",
        "assignment_group",
        "short_description",
        "status",
    ]

    missing = [col for col in required if col not in df.columns]
    return len(missing) == 0, missing