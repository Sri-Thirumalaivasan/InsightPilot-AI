import re
import pandas as pd

from core.calculations import (
    get_total,
    get_average,
    get_top_values,
    get_monthly_sales,
)


def find_column(df, candidates):
    normalized = {
        str(col).strip().lower().replace(" ", "_"): col
        for col in df.columns
    }
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def route_question(df, question):
    """Route supported natural-language questions to deterministic Pandas calculations."""
    q = question.lower().strip()

    sales_col = find_column(df, ["sales", "revenue", "total_sales", "sales_amount"])
    profit_col = find_column(df, ["profit", "net_profit", "total_profit"])
    product_col = find_column(df, ["product", "product_name", "product_id", "productid", "item", "item_name"])
    category_col = find_column(df, ["category", "product_category"])
    date_col = find_column(df, ["date", "order_date", "sales_date", "datetime"])

    if any(word in q for word in ["profit", "profitable"]):
        metric_col, metric_name = profit_col, "profit"
    else:
        metric_col, metric_name = sales_col, "sales"

    if metric_col is None:
        return None

    if any(word in q for word in ["month", "monthly"]):
        if date_col is None:
            return None
        monthly = get_monthly_sales(df, date_col, metric_col)
        if monthly.empty:
            return {"answer": "No valid monthly data was found.", "table": monthly,
                    "chart_type": None, "x": None, "y": None}
        if any(word in q for word in ["highest", "best", "top"]):
            best = monthly.loc[monthly[metric_col].idxmax()]
            answer = f"{best['Month']} had the highest {metric_name}, with {best[metric_col]:,.2f}."
        else:
            answer = f"Monthly {metric_name} was calculated for {len(monthly)} month(s)."
        return {"answer": answer, "table": monthly, "chart_type": "line",
                "x": "Month", "y": metric_col}

    if any(word in q for word in ["average", "avg", "mean"]):
        value = get_average(df, metric_col)
        return {"answer": f"Average {metric_name} is {value:,.2f}.",
                "table": None, "chart_type": None, "x": None, "y": None}

    if any(word in q for word in ["total", "sum"]):
        value = get_total(df, metric_col)
        return {"answer": f"Total {metric_name} is {value:,.2f}.",
                "table": None, "chart_type": None, "x": None, "y": None}

    if any(word in q for word in ["highest", "top", "best", "most"]):
        if "categor" in q:
            group_col, group_name = category_col, "category"
        else:
            group_col, group_name = product_col, "product"
        if group_col is None:
            return None
        match = re.search(r"\btop\s+(\d+)\b", q)
        top_n = max(1, min(int(match.group(1)), 20)) if match else 5
        table = get_top_values(df, group_col, metric_col, top_n)
        if table.empty:
            return {"answer": "No valid records were found.", "table": table,
                    "chart_type": None, "x": None, "y": None}
        best = table.iloc[0]
        answer = (
            f"The top-performing {group_name} is {best[group_col]}, "
            f"with {metric_name} of {best[metric_col]:,.2f}."
        )
        return {"answer": answer, "table": table, "chart_type": "bar",
                "x": group_col, "y": metric_col}

    if any(word in q for word in ["sales", "revenue", "profit"]):
        value = get_total(df, metric_col)
        return {"answer": f"Total {metric_name} is {value:,.2f}.",
                "table": None, "chart_type": None, "x": None, "y": None}

    return None
