"""Central configuration for SIH26138 Green Fleet Optimisation.

All tunables live here so the rest of the codebase stays declarative.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports"


def _ensure_dirs() -> None:
    for d in (PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR, MODEL_DIR, REPORT_DIR):
        d.mkdir(parents=True, exist_ok=True)


_ensure_dirs()


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

@dataclass
class FleetConfig:
    """Operational constraints for the fleet optimisation problem."""

    fleet_size: int = 50
    budget_usd: float = 500_000_000.0  # annual budget cap
    cargo_demand_per_route: dict[str, float] = field(
        default_factory=lambda: {
            "route_a": 1_000_000.0,  # tonnes/year
            "route_b": 500_000.0,
            "route_c": 250_000.0,
        }
    )
    max_delay_pct: float = 0.05  # schedule reliability


@dataclass
class OptimisationConfig:
    """Optimisation engine parameters."""

    population_size: int = 100
    generations: int = 200
    crossover_rate: float = 0.85
    mutation_rate: float = 0.15
    quantum_prob: float = 0.10  # probability of quantum-inspired operator
    quantum_tunnel_scale: float = 0.30  # relative jump magnitude
    random_seed: int = 42
    nsga2_population: int = 200
    nsga2_generations: int = 300


@dataclass
class PredictionConfig:
    """Fuel consumption prediction parameters."""

    model_type: str = "xgboost"  # xgboost | random_forest | lightgbm | linear
    test_size: float = 0.20
    cv_folds: int = 5
    target_column: str = "fuel_consumption_tonnes"
    random_seed: int = 42


@dataclass
class ScenarioConfig:
    """Alternative fuel scenario defaults."""

    fuels: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "HFO": {"price_usd_tonne": 400.0, "co2_factor": 3.114, "sox_factor": 0.035},
            "VLSFO": {"price_usd_tonne": 600.0, "co2_factor": 3.114, "sox_factor": 0.001},
            "LNG": {"price_usd_tonne": 800.0, "co2_factor": 2.750, "sox_factor": 0.000},
            "methanol": {"price_usd_tonne": 900.0, "co2_factor": 1.375, "sox_factor": 0.000},
            "hydrogen": {"price_usd_tonne": 1500.0, "co2_factor": 0.0, "sox_factor": 0.0},
            "ammonia": {"price_usd_tonne": 1200.0, "co2_factor": 0.0, "sox_factor": 0.0},
        }
    )


@dataclass
class Config:
    """Top-level configuration container."""

    fleet: FleetConfig = field(default_factory=FleetConfig)
    optimisation: OptimisationConfig = field(default_factory=OptimisationConfig)
    prediction: PredictionConfig = field(default_factory=PredictionConfig)
    scenario: ScenarioConfig = field(default_factory=ScenarioConfig)

    # Paths
    raw_data_dir: Path = field(default_factory=lambda: RAW_DATA_DIR)
    processed_data_dir: Path = field(default_factory=lambda: PROCESSED_DATA_DIR)
    model_dir: Path = field(default_factory=lambda: MODEL_DIR)
    report_dir: Path = field(default_factory=lambda: REPORT_DIR)


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from a YAML file, falling back to defaults."""
    cfg = Config()
    if path is None:
        return cfg
    p = Path(path)
    if not p.exists():
        return cfg
    with p.open() as fh:
        raw = yaml.safe_load(fh) or {}
    return _apply_overrides(cfg, raw)


def _apply_overrides(cfg: Config, raw: dict[str, Any]) -> Config:
    """Recursively apply a YAML dict onto a Config dataclass."""
    import dataclasses

    for section, section_raw in raw.items():
        if not hasattr(cfg, section):
            continue
        section_obj = getattr(cfg, section)
        if not dataclasses.is_dataclass(section_obj):
            continue
        for key, value in section_raw.items():
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
    return cfg


def save_config(cfg: Config, path: str | Path) -> None:
    """Serialise configuration to YAML."""
    import dataclasses

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    raw: dict[str, Any] = {}
    for f in dataclasses.fields(cfg):
        value = getattr(cfg, f.name)
        if dataclasses.is_dataclass(value):
            raw[f.name] = {k: getattr(value, k) for k in dataclasses.fields(value)}
        elif isinstance(value, Path):
            raw[f.name] = str(value)
        else:
            raw[f.name] = value
    with p.open("w") as fh:
        yaml.safe_dump(raw, fh, sort_keys=False, default_flow_style=False)


# Module-level singleton
CONFIG = Config()