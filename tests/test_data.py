"""Tests for the data layer: loader, manifest, preprocessor, feature engineering."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from src.sih26138.config import Config
from src.sih26138.data.loader import load_dataset, write_manifest
from src.sih26138.data.preprocessor import feature_engineering, preprocess
from src.sih26138.data.schema import FEATURE_COLUMNS, TARGET_COLUMN

RAW_DATASET = Path(__file__).resolve().parents[1] / "data" / "raw" / "dataset.csv"


def _base_records() -> pd.DataFrame:
    """Minimal valid fleet records spanning unsorted dates, with a null row."""
    return pd.DataFrame(
        {
            "vessel_id": ["VES_0000", "VES_0000", "VES_0000"],
            "observation_date": ["2023-01-03", "2023-01-01", "2023-01-02"],
            "cargo_load_tonnes": [1000.0, float("nan"), 2000.0],
            "cruising_speed_knots": [10.0, 11.0, 12.0],
            "sea_distance_nm": [100.0, 200.0, 300.0],
            "fuel_consumption_tonnes": [50.0, 60.0, 70.0],
            "weather_factor": [1.0, 1.0, 1.0],
            "load_factor": [0.5, 0.5, 0.5],
            "vessel_type": ["bulk", "bulk", "bulk"],
            "route": ["route_a", "route_a", "route_a"],
            "fuel_type": ["HFO", "HFO", "HFO"],
            "dwt": [1000.0, 1000.0, 1000.0],
            "engine_power_kw": [100.0, 100.0, 100.0],
            "engine_count": [1, 1, 1],
            "design_speed_knots": [14.0, 14.0, 14.0],
            "hull_age_years": [5.0, 5.0, 5.0],
        }
    )


def test_load_dataset_returns_fleetdataset_with_50_vessels():
    ds = load_dataset(RAW_DATASET)
    assert len(ds.vessels) == 50


def test_load_dataset_raises_filenotfound_for_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "does_not_exist.csv")


def test_load_dataset_raises_valueerror_on_invalid_row(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text(
        "vessel_id,observation_date,cargo_load_tonnes,cruising_speed_knots,"
        "sea_distance_nm,fuel_consumption_tonnes,weather_factor,load_factor,route\n"
        "VES_0000,2023-01-01,1000,-5,100,50,1.0,0.5,route_a\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as exc:
        load_dataset(csv_path)
    assert "Row 0" in str(exc.value)


def test_write_manifest_writes_sha256_of_raw_file(tmp_path, monkeypatch):
    monkeypatch.setattr("src.sih26138.config.PROCESSED_DATA_DIR", tmp_path)

    csv_path = tmp_path / "raw.csv"
    csv_path.write_text(
        "vessel_id,observation_date,cargo_load_tonnes,cruising_speed_knots,"
        "sea_distance_nm,fuel_consumption_tonnes,weather_factor,load_factor,route\n"
        "VES_0000,2023-01-01,1000,10,100,50,1.0,0.5,route_a\n",
        encoding="utf-8",
    )
    df = pd.read_csv(csv_path)

    manifest_path = write_manifest(csv_path, df)
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    assert manifest["sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()


def test_preprocess_drops_nulls_and_sorts_by_date():
    cfg = Config()
    cleaned = preprocess(_base_records(), cfg)

    assert cleaned.isna().sum().sum() == 0
    assert cleaned["observation_date"].tolist() == sorted(
        cleaned["observation_date"].tolist()
    )


def test_feature_engineering_excludes_identifiers():
    cfg = Config()
    cleaned = preprocess(_base_records(), cfg)
    X = feature_engineering(cleaned, cfg)

    assert "observation_date" not in X.columns
    assert "vessel_id" not in X.columns
    assert TARGET_COLUMN not in X.columns
    for col in FEATURE_COLUMNS:
        assert col in X.columns or col in {"vessel_type", "route", "fuel_type"}