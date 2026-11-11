# International shipment consolidation policies

One Venus model supports three mutually exclusive logistics policies. A shipment
means a coordinated international dispatch batch/occasion, **not a container**.
There is no assumed inbound container capacity, shared-material substitution or
new freight cost. The three precommitted source deliveries remain separate.

| Stable identifier | Display name | Optimized count |
| --- | --- | --- |
| `independent_materials` | Independent RM/PM Shipments | Positive product/material/month order lines |
| `per_product` | Consolidate Within Each Product | Product/month groups containing any positive RM or PM order |
| `all_products` | Consolidate All Products | Months containing any positive additional order |

Policy 1 is the backward-compatible default. Policy 2 keeps A and C as distinct
products, despite their shared customer demand. Policy 3 explicitly assumes a
common international consolidation hub; this is a user-selected assumption, not
a fact established by the original P&G case. Neither consolidation policy
asserts a physical container count. All materials currently share the configured
standard lead time; schedule extraction rejects a batch with different arrival
months rather than silently presenting it as one receipt.

## Formulation and priorities

The original six procurement decisions, lot sizes, finite lot bounds and exact
positive-order binaries remain unchanged. `additional_order_events` remains the
common material-order-line metric. `international_shipments` is the selected
objective: individual events for Policy 1, or binary OR groups for Policies 2/3.
For each group/month, its binary is at least every member event and at most their
sum. Empty groups must be zero, independently of objective direction. Multiple
lots can share one batch. There is no inbound-capacity constraint tied to the
1,200-pallet warehouse capacity.

The three annual hub service objectives run first, with monthly family priorities
unchanged. Monetary cost runs next, then selected shipment count, normalized
procurement quantity and cost cleanup. Cost is locked with zero business tolerance.
The stable internal stage identifier `international_order_events` now refers to
the selected shipment metric, as recorded in new stage metadata. Later stages
stop if a prior stage is unproven. No greedy consolidation fallback was added.
The pre-existing schedule-fixed MILP heuristic supplies only a starting candidate;
the final global shipment solve leaves all scheduling/workforce decisions free.

Every physically feasible order plan has exactly one feasible assignment of the
group binaries. Changing policy therefore cannot change the projected feasible
production/material/financial region, nor the service or monetary optimum. It can
select different plans among ties. Solver timeouts still require truthful status;
passing tests does not certify optimality.

## Streamlit use, saved runs and comparison

Original Venus: enter a required run name, select one radio option on that same
page, then Run Optimization. Only the logistics policy changes original inputs.
Customized Venus: select the policy on Materials & Procurement. That durable
scenario value remains authoritative on Review & Optimize; no duplicate final
selector is shown. Full Reset to Original restores Policy 1.

The backward-compatible optional `shipment_consolidation_policy` configuration
field defaults to Policy 1 for older JSON. New saved runs capture the identifier,
name, selected shipment count, material-order-line count, actual batch table and
shipment stage status/bound/gap. Model/reporting version is V8; the financial
definition is unchanged from explicit-ABC V7. SQLite rows and historical results
are never migrated or overwritten. Known V4–V7 historical versions classify as
legacy Policy 1 for display; unestablished versions display Legacy / Unknown.

Dashboards show International Shipments and Material Order Lines separately,
alongside policy, proof status and the batch schedule. The five financial cards
retain their formatting. Compare Runs labels policies, lists their changed-input
values, shows saved stage statuses and warns about different counting definitions.
Material Order Lines is the common comparison metric; fewer dispatch batches
alone do not establish fewer physical containers.

## Files and reproduction

- `src/shipment_policy.py`: shared policy definitions, exact MILP group links and
  verified reporting aggregation of the selected orders.
- `src/model.py`, `src/solve.py`: policy construction and selected lexicographic
  objective. Existing physical/financial constraints remain in their modules.
- `src/results.py`, `src/validation.py`, `src/report_v6.py`: batch CSV/metadata,
  reconstruction of group variables and selected objective locks, readable reports.
- `app/scenarios.py`, `app/components/shipment_policy.py`, `app/main.py`,
  `app/pages/questionnaire.py`: validated scenario mapping and shared controls.
- `app/optimizer_adapter.py`, `app/run_store.py`, `app/dashboard.py`,
  `app/history.py`, `app/comparisons.py`: persistence, two metrics and comparisons.
- `tests/test_shipment_policies.py`: exact grouping, no empty groups, arrival
  compatibility, policy-to-model mapping, known-outcome full MILPs, UI state,
  reset, saved schedules and comparisons. Existing regression suites remain.
- `src/shipment_validation.py`: reproduces the acceptance comparison and exact
  selected order/batch schedules from the three actual CLI result folders.

```powershell
.venv\Scripts\python.exe -m streamlit run app/main.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m src.shipment_validation
.venv\Scripts\python.exe -m src.solve --shipment-policy per_product --output-dir reports/new_per_product --time-limit 300
.venv\Scripts\python.exe -m src.solve --shipment-policy all_products --output-dir reports/new_all_products --time-limit 300
```

Always use a fresh output directory. CSVs include
`international_shipment_schedule.csv`, all underlying material orders, stocks,
warehouse, production and financial tables. New saved snapshots include that
table in CSV/Excel exports without recalculation or a historical re-solve.

Actual three-policy validation results are recorded in
`reports/shipment_policy_validation/RESULTS.md`. Time limits and gaps there are
part of the result, not hidden failures. Additional valid cuts or longer solves
may improve proof performance. A cost-preserving heuristic could be evaluated
later, but is not implemented in this upgrade.
