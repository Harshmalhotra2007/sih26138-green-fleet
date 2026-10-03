# Rules.md — Engineering Rules

Binding conventions for all contributors (human or AI). Deviations require an
ADR in `Decisions.md`.

---

## 1. Language & Style

- **Python ≥ 3.10.** Use `from __future__ import annotations` in every module.
- **Line length:** 100 (ruff + black enforced).
- **Formatting:** `black` + `ruff` via pre-commit.
- **Typing:** PEP 604 unions (`int | None`), never `Optional[int]` in new code.
- **Imports:** stdlib → third-party → first-party, alphabetised, one blank
  line between groups.
- **Naming:** `snake_case` functions/vars, `PascalCase` classes,
  `UPPER_SNAKE` constants, leading `_` for private.
- **Docstrings:** Google-style on every public module, class, and function.
  One-line summary, then `Args:`, `Returns:`, `Raises:` when applicable.

## 2. Architecture Rules

1. **Dependency direction:** `api`/`dashboard` → `models`/`optimisation`/
   `evaluation` → `data` → `config`. No upward imports.
2. **No circular imports.** If you need one, you have a design problem — split.
3. **Pydantic for boundaries.** Anything crossing a module boundary uses a
   Pydantic model or dataclass, never a bare dict.
4. **Config over constants.** Tunables live in `config.py` + YAML.
5. **Pure functions where possible.** Side effects confined to `loader`,
   `registry`, `reporting`, `api`.

## 3. Randomness

- **Never** call `random.seed()` or `np.random.seed()` outside `config.py`.
- Use `config.random_seed` and thread it through.
- Every stochastic function accepts an optional `seed: int | None`.

## 4. Error Handling

- Raise typed exceptions (`ValueError`, `SchemaError` subclass).
- Never bare `except:` or `except Exception: pass`.
- Log via `logging`, not `print()`, in `src/`. `print()` allowed only in
  `cli.py` and notebooks.

## 5. Quantum Framing (non-negotiable)

- Say **"quantum-inspired"**, never "quantum" alone.
- Docstrings must state: *"classical metaheuristic augmented with
  quantum-inspired operators; not executed on quantum hardware."*
- UI labels must match. This protects us from judge pushback.

## 6. Data Rules

- `data/raw/` is read-only. Never modify, never commit files > 5 MB.
- Processed artifacts go in `data/processed/` (gitignored).
- Every dataset change updates `data/schema.py` + `Memory.md` §Dataset.
- Column names are `snake_case` and exactly match `FEATURE_COLUMNS`.

## 7. Testing Rules

- Every new public function gets a test.
- Every bug fix gets a regression test.
- Tests must not hit the network.
- Use `pytest` fixtures from `tests/conftest.py`.
- Minimum coverage: **70%** on `src/sih26138/`.

## 8. Git Rules

- Branch naming: `feat/…`, `fix/…`, `docs/…`, `exp/…`.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
  `chore:`).
- One logical change per PR/commit.
- Never commit: `.env`, `data/raw/*`, `models/*.joblib`, large binaries.
- Update `Memory.md` and (if architectural) `Decisions.md` in the same PR.

## 9. Notebook Rules

- Notebooks in `notebooks/` only, numbered `01_…`, `02_…`.
- Must run top-to-bottom on a clean kernel.
- No business logic in notebooks — import from `src/sih26138/`.
- Clear outputs before commit (or use `nbstripout`).

## 10. Dependency Rules

Adding a dependency requires:
1. Justification in the PR description.
2. Pin with `>=x.y` in `pyproject.toml` **and** `requirements.txt`.
3. Update `Dockerfile` if runtime-relevant.
4. Approval if it's > 20 MB or pulls native binaries.

Forbidden without explicit approval: PyTorch, TensorFlow, JAX, Qiskit, Cirq,
PennyLane, Dask, Ray, Spark.

## 11. Security & Ethics

- No hardcoded credentials. Use `.env` (gitignored) + `.env.example`.
- No scraping of paywalled sources.
- No misleading claims about performance or quantum behaviour.

## 12. Definition of Done

A task is done when:
- [ ] Code implements the requirement.
- [ ] Tests pass (`pytest`) and coverage ≥ 70%.
- [ ] `ruff` and `black` clean.
- [ ] Docstrings on public APIs.
- [ ] `Memory.md` updated.
- [ ] ADR added if architectural.
- [ ] Demo path still works end-to-end.