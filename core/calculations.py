import pandas as pd


def get_total(df, column):
    values = pd.to_numeric(df[column], errors="coerce")
    return values.sum()


def get_average(df, column):
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    return float(values.mean()) if not values.empty else 0.0


def get_top_values(df, group_column, metric_column, top_n=5):
    data = df[[group_column, metric_column]].copy()
    data[metric_column] = pd.to_numeric(data[metric_column], errors="coerce")
    data = data.dropna(subset=[group_column, metric_column])
    return (
        data.groupby(group_column)[metric_column]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )


def get_column_summary(df):
    return pd.DataFrame({
        "Column": df.columns.astype(str),
        "Data Type": df.dtypes.astype(str).values,
        "Unique Values": df.nunique(dropna=True).values,
        "Missing Values": df.isnull().sum().values,
    })


def get_monthly_sales(df, date_column, metric_column):
    data = df[[date_column, metric_column]].copy()
    data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
    data[metric_column] = pd.to_numeric(data[metric_column], errors="coerce")
    data = data.dropna(subset=[date_column, metric_column])
    data["Month"] = data[date_column].dt.to_period("M").astype(str)
    return data.groupby("Month")[metric_column].sum().reset_index()
