import pandas as pd


def find_column(df, candidates):
    columns = {
        str(col).strip().lower().replace(" ", "_"): col
        for col in df.columns
    }
    for candidate in candidates:
        if candidate in columns:
            return columns[candidate]
    return None


def generate_business_insights(df):
    insights = []
    anomalies = pd.DataFrame()

    sales_col = find_column(df, ["sales", "revenue", "total_sales", "sales_amount"])
    profit_col = find_column(df, ["profit", "net_profit", "total_profit"])
    product_col = find_column(df, ["product", "product_name", "product_id", "productid", "item", "item_name"])
    category_col = find_column(df, ["category", "product_category"])

    if sales_col:
        sales = pd.to_numeric(df[sales_col], errors="coerce").dropna()
        if not sales.empty:
            insights.append(
                f"Total sales across {len(sales):,} valid records are {sales.sum():,.2f}."
            )

    if profit_col:
        profit = pd.to_numeric(df[profit_col], errors="coerce").dropna()
        if not profit.empty:
            insights.append(f"Total recorded profit is {profit.sum():,.2f}.")

    if sales_col and profit_col:
        paired = pd.DataFrame({
            "sales": pd.to_numeric(df[sales_col], errors="coerce"),
            "profit": pd.to_numeric(df[profit_col], errors="coerce"),
        }).dropna()
        total_sales = paired["sales"].sum()
        if total_sales != 0:
            margin = paired["profit"].sum() / total_sales * 100
            insights.append(
                f"Overall profit margin on records with both values available is {margin:.2f}%."
            )

    if product_col and sales_col:
        data = df[[product_col, sales_col]].copy()
        data[sales_col] = pd.to_numeric(data[sales_col], errors="coerce")
        ranking = (
            data.dropna(subset=[product_col, sales_col])
            .groupby(product_col)[sales_col].sum()
            .sort_values(ascending=False)
        )
        if not ranking.empty:
            insights.append(
                f"Highest-selling product: {ranking.index[0]}, with sales of {ranking.iloc[0]:,.2f}."
            )
            if len(ranking) > 1:
                insights.append(
                    f"Lowest-selling product: {ranking.index[-1]}, with sales of {ranking.iloc[-1]:,.2f}."
                )

    if category_col and sales_col:
        data = df[[category_col, sales_col]].copy()
        data[sales_col] = pd.to_numeric(data[sales_col], errors="coerce")
        ranking = (
            data.dropna(subset=[category_col, sales_col])
            .groupby(category_col)[sales_col].sum()
            .sort_values(ascending=False)
        )
        if not ranking.empty:
            insights.append(
                f"Best-performing category: {ranking.index[0]}, with sales of {ranking.iloc[0]:,.2f}."
            )

    if sales_col:
        values = pd.to_numeric(df[sales_col], errors="coerce")
        valid = values.dropna()
        if len(valid) >= 4:
            q1, q3 = valid.quantile([0.25, 0.75])
            iqr = q3 - q1
            mask = (values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)
            anomalies = df.loc[mask].copy()
            if anomalies.empty:
                insights.append("No potential sales outliers were detected using the IQR method.")
            else:
                insights.append(
                    f"Detected {len(anomalies)} potential sales outlier(s) using the IQR method. "
                    "These records may need further review."
                )

    if not insights:
        insights.append("Not enough recognizable business columns were found to generate insights.")

    return {"insights": insights, "anomalies": anomalies}
