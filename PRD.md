# PRD — SIH26138: Quantum-Inspired Fuel Consumption Prediction & Green Fleet Optimization

**Sponsor:** Egreen Quanta
**Theme:** Clean & Green Technology
**Problem Statement ID:** SIH26138
**Submission Deadline:** 5 October 2026
**Current Submissions:** 126/500 (lowest viable in software section)
**Owner:** SIH 2026 Team
**Status:** Active development
**Version:** 0.1.0

---

## 1. Problem Statement

Maritime shipping operators must simultaneously reduce fuel consumption, cut
operating costs, and comply with tightening IMO emission regulations
(2030/2050). Fleet deployment decisions — vessel mix, capacity, cruising
speed, and alternative fuel adoption — are interdependent, non-linear, and
combinatorially hard. Conventional planning tools either ignore alternative
fuels or rely on greedy heuristics that miss globally better solutions.

## 2. Goal

Build a software platform that:

1. **Predicts** fuel consumption (tonnes) for a vessel given its
   specifications and operating conditions.
2. **Optimises** fleet deployment decisions (vessel mix, capacity, cruising
   speed, fuel type, shore-power capability) against three objectives:
   total fuel, total cost, and lifecycle GHG emissions.
3. **Benchmarks** quantum-inspired metaheuristics against conventional
   methods (greedy, random, LP relaxation, standard GA/SA, NSGA-II) using
   reproducible metrics.

## 3. Non-Goals

- Real-time vessel telemetry ingestion (out of scope for hackathon).
- AIS integration or live weather feeds.
- Financial-grade cost accounting or hedging.
- Physically accurate CFD/engine simulation.
- Claiming "true" quantum computing — we implement *quantum-inspired
  classical* metaheuristics only.

## 4. Users & Personas

| Persona | Needs | How the product helps |
|---|---|---|
| Fleet planner | Reduce annual fuel & cost | Optimiser returns Pareto front of vessel mix + speed + fuel |
| Sustainability officer | Report GHG trajectory | Scenario analysis quantifies tCO2e per fuel policy |
| Marine engineer | Understand drivers of consumption | Feature-importance + per-vessel predictions |
| Judge / evaluator | Verify claims in 2 minutes | Streamlit demo: upload CSV → predict → optimise → chart |

## 5. Functional Requirements

### FR-1 Data Ingestion
- Load raw dataset from `data/raw/` (PDF → CSV/Parquet).
- Validate against `FleetRecord` / `VesselSpec` Pydantic schemas.
- Produce a cleaned, feature-engineered dataset in `data/processed/`.

### FR-2 Fuel Consumption Prediction
- Train at least three models: XGBoost (primary), Random Forest, LightGBM.
- Include Linear Regression as a sanity baseline.
- Report MAE, RMSE, R² with k-fold (or time-series) split.
- Persist best model to `models/` with a versioned registry entry.

### FR-3 Single-Objective Optimisation
- GA and SA minimise annual fuel consumption over the fleet.
- Decision variables: vessel type, capacity, cruising speed, fuel type,
  shore-power flag (per vessel).
- Constraints: cargo demand per route, budget, max delay %, fleet size.

### FR-4 Quantum-Inspired Operators
- Quantum rotation gate for population diversity (QGA-style).
- Quantum tunnelling operator for escaping local optima.
- Superposition-inspired probabilistic encoding.
- Exposed as drop-in wrappers around GA and SA (`quantum_prob` parameter).

### FR-5 Multi-Objective Optimisation
- NSGA-II producing a 3-objective Pareto front: fuel, cost, emissions.
- Hypervolume indicator for spread quality.

### FR-6 Scenario Analysis
- Fuel substitution: HFO → VLSFO → LNG → methanol → hydrogen → ammonia.
- Shore-power capability on/off.
- Output: cost/emissions deltas per scenario.

### FR-7 Benchmarking
- Compare quantum-inspired vs random, greedy, LP relaxation, standard GA,
  standard SA, NSGA-II.
- Metrics: best objective, convergence iterations, runtime, HV spread.

### FR-8 API & Dashboard
- FastAPI endpoints: `/predict`, `/optimise`, `/scenarios`.
- Streamlit dashboard with 4 tabs: Upload & Predict, Optimise Fleet,
  Scenario Analysis, Benchmark Results.
- Dockerised for judge-machine portability.

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Reproducibility | All randomness seeded via `config.random_seed` |
| Portability | Runs offline; only optional network is dataset download |
| Performance | Single optimisation run ≤ 60 s on a laptop CPU |
| Explainability | Feature importances + per-vessel predictions exposed |
| Licensing | Apache-2.0 |
| Documentation | README + these docs + docstrings on every public function |
| Testing | ≥ 70% coverage on `src/sih26138/` |

## 7. Success Metrics

- **Prediction:** XGBoost test R² ≥ 0.85 (or best available on dataset).
- **Optimisation:** Quantum-inspired GA beats standard GA on ≥ 1 benchmark
  instance without exceeding 2× runtime.
- **Demo:** End-to-end run in ≤ 3 minutes on a fresh Docker container.
- **Submission:** Idea PPT + working demo + repo + report + 3–5 min video.

## 8. Milestones (8-Week Plan)

| Week | Milestone | Exit criteria |
|---|---|---|
| 1 | Data ingestion & EDA | `01_eda.ipynb` committed; schema documented |
| 2 | Baseline predictors | XGBoost/RF/LightGBM trained, CV metrics logged |
| 3 | Single-objective optimiser | GA + SA minimise fuel; constraints enforced |
| 4 | Quantum-inspired operators | QGA/QSA implemented; benchmarked vs vanilla |
| 5 | NSGA-II | 3-objective Pareto front produced |
| 6 | Scenario analysis | 6 fuels × shore-power grid evaluated |
| 7 | Benchmark suite | Full comparison table + convergence charts |
| 8 | Dashboard + demo | Streamlit + FastAPI + Docker + video |

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Dataset schema unclear | Blocks Week 1–2 | Deep EDA; synthetic fallback data |
| "Quantum" overclaim backfires | Judge penalty | Frame explicitly as quantum-*inspired* |
| Multi-objective slow | Misses Week 5 | Weighted-sum first, then NSGA-II |
| Missing alt-fuel data | Weak scenarios | Use IMO/public emission factors; document |
| Demo failure on judge host | Disqualification | Docker + Colab notebook backup |

## 10. Out-of-Scope for v0.1.0

- Multi-user auth, cloud deployment, billing.
- Real-time AIS/weather.
- Reinforcement learning controllers.