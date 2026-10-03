# Decisions.md — Architecture Decision Records

Lightweight ADRs. One entry per significant decision. Format:
**Context → Decision → Consequences → Alternatives considered.**

---

## ADR-001 — Choose SIH26138 over SIH26150

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Two candidate problem statements were shortlisted. SIH26150 was
an alternative green-tech PS; SIH26138 (Egreen Quanta) had only 126/500
submissions — the lowest viable in the software section — reducing
competition while keeping a serious sponsor.

**Decision.** Proceed with **SIH26138 — Quantum-Inspired Fuel Consumption
Prediction & Green Fleet Optimization**.

**Consequences.**
- Lower submission count → better odds.
- Requires handling a PDF dataset (extra ingestion work).
- Quantum-inspired framing must be honest to avoid judge pushback.

**Alternatives.** SIH26150 — rejected: higher saturation, weaker sponsor
alignment.

---

## ADR-002 — Apache-2.0 License

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Need a permissive license that allows judges to inspect, run,
and reuse.

**Decision.** Apache-2.0.

**Consequences.** Permissive, patent grant included, well understood by
evaluators. Compatible with all chosen dependencies.

**Alternatives.** MIT (simpler, no patent grant), GPL-3.0 (rejected:
copyleft complicates reuse).

---

## ADR-003 — XGBoost as Primary Fuel-Consumption Predictor

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Dataset is tabular, mixed categorical/numeric, likely a few
thousand rows. Need strong performance, fast training, feature importance.

**Decision.** **XGBoost** primary; Random Forest and LightGBM as ensemble
alternatives; Linear Regression as sanity baseline.

**Consequences.**
- Strong tabular performance out of the box.
- Built-in feature importance for explainability.
- Adds native-binary dependency (handled in Docker).

**Alternatives.** Neural nets (rejected: overkill, harder to explain, slower
to iterate in an 8-week window). CatBoost (rejected: similar to LightGBM,
no clear win).

---

## ADR-004 — "Quantum-Inspired" Framing Locked

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Sponsor name ("Egreen Quanta") and PS title both use "quantum".
A naive reading suggests real quantum hardware. We have none, and judges
will penalise overclaiming.

**Decision.** Every docstring, comment, UI label, and slide says
**"quantum-inspired classical metaheuristic"**. The operators we implement
are:
- Quantum rotation gate (QGA-style population update)
- Quantum tunnelling (adaptive large-jump mutation)
- Superposition-inspired probabilistic encoding

**Consequences.**
- Honest, defensible, still on-theme.
- Must police language across code, docs, and UI.

**Alternatives.** Real quantum SDKs (rejected: no hardware, no advantage at
this problem size). Silent ambiguity (rejected: reputational risk).

---

## ADR-005 — No Distributed / GPU Compute

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Optimisation instances are small (≈50 vessels). Judge machines
may be laptops.

**Decision.** Single-process CPU execution. `n_jobs=1` for stochastic
solvers (reproducibility). Gradient boosting may use `n_jobs=-1` for
training only.

**Consequences.**
- Runs anywhere.
- No Dask/Ray/Spark dependencies.
- Optimisation runs must finish ≤ 60 s per instance.

**Alternatives.** Ray/Dask (rejected: complexity, no payoff at this scale).

---

## ADR-006 — Dataclass Config + YAML Override Pattern

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Need tunables without scattering constants. Need reproducibility
via seed.

**Decision.** `@dataclass` config tree in `config.py` with `load_config` /
`save_config` YAML round-trip. `config/default.yaml` for shared defaults,
`config/local.yaml` (gitignored) for local overrides.

**Consequences.**
- Single import for any tunable.
- YAML is versionable and human-editable.
- Config snapshot written into every optimisation report.

**Alternatives.** Hydra (rejected: heavier than needed). Pydantic Settings
(considered; dataclasses are lighter and already used in `schema.py`).

---

## ADR-007 — Pydantic v2 at Every Module Boundary

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Raw dataset schema is unknown; we need early, loud failures.

**Decision.** Use Pydantic v2 models (`FleetRecord`, `VesselSpec`,
`FleetDataset`, API request/response models) at every boundary.

**Consequences.**
- Schema drift caught at ingestion, not deep in training.
- `FEATURE_COLUMNS` list is the single source of truth.
- One more dependency (already required by FastAPI).

