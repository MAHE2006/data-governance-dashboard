"""
app.py — Enterprise Data Governance Dashboard
===============================================
Run with:
    streamlit run app.py

Tabs:
  1. Overview            -> executive KPIs (health, compliance, open risk)
  2. Data Catalog         -> filterable dataset inventory (ownership, classification, metadata)
  3. Quality Profiler     -> upload ANY real CSV and profile it live with quality_engine.py
  4. Compliance & Policy  -> policy coverage + compliance breakdowns
  5. Remediation Workflow -> stakeholders view/raise/update remediation tickets
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from pathlib import Path

from quality_engine import profile_dataframe
from generate_governance_data import generate_catalog, generate_remediation_log

DATA_DIR = Path(__file__).parent / "data"
CATALOG_PATH = DATA_DIR / "governance_catalog.csv"
REMEDIATION_PATH = DATA_DIR / "remediation_log.csv"

st.set_page_config(page_title="Enterprise Data Governance Dashboard",
                    layout="wide", page_icon="🛡️")


# ---------------------------------------------------------------------------
# Data loading (auto-generates on first run if missing)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    if not CATALOG_PATH.exists():
        DATA_DIR.mkdir(exist_ok=True)
        cat = generate_catalog()
        cat.to_csv(CATALOG_PATH, index=False)
    else:
        cat = pd.read_csv(CATALOG_PATH)

    if not REMEDIATION_PATH.exists():
        rem = generate_remediation_log(cat)
        rem.to_csv(REMEDIATION_PATH, index=False)
    else:
        rem = pd.read_csv(REMEDIATION_PATH)

    return cat, rem


catalog, remediation = load_data()

# Session-state copy so in-app edits (new tickets, status changes) persist
# for the duration of the session without mutating the file on disk.
if "remediation" not in st.session_state:
    st.session_state.remediation = remediation.copy()
if "catalog" not in st.session_state:
    st.session_state.catalog = catalog.copy()

cat_df = st.session_state.catalog
rem_df = st.session_state.remediation

st.title("🛡️ Enterprise Data Governance Dashboard")
st.caption("Centralized monitoring of data ownership, quality, classification, and policy compliance.")

tab_overview, tab_catalog, tab_profiler, tab_compliance, tab_remediation = st.tabs(
    ["📊 Overview", "📚 Data Catalog", "🔬 Quality Profiler", "⚖️ Compliance & Policy", "🛠️ Remediation Workflow"]
)

# ---------------------------------------------------------------------------
# TAB 1 — OVERVIEW (Executive KPIs)
# ---------------------------------------------------------------------------
with tab_overview:
    st.subheader("Executive KPI Summary")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Datasets Tracked", len(cat_df))
    col2.metric("Avg. Data Health Score", f"{cat_df['overall_quality_score'].mean():.1f} / 100")
    pct_compliant = (cat_df["compliance_status"] == "Compliant").mean() * 100
    col3.metric("% Compliant", f"{pct_compliant:.1f}%")
    open_tickets = (rem_df["status"].isin(["Open", "In Progress"])).sum()
    col4.metric("Open Remediation Tickets", int(open_tickets))
    pii_count = (cat_df["pii_flag"] == "Y").sum()
    col5.metric("Datasets Holding PII", int(pii_count))

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Data Health Score Distribution**")
        fig = px.histogram(cat_df, x="overall_quality_score", nbins=20,
                            color_discrete_sequence=["#4C6EF5"])
        fig.update_layout(xaxis_title="Overall Quality Score", yaxis_title="Dataset Count",
                           margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Compliance Status Breakdown**")
        comp_counts = cat_df["compliance_status"].value_counts().reset_index()
        comp_counts.columns = ["status", "count"]
        fig2 = px.pie(comp_counts, names="status", values="count", hole=0.45,
                       color="status",
                       color_discrete_map={"Compliant": "#2F9E44", "Non-Compliant": "#E03131",
                                            "Under Review": "#F08C00"})
        fig2.update_layout(margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Avg. Data Health Score by Department**")
    dept_health = cat_df.groupby("department")["overall_quality_score"].mean().sort_values().reset_index()
    fig3 = px.bar(dept_health, x="overall_quality_score", y="department", orientation="h",
                   color="overall_quality_score", color_continuous_scale="RdYlGn", range_color=[40, 100])
    fig3.update_layout(margin=dict(t=10), xaxis_title="Avg. Quality Score", yaxis_title="")
    st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2 — DATA CATALOG (metadata + ownership + classification tracking)
# ---------------------------------------------------------------------------
with tab_catalog:
    st.subheader("Dataset Metadata Catalog")
    st.caption("Ownership, classification, and metadata tracking across all registered datasets.")

    f1, f2, f3, f4 = st.columns(4)
    dept_filter = f1.multiselect("Department", sorted(cat_df["department"].unique()))
    class_filter = f2.multiselect("Classification", sorted(cat_df["classification"].unique()))
    comp_filter = f3.multiselect("Compliance Status", sorted(cat_df["compliance_status"].unique()))
    pii_filter = f4.selectbox("PII Only", ["All", "Yes", "No"])

    filtered = cat_df.copy()
    if dept_filter:
        filtered = filtered[filtered["department"].isin(dept_filter)]
    if class_filter:
        filtered = filtered[filtered["classification"].isin(class_filter)]
    if comp_filter:
        filtered = filtered[filtered["compliance_status"].isin(comp_filter)]
    if pii_filter != "All":
        filtered = filtered[filtered["pii_flag"] == ("Y" if pii_filter == "Yes" else "N")]

    st.dataframe(
        filtered.style.background_gradient(subset=["overall_quality_score"], cmap="RdYlGn", vmin=40, vmax=100),
        use_container_width=True, height=420,
    )
    st.caption(f"Showing {len(filtered)} of {len(cat_df)} datasets.")

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export filtered catalog as CSV", csv, "governance_catalog_filtered.csv", "text/csv")

# ---------------------------------------------------------------------------
# TAB 3 — QUALITY PROFILER (real profiling engine on any uploaded dataset)
# ---------------------------------------------------------------------------
with tab_profiler:
    st.subheader("Live Data Quality Profiler")
    st.caption("Upload any real-world CSV (e.g. a Kaggle dataset) to compute governance-grade quality KPIs.")

    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.write(f"Loaded **{df.shape[0]:,} rows × {df.shape[1]} columns**")

        report, col_report = profile_dataframe(df)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Overall Quality Score", f"{report['overall_quality_score']}")
        m2.metric("Completeness", f"{report['completeness_score']}%")
        m3.metric("Uniqueness", f"{report['uniqueness_score']}%")
        m4.metric("Validity", f"{report['validity_score']}%")
        m5.metric("Consistency", f"{report['consistency_score']}%")

        radar_df = pd.DataFrame({
            "dimension": ["Completeness", "Uniqueness", "Validity", "Consistency"],
            "score": [report["completeness_score"], report["uniqueness_score"],
                      report["validity_score"], report["consistency_score"]],
        })
        fig = px.line_polar(radar_df, r="score", theta="dimension", line_close=True, range_r=[0, 100])
        fig.update_traces(fill="toself")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Column-level breakdown**")
        st.dataframe(
            col_report.style.background_gradient(subset=["validity_score"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
        )
    else:
        st.info("No file uploaded yet. Try a real dataset — see the README for Kaggle links "
                "(e.g. Titanic, Melbourne Housing Snapshot) to see the profiler flag real-world issues.")

# ---------------------------------------------------------------------------
# TAB 4 — COMPLIANCE & POLICY
# ---------------------------------------------------------------------------
with tab_compliance:
    st.subheader("Regulatory & Policy Compliance")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Datasets per Policy**")
        policy_counts = cat_df["policy_name"].value_counts().reset_index()
        policy_counts.columns = ["policy", "count"]
        fig = px.bar(policy_counts, x="count", y="policy", orientation="h",
                      color_discrete_sequence=["#5F3DC4"])
        fig.update_layout(margin=dict(t=10), yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Compliance Status by Classification**")
        cross = pd.crosstab(cat_df["classification"], cat_df["compliance_status"])
        fig2 = px.bar(cross, barmode="stack",
                       color_discrete_map={"Compliant": "#2F9E44", "Non-Compliant": "#E03131",
                                            "Under Review": "#F08C00"})
        fig2.update_layout(margin=dict(t=10), xaxis_title="", yaxis_title="Dataset Count")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Non-Compliant / Under Review Datasets requiring attention**")
    at_risk = cat_df[cat_df["compliance_status"] != "Compliant"].sort_values("overall_quality_score")
    st.dataframe(at_risk[["dataset_id", "dataset_name", "department", "owner", "classification",
                           "compliance_status", "overall_quality_score", "policy_name"]],
                 use_container_width=True, height=350)

# ---------------------------------------------------------------------------
# TAB 5 — REMEDIATION WORKFLOW (simulated governance workflow)
# ---------------------------------------------------------------------------
with tab_remediation:
    st.subheader("Remediation Workflow")
    st.caption("Stakeholders identify issues from the catalog and track them to resolution here.")

    st.markdown("### Raise a new remediation ticket")
    with st.form("new_ticket_form", clear_on_submit=True):
        rc1, rc2, rc3 = st.columns(3)
        ds_choice = rc1.selectbox("Dataset", cat_df["dataset_id"] + " — " + cat_df["dataset_name"])
        issue_type = rc2.selectbox("Issue Type", ["Missing Values", "Duplicate Records", "Schema Drift",
                                                    "Stale / Not Refreshed", "PII Exposure Risk",
                                                    "Invalid Format", "Referential Integrity Break",
                                                    "Access Control Gap"])
        severity = rc3.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        description = st.text_area("Description")
        submitted = st.form_submit_button("Create Ticket")

        if submitted:
            ds_id = ds_choice.split(" — ")[0]
            ds_name = ds_choice.split(" — ")[1]
            owner_row = cat_df.loc[cat_df["dataset_id"] == ds_id, "steward"]
            assigned_to = owner_row.values[0] if len(owner_row) else "Unassigned"
            new_id = f"TCK-{len(st.session_state.remediation) + 1:05d}"
            new_row = {
                "ticket_id": new_id, "dataset_id": ds_id, "dataset_name": ds_name,
                "issue_type": issue_type, "severity": severity,
                "description": description or f"{issue_type} reported on {ds_name}.",
                "assigned_to": assigned_to, "status": "Open",
                "created_date": pd.Timestamp.today().strftime("%Y-%m-%d"), "resolved_date": "",
            }
            st.session_state.remediation = pd.concat(
                [st.session_state.remediation, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Ticket {new_id} created and assigned to {assigned_to}.")
            st.rerun()

    st.divider()
    st.markdown("### Ticket Tracker")

    status_filter = st.multiselect("Filter by status", ["Open", "In Progress", "Resolved"],
                                     default=["Open", "In Progress"])
    tickets_view = st.session_state.remediation
    if status_filter:
        tickets_view = tickets_view[tickets_view["status"].isin(status_filter)]

    for idx, row in tickets_view.iterrows():
        with st.expander(f"{row['ticket_id']} · {row['dataset_name']} · {row['severity']} · {row['status']}"):
            st.write(f"**Issue:** {row['issue_type']}")
            st.write(f"**Description:** {row['description']}")
            st.write(f"**Assigned to:** {row['assigned_to']}  |  **Created:** {row['created_date']}")
            new_status = st.selectbox("Update status", ["Open", "In Progress", "Resolved"],
                                       index=["Open", "In Progress", "Resolved"].index(row["status"])
                                       if row["status"] in ["Open", "In Progress", "Resolved"] else 0,
                                       key=f"status_{row['ticket_id']}")
            if st.button("Save", key=f"save_{row['ticket_id']}"):
                st.session_state.remediation.loc[
                    st.session_state.remediation["ticket_id"] == row["ticket_id"], "status"] = new_status
                if new_status == "Resolved":
                    st.session_state.remediation.loc[
                        st.session_state.remediation["ticket_id"] == row["ticket_id"], "resolved_date"
                    ] = pd.Timestamp.today().strftime("%Y-%m-%d")
                st.success("Updated.")
                st.rerun()
