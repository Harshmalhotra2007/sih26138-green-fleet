"""Pytest configuration and synthetic data generator for SIH26138.

Since the sponsor did not provide a real dataset, this module generates
physically plausible synthetic fleet voyage records for development and
testing. The generator respects maritime engineering relationships:
- Fuel consumption ~ cargo_load^0.7 * speed^3 * distance * weather_factor
- Different vessel types have different base consumption profiles
- Alternative fuels have different emission factors
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Deterministic seed
RNG = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

VESSEL_TYPES = [
    # type, dwt, engine_kw, engines, design_speed, base_fuel_t_per_day
    ("bulk", 80000, 12000, 1, 14.5, 25.0),
    ("tanker", 150000, 20000, 1, 15.0, 35.0),
    ("container", 100000, 45000, 1, 22.0, 40.0),
    ("general_cargo", 30000, 6000, 1, 16.0, 8.0),
    ("ro_ro", 25000, 15000, 1, 18.0, 7.0),
]

ROUTES = {
    "route_a": 4500.0,   # nm
    "route_b": 6200.0,
    "route_c": 2800.0,
}

FUEL_TYPES = [
    "HFO", "VLSFO", "LNG", "methanol", "hydrogen", "ammonia"
]

FUEL_EMISSION_FACTORS = {
    "HFO": {"co2": 3.114, "sox": 0.035},
    "VLSFO": {"co2": 3.114, "sox": 0.001},
    "LNG": {"co2": 2.750, "sox": 0.000},
    "methanol": {"co2": 1.375, "sox": 0.000},
    "hydrogen": {"co2": 0.0, "sox": 0.0},
    "ammonia": {"co2": 0.0, "sox": 0.0},
}

FUEL_BASE_CONSUMPTION = {
    "HFO": 1.0,
    "VLSFO": 1.02,     # slightly less energy dense
    "LNG": 0.95,       # cleaner burn
    "methanol": 1.15,
    "hydrogen": 0.8,
    "ammonia": 0.9,
}


def generate_vessel_fleet(n_vessels: int = 50) -> pd.DataFrame:
    """Generate a fleet of vessels with static specs."""
    vessels = []
    for i in range(n_vessels):
        # RNG.choice on a list of tuples returns an array of strings, so
        # index the list directly instead.
        vtype, dwt, eng_kw, eng_cnt, des_spd, base_fuel = VESSEL_TYPES[RNG.integers(0, len(VESSEL_TYPES))]
        hull_age = RNG.uniform(0, 25)
        fuel_type = str(FUEL_TYPES[RNG.choice(len(FUEL_TYPES), p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.05])])
        vessels.append({
            "vessel_id": f"VES_{i:04d}",
            "vessel_type": vtype,
            "dwt": round(dwt * RNG.uniform(0.8, 1.2), 1),
            "engine_power_kw": round(eng_kw * RNG.uniform(0.9, 1.1), 1),
            "engine_count": eng_cnt,
            "design_speed_knots": round(des_spd * RNG.uniform(0.95, 1.05), 1),
            "hull_age_years": round(hull_age, 1),
            "fuel_type": fuel_type,
            "base_fuel_t_per_day": base_fuel,
        })
    return pd.DataFrame(vessels)


def generate_voyages(
    vessels: pd.DataFrame,
    n_voyages: int = 5000,
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-31",
) -> pd.DataFrame:
    """Generate synthetic voyage records for the fleet.

    Physics-based formula:
    fuel = base * (cargo/dwt)^0.7 * (speed/design_speed)^3 * distance * weather * fuel_factor * age_factor
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days
    records = []

    for _ in range(n_voyages):
        v = vessels.sample(1, random_state=RNG.integers(0, 2**31)).iloc[0]
        route = str(RNG.choice(list(ROUTES.keys())))
        distance = ROUTES[route] * RNG.uniform(0.95, 1.05)

        cargo = RNG.uniform(0.3, 1.0) * v["dwt"]
        speed = RNG.uniform(0.85, 1.0) * v["design_speed_knots"]
        weather = RNG.lognormal(mean=0.0, sigma=0.15)  # lognormal around 1.0
        weather = np.clip(weather, 0.7, 1.8)
        load_factor = cargo / v["dwt"]

        # Voyage duration in days = distance / (speed * 24)
        voyage_days = distance / (speed * 24.0)

        # Base fuel consumption in tonnes/day at design speed, full load
        base_t_per_day = v["base_fuel_t_per_day"]

        # Physics scaling: fuel ~ load^0.7 * speed^3 * weather * fuel_factor * age_factor
        fuel = (
            base_t_per_day
            * (load_factor ** 0.7)
            * ((speed / v["design_speed_knots"]) ** 3)
            * weather
            * FUEL_BASE_CONSUMPTION[v["fuel_type"]]
            * (1.0 + 0.005 * v["hull_age_years"])  # hull fouling
            * voyage_days
        )
        fuel = max(0.1, fuel * RNG.lognormal(mean=0.0, sigma=0.08))  # noise

        # Random date
        obs_date = start + timedelta(days=int(RNG.integers(0, total_days)))
        # Ensure temporal order by vessel (sort later)
        records.append({
            "vessel_id": v["vessel_id"],
            "observation_date": obs_date.strftime("%Y-%m-%d"),
            "cargo_load_tonnes": round(cargo, 1),
            "cruising_speed_knots": round(speed, 2),
            "sea_distance_nm": round(distance, 1),
            "fuel_consumption_tonnes": round(fuel, 3),
            "weather_factor": round(weather, 3),
            "load_factor": round(load_factor, 3),
            "route": route,
            "fuel_type": v["fuel_type"],
        })

    df = pd.DataFrame(records)
    # Merge vessel static specs into voyage records (one row per voyage).
    # Drop the per-voyage fuel_type (already in vessels) to avoid duplicate columns.
    df = df.drop(columns=["fuel_type"])
    df = df.merge(vessels, on="vessel_id", how="left")
    # Drop helper column used only for physics
    df = df.drop(columns=["base_fuel_t_per_day"])
    # Sort by date then vessel for TimeSeriesSplit
    df = df.sort_values(["observation_date", "vessel_id"]).reset_index(drop=True)
    return df


def generate_dataset(
    n_vessels: int = 50,
    n_voyages: int = 5000,
    output_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate complete dataset: vessels + voyages.

    Returns (vessels_df, voyages_df). If output_path provided, saves CSV.
    """
    vessels = generate_vessel_fleet(n_vessels)
    voyages = generate_voyages(vessels, n_voyages)

    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        voyages.to_csv(p, index=False)
        print(f"Saved {len(voyages)} voyages to {p}")

    return vessels, voyages


# Convenience function for direct CLI use
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic fleet dataset")
    parser.add_argument("--vessels", type=int, default=50)
    parser.add_argument("--voyages", type=int, default=5000)
    parser.add_argument("--output", type=str, default="data/raw/dataset.csv")
    args = parser.parse_args()

    vessels, voyages = generate_dataset(args.vessels, args.voyages, args.output)
    print(f"Generated {len(vessels)} vessels, {len(voyages)} voyages")
    print(voyages.dtypes)
    print(voyages.head())