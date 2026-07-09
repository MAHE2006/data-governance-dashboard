"""
generate_governance_data.py
----------------------------
Generates a realistic synthetic Enterprise Data Governance catalog:
  - data/governance_catalog.csv   -> one row per tracked dataset (metadata,
                                      ownership, classification, quality scores,
                                      compliance status)
  - data/remediation_log.csv      -> open/closed remediation tickets linked
                                      to datasets with quality/compliance issues

No external services or internet access required — pure Python + NumPy/Pandas,
fully reproducible via a fixed random seed.

Run:
    python generate_governance_data.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

RNG = np.random.default_rng(42)
OUT_DIR = Path(__file__).parent / "data"
OUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Reference / lookup lists (mirrors a real enterprise data catalog)
# ---------------------------------------------------------------------------
DEPARTMENTS = ["Finance", "Sales", "Marketing", "HR", "Operations",
               "Customer Support", "Product", "Legal & Compliance", "IT"]

SOURCE_SYSTEMS = ["Salesforce", "SAP ERP", "Workday", "Snowflake DW",
                   "MySQL Prod DB", "Google Analytics", "Zendesk",
                   "Internal API", "S3 Data Lake"]

CLASSIFICATIONS = ["Public", "Internal", "Confidential", "Restricted"]
CLASS_WEIGHTS = [0.10, 0.40, 0.35, 0.15]

POLICIES = ["GDPR-Data-Minimization", "CCPA-Consumer-Rights", "SOX-Financial-Controls",
            "HIPAA-PHI-Protection", "Internal-Retention-Policy", "PCI-DSS-Cardholder-Data"]

OWNERS = ["A. Menon", "R. Fernandes", "S. Khan", "P. Iyer", "J. Thompson",
          "L. Rodriguez", "M. Chen", "K. Osei", "D. Novak", "T. Yamamoto"]

STEWARDS = ["Data Steward - " + d for d in DEPARTMENTS]

DATASET_TOPICS = [
    "Customer Master", "Sales Transactions", "Product Catalog", "Employee Records",
    "Payroll Data", "Vendor Contracts", "Marketing Campaigns", "Web Clickstream",
    "Support Tickets", "Invoice Records", "Inventory Levels", "Shipping Logs",
    "Financial Ledger", "Customer Feedback", "Lead Scoring", "Churn Predictions",
    "Subscription Billing", "Audit Trail", "User Consent Log", "Asset Register",
]

ISSUE_TYPES = ["Missing Values", "Duplicate Records", "Schema Drift",
               "Stale / Not Refreshed", "PII Exposure Risk", "Invalid Format",
               "Referential Integrity Break", "Access Control Gap"]

SEVERITIES = ["Low", "Medium", "High", "Critical"]
SEVERITY_WEIGHTS = [0.35, 0.35, 0.22, 0.08]


def _random_date(start_days_ago: int, end_days_ago: int) -> str:
    days_ago = RNG.integers(end_days_ago, start_days_ago)
    return (datetime.today() - timedelta(days=int(days_ago))).strftime("%Y-%m-%d")


def generate_catalog(n_datasets: int = 60) -> pd.DataFrame:
    rows = []
    for i in range(1, n_datasets + 1):
        dept = RNG.choice(DEPARTMENTS)
        classification = RNG.choice(CLASSIFICATIONS, p=CLASS_WEIGHTS)
        pii_flag = "Y" if classification in ("Confidential", "Restricted") and RNG.random() < 0.7 else "N"

        # Quality dimension scores (0-100). Slightly correlated so the overall
        # score looks realistic rather than pure noise.
        base = RNG.normal(78, 12)
        completeness = float(np.clip(base + RNG.normal(0, 6), 30, 100))
        accuracy = float(np.clip(base + RNG.normal(0, 8), 25, 100))
        consistency = float(np.clip(base + RNG.normal(0, 7), 25, 100))
        timeliness = float(np.clip(base + RNG.normal(0, 10), 20, 100))
        uniqueness = float(np.clip(base + RNG.normal(0, 5), 35, 100))

        overall = round(np.mean([completeness, accuracy, consistency, timeliness, uniqueness]), 1)

        # Compliance status correlates with quality + classification sensitivity
        if overall >= 85 and pii_flag == "N":
            compliance = "Compliant"
        elif overall < 60 or (pii_flag == "Y" and overall < 75):
            compliance = "Non-Compliant"
        else:
            compliance = RNG.choice(["Compliant", "Under Review"], p=[0.55, 0.45])

        remediation_status = "None"
        if compliance == "Non-Compliant":
            remediation_status = RNG.choice(["Open", "In Progress"], p=[0.6, 0.4])
        elif overall < 70:
            remediation_status = RNG.choice(["None", "Open", "In Progress", "Resolved"],
                                             p=[0.25, 0.35, 0.25, 0.15])

        rows.append({
            "dataset_id": f"DS-{i:04d}",
            "dataset_name": f"{RNG.choice(DATASET_TOPICS)} - {dept}",
            "department": dept,
            "owner": RNG.choice(OWNERS),
            "steward": f"Data Steward - {dept}",
            "source_system": RNG.choice(SOURCE_SYSTEMS),
            "classification": classification,
            "pii_flag": pii_flag,
            "completeness_score": round(completeness, 1),
            "accuracy_score": round(accuracy, 1),
            "consistency_score": round(consistency, 1),
            "timeliness_score": round(timeliness, 1),
            "uniqueness_score": round(uniqueness, 1),
            "overall_quality_score": overall,
            "compliance_status": compliance,
            "policy_name": RNG.choice(POLICIES),
            "row_count": int(RNG.integers(500, 5_000_000)),
            "retention_period_days": int(RNG.choice([365, 730, 1095, 1825, 2555])),
            "last_reviewed_date": _random_date(180, 1),
            "last_updated": _random_date(60, 0),
            "remediation_status": remediation_status,
        })
    return pd.DataFrame(rows)


def generate_remediation_log(catalog: pd.DataFrame) -> pd.DataFrame:
    tickets = []
    ticket_no = 1
    needs_ticket = catalog[catalog["remediation_status"].isin(["Open", "In Progress", "Resolved"])]

    for _, ds in needs_ticket.iterrows():
        n_issues = RNG.integers(1, 3)
        for _ in range(n_issues):
            severity = RNG.choice(SEVERITIES, p=SEVERITY_WEIGHTS)
            status = ds["remediation_status"] if ds["remediation_status"] != "None" else "Open"
            created = _random_date(90, 5)
            resolved = ""
            if status == "Resolved":
                resolved = _random_date(4, 0)

            tickets.append({
                "ticket_id": f"TCK-{ticket_no:05d}",
                "dataset_id": ds["dataset_id"],
                "dataset_name": ds["dataset_name"],
                "issue_type": RNG.choice(ISSUE_TYPES),
                "severity": severity,
                "description": f"{RNG.choice(ISSUE_TYPES)} detected during automated scan of '{ds['dataset_name']}'.",
                "assigned_to": ds["steward"],
                "status": status,
                "created_date": created,
                "resolved_date": resolved,
            })
            ticket_no += 1
    return pd.DataFrame(tickets)


if __name__ == "__main__":
    catalog_df = generate_catalog(n_datasets=60)
    catalog_path = OUT_DIR / "governance_catalog.csv"
    catalog_df.to_csv(catalog_path, index=False)

    remediation_df = generate_remediation_log(catalog_df)
    remediation_path = OUT_DIR / "remediation_log.csv"
    remediation_df.to_csv(remediation_path, index=False)

    print(f"✔ Generated {len(catalog_df)} dataset records  -> {catalog_path}")
    print(f"✔ Generated {len(remediation_df)} remediation tickets -> {remediation_path}")
