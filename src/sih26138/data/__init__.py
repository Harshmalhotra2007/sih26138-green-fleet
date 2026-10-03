"""Data layer: loading, validation, and preprocessing."""

from .loader import load_dataset, load_external_fuel_properties
from .preprocessor import preprocess, feature_engineering
from .schema import FleetRecord, FleetDataset

__all__ = ["load_dataset", "load_external_fuel_properties", "preprocess", "feature_engineering", "FleetRecord", "FleetDataset"]