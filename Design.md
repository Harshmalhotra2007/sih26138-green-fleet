# Design.md — System & UX Design

Covers **what** the product looks like and **how users experience it**.
For internal wiring see `Architecture.md`.

---

## 1. Design Principles

1. **Judge-verifiable in 2 minutes.** Every screen must answer "does it work?"
   without reading docs.
2. **Open data in, honest numbers out.** No hidden magic; show inputs,
   assumptions, and outputs side by side.
3. **Explainable by default.** Feature importances, constraint slacks, and
   Pareto fronts are first-class UI elements.
4. **Offline-first.** Demo must run without internet.
5. **Quantum-honest.** Every mention says "quantum-inspired classical".

## 2. Information Architecture

```
Streamlit Dashboard (default entry point)
├── Tab 1 — Upload & Predict
├── Tab 2 — Optimise Fleet
├── Tab 3 — Scenario Analysis
└── Tab 4 — Benchmark Results

FastAPI Service (programmatic)
├── POST /predict
├── POST /optimise
└── POST /scenarios
```

## 3. Screen-by-Screen Design

### Tab 1 — Upload & Predict
- **Input:** CSV upload *or* "use bundled sample" button.
- **Validation:** schema check against `FEATURE_COLUMNS`; red banner on
  missing columns.
- **Output:**
  - Table: `vessel_id | predicted_fuel_tonnes | ±MAE`
  - Bar chart: top-10 vessels by predicted consumption.
  - Feature-importance plot (SHAP-style or XGBoost gain).
- **Empty state:** "Upload a CSV or click *Use sample dataset*."

### Tab 2 — Optimise Fleet
- **Inputs (sidebar):**
  - Algorithm: GA / SA / Quantum-GA / Quantum-SA / NSGA-II
  - Population size, generations, seed
  - Budget slider, fleet-size slider
  - Route demand table (editable)
- **Output:**
  - Progress bar during run.
  - Pareto front (2D or 3D scatter): fuel vs cost vs emissions.
  - Selected solution card: vessel mix table, speed, fuel, cost, tCO2e.
  - Convergence plot: best objective vs generation.
- **Failure state:** "No feasible solution — relax budget or demand."

### Tab 3 — Scenario Analysis
- **Inputs:** fuel-mix sliders (HFO/VLSFO/LNG/methanol/H2/NH3), shore-power
  toggle, carbon-price input.
- **Output:**
  - Grouped bar chart: cost & emissions per scenario.
  - Delta table vs baseline HFO.
  - Sankey-style flow of fuel substitution (optional stretch).

### Tab 4 — Benchmark Results
- **Inputs:** precomputed JSON in `reports/benchmarks/`.
- **Output:**
  - Table: algorithm × {best obj, iterations, runtime, HV}.
  - Boxplots of objective across seeds.
  - "Quantum-inspired vs vanilla" headline deltas.

## 4. API Contract (excerpt)

```json
POST /predict
Request:
{
  "records": [
    {"vessel_id":"V001","vessel_type":"bulk","dwt":75000,
     "engine_power_kw":12000,"cruising_speed_knots":13.5,
     "cargo_load_tonnes":60000,"sea_distance_nm":1200,
     "weather_factor":1.0,"load_factor":0.8,"fuel_type":"HFO"}
  ]
}
Response:
{
  "predictions": [
    {"vessel_id":"V001","fuel_consumption_tonnes":42.7,"model":"xgboost-v0.1.0"}
  ]
}
```

Full request/response models live in `src/sih26138/api/schemas.py`.

## 5. Visual Language

- **Palette:** deep navy (#0B2545), teal accent (#1B998B), warm amber
  (#F4A259) for warnings, slate greys for text.
- **Typography:** system sans (Inter if available); monospace for numbers.
- **Charts:** Matplotlib/Seaborn, consistent colour per fuel type.
- **Icons:** emoji only where they aid scanning (🌊 🚢 ⚡), never decorative.

## 6. Fuel Colour Map (use everywhere)

| Fuel | Hex |
|---|---|
| HFO | `#3B3B3B` |
| VLSFO | `#6B6B6B` |
| LNG | `#2A9D8F` |
| Methanol | `#E9C46A` |
| Hydrogen | `#4CC9F0` |
| Ammonia | `#9D4EDD` |

## 7. Accessibility

- Colour-blind-safe palettes (viridis / cividis fallback).
- All charts have text alternatives in the caption.
- No information conveyed by colour alone.

## 8. Demo Script (3 minutes)

1. **0:00–0:30** — Open dashboard, click *Use sample dataset*.
2. **0:30–1:00** — Show predictions table + feature importance.
3. **1:00–2:00** — Run Quantum-GA optimisation; show Pareto front.
4. **2:00–2:30** — Switch to Scenario tab; toggle methanol; show delta.
5. **2:30–3:00** — Benchmark tab: quantum-inspired beats vanilla GA.