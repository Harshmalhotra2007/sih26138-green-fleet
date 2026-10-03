# Testing.md — Testing Strategy

**Framework:** pytest (+ pytest-cov)
**Minimum coverage:** 70% on `src/sih26138/`
**Network:** tests must run fully offline

---

## 1. Test Pyramid

```
        ┌─────────────────────┐
        │  End-to-end (few)   │  CLI + API smoke
        ├─────────────────────┤
        │ Integration (some)  │  data → model → optimiser
        ├─────────────────────┤
        │     Unit (many)     │  every public function
        └─────────────────────┘
```

## 2. Layout

```
tests/
├── conftest.py            # shared fixtures (synthetic data, tmp dirs, seeds)
├── test_data.py           # loader, preprocessor, schema
├── test_models.py         # predictor fit/predict/save/load
├── test_optimisation.py   # GA, SA, QGA, QSA, NSGA-II, benchmark
├── test_api.py            # FastAPI TestClient
└── test_cli.py            # smoke test for `sih26138` entry point
```

## 3. Fixtures (`tests/conftest.py`)

```python
import numpy as np
import pandas as pd
import pytest

from src.sih26138.config import Config
from src.sih26138.data.schema import FEATURE_COLUMNS, TARGET_COLUMN


@pytest.fixture
def seed() -> int:
    return 42


@pytest.fixture
def synthetic_features(seed: int) -> pd.DataFrame:
    """Deterministic synthetic feature matrix matching FEATURE_COLUMNS."""
    rng = np.random.default_rng(seed)
    n = 500
    df = pd.DataFrame({
        "vessel_type": rng.choice(
            ["bulk", "tanker", "container", "general_cargo", "ro_ro"], n
        ),
        "dwt": rng.uniform(5_000, 150_000, n),
        "engine_power_kw": rng.uniform(2_000, 30_000, n),
        "engine_count": rng.integers(1, 3, n),
        "design_speed_knots": rng.uniform(10, 22, n),
        "hull_age_years": rng.uniform(0, 25, n),
        "cargo_load_tonnes": rng.uniform(0, 100_000, n),
        "cruising_speed_knots": rng.uniform(8, 20, n),
        "sea_distance_nm": rng.uniform(100, 5_000, n),
        "weather_factor": rng.uniform(0.8, 1.4, n),
        "load_factor": rng.uniform(0.3, 1.0, n),
        "route": rng.choice(["route_a", "route_b", "route_c"], n),
        "fuel_type": rng.choice(["HFO", "VLSFO", "LNG"], n),
    })
    df[TARGET_COLUMN] = (
        0.02 * df["engine_power_kw"]
        + 0.5 * df["cruising_speed_knots"]
        + 0.0001 * df["sea_distance_nm"]
        + rng.normal(0, 1, n)
    )
    return df


@pytest.fixture
def synthetic_dataset(synthetic_features) -> pd.DataFrame:
    return synthetic_features[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()


@pytest.fixture
def config() -> Config:
    cfg = Config()
    cfg.optimisation.population_size = 20
    cfg.optimisation.generations = 10
    cfg.fleet.fleet_size = 10
    return cfg
```

## 4. Test Categories

### 4.1 Data layer (`test_data.py`)
- `load_dataset` returns a `FleetDataset` with required columns.
- `validate_feature_matrix` raises on missing columns.
- `coerce_feature_matrix` converts numeric strings to numbers.
- `preprocess` produces no NaNs in numeric columns.
- `feature_engineering` is deterministic given the same seed.

### 4.2 Models (`test_models.py`)
- Each predictor trains on synthetic data and beats the mean baseline
  (R² > 0).
- `save` → `load` round-trip preserves predictions exactly.
- Registry lists and retrieves the saved model by name+version.
- Feature importances are non-negative and sum > 0.

### 4.3 Optimisation (`test_optimisation.py`)
- **Feasibility:** all returned solutions satisfy cargo demand, budget,
  fleet size.
- **Determinism:** same seed → identical best objective.
- **Monotonicity:** GA best-objective is non-increasing across generations.
- **Quantum wrapper:** `QuantumInspiredGA(quantum_prob=0)` ≡ `GA`.
- **Quantum wrapper:** `QuantumInspiredGA(quantum_prob=1)` still feasible.
- **NSGA-II:** Pareto front is non-dominated (no solution dominates
  another).
- **Benchmark:** running all baselines on a tiny instance completes
  without error and writes a JSON report.

### 4.4 API (`test_api.py`)
- `POST /predict` with valid payload returns 200 + predictions.
- `POST /predict` with missing column returns 422.
- `POST /optimise` with tiny instance returns 200 + a feasible solution.
- `POST /scenarios` returns one row per scenario.

### 4.5 CLI (`test_cli.py`)
- `sih26138 --help` exits 0.
- `sih26138 preprocess` on a fixture file produces `data/processed/`.

## 5. What We Do **Not** Test

- Streamlit UI internals (manual demo checklist instead — see §7).
- Exact numeric outputs of stochastic solvers (too brittle).
- Third-party library behaviour (XGBoost, SciPy).

## 6. Coverage Policy

- Run: `pytest --cov=src/sih26138 --cov-report=term-missing`.
- Gate: **70%** overall.
- Modules below 60% must be justified in the PR description.
- `config.py` and `schema.py` are expected at **> 90%** (pure logic).

## 7. Manual Demo Checklist (before submission)

- [ ] Fresh clone → `pip install -r requirements.txt` succeeds.
- [ ] `docker compose up` brings up dashboard (8501) + API (8000).
- [ ] Sample dataset loads without error.
- [ ] `/predict` returns sensible numbers.
- [ ] `/optimise` completes in ≤ 60 s.
- [ ] Pareto front renders.
- [ ] Scenario tab toggles fuels and updates charts.
- [ ] Benchmark tab shows quantum-inspired vs vanilla delta.
- [ ] All tabs work **offline**.
- [ ] Colab fallback notebook runs end-to-end.

## 8. Performance Tests

```python
def test_ga_runtime_small_instance(config):
    import time
    from src.sih26138.optimisation.ga import GeneticAlgorithm
    from src.sih26138.optimisation.problem import FleetProblem
    problem = FleetProblem.synthetic(n_vessels=10, seed=42)
    ga = GeneticAlgorithm(config.optimisation)
    t0 = time.perf_counter()
    ga.solve(problem)
    assert time.perf_counter() - t0 < 10.0
```

## 9. CI (when applicable)

```yaml
# .github/workflows/ci.yml (sketch)
- run: ruff check src tests
- run: black --check src tests
- run: mypy src
- run: pytest --cov=src/sih26138 --cov-fail-under=70
```

## 10. Bug-Fix Protocol

1. Reproduce with a failing test.
2. Fix the code.
3. Confirm the test passes.
4. Commit test + fix together (`fix: …` + regression test).

---

**Rule:** if you add a public function and there is no test for it, the task
is not done.