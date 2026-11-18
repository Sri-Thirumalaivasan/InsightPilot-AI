
import pandas as pd

from core.calculations import (
    get_total,
    get_average,
    get_top_values,
    get_monthly_sales
)

# Sample dataset
df = pd.DataFrame({
    "Date": [
        "2026-01-01",
        "2026-01-02",
        "2026-02-01",
        "2026-02-02"
    ],
    "Product": [
        "Laptop", "Mobile", "Laptop", "Tablet"
    ],
    "Sales": [50000, 25000, 60000, 20000],
    "Profit": [8000, 4000, 10000, 3000]
})

print("\nTOTAL SALES:")
print(get_total(df, "Sales"))

print("\nAVERAGE PROFIT:")
print(get_average(df, "Profit"))

print("\nTOP PRODUCTS:")
print(get_top_values(df, "Product", "Sales"))

print("\nMONTHLY SALES:")
print(get_monthly_sales(df, "Date", "Sales"))
