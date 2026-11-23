# InsightPilot AI

> **A local LLM-assisted data analytics workspace for exploring datasets, answering business questions, and generating reports.**

Built with **Python · Pandas · Streamlit · Plotly · Ollama · Qwen 2.5 1.5B**

InsightPilot AI lets users upload CSV and Excel files, inspect data quality, explore interactive visualisations, ask supported questions in natural language, discover business findings, and export Excel/PDF reports. Supported numerical questions are calculated with Pandas; the local LLM is used as a fallback for contextual questions.

<p align="center">
  <img src="docs/images/dashboard-showcase.jpg" alt="InsightPilot AI dashboard screens: overview, explore data, AI analyst, and insights and reports" width="800">
</p>

<p align="center">
  <strong>Overview · Explore Data · AI Analyst · Insights & Reports</strong>
</p>

---

## Features

| Area | What it does |
|---|---|
| Dataset upload | Loads CSV and Excel (.xlsx) files |
| Dataset overview | Shows records, columns, missing values, duplicates, data preview and column profile |
| Visual analytics | Builds interactive Plotly charts from selected dimensions and numeric measures |
| Advanced analytics | Calculates totals, averages, top performers, monthly trends and column summaries |
| Natural-language questions | Routes supported questions to deterministic Pandas calculations |
| Local LLM fallback | Uses Ollama with Qwen 2.5 1.5B for questions not covered by the query router |
| Automatic business insights | Summarises sales/profit metrics, product/category performance and potential IQR outliers |
| Business recommendations | Produces rule-based recommendations based on detected dataset metrics |
| Business reports | Exports multi-sheet Excel workbooks and PDF analytics reports |
| Dataset download | Exports the active DataFrame as CSV |

## Screenshots

The showcase above contains real captures of the running local Streamlit application:

- **Overview:** workspace header, dataset status and KPI cards.
- **Explore Data:** interactive sales-by-product chart with selectable dimensions and aggregation.
- **AI Analyst:** question form and calculated response.
- **Insights & Reports:** automated findings and report/recommendation sections.

## Architecture

![InsightPilot AI architecture](docs/architecture.svg)

The application is organised into four main layers:

1. **Streamlit interface** — handles uploads, navigation, controls and output.
2. **Pandas analytics** — profiles the active DataFrame and performs deterministic calculations.
3. **Question handling** — routes recognised analytical questions to Pandas; uses the local Ollama/Qwen model for fallback contextual responses.
4. **Insight and report generation** — produces business findings, rule-based recommendations, Excel workbooks and PDF reports.

## Technology stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| UI | Streamlit |
| Data manipulation | Pandas, NumPy |
| Visualisation | Plotly Express |
| Local LLM runtime | Ollama |
| Model | Qwen 2.5 1.5B |
| Excel support | OpenPyXL |
| PDF generation | ReportLab |

## Project structure

```text
InsightPilot-AI/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── core/
│   ├── calculations.py
│   ├── insights_engine.py
│   ├── llm_engine.py
│   ├── query_router.py
│   ├── recommendation_engine.py
│   └── test_llm.py
├── reports/
│   └── report_generator.py
├── docs/
│   ├── architecture.svg
│   └── images/
│       └── dashboard-showcase.jpg
├── test_calculations.py
├── test_report.py
└── test_pdf_report.py
```

## Getting started (Windows PowerShell)

### Prerequisites

- Python 3.11
- Git
- Ollama installed locally
- Enough available RAM and disk space to run the selected local model (performance depends on hardware)

### 1. Clone the repository

```powershell
git clone https://github.com/Sri-Thirumalaivasan/InsightPilot-AI.git
cd InsightPilot-AI
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install and prepare the local model

Install Ollama from [ollama.com/download](https://ollama.com/download), then pull the model:

```powershell
ollama pull qwen2.5:1.5b
ollama list
```

The model name is configured in `core/llm_engine.py`. Ollama must be running for the LLM fallback feature. Recognised Pandas analytical queries do not need the LLM.

### 5. Run the application

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`; if that port is busy, Streamlit may choose another).