**Alternatives.** Marshmallow (rejected: slower, less ergonomic). Plain
dataclasses + manual checks (rejected: boilerplate, weaker validation).

---

## ADR-008 — Streamlit + FastAPI (Not a Single SPA)

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Need a demo judges can drive AND a programmatic surface for
verification.

**Decision.** **Streamlit** for the interactive dashboard; **FastAPI** for
`/predict`, `/optimise`, `/scenarios`. Both call the same domain layer.

**Consequences.**
- Fast to build, easy to demo.
- Domain logic stays UI-agnostic.
- Two deployment targets (both in `docker-compose.yml`).

**Alternatives.** Gradio (rejected: weaker layout control). Full React SPA
(rejected: time sink).

---

## ADR-009 — Benchmark Baselines Fixed at Six

**Date:** 2026-10-02
**Status:** Accepted

**Context.** "Quantum-inspired" claims need credible baselines or they are
meaningless.

**Decision.** Every quantum-inspired solver is benchmarked against:
1. Random search (lower bound)
2. Greedy heuristic
3. LP relaxation (`scipy.optimize.linprog`)
4. Standard GA (no quantum ops)
5. Standard SA (no quantum ops)
6. NSGA-II (for multi-objective)

Metrics: best objective, iterations to converge, wall-clock runtime,
hypervolume (multi-objective).

**Consequences.**
- Credible claims.
- Extra implementation work in Week 7.

**Alternatives.** Fewer baselines (rejected: weak evidence).

---

## ADR-010 — Docker as Primary Demo Path, Colab as Fallback

**Date:** 2026-10-02
**Status:** Accepted

**Context.** Judge machines are unknown. Network may be unavailable.

**Decision.** `docker compose up` is the canonical demo. A
`notebooks/05_demo_colab.ipynb` fallback exists for hosts without Docker.

**Consequences.**
- Two demo paths to maintain.
- Offline-first requirement on both.

**Alternatives.** Docker only (rejected: risky). Colab only (rejected:
network dependency).

---

## ADR-010a — Synthetic Dataset as Fallback

**Date:** 2026-10-02
**Status:** Accepted (temporary)

**Context.** The Google Drive link in `Memory.md` §3 (`1h0pt48eJAq-...`)
points to the **problem statement PDF**, not a dataset. The sponsor did
not provide a real dataset. The project needs data to develop the
prediction model.

**Decision.** Generate a synthetic dataset using a physics-based generator
in `tests/conftest.py`. Save to `data/raw/dataset.csv` (5,000 rows, 50
vessels, 2023-2024). The generator is the single source of truth until a
real dataset is acquired.

**Consequences.**
- Development can proceed immediately.
- Model performance numbers are meaningless until real data arrives.
- The generator must be re-run (or replaced) when real data is available.
- All downstream code must treat `data/raw/dataset.csv` as a stub.

**Alternatives.** Block on sponsor (rejected: deadline is 2026-10-05).
Use a different dataset (rejected: off-domain, would break the problem
alignment).

---

## ADR-011 — TimeSeriesSplit over Random KFold for CV

**Date:** 2026-10-02
**Status:** Accepted

**Context.** The fuel consumption prediction model will be evaluated by
cross-validation. Real fleet data (when available) is temporal: vessels
operate over time, weather/load conditions drift, and future voyages must be
predicted from past ones. Random KFold would leak future information into
training folds, inflating metrics. We are generating synthetic data with an
`observation_date` column spanning ~2 years.

**Decision.** Use **`TimeSeriesSplit(n_splits=5)`** for all CV. The feature
matrix will be sorted by `observation_date` before splitting. No random
shuffling.

**Consequences.**
- Honest, production-realistic performance estimates.
- Requires `observation_date` in the feature matrix (added to schema, even if
  not a model feature).
- Slightly fewer training samples per fold vs random KFold (early folds
  smaller), but acceptable.

**Alternatives.** Random KFold with `shuffle=True` (rejected: temporal
leakage, optimistically biased metrics). GroupKFold by vessel_id (rejected:
doesn't respect temporal order, same leakage risk). Purged/Embargoed CV
(rejected: overkill for this scale; TimeSeriesSplit is standard and
sufficient).