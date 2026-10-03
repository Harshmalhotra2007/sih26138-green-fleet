"""Data loader for the fleet dataset.

Reads raw CSV files into validated Pydantic containers, builds the
vessel registry, and writes a data manifest for reproducibility.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from .schema import FleetDataset, FleetRecord, VesselSpec

# Static vessel columns — identical across rows for the same vessel.
_VESSEL_STATIC_COLUMNS = [
    "vessel_id",
    "vessel_type",
    "dwt",
    "engine_power_kw",
    "engine_count",
    "design_speed_knots",
    "hull_age_years",
    "fuel_type",
]


def _build_vessel_registry(records: pd.DataFrame) -> dict[str, VesselSpec]:
    """Build a vessel registry from the first occurrence of each vessel_id."""
    vessels: dict[str, VesselSpec] = {}
    seen: set[str] = set()
    for row in records.to_dict("records"):
        vid = row["vessel_id"]
        if vid in seen:
            continue
        seen.add(vid)
        spec = {k: row[k] for k in _VESSEL_STATIC_COLUMNS if k in row}
        try:
            vessels[vid] = VesselSpec(**spec)
        except ValidationError as exc:
            raise ValueError(
                f"Vessel {vid} has invalid static spec: {exc.errors()}"
            ) from exc
    return vessels


def _validate_row(row: dict[str, Any], idx: int) -> FleetRecord:
    """Validate a single row against FleetRecord, raising a row-indexed error."""
    try:
        return FleetRecord(**row)
    except ValidationError as exc:
        errors = exc.errors()
        if errors:
            field = errors[0].get("loc", ("unknown",))[0]
            msg = errors[0].get("msg", "invalid")
        else:
            field = "unknown"
            msg = "invalid"
        raise ValueError(
            f"Row {idx}: {field}={row.get(field)!r} {msg}"
        ) from exc


def load_dataset(path: str | Path) -> FleetDataset:
    """Load a raw CSV dataset and validate every row.

    Args:
        path: Path to the raw CSV file.

    Returns:
        A validated FleetDataset with a vessel registry and records frame.

    Raises:
        FileNotFoundError: if the CSV does not exist.
        ValueError: if a row fails FleetRecord validation (row index +
            failing field reported).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {p}")

    df = pd.read_csv(p)

    # Validate every row, reporting the row index and failing field.
    validated_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(df.to_dict("records")):
        rec = _validate_row(row, idx)
        validated_rows.append(rec.model_dump())

    records = pd.DataFrame(validated_rows)
    vessels = _build_vessel_registry(records)

    return FleetDataset(vessels=vessels, records=records)


def load_external_fuel_properties() -> dict[str, dict[str, float]]:
    """Load fuel property tables (price, emission factors).

    Falls back to the in-code ScenarioConfig defaults when no external
    file is present.

    Returns:
        Dict mapping fuel name -> {price_usd_tonne, co2_factor, sox_factor}.
    """
    from src.sih26138.config import Config

    return Config().scenario.fuels


def write_manifest(raw_csv_path: Path, df: pd.DataFrame) -> Path:
    """Write a data manifest recording the raw-file hash and row count.

    The hash is computed over the raw CSV bytes on disk, so it detects
    any change to the source file regardless of how the DataFrame was
    loaded.

    Args:
        raw_csv_path: Path to the raw CSV file.
        df: The validated DataFrame loaded from that file.

    Returns:
        Path to the written manifest JSON (data/processed/manifest.json).
    """
    from src.sih26138.config import PROCESSED_DATA_DIR

    raw_bytes = Path(raw_csv_path).read_bytes()
    file_hash = hashlib.sha256(raw_bytes).hexdigest()

    manifest = {
        "raw_file": str(raw_csv_path),
        "sha256": file_hash,
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns),
    }

    out_path = PROCESSED_DATA_DIR / "manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return out_path