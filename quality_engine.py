"""
quality_engine.py
------------------
A lightweight, dependency-free (pandas/numpy only) data profiling engine.
Computes the standard data-quality dimensions used in enterprise governance
programs, on ANY dataframe you hand it (e.g. a real Kaggle CSV):

    - Completeness  : % of non-null cells
    - Uniqueness    : % of non-duplicate rows
    - Validity      : % of values matching an expected type/pattern per column
    - Consistency   : % of columns with a single stable dtype (no mixed types)
    - Overall score : weighted average of the above (0-100)

Import and use directly:

    from quality_engine import profile_dataframe
    report, column_report = profile_dataframe(df)
"""

from __future__ import annotations
import re
import numpy as np
import pandas as pd

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

WEIGHTS = {
    "completeness": 0.30,
    "uniqueness": 0.20,
    "validity": 0.30,
    "consistency": 0.20,
}


def _completeness(df: pd.DataFrame) -> float:
    total_cells = df.shape[0] * df.shape[1]
    if total_cells == 0:
        return 0.0
    non_null = df.notna().sum().sum()
    return round(100 * non_null / total_cells, 2)


def _uniqueness(df: pd.DataFrame) -> float:
    if len(df) == 0:
        return 0.0
    dup_ratio = df.duplicated().sum() / len(df)
    return round(100 * (1 - dup_ratio), 2)


def _column_validity(series: pd.Series) -> float:
    """Heuristic validity check per column based on inferred semantics."""
    non_null = series.dropna()
    if non_null.empty:
        return 0.0

    name = series.name.lower() if isinstance(series.name, str) else ""

    # Email-like columns
    if "email" in name:
        valid = non_null.astype(str).str.match(EMAIL_RE)
        return round(100 * valid.mean(), 2)

    # Date-like columns
    if "date" in name or "_at" in name or "time" in name:
        parsed = pd.to_datetime(non_null, errors="coerce")
        return round(100 * parsed.notna().mean(), 2)

    # Numeric columns: flag negative values in fields that should be >= 0
    if pd.api.types.is_numeric_dtype(series):
        if any(k in name for k in ["age", "price", "amount", "qty", "quantity",
                                    "count", "score", "salary", "revenue"]):
            valid = non_null >= 0
            return round(100 * valid.mean(), 2)
        return 100.0  # numeric with no obvious constraint -> treat as valid

    # Categorical/text: valid if non-empty string after stripping whitespace
    valid = non_null.astype(str).str.strip().ne("")
    return round(100 * valid.mean(), 2)


def _validity(df: pd.DataFrame) -> float:
    if df.shape[1] == 0:
        return 0.0
    scores = [_column_validity(df[c]) for c in df.columns]
    return round(float(np.mean(scores)), 2)


def _consistency(df: pd.DataFrame) -> float:
    """Checks whether each object column holds a single consistent Python type
    (e.g. not a mix of str and int within the same column)."""
    if df.shape[1] == 0:
        return 0.0
    consistent_cols = 0
    for c in df.columns:
        col = df[c].dropna()
        if col.empty:
            consistent_cols += 1
            continue
        types_seen = col.map(type).nunique()
        if types_seen <= 1:
            consistent_cols += 1
    return round(100 * consistent_cols / df.shape[1], 2)


def profile_dataframe(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Returns:
        report        : dict with overall KPI scores for the dataset
        column_report : per-column completeness / validity breakdown (DataFrame)
    """
    completeness = _completeness(df)
    uniqueness = _uniqueness(df)
    validity = _validity(df)
    consistency = _consistency(df)

    overall = round(
        completeness * WEIGHTS["completeness"]
        + uniqueness * WEIGHTS["uniqueness"]
        + validity * WEIGHTS["validity"]
        + consistency * WEIGHTS["consistency"],
        2,
    )

    report = {
        "row_count": len(df),
        "column_count": df.shape[1],
        "completeness_score": completeness,
        "uniqueness_score": uniqueness,
        "validity_score": validity,
        "consistency_score": consistency,
        "overall_quality_score": overall,
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing_cells": int(df.isna().sum().sum()),
    }

    col_rows = []
    for c in df.columns:
        col_rows.append({
            "column": c,
            "dtype": str(df[c].dtype),
            "missing_pct": round(100 * df[c].isna().mean(), 2),
            "unique_values": int(df[c].nunique(dropna=True)),
            "validity_score": _column_validity(df[c]),
        })
    column_report = pd.DataFrame(col_rows)

    return report, column_report


if __name__ == "__main__":
    # Quick self-test with a deliberately messy sample dataset
    sample = pd.DataFrame({
        "customer_id": [1, 2, 2, 4, None],
        "email": ["a@x.com", "bad-email", "c@y.com", None, "d@z.com"],
        "signup_date": ["2024-01-01", "2024-13-45", "2024-02-01", "2024-03-01", None],
        "age": [25, -5, 40, 31, 29],
    })
    report, col_report = profile_dataframe(sample)
    print("Overall report:", report)
    print(col_report)
