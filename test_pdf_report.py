
import pandas as pd

from reports.report_generator import create_pdf_report

df = pd.DataFrame({
    "Date": ["2026-01-01", "2026-01-02", "2026-02-01"],
    "Product": ["Laptop", "Mobile", "Tablet"],
    "Category": ["Electronics", "Electronics", "Electronics"],
    "Sales": [50000, 25000, 20000],
    "Profit": [8000, 4000, 3000]
})

insights = [
    "Laptop generated the highest sales.",
    "Electronics is the leading category."
]

recommendations = [
    {
        "priority": "High",
        "title": "Review low-performing products",
        "finding": "Tablet has the lowest sales.",
        "action": "Investigate customer demand and pricing."
    }
]

print("Generating PDF report...")

report = create_pdf_report(
    df,
    insights,
    recommendations
)

with open("InsightPilot_Business_Report.pdf", "wb") as file:
    file.write(report.getvalue())

print("PDF report created successfully!")
