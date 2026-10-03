"""Data preprocessing and feature engineering.

Cleans raw records (clipping, dtype coercion, NaN handling) and produces a
feature matrix suitable for training. The target column is never clipped —
only FEATURE columns are winsorised at the 1st/99th percentile.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import FEATURE_COLUMNS, TARGET_COLUMN

# Columns that are identifiers / metadata, not model features.
_NON_FEATURE_COLUMNS = ["vessel_id", "observation_date", TARGET_COLUMN]

# Categorical columns that get one-hot encoded rather than ordinal-encoded.
_CATEGORICAL_COLUMNS = ["vessel_type", "route", "fuel_type"]

_NUMERIC_FEATURE_COLUMNS = [
    "dwt",
    "engine_power_kw",
    "engine_count",
    "design_speed_knots",
    "hull_age_years",
    "cargo_load_tonnes",
    "cruising_speed_knots",
    "sea_distance_nm",
    "weather_factor",
    "load_factor",
]


def preprocess(records: pd.DataFrame, cfg: Any) -> pd.DataFrame:
    """Clean raw voyage records into a model-ready DataFrame.

    Steps:
    1. Coerce numeric dtypes.
    2. Drop rows with NaN in any FEATURE column or the target.
    3. Winsorise (clip) each FEATURE column at the 1st/99th percentile.
       The target column is intentionally left untouched.

    Args:
        records: Raw records DataFrame from loader.
        cfg: Config object (used for seed if needed in future).

    Returns:
        Cleaned DataFrame with the same columns as records.
    """
    df = records.copy()

    # 1. Coerce numeric columns.
    for col in _NUMERIC_FEATURE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if TARGET_COLUMN in df.columns:
        df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")

    # 2. Drop rows with NaN in features or target.
    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    cols_to_check = feature_cols + ([TARGET_COLUMN] if TARGET_COLUMN in df.columns else [])
    df = df.dropna(subset=cols_to_check).reset_index(drop=True)

    # Ensure observation_date is datetime and sort ascending for TimeSeriesSplit (ADR-011).
    if "observation_date" in df.columns:
        df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
        df = df.sort_values("observation_date").reset_index(drop=True)

    # 3. Winsorise FEATURE columns only — never the target.
    for col in feature_cols:
        if col in _NUMERIC_FEATURE_COLUMNS:
            lo = df[col].quantile(0.01)
            hi = df[col].quantile(0.99)
            if pd.notna(lo) and pd.notna(hi):
                df[col] = df[col].clip(lower=lo, upper=hi)

    return df


def feature_engineering(clean: pd.DataFrame, cfg: Any) -> pd.DataFrame:
    """Build the feature matrix from cleaned records.

    One-hot encodes categorical features (vessel_type, route, fuel_type),
    drops identifier/metadata columns, and returns a numeric matrix.

    Args:
        clean: Cleaned DataFrame from preprocess().
        cfg: Config object (unused, kept for API symmetry).

    Returns:
        Numeric feature matrix (one row per voyage).
    """
    df = clean.copy()

    # One-hot encode categorical columns.
    for col in _CATEGORICAL_COLUMNS:
        if col in df.columns:
            df = pd.get_dummies(df, columns=[col], prefix=col, dtype=int)

    # Drop identifier / metadata / target columns.
    drop_cols = [c for c in _NON_FEATURE_COLUMNS if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df.reset_index(drop=True)


def save_features(X: pd.DataFrame, path: str | Path) -> Path:
    """Save a feature matrix to Parquet.

    Args:
        X: Feature matrix.
        path: Destination Parquet path.

    Returns:
        The path written.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    X.to_parquet(p, index=False)
    return p


def load_features(path: str | Path) -> pd.DataFrame:
    """Load a feature matrix from Parquet.

    Args:
        path: Source Parquet path.

    Returns:
        The feature matrix.
    """
    return pd.read_parquet(Path(path))