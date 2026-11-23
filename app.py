import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from core.llm_engine import ask_ai
from core.calculations import (
    get_total,
    get_average,
    get_top_values,
    get_column_summary,
    get_monthly_sales,
)
from core.query_router import route_question
from core.insights_engine import generate_business_insights
from core.recommendation_engine import generate_recommendations
from reports.report_generator import (
    create_excel_report,
    create_pdf_report,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="InsightPilot AI | Data Workspace",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0e1117;
    }
    [data-testid="stHeader"] {
        background: rgba(14, 17, 23, 0.85);
    }
    [data-testid="stSidebar"] {
        background: #151a23;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }
    .hero {
        padding: 1.5rem 1.7rem;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        background: linear-gradient(120deg, #17243a 0%, #18202c 55%, #211c35 100%);
        margin-bottom: 1.4rem;
    }
    .hero-kicker {
        color: #9db8e8;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .hero h1 {
        margin: 0.35rem 0 0.35rem 0;
        font-size: 2.35rem;
        font-weight: 750;
        color: #f5f7fb;
    }
    .hero p {
        color: #b8c2d2;
        margin-bottom: 0;
        font-size: 1rem;
    }
    .section-intro {
        color: #9ca9bb;
        margin-top: -0.45rem;
        margin-bottom: 1.1rem;
    }
    div[data-testid="stMetric"] {
        background: #171e29;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 1rem 1.1rem;
        border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] {
        color: #aebbd0;
    }
    div[data-testid="stMetricValue"] {
        color: #f5f7fb;
    }
    div[data-testid="stDownloadButton"] button {
        width: 100%;
        border-radius: 10px;
        min-height: 2.8rem;
        font-weight: 650;
    }
    div[data-testid="stFileUploader"] {
        border: 1px dashed rgba(160,180,220,0.35);
        border-radius: 12px;
        padding: 0.4rem;
    }
    .small-muted {
        color: #8996a8;
        font-size: 0.82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DEMO DATA
# =========================================================

demo_data = pd.DataFrame(
    {
        "Date": pd.date_range("2026-01-01", periods=10, freq="D"),
        "Product": [
            "Laptop", "Mobile", "Headphones", "Laptop", "Tablet",
            "Mobile", "Headphones", "Tablet", "Laptop", "Mobile",
        ],
        "Category": [
            "Electronics", "Electronics", "Accessories",
            "Electronics", "Electronics", "Electronics",
            "Accessories", "Electronics", "Electronics",
            "Electronics",
        ],
        "Sales": [
            55000, 25000, 3000, 60000, 18000,
            27000, 3500, 20000, 52000, 29000,
        ],
        "Profit": [
            8000, 4000, 700, 9500, 2500,
            4500, 900, 3000, 7800, 4800,
        ],
    }
)


# =========================================================
# SIDEBAR — DATA WORKSPACE
# =========================================================

st.sidebar.markdown("## 📁 Data Workspace")
st.sidebar.caption("Upload a CSV or Excel file to begin analysing.")

uploaded_file = st.sidebar.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx"],
    help="Supported formats: CSV and Excel (.xlsx).",
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        dataset_name = uploaded_file.name
        data_source_label = "Uploaded dataset"
        st.sidebar.success(f"Loaded: {uploaded_file.name}")

    except Exception as error:
        st.sidebar.error(f"Unable to read the file: {error}")
        st.stop()
else:
    df = demo_data.copy()
    dataset_name = "Built-in demo dataset"
    data_source_label = "Demo dataset"
    st.sidebar.info("Showing the built-in demo dataset.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Workspace status**")
st.sidebar.write(f"Rows: `{len(df):,}`")
st.sidebar.write(f"Columns: `{len(df.columns):,}`")
st.sidebar.write(f"Source: `{data_source_label}`")
st.sidebar.markdown("---")
st.sidebar.caption("InsightPilot AI · Local LLM + Pandas analytics")


# =========================================================
# DATA VALIDATION & SHARED PREPARATION
# =========================================================

if df.empty:
    st.warning("The selected dataset contains no records.")
    st.stop()

if len(df.columns) == 0:
    st.warning("The selected dataset does not contain any columns.")
    st.stop()

# Remove completely empty column names only from display logic;
# retain the original dataframe so exports do not silently change it.
numeric_columns = df.select_dtypes(include="number").columns.tolist()
categorical_columns = df.select_dtypes(
    include=["object", "str", "category", "bool"]
).columns.tolist()

date_columns = []
for column in df.columns:
    if pd.api.types.is_datetime64_any_dtype(df[column]):
        date_columns.append(column)
    elif any(token in str(column).lower() for token in ("date", "time")):
        parsed = pd.to_datetime(df[column], errors="coerce")
        if parsed.notna().any():
            date_columns.append(column)

total_rows = len(df)
total_columns = len(df.columns)
missing_values = int(df.isnull().sum().sum())
duplicate_rows = int(df.duplicated().sum())


# =========================================================
# HEADER
# =========================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-kicker">Your AI-powered analytics workspace</div>
        <h1>📊 InsightPilot AI</h1>
        <p>Explore data, uncover business patterns, ask questions and generate reports.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

source_col, date_col = st.columns([3, 1])
with source_col:
    st.caption(f"📂 Current dataset: **{dataset_name}**")
with date_col:
    st.caption(f"🕒 {datetime.now().strftime('%d %b %Y')}")


# =========================================================
# NAVIGATION
# =========================================================

overview_tab, explore_tab, ai_tab, reports_tab = st.tabs(
    [
        "🏠 Overview",
        "🔎 Explore Data",
        "🤖 AI Analyst",
        "📑 Insights & Reports",
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

with overview_tab:
    st.subheader("Dataset Overview")
    st.markdown(
        '<p class="section-intro">A quick health check of the active dataset.</p>',
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Total Records", f"{total_rows:,}")
    metric_cols[1].metric("Total Columns", f"{total_columns:,}")
    metric_cols[2].metric("Missing Values", f"{missing_values:,}")
    metric_cols[3].metric("Duplicate Rows", f"{duplicate_rows:,}")

    st.markdown("---")
    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Dataset Preview")
        st.dataframe(
            df.head(12),
            width="stretch",
            hide_index=True,
        )

    with right:
        st.subheader("Data Quality")
        quality_data = pd.DataFrame(
            {
                "Check": [
                    "Complete cells",
                    "Missing cells",
                    "Duplicate rows",
                    "Unique rows",
                ],
                "Value": [
                    f"{(df.size - missing_values):,}",
                    f"{missing_values:,}",
                    f"{duplicate_rows:,}",
                    f"{df.drop_duplicates().shape[0]:,}",
                ],
            }
        )
        st.dataframe(
            quality_data,
            width="stretch",
            hide_index=True,
        )

        if missing_values == 0 and duplicate_rows == 0:
            st.success("No missing values or duplicate rows detected.")
        else:
            st.warning("Review missing values and duplicate rows before analysis.")

    st.markdown("---")
    st.subheader("Column Profile")
    profile = pd.DataFrame(
        {
            "Column": df.columns.astype(str),
            "Data Type": df.dtypes.astype(str).values,
            "Missing Values": df.isnull().sum().values,
            "Unique Values": df.nunique(dropna=True).values,
        }
    )
    st.dataframe(profile, width="stretch", hide_index=True)


# =========================================================
# EXPLORE DATA
# =========================================================

with explore_tab:
    st.subheader("Visual Analytics")
    st.markdown(
        '<p class="section-intro">Build a quick chart by selecting a dimension and a measure.</p>',
        unsafe_allow_html=True,
    )

    if categorical_columns and numeric_columns:
        chart_col1, chart_col2, chart_col3 = st.columns([1.2, 1.2, 1])

        with chart_col1:
            x_column = st.selectbox(
                "Category / X-axis",
                categorical_columns,
                key="overview_x_column",
            )

        with chart_col2:
            y_column = st.selectbox(
                "Numeric / Y-axis",
                numeric_columns,
                key="overview_y_column",
            )

        with chart_col3:
            aggregation = st.selectbox(
                "Aggregation",
                ["Sum", "Average", "Count"],
                key="overview_aggregation",
            )

        if aggregation == "Sum":
            chart_data = (
                df.groupby(x_column, dropna=False)[y_column]
                .sum()
                .reset_index()
            )
        elif aggregation == "Average":
            chart_data = (
                df.groupby(x_column, dropna=False)[y_column]
                .mean()
                .reset_index()
            )
        else:
            chart_data = (
                df.groupby(x_column, dropna=False)[y_column]
                .count()
                .reset_index()
            )

        chart_data[x_column] = chart_data[x_column].fillna("(Missing)")
        chart_data = chart_data.sort_values(
            y_column,
            ascending=False,
        ).head(30)

        fig = px.bar(
            chart_data,
            x=x_column,
            y=y_column,
            title=f"{aggregation} of {y_column} by {x_column}",
            text_auto=".2s",
            template="plotly_dark",
        )
        fig.update_layout(
            height=430,
            margin=dict(l=15, r=15, t=55, b=15),
            xaxis_title=x_column,
            yaxis_title=y_column,
        )
        st.plotly_chart(fig, width="stretch")

    else:
        st.info(
            "A chart needs at least one categorical column and one numeric column."
        )

    st.markdown("---")
    st.subheader("Advanced Data Analytics")

    if numeric_columns:
        analysis_type = st.selectbox(
            "Choose analysis",
            [
                "Total",
                "Average",
                "Top Performers",
                "Monthly Trend",
                "Column Summary",
                "Statistical Summary",
            ],
            key="advanced_analysis_type",
        )

        if analysis_type in ["Total", "Average"]:
            selected_metric = st.selectbox(
                "Select numeric column",
                numeric_columns,
                key="advanced_metric_column",
            )

            if analysis_type == "Total":
                result_value = get_total(df, selected_metric)
                st.metric(f"Total {selected_metric}", f"{result_value:,.2f}")
            else:
                result_value = get_average(df, selected_metric)
                st.metric(f"Average {selected_metric}", f"{result_value:,.2f}")

        elif analysis_type == "Top Performers":
            group_columns = [
                col for col in df.columns if col not in numeric_columns
            ]

            if group_columns:
                group_col, metric_col = st.columns(2)

                with group_col:
                    selected_group = st.selectbox(
                        "Group by",
                        group_columns,
                        key="advanced_group_column",
                    )

                with metric_col:
                    selected_metric = st.selectbox(
                        "Performance metric",
                        numeric_columns,
                        key="advanced_ranking_metric",
                    )

                top_n = st.slider(
                    "Number of top performers",
                    min_value=1,
                    max_value=10,
                    value=5,
                )

                result_table = get_top_values(
                    df,
                    selected_group,
                    selected_metric,
                    top_n,
                )

                st.dataframe(
                    result_table,
                    width="stretch",
                    hide_index=True,
                )

                fig = px.bar(
                    result_table,
                    x=selected_group,
                    y=selected_metric,
                    title=f"Top {top_n} by {selected_metric}",
                    text_auto=".2s",
                    template="plotly_dark",
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No suitable grouping columns were found.")

        elif analysis_type == "Monthly Trend":
            if date_columns:
                date_col, metric_col = st.columns(2)

                with date_col:
                    selected_date = st.selectbox(
                        "Select date column",
                        date_columns,
                        key="monthly_date_column",
                    )

                with metric_col:
                    selected_metric = st.selectbox(
                        "Select numeric metric",
                        numeric_columns,
                        key="monthly_metric_column",
                    )

                try:
                    result_table = get_monthly_sales(
                        df,
                        selected_date,
                        selected_metric,
                    )
                    st.dataframe(
                        result_table,
                        width="stretch",
                        hide_index=True,
                    )

                    if not result_table.empty and "Month" in result_table.columns:
                        fig = px.line(
                            result_table,
                            x="Month",
                            y=selected_metric,
                            markers=True,
                            title=f"Monthly {selected_metric}",
                            template="plotly_dark",
                        )
                        st.plotly_chart(fig, width="stretch")
                except Exception as error:
                    st.error(f"Unable to calculate the monthly trend: {error}")
            else:
                st.info("No valid date column was detected.")

        elif analysis_type == "Column Summary":
            st.dataframe(
                get_column_summary(df),
                width="stretch",
            )

        elif analysis_type == "Statistical Summary":
            st.dataframe(
                df[numeric_columns].describe().round(2),
                width="stretch",
            )
    else:
        st.warning("No numeric columns are available for analysis.")


# =========================================================
# AI ANALYST
# =========================================================

with ai_tab:
    st.subheader("Ask InsightPilot AI")
    st.markdown(
        '<p class="section-intro">Ask questions about the active dataset using Pandas analytics and your local Ollama model.</p>',
        unsafe_allow_html=True,
    )

    dataset_context = f"""
Dataset name: {dataset_name}
Total rows: {len(df)}
Total columns: {len(df.columns)}

Column names and data types:
{df.dtypes.to_string()}

Missing values:
{df.isnull().sum().to_string()}

Numeric statistical summary:
{df.describe().to_string() if numeric_columns else "No numeric columns"}

First five records:
{df.head(5).to_string(index=False)}
"""

    with st.form("ai_question_form", clear_on_submit=False):
        user_question = st.text_input(
            "Your question",
            placeholder="Example: Which product generated the highest sales?",
        )
        ask_button = st.form_submit_button(
            "✨ Ask InsightPilot AI",
            width="stretch",
        )

    if ask_button:
        if not user_question.strip():
            st.warning("Please enter a question.")
        else:
            result = None

            with st.spinner("Analysing your question..."):
                try:
                    result = route_question(df, user_question)
                except Exception:
                    result = None

                if result is not None:
                    answer = result.get("answer", "Analysis completed.")
                    analysis_source = "Pandas Analytics Engine"
                else:
                    try:
                        answer = ask_ai(user_question, dataset_context)
                        analysis_source = "Qwen Local AI"
                    except Exception as error:
                        answer = None
                        analysis_source = "Unavailable"
                        st.warning(
                            "Qwen could not be reached from this app host. "
                            "Pandas-powered analytical questions, charts, insights, "
                            "and report exports remain available. The local Ollama "
                            "service on your personal computer is not automatically "
                            "accessible to a cloud deployment. To enable Qwen online, "
                            "configure a securely hosted Ollama endpoint."
                        )

            if answer is not None:
                st.markdown("### 💡 AI Analysis")
                st.caption(f"Analysis powered by: {analysis_source}")
                st.markdown(answer)

                if result is not None and result.get("table") is not None:
                    st.subheader("Calculation Results")
                    st.dataframe(
                        result["table"],
                        width="stretch",
                        hide_index=True,
                    )

                if result is not None and result.get("chart_type"):
                    chart_type = result["chart_type"]
                    result_table = result.get("table")

                    if result_table is not None and not result_table.empty:
                        if chart_type == "bar":
                            fig = px.bar(
                                result_table,
                                x=result["x"],
                                y=result["y"],
                                title="Performance Ranking",
                                text_auto=".2s",
                                template="plotly_dark",
                            )
                        else:
                            fig = px.line(
                                result_table,
                                x=result["x"],
                                y=result["y"],
                                markers=True,
                                title="Monthly Performance Trend",
                                template="plotly_dark",
                            )

                        st.plotly_chart(fig, width="stretch")


# =========================================================
# INSIGHTS & REPORTS
# =========================================================

with reports_tab:
    st.subheader("Automatic Business Insights")
    st.markdown(
        '<p class="section-intro">Automatically generated findings from the current dataset.</p>',
        unsafe_allow_html=True,
    )

    try:
        with st.spinner("Discovering business insights..."):
            business_report = generate_business_insights(df)

        for insight in business_report.get("insights", []):
            st.success(f"📌 {insight}")

        anomalies = business_report.get("anomalies")

        if anomalies is not None and not anomalies.empty:
            with st.expander("🔎 Review Potential Outliers"):
                st.caption(
                    "IQR-based outliers are potential anomalies, not necessarily data errors."
                )
                st.dataframe(
                    anomalies,
                    width="stretch",
                    hide_index=True,
                )

    except Exception as error:
        st.error(f"Unable to generate business insights: {error}")
        business_report = {"insights": [], "anomalies": pd.DataFrame()}

    st.markdown("---")
    st.subheader("AI Business Recommendations")

    try:
        recommendations = generate_recommendations(df)

        if recommendations:
            for item in recommendations:
                with st.container(border=True):
                    st.markdown(f"#### {item.get('title', 'Recommendation')}")
                    st.caption(
                        f"Priority: {item.get('priority', 'Not specified')}"
                    )
                    st.write("**Finding:**", item.get("finding", ""))
                    st.write(
                        "**Recommended action:**",
                        item.get("action", ""),
                    )
        else:
            st.info("No recommendations were generated for this dataset.")

    except Exception as error:
        st.error(f"Unable to generate recommendations: {error}")
        recommendations = []

    st.markdown("---")
    st.subheader("Download Business Reports")
    st.caption(
        "Export the active dataset together with its KPIs, insights and recommendations."
    )

    export_col1, export_col2 = st.columns(2)

    try:
        excel_report = create_excel_report(
            df,
            business_report.get("insights", []),
            recommendations,
            dataset_name=dataset_name,
        )

        with export_col1:
            st.download_button(
                label="📊 Download Excel Report",
                data=excel_report,
                file_name="InsightPilot_Business_Report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )

        pdf_report = create_pdf_report(
            df,
            business_report.get("insights", []),
            recommendations,
            dataset_name=dataset_name,
        )

        with export_col2:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_report,
                file_name="InsightPilot_Business_Report.pdf",
                mime="application/pdf",
                width="stretch",
            )

    except Exception as error:
        st.error(f"Unable to prepare business reports: {error}")

    st.markdown("---")
    st.subheader("Download Current Dataset")

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Current Dataset (CSV)",
        data=csv_data,
        file_name="insightpilot_processed_data.csv",
        mime="text/csv",
        width="stretch",
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")
footer_left, footer_right = st.columns(2)

with footer_left:
    st.caption("InsightPilot AI · Built with Python, Pandas, Plotly and Streamlit")

with footer_right:
    st.caption("Local AI inference · Ollama + Qwen")
