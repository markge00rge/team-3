# Persistent saved runs

See [SAVED_RUNS_GUIDE.md](SAVED_RUNS_GUIDE.md) for named optimizations, local SQLite
history, read-only historical configurations, two-run comparisons and exact
Operating Expenses / Total Delivery Cost cards.

# V6 update

Active formulation: [V6_SCOPE.md](V6_SCOPE.md). The application supports optional
additional-crew dismissal/retraining and six material prices. Five financial cards
reconcile operating expense, additional A/C orders and production-linked B materials
to Total Delivery Cost. Earlier operating-only financial totals below are historical.

# P&G Venus Supply Chain Optimizer

## Cairo Plant Supply Chain Optimizer — interactive Venus application

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

Open http://localhost:8501. Run Original Case executes a **new real V5 MILP**;
Customize Parameters opens seven prefilled sections. Dashboards, comparisons,
CSV/Excel exports and reloadable scenario JSON use checked solver output.
See [APP_GUIDE.md](APP_GUIDE.md) for the editable-field allowlist, locked fields,
validation, worker execution, demonstration and limitations. “Create a New Plant”
is Coming Next. Original source documents and historical reports are preserved.
See [APP_VALIDATION.md](APP_VALIDATION.md) for the four real acceptance solves,
CLI parity, genuine timeout test and final 159-test validation.


Current backend: **V5, strict Scenario A only**. See [V5_SCOPE.md](V5_SCOPE.md),
[ASSUMPTIONS.md](ASSUMPTIONS.md), and
[FINAL_OPTIMIZER_READINESS.md](FINAL_OPTIMIZER_READINESS.md).

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.solve --output-dir reports/v5 --time-limit 180
.\.venv\Scripts\python.exe -m src.reporting --report-dir reports/v5
```

The last command regenerates operational, cash, productivity and financial
reports without solving. `reports/v5/solve_status.json` records actual proof
status; a published monetary-optimal plan need not have a proven secondary
event optimum. V4 and V2.1 below are historical baselines. The Streamlit interface
is documented in the application section above.

A Python mixed-integer linear programming (MILP) project for a P&G Venus supply chain case study over a 12-month planning horizon.

The optimizer uses **Pyomo** to formulate the model and **HiGHS** (through `highspy`) to solve it. **pandas** and **openpyxl** support tabular and Excel data handling, and **pytest** supports automated testing.

## Project structure

- `data/`: Input datasets for the supply chain case study.
- `src/`: Data loading, model formulation, solving and results extraction.
- `tests/`: Automated data and optimization tests.
- `requirements.txt`: Python dependencies.

## Current status

V4 integrates optimized qualification, daily L2 sequencing, optional crews/
operating-profile upgrades and chronological A-material scrap/IDE with A/C lots,
international order events, warehouse, transport and monthly supply planning.
Every month has exactly four weeks/28 planning days. B materials use smooth replenishment;
assumption; their physical stock is unspecified, not zero.
This is not a solution to the complete P&G case. See [MODEL_SCOPE.md](MODEL_SCOPE.md)
and [V4_SCOPE.md](V4_SCOPE.md) for current rules, assumptions and proof-status safeguards.
V2.1 Scenario A is preserved as a historical baseline.

## Run the model

From the workspace root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m src.solve
.\.venv\Scripts\python.exe -m src.solve --time-limit 180 --output-dir reports/v4
```

This validates source data, minimizes shortages at P1 then P2 then P3, and
minimizes modeled cost while preserving service optima. It then minimizes
new material-specific international order events at **strict minimum monetary
cost**, followed by procurement quantity and final cost cleanup. Only Scenario A
is supported; no 2% tolerance or Scenario B is run. It prints
hub service, monthly production/inventory/trucks, A/C material balances,
additional orders/events/arrivals, warehouse occupancy/blocks, fixed incoming
shipments separately, B theoretical consumption and costs. The optional
output directory receives daily/monthly CSV tables, a readable report,
qualification/IDE details, staffing and solver-stage JSON. The time limit is
per stage (default 120 seconds). Later stages run only after earlier optima
are proven. A limit returns nonzero; any feasible incumbent is clearly labelled
as not fully lexicographic optimal, with available bounds/gaps. The run does not
install packages or write to the original inputs.

- `src/model.py`: Formulates the MILP from the existing `CaseData` object.
- `src/scheduling.py`: Adds the exact 28-day schedule, qualification, crewing and scrap.
- `src/solve.py`: Executes and checks the seven lexicographic stages.
- `src/results.py`: Extracts structured data frames and formats the report.
- `src/validation.py`: Audits active constraint residuals, bounds and integrality.
- `tests/test_model.py`: Tests physical balances, limits, service priorities,
  cost results, partial trucks, material conservation, BOM, procurement lead
  times/lots/events, warehouse blocks/cost, B independence,
  infeasibility and nonoptimal solver handling.
- `tests/test_v4.py`: Independent synthetic schedules for transition/scrap,
  configuration carry, qualification exemptions, paid training and upgrades.

## Run validation

From the workspace root in PowerShell, using the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe src/data_loader.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.validation --report-dir reports/v4
```

With another environment containing the requirements, use `python` instead of
`.\.venv\Scripts\python.exe`. Validation reads the original Word and Excel files
in `data/` without modifying them and displays totals, errors and unresolved
source inputs. See [DATA_REVIEW.md](DATA_REVIEW.md) for table provenance, all
business rules and missing inputs. A validation PASS does not mean all inputs
needed for a future optimizer are available.

`src/data_loader.py` exposes `load_case()` returning a `CaseData` object with
normalized data frames, rule parameters, original tables and Word paragraphs.
Demand remains pooled as A/C and B; no A/C split is invented.

The latest verified V4 result and its proof limits are in
[reports/v4/ANALYSIS.md](reports/v4/ANALYSIS.md). Service and minimum cost are
proven; the procurement-event stage reached its time limit. The reports do not
claim full lexicographic optimality.

## Reconcile the saved V4 finances without solving

```powershell
.\.venv\Scripts\python.exe -m src.results --report-dir reports/v4
```

This reads saved decisions and original case rates without running a solver.
It writes `monthly_production_inventory.csv`, `monthly_inventory_by_product.csv`,
`monthly_cost_breakdown.csv` and `FINANCIAL_RECONCILIATION.md`, and updates a
single generated appendix in `summary.txt`. Repeated runs are idempotent.
Raw decisions, solver status, model formulation and V2.1 history are untouched.
The report investigates the user-provided Excel total of $1,217,953.00; use
`--excel-total` to compare another grand total. Missing Excel cost components
are not inferred as facts.

`src/reconciliation.py` recomputes balances and finances independently from
quantities; `tests/test_reconciliation.py` checks reconciliation, product values,
fractional precision and preservation of existing inputs.
