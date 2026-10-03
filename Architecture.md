# Architecture.md — System Architecture

**Version:** 0.1.0
**Last updated:** 2026-10-02

---

## 1. Context

```
┌────────────────────────┐        ┌───────────────────────────┐
│  Fleet operator /      │        │  SIH Judges / Evaluators  │
│  sustainability team   │        │                           │
└───────────┬────────────┘        └─────────────┬─────────────┘
            │                                   │
            ▼                                   ▼
     ┌──────────────────────────────────────────────────┐
     │        sih26138-green-fleet platform             │
     │  Streamlit dashboard  +  FastAPI service         │
     └──────────────────────────────────────────────────┘
                        │
                        ▼
     ┌──────────────────────────────────────────────────┐
     │  Offline artifacts: dataset, models, reports     │
     └──────────────────────────────────────────────────┘
```

No external services at runtime. Optional network only for initial dataset
download.

## 2. Container / Module View

```
src/sih26138/
├── config.py            # dataclass config + YAML load/save
├── data/                # ingestion, validation, preprocessing
│   ├── loader.py
│   ├── preprocessor.py
│   └── schema.py        # Pydantic contracts + FEATURE_COLUMNS
├── models/              # fuel-consumption predictors
│   ├── predictor.py     # XGB/RF/LGBM/Linear
│   ├── baseline.py      # naive baselines (mean, per-type mean)
│   └── registry.py      # save/load/version models
├── optimisation/
│   ├── problem.py       # OptimisationProblem protocol
│   ├── ga.py            # Genetic Algorithm
│   ├── sa.py            # Simulated Annealing
│   ├── quantum_inspired.py  # QGA / QSA wrappers
│   ├── nsga2.py         # multi-objective
│   └── benchmark.py     # comparison harness
├── evaluation/
│   ├── metrics.py       # fuel, cost, emissions, schedule
│   ├── scenarios.py     # alt-fuel substitution
│   └── reporting.py     # tables + charts
├── api/
│   ├── main.py          # FastAPI app factory
│   ├── routes/          # predict, optimise, scenarios
│   └── schemas.py       # request/response Pydantic
├── dashboard/
│   └── streamlit_app.py
└── cli.py               # `sih26138` entry point
```

### Dependency direction (enforced)

```
api / dashboard
      │
      ▼
models / optimisation / evaluation
      │
      ▼
     data
      │
      ▼
    config
```

**Rule:** imports only flow downward. A `data` module must never import
`models`. `config` imports nothing from the package.

## 3. Component Responsibilities

| Component | Owns | Must not |
|---|---|---|
| `config.py` | Tunables, paths, seeds | Business logic |
| `data.loader` | Reading raw files, shape/type validation | Feature engineering |
| `data.preprocessor` | Cleaning, feature engineering, encoding | Training |
| `data.schema` | Pydantic contracts, column lists | I/O |
| `models.predictor` | fit/predict/save/load | Optimisation |
| `models.registry` | Versioned persistence | Model math |
| `optimisation.problem` | Decision vars, objectives, constraints | Solver logic |
| `optimisation.ga/sa/nsga2` | Search algorithms | Problem definition |
| `optimisation.quantum_inspired` | Quantum-inspired operators | Full solvers (wrappers only) |
| `optimisation.benchmark` | Run solvers × instances, collect metrics | Visualisation |
| `evaluation.metrics` | Numeric KPIs | Chart styling |
| `evaluation.reporting` | Tables + figures | Metric math |
| `api` | HTTP surface | Domain logic |
| `dashboard` | UI | Domain logic |

## 4. Data Flow

### Training
```
data/raw/*.pdf|.csv
   → loader.load_dataset()
   → schema.FleetDataset (validated)
   → preprocessor.preprocess() + feature_engineering()
   → data/processed/features.parquet
   → models.predictor.fit()
   → models.registry.save()
```

### Inference
```
HTTP POST /predict  →  api.schemas.PredictRequest
   →  loader.load_external_fuel_properties()
   →  preprocessor.feature_engineering()
   →  models.registry.load()
   →  predictor.predict()
   →  PredictResponse
```

### Optimisation
```
config.optimisation + config.fleet
   → optimisation.problem.FleetProblem
   → solver (ga | sa | quantum_inspired | nsga2)
   → evaluation.metrics
   → evaluation.reporting
   → reports/optimisation/<run_id>.json
```

## 5. Optimisers (registry)

| Name | Type | Objectives | Notes |
|---|---|---|---|
| `random_search` | Baseline | 1 | Lower bound |
| `greedy` | Baseline | 1 | Cheapest vessel first |
| `lp_relaxation` | Baseline | 1 | Continuous relaxation via `scipy.optimize.linprog` |
| `ga` | Metaheuristic | 1 | Standard GA |
| `sa` | Metaheuristic | 1 | Standard SA |
| `quantum_ga` | Quantum-inspired | 1 | GA + rotation + tunnelling |
| `quantum_sa` | Quantum-inspired | 1 | SA + tunnelling |
| `nsga2` | Metaheuristic | 3 | Fuel / cost / emissions |

## 6. Prediction Models (registry)

| Name | Backend | Role |
|---|---|---|
| `linear` | sklearn | Sanity baseline |
| `random_forest` | sklearn | Robust baseline |
| `lightgbm` | lightgbm | Fast gradient boosting |
| `xgboost` | xgboost | **Primary** |

## 7. Persistence Layout

```
data/raw/                 # read-only inputs
data/processed/           # features.parquet, splits
data/external/            # fuel properties, emission factors
models/                   # <model>-<version>.joblib + metadata.json
reports/
├── benchmarks/           # benchmark_<date>.json
├── optimisation/         # run_<uuid>.json
└── figures/              # *.png for slides
```

## 8. Concurrency & Performance

- Single-process; no distributed training.
- Optimisation runs are CPU-bound and single-threaded by default
  (`n_jobs=1`) for reproducibility. Multithreading optional via config.
- XGBoost/LightGBM allowed `n_jobs=-1` for training only.

## 9. Reproducibility

- `config.random_seed` seeds Python, NumPy, and framework RNGs.
- Every optimisation run writes its full config + seed + git SHA into the
  report JSON.
- Dataset hash (SHA-256) recorded in `data/processed/manifest.json`.

## 10. Extensibility Points

- **New solver:** implement `OptimisationProblem` + register.
- **New fuel:** add to `ScenarioConfig.fuels` and colour map in `Design.md`.
- **New metric:** add to `evaluation/metrics.py`; expose in benchmark table.
- **New model:** implement fit/predict/save/load; register.

## 11. Deployment

- **Local:** `make run-dashboard`, `make run-api`.
- **Docker:** `docker compose up` exposes Streamlit (8501) + API (8000).
- **Fallback:** `notebooks/05_demo_colab.ipynb` for judge machines without
  Docker.