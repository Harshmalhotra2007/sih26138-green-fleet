# Agents.md — AI Coding Agent Guide

This file tells AI coding assistants (Cursor, Claude Code, Copilot, Aider,
etc.) how to work inside the **sih26138-green-fleet** repository.

**Read this file first, then `Memory.md`, `Rules.md`, and `Architecture.md`
before making any change.**

---

## 1. Project in One Paragraph

We are building a Python platform for SIH 2026 problem statement **SIH26138**
(sponsor: Egreen Quanta). It has three pillars:
(1) predict maritime fuel consumption from vessel specs + operating
conditions, (2) optimise fleet deployment using **quantum-inspired classical**
metaheuristics, and (3) benchmark those heuristics against conventional
baselines. Everything is exposed via a FastAPI service and a Streamlit
dashboard. The dataset lives in `data/raw/`; processed artifacts in
`data/processed/`; trained models in `models/`.

## 2. Golden Rules for Agents

1. **Never rename public APIs** (`load_dataset`, `preprocess`, `predict`,
   `optimise`, `benchmark`) without updating `Architecture.md` and adding an
   ADR to `Decisions.md`.
2. **Never introduce new heavy dependencies** (PyTorch, TensorFlow, Dask,
   Ray, quantum SDKs) without asking. The stack is deliberately light.
3. **All randomness goes through `config.random_seed`.** Do not call
   `random.seed()` or `np.random.seed()` ad hoc.
4. **Do not claim real quantum advantage.** Comments, docstrings, and UI
   labels must say "quantum-inspired" not "quantum".
5. **Keep the dependency direction:** `api`/`dashboard` → `models`/
   `optimisation`/`evaluation` → `data` → `config`. Never import upward.
6. **Every new module gets a test in `tests/`.** Follow `Testing.md`.
7. **Prefer dataclasses/Pydantic** over raw dicts for anything crossing a
   module boundary.
8. **No notebooks in `src/`.** Notebooks live in `notebooks/` only.
9. **Config, not constants.** Anything tunable goes in `config/default.yaml`
   and `src/sih26138/config.py`.
10. **Commit messages:** `feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
    `chore:` (Conventional Commits).

## 3. Task Playbook

### Adding a new optimiser
1. Create `src/sih26138/optimisation/<name>.py`.
2. Subclass or implement against the `OptimisationProblem` protocol in
   `problem.py`.
3. Register it in `optimisation/__init__.py`.
4. Add a benchmark entry in `optimisation/benchmark.py`.
5. Add tests: convergence, constraint satisfaction, determinism with seed.
6. Add a row to `Architecture.md` §"Optimisers".

### Adding a new predictor
1. Create or extend `models/predictor.py` with a class implementing
   `fit`, `predict`, `save`, `load`.
2. Register in `models/registry.py`.
3. Add to `PredictionConfig.model_type` enum.
4. Add a test that trains on synthetic data and checks R² > 0.

### Changing the dataset schema
1. Update `data/schema.py` Pydantic models.
2. Update `FEATURE_COLUMNS` and `TARGET_COLUMN`.
3. Update `data/preprocessor.py` to emit the new columns.
4. Add a schema-version note to `Memory.md` §"Dataset".
5. Add an ADR to `Decisions.md`.

## 4. What Not to Touch Without Explicit Instruction

- `config.py` dataclass field names (they are read by YAML).
- `pyproject.toml` `[project.scripts]` entry point.
- The `QUANTUM_*` naming convention (it is part of our framing).
- `data/raw/` — treat as read-only; never commit large binaries.

## 5. Where to Look

| Question | File |
|---|---|
| Why was X chosen? | `Decisions.md` |
| How is Y wired? | `Architecture.md` |
| What are the coding conventions? | `Rules.md` |
| What is the current state / TODO? | `Memory.md` |
| How do I test Z? | `Testing.md` |
| What does the product do? | `PRD.md` |
| What does the UI look like? | `Design.md` |

## 6. Output Expectations

When you finish a task, produce:
1. A diff of changed files.
2. A one-paragraph summary.
3. Any new ADR entries (append to `Decisions.md`).
4. Any `Memory.md` updates (active branch, TODO status).
5. Suggested commit message.