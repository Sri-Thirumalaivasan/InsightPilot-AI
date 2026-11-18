import io
from datetime import datetime
from xml.sax.saxutils import escape

import pandas as pd
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)


def find_column(df, candidates):
    columns = {
        str(col).strip().lower().replace(" ", "_"): col
        for col in df.columns
    }
    for candidate in candidates:
        normalized = candidate.strip().lower().replace(" ", "_")
        if normalized in columns:
            return columns[normalized]
    return None


def get_report_columns(df):
    return {
        "sales": find_column(df, ["sales", "revenue", "total_sales", "sales_amount"]),
        "profit": find_column(df, ["profit", "net_profit", "total_profit"]),
        "product": find_column(df, [
            "product", "product_name", "item", "item_name", "product_id", "productid"
        ]),
        "category": find_column(df, ["category", "product_category"]),
    }


def calculate_kpis(df, columns):
    kpis = [
        ["Metric", "Value"],
        ["Total Records", len(df)],
        ["Total Columns", len(df.columns)],
        ["Missing Values", int(df.isnull().sum().sum())],
        ["Duplicate Rows", int(df.duplicated().sum())],
    ]

    sales_col, profit_col = columns["sales"], columns["profit"]

    if sales_col:
        sales = pd.to_numeric(df[sales_col], errors="coerce").dropna()
        if not sales.empty:
            kpis.extend([
                ["Total Sales", float(sales.sum())],
                ["Average Sales", float(sales.mean())],
            ])

    if profit_col:
        profit = pd.to_numeric(df[profit_col], errors="coerce").dropna()
        if not profit.empty:
            kpis.extend([
                ["Total Profit", float(profit.sum())],
                ["Average Profit", float(profit.mean())],
            ])

    if sales_col and profit_col:
        paired = pd.DataFrame({
            "sales": pd.to_numeric(df[sales_col], errors="coerce"),
            "profit": pd.to_numeric(df[profit_col], errors="coerce"),
        }).dropna()
        total_sales = paired["sales"].sum()
        if total_sales != 0:
            kpis.append(["Profit Margin (%)", float(paired["profit"].sum() / total_sales * 100)])

    return kpis


def create_ranking(df, group_column, metric_column):
    if not group_column or not metric_column:
        return pd.DataFrame()
    data = df[[group_column, metric_column]].copy()
    data[metric_column] = pd.to_numeric(data[metric_column], errors="coerce")
    data = data.dropna(subset=[group_column, metric_column])
    if data.empty:
        return pd.DataFrame()
    ranking = (
        data.groupby(group_column, as_index=False)[metric_column]
        .sum()
        .sort_values(metric_column, ascending=False)
        .reset_index(drop=True)
    )
    ranking.insert(0, "Rank", range(1, len(ranking) + 1))
    return ranking


def create_excel_report(df, insights, recommendations, dataset_name="Uploaded dataset"):
    output = io.BytesIO()
    columns = get_report_columns(df)

    kpis = calculate_kpis(df, columns)
    kpi_df = pd.DataFrame(kpis[1:], columns=kpis[0])

    product_ranking = create_ranking(df, columns["product"], columns["sales"])
    if not product_ranking.empty:
        label = "Product ID" if str(columns["product"]).lower().replace(" ", "_") in ("product_id", "productid") else "Product"
        product_ranking = product_ranking.rename(columns={
            columns["product"]: label,
            columns["sales"]: "Total Sales",
        })

    category_ranking = create_ranking(df, columns["category"], columns["sales"])
    if not category_ranking.empty:
        category_ranking = category_ranking.rename(columns={
            columns["category"]: "Category",
            columns["sales"]: "Total Sales",
        })

    insights_df = pd.DataFrame({"Business Insights": [str(x) for x in insights]})
    recommendations_df = pd.DataFrame([
        {
            "Priority": item.get("priority", "Not specified"),
            "Recommendation": item.get("title", ""),
            "Finding": item.get("finding", ""),
            "Suggested Action": item.get("action", ""),
        }
        for item in recommendations
    ])
    metadata_df = pd.DataFrame([
        ["Report Name", "InsightPilot AI Business Analytics Report"],
        ["Dataset Name", dataset_name],
        ["Generated On", datetime.now().strftime("%d-%m-%Y %H:%M:%S")],
        ["Total Records", len(df)],
        ["Total Columns", len(df.columns)],
    ], columns=["Information", "Value"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        metadata_df.to_excel(writer, sheet_name="Report Info", index=False)
        kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)
        df.to_excel(writer, sheet_name="Dataset", index=False)
        if not product_ranking.empty:
            product_ranking.to_excel(writer, sheet_name="Product Ranking", index=False)
        if not category_ranking.empty:
            category_ranking.to_excel(writer, sheet_name="Category Ranking", index=False)
        insights_df.to_excel(writer, sheet_name="Business Insights", index=False)
        recommendations_df.to_excel(writer, sheet_name="Recommendations", index=False)

        for ws in writer.sheets.values():
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="17365D")
            for cells in ws.columns:
                width = max(len(str(c.value or "")) for c in cells)
                ws.column_dimensions[cells[0].column_letter].width = min(max(width + 3, 12), 45)

    output.seek(0)
    return output


