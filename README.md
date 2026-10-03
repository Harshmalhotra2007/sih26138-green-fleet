# SIH26138 — Quantum-Inspired Fuel Consumption Prediction & Green Fleet Optimization

**Sponsor:** Egreen Quanta  
**Theme:** Clean & Green Technology  
**Problem Statement:** SIH26138  

---

## Overview

SIH26138 Green Fleet Optimization is an AI-driven platform for:
1. **Predicting** fuel consumption across vessel types and operating conditions.
2. **Optimising** fleet deployment (vessel mix, cargo loading, cruising speed, and alternative fuel transitions).
3. **Benchmarking** quantum-inspired metaheuristics against conventional optimization algorithms (Genetic Algorithm, Simulated Annealing, NSGA-II).

---

## Architecture & Project Structure

```text
sih26138-green-fleet/
├── data/
│   ├── raw/                  # Raw dataset (CSV)
│   ├── processed/            # Cleaned data and feature matrices
│   └── external/             # Fuel pricing and emission profiles
├── src/
│   └── sih26138/
│       ├── config.py         # Central dataclass & YAML configuration
│       └── data/
│           ├── schema.py     # Pydantic data contracts
│           ├── loader.py     # Dataset loader and manifest hashing
│           └── preprocessor.py # Data cleaning and feature engineering
├── tests/
│   ├── conftest.py           # Physics-based synthetic data generator
│   └── test_data.py          # Data layer test suite
├── pyproject.toml            # Project packaging metadata
├── requirements.txt          # Core dependencies
└── README.md
```

---

## Getting Started

### Installation

```bash
git clone https://github.com/Harshmalhotra2007/sih26138-green-fleet.git
cd sih26138-green-fleet
pip install -r requirements.txt
```

### Running Tests

```bash
pytest
```

---

## License

Apache-2.0
