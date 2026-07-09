# Enterprise Data Governance Dashboard

A working demo of a centralized data-governance monitoring platform, covering
everything in your project brief:

| Bullet point | Where it's implemented |
|---|---|
| Centralized dashboard for ownership, quality, compliance | `app.py` (all 5 tabs) |
| Data classification & metadata tracking | `generate_governance_data.py` → `data/governance_catalog.csv`, **Data Catalog** tab |
| KPIs for data health, reducing inconsistencies | **Overview** tab (health score, % compliant, distributions) |
| Interactive dashboards for issue identification + remediation | **Remediation Workflow** tab (raise/track/resolve tickets) |
| Simulated governance workflow aligned to regulations | Policy tags (GDPR, HIPAA, SOX, PCI-DSS...) in **Compliance & Policy** tab |

---

## 1. Project structure

```
governance_dashboard/
├── app.py                        # Streamlit dashboard (run this)
├── generate_governance_data.py   # Synthetic catalog + remediation ticket generator
├── quality_engine.py             # Real data-quality profiling engine (completeness,
│                                  # uniqueness, validity, consistency, overall score)
├── requirements.txt
├── README.md
└── data/
    ├── governance_catalog.csv    # 60 simulated enterprise datasets w/ metadata
    └── remediation_log.csv       # Linked remediation tickets
```

---

## 2. How to run it

### Step 1 — Install Python 3.9+ if you don't have it
Check with `python3 --version`.

### Step 2 — Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Generate the synthetic governance catalog
This creates `data/governance_catalog.csv` and `data/remediation_log.csv`.
(The dashboard will also auto-generate these on first run if you skip this step.)
```bash
python generate_governance_data.py
```

### Step 5 — Launch the dashboard
```bash
streamlit run app.py
```
This opens `http://localhost:8501` in your browser automatically.

### Step 6 (optional) — Test the quality engine standalone
```bash
python quality_engine.py
```
Runs a self-test on a small messy sample and prints the computed scores.

---

## 3. Using the Quality Profiler tab with a real dataset

The **Quality Profiler** tab lets you upload *any* CSV and get live governance
scores (completeness, uniqueness, validity, consistency) computed by
`quality_engine.py` — this is the part of the project that proves the KPIs
work on real, messy data rather than only the synthetic catalog.

### Recommended open datasets to download and try (all free, no login walls beyond a Kaggle account):

1. **Titanic - Machine Learning from Disaster**
   https://www.kaggle.com/competitions/titanic/data
   → Has real missing values (`Age`, `Cabin`, `Embarked`) — good for demoing completeness/validity scoring.

2. **Melbourne Housing Snapshot**
   https://www.kaggle.com/datasets/dansbecker/melbourne-housing-snapshot
   → Naturally messy real-estate data with many missing fields and mixed quality — great stress-test for the profiler.

3. **Online Retail Dataset (UCI / Kaggle mirror)**
   https://www.kaggle.com/datasets/carrie1/ecommerce-data
   → Contains duplicate invoices and missing `CustomerID` — good for uniqueness/completeness KPIs.

4. **Telco Customer Churn**
   https://www.kaggle.com/datasets/blastchar/telco-customer-churn
   → Good for validity checks (e.g. blank strings hiding as missing values).

Download any CSV, unzip if needed, then in the **Quality Profiler** tab click
"Browse files" and select it. No code changes needed — the engine inspects
column names/dtypes automatically to decide what "valid" means per column.

> If you don't want to use Kaggle, any CSV works — company export, a public
> government open-data portal file, etc. The profiler is fully generic.

---

## 4. Regenerating a bigger/different synthetic catalog

Open `generate_governance_data.py` and change:
```python
catalog_df = generate_catalog(n_datasets=60)   # bump this number up
```
then re-run `python generate_governance_data.py`. The random seed (`RNG = np.random.default_rng(42)`)
keeps output reproducible — remove/change the seed if you want fresh random data each run.

---

## 5. Extending this into a full project write-up

Suggested sections for your report/presentation:
- **Architecture diagram**: CSV/DB catalog → profiling engine → Streamlit dashboard → stakeholder remediation loop.
- **KPI definitions**: define each quality dimension (completeness, accuracy, consistency, timeliness, uniqueness) with formulas — all are implemented in `quality_engine.py` and can be quoted directly.
- **Sample screenshots**: run the app locally and screenshot each tab.
- **Future work**: connect to a real warehouse (Snowflake/BigQuery) via SQL instead of CSV, add role-based access control, schedule the profiler as an Airflow job, add email/Slack alerts on new "Non-Compliant" tickets.

---

## 6. Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` inside your active virtual environment |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Blank charts | Make sure `data/governance_catalog.csv` exists — run `python generate_governance_data.py` |
| Uploaded CSV shows odd validity scores | The engine infers meaning from column names (e.g. `email`, `date`, `age`) — rename columns if your dataset uses very different naming |
