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


def generate_recommendations(df):
    recommendations = []

    sales_col = find_column(df, ["sales", "revenue", "total_sales", "sales_amount"])
    profit_col = find_column(df, ["profit", "net_profit", "total_profit"])
    product_col = find_column(df, ["product", "product_name", "product_id", "productid", "item", "item_name"])
    category_col = find_column(df, ["category", "product_category"])

    if sales_col and product_col:
        data = df[[product_col, sales_col]].copy()
        data[sales_col] = pd.to_numeric(data[sales_col], errors="coerce")
        ranking = (
            data.dropna(subset=[product_col, sales_col])
            .groupby(product_col)[sales_col].sum()
            .sort_values(ascending=False)
        )
        if len(ranking) >= 2:
            recommendations.append({
                "priority": "High",
                "title": "Review low-performing products",
                "finding": f"{ranking.index[-1]} has the lowest recorded sales ({ranking.iloc[-1]:,.2f}).",
                "action": "Investigate its pricing, demand, availability and customer feedback before deciding on promotions or inventory changes.",
            })
            recommendations.append({
                "priority": "Medium",
                "title": "Study the best-selling product",
                "finding": f"{ranking.index[0]} leads sales with {ranking.iloc[0]:,.2f}.",
                "action": "Examine what drives its performance and test whether similar strategies work for other products.",
            })

    if sales_col and category_col:
        data = df[[category_col, sales_col]].copy()
        data[sales_col] = pd.to_numeric(data[sales_col], errors="coerce")
        ranking = (
            data.dropna(subset=[category_col, sales_col])
            .groupby(category_col)[sales_col].sum()
            .sort_values(ascending=False)
        )
        if len(ranking) >= 2:
            recommendations.append({
                "priority": "Medium",
                "title": "Evaluate category opportunities",
                "finding": f"{ranking.index[0]} leads category sales with {ranking.iloc[0]:,.2f}.",
                "action": "Review the products and customer segments driving this category, and evaluate whether its successful practices can be replicated.",
            })

    if sales_col and profit_col:
        paired = pd.DataFrame({
            "sales": pd.to_numeric(df[sales_col], errors="coerce"),
            "profit": pd.to_numeric(df[profit_col], errors="coerce"),
        }).dropna()
        total_sales = paired["sales"].sum()
        if total_sales > 0:
            margin = paired["profit"].sum() / total_sales * 100
            if margin < 10:
                priority, title, action = (
                    "High",
                    "Investigate profitability",
                    "Review operating costs, discounts, pricing and product-level profitability.",
                )
            elif margin < 20:
                priority, title, action = (
                    "Medium",
                    "Review profit improvement opportunities",
                    "Identify products with stronger margins and investigate opportunities to reduce avoidable costs.",
                )
            else:
                priority, title, action = (
                    "Low",
                    "Monitor profitability",
                    "Track margin by product and category to identify changes in profitability.",
                )
            recommendations.append({
                "priority": priority,
                "title": title,
                "finding": f"Overall profit margin is {margin:.2f}%.",
                "action": action,
            })

    if not recommendations:
        recommendations.append({
            "priority": "Low",
            "title": "Improve dataset coverage",
            "finding": "Insufficient recognized business data was available.",
            "action": "Provide suitable sales, product or category columns to generate more specific recommendations.",
        })

    return recommendations