def create_pdf_report(df, insights, recommendations, dataset_name="Uploaded dataset"):
    output = io.BytesIO()
    columns = get_report_columns(df)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "IPTitle", parent=styles["Title"], fontSize=22, leading=27,
        alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        "IPSubtitle", parent=styles["Normal"], alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"), spaceAfter=12
    )
    heading_style = ParagraphStyle(
        "IPHeading", parent=styles["Heading2"], fontSize=13,
        leading=17, textColor=colors.HexColor("#17365D"),
        spaceBefore=12, spaceAfter=8
    )
    body_style = ParagraphStyle(
        "IPBody", parent=styles["BodyText"], fontSize=9, leading=13, spaceAfter=5
    )
    small_style = ParagraphStyle(
        "IPSmall", parent=styles["BodyText"], fontSize=8, leading=11
    )

    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm
    )
    story = []
    section_number = 0

    def add_section(title):
        nonlocal section_number
        section_number += 1
        story.append(Paragraph(f"{section_number}. {escape(title)}", heading_style))

    def add_table(rows, widths):
        table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F2F5F9")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([table, Spacer(1, 8)])

    story.extend([
        Paragraph("InsightPilot AI", title_style),
        Paragraph("Business Analytics Report", subtitle_style),
        Paragraph(f"Dataset: {escape(str(dataset_name))}", body_style),
        Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", body_style),
        Spacer(1, 12),
    ])

    add_section("Dataset Overview")
    add_table([
        ["Metric", "Value"],
        ["Total Records", str(len(df))],
        ["Total Columns", str(len(df.columns))],
        ["Missing Values", str(int(df.isnull().sum().sum()))],
        ["Duplicate Rows", str(int(df.duplicated().sum()))],
    ], [75 * mm, 75 * mm])

    add_section("Key Performance Indicators")
    kpi_rows = [["KPI", "Value"]]
    for name, value in calculate_kpis(df, columns)[1:]:
        formatted = f"{value:.2f}%" if "Margin" in name else (f"{value:,.2f}" if isinstance(value, (int, float)) else str(value))
        kpi_rows.append([escape(str(name)), escape(formatted)])
    add_table(kpi_rows, [75 * mm, 75 * mm])

    product_ranking = create_ranking(df, columns["product"], columns["sales"])
    if not product_ranking.empty:
        add_section("Product Performance")
        product_label = "Product ID" if str(columns["product"]).lower().replace(" ", "_") in ("product_id", "productid") else "Product"
        rows = [["Rank", product_label, "Total Sales"]]
        for _, row in product_ranking.head(10).iterrows():
            rows.append([
                str(int(row["Rank"])),
                escape(str(row[columns["product"]])),
                f"{row[columns['sales']]:,.2f}",
            ])
        add_table(rows, [20 * mm, 65 * mm, 65 * mm])

    category_ranking = create_ranking(df, columns["category"], columns["sales"])
    if not category_ranking.empty:
        add_section("Category Performance")
        rows = [["Rank", "Category", "Total Sales"]]
        for _, row in category_ranking.iterrows():
            rows.append([
                str(int(row["Rank"])),
                escape(str(row[columns["category"]])),
                f"{row[columns['sales']]:,.2f}",
            ])
        add_table(rows, [20 * mm, 65 * mm, 65 * mm])

    add_section("Business Insights")
    if insights:
        for insight in insights:
            story.append(Paragraph(f"• {escape(str(insight))}", body_style))
    else:
        story.append(Paragraph("No business insights were supplied.", body_style))
    story.append(Spacer(1, 8))

    add_section("Business Recommendations")
    if recommendations:
        for item in recommendations:
            block = [
                Paragraph(
                    f"<b>{escape(str(item.get('title', 'Recommendation')))}</b> "
                    f"(Priority: {escape(str(item.get('priority', 'Not specified')))})",
                    body_style,
                ),
                Paragraph(f"<b>Finding:</b> {escape(str(item.get('finding', '')))}", body_style),
                Paragraph(f"<b>Recommended action:</b> {escape(str(item.get('action', '')))}", body_style),
                Spacer(1, 8),
            ]
            story.append(KeepTogether(block))
    else:
        story.append(Paragraph("No recommendations were generated.", body_style))

    story.extend([
        Spacer(1, 12),
        Paragraph(
            "Generated by InsightPilot AI. Statistical outliers are potential anomalies "
            "and should be reviewed before business decisions.",
            small_style,
        ),
    ])

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    output.seek(0)
    return output
