# Enterprise Data Governance Dashboard

A working demo of what a centralized data-governance monitoring tool could
look like — I built this to cover the core things a real governance
platform needs to do: track ownership, flag quality issues, monitor
compliance, and give someone a way to actually act on problems instead of
just staring at a dashboard.

Quick map of what's implemented where:

| What it does | Where |
|---|---|
| Centralized dashboard for ownership, quality, compliance | `app.py` (all 5 tabs) |
| Data classification & metadata tracking | `generate_governance_data.py` → `data/governance_catalog.csv`, Data Catalog tab |
| KPIs for data health | Overview tab — health score, % compliant, distributions |
| Issue identification + remediation | Remediation Workflow tab — raise/track/resolve tickets |
| Governance workflow tied to regulations | Policy tags (GDPR, HIPAA, SOX, PCI-DSS...) in Compliance & Policy tab |

---

## 1. Project structure

```
governance_dashboard/
├── app.py                        # Streamlit dashboard — run this
├── generate_governance_data.py   # builds the synthetic catalog + tickets
├── quality_engine.py             # actual data-quality profiling logic
│                                  # (completeness, uniqueness, validity,
│                                  # consistency, overall score)
├── requirements.txt
├── README.md
└── data/
    ├── governance_catalog.csv    # 60 fake "enterprise" datasets w/ metadata
    └── remediation_log.csv       # tickets linked to catalog entries
```

---

## 2. How to run it

**Step 1 — Python 3.9+**
Check with `python3 --version`.

**Step 2 — virtual environment (recommended, not required)**
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**Step 3 — install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — generate the catalog**
This creates `data/governance_catalog.csv` and `data/remediation_log.csv`.
(Honestly you can skip this — the app auto-generates them on first run if
they don't exist yet — but I like running it manually so I know exactly
what data I'm looking at.)
```bash
python generate_governance_data.py
```

**Step 5 — launch it**
```bash
streamlit run app.py
```
Opens `http://localhost:8501` automatically.

**Step 6 (optional) — test the quality engine on its own**
```bash
python quality_engine.py
```
Runs a self-test on a small messy sample and prints the scores it computes.

---

## 3. The part I'm actually proud of: the Quality Profiler tab

Everything else in this app runs on synthetic data I generated myself,
which is fine for demoing the UI but doesn't prove the scoring logic
actually works. So the Quality Profiler tab lets you upload *any* CSV and
get live completeness/uniqueness/validity/consistency scores computed by
`quality_engine.py` — this is the part that shows the KPIs hold up on real,
messy data and not just my own synthetic catalog.

A few datasets that work well for testing this (all free, no login beyond
maybe a Kaggle account):

1. **Titanic** — https://www.kaggle.com/competitions/titanic/data
   Real missing values in `Age`, `Cabin`, `Embarked` — good for testing
   completeness/validity scoring.

2. **Melbourne Housing Snapshot** — https://www.kaggle.com/datasets/dansbecker/melbourne-housing-snapshot
   Naturally messy real-estate data, lots of missing fields — decent
   stress test for the profiler.

3. **Online Retail (Kaggle mirror)** — https://www.kaggle.com/datasets/carrie1/ecommerce-data
   Duplicate invoices, missing CustomerID — good for uniqueness/completeness.

4. **Telco Customer Churn** — https://www.kaggle.com/datasets/blastchar/telco-customer-churn
   Good for validity checks, like blank strings hiding as missing values.

Download any of these, unzip if needed, go to the Quality Profiler tab,
click "Browse files," pick it. No code changes needed — the engine looks at
column names and dtypes to figure out what "valid" means per column.

Honestly, any CSV works — a company export, an open-data portal file,
whatever. The profiler isn't hardcoded to a specific schema.

---

## 4. Making the synthetic catalog bigger

Open `generate_governance_data.py` and bump this up:
```python
catalog_df = generate_catalog(n_datasets=60)
```
then re-run `python generate_governance_data.py`. There's a fixed random
seed (`RNG = np.random.default_rng(42)`) so the output is reproducible —
remove or change it if you want different random data every run.

---

## 5. Things I'd add if I kept working on this

- An actual architecture diagram: CSV/DB catalog → profiling engine →
  Streamlit dashboard → remediation loop
- Formal KPI definitions written up (completeness, accuracy, consistency,
  timeliness, uniqueness) — the formulas already exist in
  `quality_engine.py`, just need to document them properly
- Screenshots of each tab for a write-up
- Connect to a real warehouse (Snowflake/BigQuery) via SQL instead of CSVs
- Role-based access control
- Run the profiler as a scheduled Airflow job instead of manually
- Slack/email alerts when a new ticket gets marked "Non-Compliant"

---

## 6. Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: streamlit` | `pip install -r requirements.txt` inside your active venv |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Blank charts | Make sure `data/governance_catalog.csv` exists — run `python generate_governance_data.py` |
| Uploaded CSV gives weird validity scores | The engine guesses meaning from column names (`email`, `date`, `age`, etc.) — rename columns if your dataset uses very different naming |
