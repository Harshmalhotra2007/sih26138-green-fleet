"""Data contracts for the fleet dataset.

These Pydantic models validate the schema of the raw dataset and the
processed feature matrix used downstream.
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


class VesselSpec(BaseModel):
    """Static characteristics of a single vessel."""

    model_config = ConfigDict(extra="allow")

    vessel_id: str
    vessel_type: str  # bulk, tanker, container, general_cargo, ro_ro
    dwt: float = Field(..., gt=0, description="Deadweight tonnage")
    engine_power_kw: float = Field(..., gt=0)
    engine_count: int = Field(default=1, ge=1)
    design_speed_knots: float = Field(..., gt=0)
    hull_age_years: float = Field(default=0.0, ge=0)
    fuel_type: str = Field(default="HFO")


class FleetRecord(BaseModel):
    """A single operational observation for a vessel."""

    model_config = ConfigDict(extra="allow")

    vessel_id: str
    observation_date: str
    cargo_load_tonnes: float = Field(..., ge=0)
    cruising_speed_knots: float = Field(..., gt=0)
    sea_distance_nm: float = Field(..., ge=0)
    fuel_consumption_tonnes: float = Field(..., ge=0)
    weather_factor: float = Field(default=1.0, ge=0.5, le=2.0)
    load_factor: float = Field(default=1.0, ge=0.0, le=1.0)
    route: str | None = None


class FleetDataset(BaseModel):
    """Container for the full fleet dataset."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vessels: dict[str, VesselSpec] = Field(default_factory=dict)
    records: pd.DataFrame = Field(default_factory=pd.DataFrame)

    @field_validator("records")
    @classmethod
    def _validate_records(cls, value: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(value, pd.DataFrame):
            raise TypeError("records must be a pandas DataFrame")
        required = {"vessel_id", "fuel_consumption_tonnes", "cruising_speed_knots"}
        missing = required - set(value.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        return value


# ---------------------------------------------------------------------------
# Feature matrix contract
# ---------------------------------------------------------------------------

FEATURE_COLUMNS = [
    "vessel_type",
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
    "route",
    "fuel_type",
]

TARGET_COLUMN = "fuel_consumption_tonnes"


def validate_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the feature matrix contains every required column."""
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Feature matrix missing columns: {missing}")
    return df[FEATURE_COLUMNS]


def coerce_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce dtypes and validate the feature matrix."""
    numeric_cols = [
        "dwt", "engine_power_kw", "engine_count", "design_speed_knots",
        "hull_age_years", "cargo_load_tonnes", "cruising_speed_knots",
        "sea_distance_nm", "weather_factor", "load_factor",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "vessel_type" in df.columns:
        df["vessel_type"] = df["vessel_type"].astype(str)
    if "fuel_type" in df.columns:
        df["fuel_type"] = df["fuel_type"].astype(str)
    if "route" in df.columns:
        df["route"] = df["route"].astype("category")
    return df