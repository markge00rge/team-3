# V5 backend: monthly family priorities and operational diagnostics

This records the mathematical backend milestone before interface development.
The current Streamlit layer is documented in APP_GUIDE.md and APP_VALIDATION.md;
it preserves this strict Scenario A formulation.

The integrated V4 daily manufacturing, staffing, qualification, material scrap,
procurement, warehouse and transport formulation is retained. V5 adds exact
monthly family allocation priorities and reporting; no GUI or Scenario B.

For every higher/lower regional pair, family and month, binary release `z` obeys
`unserved[higher] <= demand[higher] * (1-z)` and
`shipments[lower,family] <= demand[lower] * z`.
Lower-hub shipments therefore imply zero higher-hub shortage for that same
family/month. All ordered pairs are required to cover zero-demand middle hubs.
The bounds are source demand, not arbitrary constants. Annual service stages
remain unchanged; there are no additional lexicographic stages.

Order: annual P1 service, annual P2, annual P3, strict monetary minimum,
material-specific event count, normalized procurement quantities, cost cleanup.
All earlier optima remain locked; there is no monetary tolerance. A timeout
retains a checked incumbent, reports bound/gap, and does not advance to later
tie-breaks. CLI publication can succeed for an audited monetary-optimal plan
even if secondary proof is incomplete; `solve_status.json.success` still means
all stages proved optimal. Solver proof, numerical feasibility, and accepted
physical assumptions are separate claims.

Safe performance changes: redundant demand-derived shipment/unserved bounds,
per-order quantity bounds derived from existing lot bounds, and per-line daily
production bounds equal to the line's rate. Existing event iff-lot links, full
upgraded useful-procurement bounds, APPsi warm starts and schedule-fixed primal
heuristic remain. The heuristic never fixes the main model. No invalid global
symmetry ordering of receipt dates is imposed: monthly material availability
and warehouse occupancy make order timings nonequivalent.

`parameters.editable_case()` copies CaseData and validates editable structure.
Source regression validation remains separate. Model rebuilds are supported;
no live mutation is required. Profiles, salaries, MOQ, fleet, demand, initial
stock, lead time, qualification duration and holding/warehouse/transport rates
come from CaseData. Optional `upgrade_permissions` and
`qualification_allowed_months` restrict choices without editing constraints.
The 28-day convention, one-month training and one-day routine changeovers are
supported fixed conventions; unsupported values are rejected explicitly.

`kpis.py` computes both C:D ratios independently from daily schedule quantities
and monthly actual production. Capacity is not actual production; supply adds
opening FP once; shipments measure delivered service. Undefined ratios remain
blank/JSON null. Ratios below one are flagged without constraining optimization.
`reporting.py` joins 12-month operations, productivity, cash, source-valued
AC materials and independent financial reconciliation. Inventory snapshots are
not summed as annual stock. CSV precision is retained; rounding is display only.

Run with the project's existing environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.solve --output-dir reports/v5 --time-limit 180
.\.venv\Scripts\python.exe -m src.reporting --report-dir reports/v5
.\.venv\Scripts\python.exe -m src.validation --report-dir reports/v5
```

The reporting command does not solve. Source documents and V4/V2.1 reports are
preserved. The central current assumptions are ASSUMPTIONS.md; actual run proof
and comparative values are in reports/v5/ANALYSIS.md and solve_status.json.