## Example questions

The query router recognises common question patterns when matching columns exist in the uploaded data:

```text
What is the total sales?
What is the total profit?
What is the average sales?
Which product generated the highest sales?
Which category generated the highest sales?
Show the top 5 products by sales.
Which month had the highest sales?
```

Column-name matching is intentionally limited to common business fields and the alternatives defined in `core/query_router.py`. Questions outside the supported patterns are sent to the local LLM with a compact dataset context.

## How the AI answers questions

- **Supported analytics:** Pandas calculates values from the full active DataFrame. This avoids asking a language model to perform arithmetic or invent rankings.
- **Contextual fallback:** Qwen receives the column names/types, missing-value counts, numeric summary and a small sample of records. It does not receive a full-dataset representation.
- **Recommendations:** Business recommendations are rule-based suggestions derived from detected metrics; they are not model-generated predictions.

## Deploy to Streamlit Community Cloud

The dashboard can be deployed from this public GitHub repository:

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app**.
3. Choose repository `Sri-Thirumalaivasan/InsightPilot-AI`.
4. Select branch `main`.
5. Set the app file path to `app.py`.
6. In **Advanced settings**, select **Python 3.11** to match the tested local environment.
7. Select **Deploy** and wait for the build logs to complete.

The repository includes a root-level `requirements.txt`, which Community Cloud uses to install the Python dependencies.

### Cloud deployment note: local Qwen model

The public Streamlit app can run dataset uploads, Pandas calculations, Plotly charts, automatic insights, recommendations, and Excel/PDF exports in the cloud. The Qwen fallback uses Ollama. A cloud container cannot reach the Ollama service running on your personal computer through `localhost`. Therefore, Qwen fallback questions may show a notice on the public deployment unless you configure a separately hosted, securely accessible Ollama service. Supported Pandas analytical questions do not require Ollama.

## Reports

The **Insights & Reports** tab generates:

- **Excel:** report information, KPI summary, source dataset, product ranking, category ranking when a category field exists, business insights and recommendations.
- **PDF:** dataset overview, KPIs, available product/category rankings, business insights and recommendations.

Reports are generated from the currently active DataFrame. The built-in sample dataset contains **10 rows and 5 columns** and is demonstration data, not real company data. When a file is uploaded, the report reflects that uploaded dataset.

## Run the included checks

Run commands from the project root with the virtual environment activated:

```powershell
python -m compileall app.py core reports
python test_calculations.py
python test_report.py
python test_pdf_report.py
```

To test the local model connection (Ollama must be running and the model pulled):

```powershell
python core/test_llm.py
```

## Current limitations

- The query router supports known question patterns and common column names; it is not a general-purpose natural-language-to-SQL engine.
- The local LLM fallback receives a compact dataset context rather than every row.
- Category or product-name analysis requires those columns (or an appropriate lookup table) to exist in the uploaded data.
- IQR outlier detection identifies potential anomalies, not necessarily incorrect records.
- Recommendations are rules-based prompts for investigation, not professional business advice.
- The current upload interface supports CSV and .xlsx files.

## Future improvements

- More flexible schema/column mapping and date detection.
- Additional deterministic query types and automated tests for edge cases.
- More chart types and chart exports.
- PDF charts, report branding and custom date filters.
- Optional database-backed analysis for larger datasets.
- Configurable model selection and resource-aware model handling.

## Privacy

Dataset processing and report generation run in the local Python application. The LLM integration communicates with the local Ollama service. Review any future external integrations before using confidential or sensitive datasets.

## Author

**Sri Thirumalai Vasan S** — [GitHub](https://github.com/Sri-Thirumalaivasan)

---

*InsightPilot AI is a hands-on portfolio project demonstrating data analytics, dashboard development, local LLM integration and report automation.*
