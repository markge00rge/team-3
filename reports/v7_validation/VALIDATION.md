# V7 backend and application validation - 10 November 2026

Branch: `product-b-upgrade`; checkpoint `2cbcdbd` remains intact. Original source
files and historical solver reports were preserved. All 172 protected file digests
match, as do all three pre-existing SQLite run payload digests. No historical run
was deleted, rewritten or recalculated for viewing.

## Automated checks

- Complete suite: **237 passed** (`v7_final_full_tests.log`).
- Final targeted material/editor/history/report checks: **28 passed**, with no
  warnings (`v7_final_targeted_tests.log`). This follows cleanup of a pandas
  metadata-only concatenation warning seen in the full run.
- Additional no-substitution / qualification stock-retention check passed
  (`v7_substitution_test.log`).
- Real original and customized B-stock scenarios execute Pyomo + HiGHS through
  the existing application adapter and save actual audited results to SQLite.
- Original/default B stocks 200,000 kg / 750,000 EA and edited values, including
  zero, reach actual Pyomo inputs. B BOM/prices affect constraints/objective.
- Known-outcome shortage MILPs block B without material before January; more
  opening B stock removes the early shortage when line capacity is sufficient.
- Tests cover BOM, conservation, B isolation through qualification, lot/event
  links, three-month receipts, no phantom fixed arrivals, order-month cost,
  all-five-cost reconciliation, warehouse occupancy, 3PL blocks, unchanged B
  FP valuation/holding, historical versions and read-only saved-run comparison.
- Saved result tables equal exported numerical CSV tables exactly after JSON
  round-trip. Reports regenerate idempotently from captured effective inputs,
  even when current source price defaults are changed in a test.
- Headless Chrome component checks pass at requested widths 1024, 1280, 1366,
  1440, 1920 for both individual and comparison financial cards. No measured
  clipping or horizontal overflow. Actual Streamlit views are also AppTest-tested.

## Official original-case result

Published report copy: `reports/v7/`, from actual new run
`reports/app_runs/v7_final_original_20261110`.
Saved run ID: `fbf7d657d22141d4b70ab346a9aeb1a0`.

| Item | Value |
| --- | ---: |
| Service | 3,095 / 3,095 MSU (100%) |
| Operating expense, excluding material purchases | $1,215,467.50 |
| Additional A material purchases | $0.00 |
| Additional B material purchases | $4,700,000.00 |
| Additional C material purchases | $3,950,000.00 |
| Total Delivery Cost | $9,865,467.50 |
| B RM ordered | 750,000 kg (15 lots) |
| B PM ordered | 2,375,000 EA (19 lots) |
| Ending B RM / PM | 38,000 kg / 85,000 EA |
| Peak month-end occupancy | 1,198 pallets |
| External storage | 0 blocks / $0 |
| B FP holding | $7,342.50 |
| All FP holding | $56,167.50 |
| Qualification | December planning days 17-19 |
| Hiring / dismissal / upgrades | None |

Service stages and monetary stage: status `ok`, termination `optimal`, gap 0.
Procurement events: status `aborted`, termination `maxTimeLimit` at 300 seconds,
incumbent **10**, bound **8**, gap **20%**. It is not a proven event minimum.
Quantity minimization and cleanup were not run. No service or cost optima were
relaxed. The plan remains service- and monetary-optimal, not fully lexicographic optimal.
Independent audit: 13,376 active constraints, 7,579 variable levels, maximum
violation 1.396984e-9 against tolerance 1e-5.

The ten new events in this selected plan are five B and five C. Three fixed A/C
incoming shipments remain separate. The lower bound does not prove which eight
or nine events could suffice; do not infer a unique required purchasing schedule.

## Customized B-stock acceptance

`reports/app_runs/v7_higher_b_stock_20261110`: B opening RM 240,000 kg / PM 800,000 EA.
All service and monetary stages proven optimal, service 100%, cost $9,565,467.50.
Its event stage timed out at 240 seconds: incumbent 10, bound 7, gap 30%; later
stages not run. This confirms stock edits affect actual procurement and cost.
Default and customized records have V7 financial metadata; V6 comparisons warn
about changed B consumption-versus-purchasing definitions and suppress misleading
monetary differences. Historical source tables remain viewable without optimization.

## Financial comparison / limitations

V6 charged B production consumption $5,776,000 with no physical B stock model.
V7 charges new B orders $4,700,000 and adopts previously available B opening stocks.
Operating expense and A/C purchase totals are unchanged in the selected default
plan. The $1,076,000 total difference is a scope/accounting difference, not a
like-for-like efficiency saving. Stocks purchased in full lots leave $224,000 of
B material at year-end; no disposal or salvage is invented.

Packaging ages/expiry, intramonth warehouse peaks, formal C:D feasibility and
arbitrary plant generalization remain outside the accepted scope. B physical
RM/PM and its footprint are now explicitly included; its former footprint exclusion
no longer applies. No fictitious freight or material carrying fee is introduced.

See `reports/v7/FINAL_RESULTS.md` for the complete monthly balances, orders,
warehouse, FP holding, workforce, service and financial tables; `V7_SCOPE.md` for
formulation, assumptions, versioning and file responsibilities.
