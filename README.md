# P&G Venus Supply Chain Optimizer

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
