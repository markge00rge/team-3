# Venus interactive application: implementation and validation

Validated on 2026-11-09 in branch `v5-development`. Pre-existing workspace
changes were retained. The application uses Streamlit 1.65.0 and Plotly 6.9.0
in the project's existing virtual environment; no separate frontend framework.

## Delivered workflow

- Home presents Venus Case Study and the explicit New Plant Coming Next screen.
- Venus entry offers a fresh original solve without a questionnaire, or seven
  prefilled sections with direct navigation, reset, changed-value review and
  durable drafts.
- An explicit 118-key allowlist maps the supported business configuration into
  a fresh CaseData copy. Structural edits and unknown fields are rejected.
- The demand spreadsheet has six hub/family rows and twelve planning months;
  live month/hub/family/year totals, changed-cell detail, reset and CSV import/export.
- Real worker processes execute the existing V5 MILP. Stage events, failures,
  timeouts, proven optima and audited incumbents are displayed without fake progress.
- Dashboards cover manufacturing, transition, staffing, materials/lots, warehouse,
  working capital, regional distribution, costs, productivity, both cumulative
  C:D measures, and actual solver proof. Twelve KPI cards and fifteen charts
  rendered successfully in the original-run AppTest.
- Side-by-side comparisons, result CSVs, an all-table Excel workbook, scenario JSON
  and solver-proof JSON were exercised. New Plant has no optimization engine.

## Real optimization acceptance

All four runs below proved **all seven stages optimal**, with zero reported
gap. Each retained four international material-specific procurement events.
Independent numerical audits passed; maximum residual across these cases was
approximately 2.29e-8 against the 1e-5 audit tolerance.

| Scenario | Demand MSU | Service | Annual modeled USD |
| --- | ---: | ---: | ---: |
| Original Venus | 3,095 | 100% | 1,215,467.50 |
| FP holding rate 2%, rather than 1.5% | 3,095 | 100% | 1,234,190.00 |
| Monthly salary $1,100/operator, rather than $1,000 | 3,095 | 100% | 1,299,467.50 |
| June H1 A/C demand 115 MSU, rather than 105 | 3,105 | 100% | 1,219,577.50 |

The holding case charges $74,890 holding versus $56,167.50 originally. The
salary case charges $924,000 base salaries versus $840,000. The demand case
produces 1,330 MSU C versus 1,320, with holding $59,317.50 and transportation
$289,960. These figures are extracted from real solved plans, not illustrative
or substituted dashboard numbers. Holding-rate 2% is an expense-rate sensitivity,
**not** a monetary objective tolerance; only strict Scenario A is implemented.

`reports/app_runs/acceptance_verification.json` contains all outcome metadata;
`acceptance_summary.csv` gives the compact comparison. Each acceptance directory
contains the exact scenario, raw decisions, financial reconciliation, KPIs,
transition, stage proof and numerical audit.

## Original-case CLI/UI equivalence

The independent CLI run in `reports/app_runs/cli_original/` and the UI adapter
run in `acceptance_original/` both prove $1,215,467.50, full service, four
events and 2,300 MSU-equivalent procurement quantities. Tests compare the actual
current validated V5 report; no app regression constant replaces a later result.
An independent signature test compares every active linear constraint, variable
bound, fixed level and integer domain between direct source loading and the
original scenario adapter. `app/validated_baseline.json` records source/report
fingerprints and warns if the benchmark or engine changes.

## Genuine live-button timeout check

A Streamlit AppTest clicked the actual Run Original Case button, without mocking
the worker, at a deliberately short 30-second-per-stage limit. The job pointer
is `reports/app_runs/live_ui_job.json`. All three service stages proved zero
shortage. Monetary optimization timed out with a checked incumbent $1,216,561,
lower bound approximately $1,213,771.6641 and gap 0.22928%. Later tie-breaks did
not run. The app published **Feasible plan cost**, not **Minimum modeled annual
cost**, and displayed the incomplete proof. This smoke test validates timeout
handling; it does not supersede the proven original 180-second acceptance runs.

## Automated and startup validation

The final complete suite passed **159 tests with no skips** in 148.84 seconds;
the output is `reports/app_runs/TEST_RESULTS.log`. It
covers the original backend regressions, all allowed mappings, actual model
expressions, original mathematical equivalence, scenario immutability,
navigation/reset, spreadsheet callbacks, every questionnaire page, actual saved
acceptance runs, CLI equivalence, solver progress events, Excel export, dashboards
and the genuine timeout display. Acceptance artifact tests use real solver
outputs; missing artifacts are skipped explicitly, never fabricated.

The Streamlit server started successfully at http://127.0.0.1:8501 and returned
HTTP 200 / `ok` on its health endpoint. The Home, Venus, Coming Next, all seven
sections, original-run dashboard and comparison screen rendered without AppTest
exceptions. Browser-specific visual QA and production deployment are separate
from these automated render tests.

## Backend changes and safeguards

No mathematical constraint, objective or accepted business rule changed.
Narrow changes are:

1. `solve_lexicographic(..., stage_callback=None)` emits observational stage events.
2. Independent financial reconciliation tolerates a truthful not-run monetary
   stage when exporting an earlier feasible incumbent.
3. Reporting-only source pallet metadata replaces hardcoded conversions in the
   conservative intramonth peak export. A regression checks edited RM/PM factors.

No multi-month training, new structural crew rules, storage-availability switch
or spot-supply cap was implemented or exposed. These controls are read-only.
The original case documents and historical V2/V2.1/V4/V5 reports are preserved;
146 source/historical files have recorded fingerprints in
`reports/app_runs/protected_fingerprints.json`. All 146 matched after completion.

## Scope and next steps

APP_GUIDE.md gives the exact allowlist, locked fields, JSON schema and launch
commands. ASSUMPTIONS.md remains the model authority: no detailed packaging ages,
no specified B material stock/space, no independently verified intramonth warehouse
peak, and no invented overtime/headcount rules. Inventory cash is not added to
expenses. General-purpose new plants require a generalized mathematical schema,
arbitrary eligibility/family/transition rules and independently tested adapters.
Authentication, deployment hardening and persistent multi-user run administration
are future application work, not claims of this local case-competition milestone.
