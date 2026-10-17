# Enterprise Data Governance Dashboard

A Python-based dashboard for monitoring enterprise data quality, exploring governance metadata, tracking compliance indicators, and managing remediation workflows.

**Live Demo - https://data-governance-dashboard-bhdq45av4er6i2faashnqu.streamlit.app/)** 

**GitHub Repository - https://github.com/MAHE2006/data-governance-dashboard**

## Overview

This project brings data quality monitoring and governance workflows together in one interactive dashboard. It combines synthetic enterprise governance data with an upload-based profiler that lets users evaluate the quality of their own CSV datasets.

## Key Features

- **Interactive Data Quality Profiling:** Upload a CSV file and evaluate its quality across multiple dimensions.
- **Custom Quality Engine:** Calculate completeness, uniqueness, validity, and consistency metrics instead of relying only on predefined dashboard values.
- **Data Catalog:** Explore dataset metadata, ownership, classification, and quality indicators.
- **Governance Monitoring:** View policy tags and illustrative compliance indicators.
- **Remediation Workflow:** Track data quality issues using a ticket-based workflow.
- **Visual Analytics:** Explore governance metrics through interactive charts and dashboard components.

## What Makes This Project Different?

- **Custom-built profiling logic:** Developed a Python quality engine to evaluate datasets across multiple quality dimensions.
- **Beyond static dashboards:** Enabled users to upload their own CSV files and inspect quality metrics dynamically.
- **Multi-dimensional quality assessment:** Examined data quality through completeness, uniqueness, validity, and consistency rather than a single overall score.
- **End-to-end integration:** Connected data processing, quality evaluation, and interactive visualization in one deployed application.
- **Governance-focused design:** Brought catalog metadata, policy indicators, and remediation tracking into the same dashboard.

## Tech Stack

- **Language:** Python
- **Dashboard:** Streamlit
- **Data Processing:** Pandas, NumPy
- **Visualizations:** Plotly
- **Data Quality Engine:** Custom Python modules
- **Data Storage:** CSV files

## How It Works

1. Generate and load synthetic enterprise governance data.
2. Process datasets using the custom quality engine.
3. Calculate and display data quality metrics.
4. Present governance information through interactive dashboard sections.
5. Allow users to upload CSV files for on-demand quality profiling.

## Run Locally

```bash
git clone https://github.com/MAHE2006/data-governance-dashboard.git
cd data-governance-dashboard

python -m venv venv
```

Activate the environment on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies and launch the app:

```bash
pip install -r requirements.txt
python generate_governance_data.py
streamlit run app.py
```

## Project Status

Deployed working demo. The application uses synthetic governance data, and its compliance indicators are illustrative rather than a formal regulatory compliance assessment.
