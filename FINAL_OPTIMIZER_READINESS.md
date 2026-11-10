# Active V6 extension

The financial/workforce update is documented in [V6_SCOPE.md](V6_SCOPE.md).
The earlier V5 readiness assessment below is historical. Additional A/C purchases
and B production-linked materials now enter the true monetary objective. Optional
crew dismissal and full retraining after rehire are implemented; prices, wages,
training months, crew size and dismissal expense flow through the scenario adapter.
See `reports/app_runs/v6_original_resumed/` for the fresh real application run and
`reports/v6/` for the earlier V6 run. Solver proof is per run, not inferred from
tests. Original documents and historical reports are protected by fingerprint audit.

---

# Final optimizer backend readiness — V5

This is the mathematical readiness record from before interface development.
The Streamlit application is now implemented; see APP_GUIDE.md and
APP_VALIDATION.md. The backend requirements/assumptions below remain applicable.

Ready for an editable-input interface **within the accepted model scope**,
subject to the final test/run status in reports/v5. This is not a certification
of every physical real-world supply-chain condition. No interface is built.
ASSUMPTIONS.md is the central register; DATA_REVIEW.md retains original-source
provenance and contradictions. V4_SCOPE.md is the historical V4 specification.

## Verified V5 optimization result

The complete automated suite passed **107 tests** in the final full run
(`reports/v5/test_run.log`). Original case and historical V4 fingerprints match;
no source document or historical report was changed.

All seven stages returned `ok / optimal`, with equal lower/upper bounds and
zero reported gap. Service is 3,095/3,095 MSU; minimum monetary cost remains
**$1,215,467.50**. Four additional international events are now **proven minimal**;
the normalized procurement minimum is 2,300 MSU-equivalent material quantities.
The independent exported-plan audit passed 12,432 active constraints and 6,735
variable levels, including the proven service, cost, event and quantity locks.
Maximum residual was approximately 3.26e-9 at tolerance 1e-5.

The selected qualification is December planning days 10–12, versus V4 days
16–18. Annual production remains A=230, B=1,520, C=1,320 MSU; no hires/upgrades,
no external blocks, 35 spot trucks, and $30,300 IDE remain unchanged. V5 selects
nine routine L2 changes versus V4's ten, leaving 3,630 versus 3,622 MSU available
capacity. The extra eight MSU is unused: daily configuration timing is not a
separate objective, so this does not establish a unique or intrinsically superior
schedule. Procurement quantities remain C RM=550,000 kg, PM=3,000,000 EA,
with zero additional A procurement. Timings vary among equivalent optimal plans.
No cost change beyond numerical floating-point residuals was found.

The selected December transition consumes all 115,000 kg opening A RM and
575,000 EA A PM before scrap, preserving A's material value while permitting
25 MSU C in December to cover demand beyond A's 230 MSU production plus 10 MSU
opening FP. Earlier qualification would leave more A material unused in such
a plan. Base crews prebuild 222 MSU FP by April for summer peaks; neither an
upgrade nor external blocks is selected in the cost optimum. This explains
the plan's material/capacity/cash trade-offs without asserting a unique day.

## Original case requirements and traceability

| Requirement / original deliverable | Status and corresponding implementation | Automated evidence |
| --- | --- | --- |
| 12-month plan, four-week calendar, line eligibility and rates | `scheduling.month_days`, `operating`, `daily_schedule_capacity`; `model.production_limit` historical only, `integrated_month_capacity` current | `test_four_week_calendar`, `test_production_limits_and_eligibility`, `test_v4_capacity_downtime_cash_and_productivity` |
| Shared A/C forecast, separate B forecast | `model.demand_balance`, `family_members`; no invented product split | `test_demand_accounting`, `test_no_arbitrary_ac_demand_split`, `test_exact_monthly_family_priorities` |
| Annual regional service priorities | `solve.solve_lexicographic`, equality service locks | `test_strict_hub_priority_under_scarcity`, `test_costs_and_stages` |
| Monthly regional priority, independently by family | `priorities.priority_higher_served`, `priority_lower_shipments` all pairs | `test_exact_monthly_family_priorities`, `test_zero_middle_demand_cannot_bypass_cairo_shortage` |
| Qualification/launch and permanent A→C production transition | `one_qualification`, `transition_flow`, `daily_shutdown_capacity`, `no_a_after_transition`, `no_c_before_qualification` | `test_qualification_cannot_use_nonworking_days`, `test_transition_and_shutdown_block_forbidden_production`, `test_optimizer_chooses_to_consume_a_before_qualification` |
| L2 actual switches and at most one per month | `config_enter`, `config_leave`, `no_fake_changeover`, `changeover_scheduled`, `monthly_changeovers`, configuration carry | `test_exact_l2_configuration_carry_and_changeovers`, `test_changeover_day_cannot_also_produce` |
| Crewing, optional upgrades, paid training, salaries/hiring | `one_hire`, `upgrade_training`, `employed`, `operating`, `new_salary_cost`, `hiring_cost` | `test_training_blocks_extra_days_until_next_month`, `test_both_or_neither_upgrades_are_feasible`, `test_optimizer_selects_only_l2_hire_when_required_for_service` |
| Strict labor ceiling / premium overtime | Not modeled: numerical ceiling/rates absent; only two supported optional crews | Source missing-data checks; ASSUMPTIONS.md |
| A/C BOM, initial stocks, fixed pipeline, separate materials | `daily_material_balance`, monthly links, `bom_quantity`, `fixed_material_arrival` | `test_material_balances_bom_and_fixed_arrivals`, `test_c_cannot_consume_november_arrival_in_october`, `test_exact_fixed_arrivals` |
| Additional material procurement, three-month SF, lots | `order_arrival_month`, `additional_material_arrival`, `order_lot_link`, bounded `integer_lots` | `test_procurement_lead_times_moq_and_no_excess`, `test_lots_events_storage_and_service` |
| B smooth material replenishment | No B material variables/constraints; consumption expression only | `test_no_b_material_variables_and_no_scenario_b`, `test_b_consumption_is_information_only` |
| A phase-out RM/PM scrap and IDE | `scrap_only_at_start`, `no_usable_a_after_transition`, `daily_material_balance`, `no_late_a_receipts`, four IDE expressions | `test_chronological_scrap_and_finished_goods_sellthrough`, `test_new_a_receipts_after_transition_are_not_allowed` |
| Finished-goods inventory, sell-through, valuation/holding | `inventory_balance`, `holding_cost`; no A FG sales deadline | `test_inventory_balances`, `test_chronological_scrap_and_finished_goods_sellthrough`, reconciliation product valuation/holding tests |
| Packaging one-year expiry | Accepted unverified usable-packaging assumption; batch ages unavailable, aging intentionally omitted | Loader reports missing ages; ASSUMPTIONS.md |
| Warehouse/3PL blocks and cash | `tracked_pallets`, `warehouse_capacity`, `external_storage_cost`; derived material and FP valuations | `test_lots_events_storage_and_service`, `test_monthly_costs_sum_to_reported_objective`, `test_v4_capacity_downtime_cash_and_productivity` |
| Fleet, destination separation, full truck charges, spot surcharge | `transport_capacity`, `fleet_capacity`, `transport_cost` | `test_transport_capacity_fleet_and_partial_loads`, `test_partial_truck_is_paid_in_full`, synthetic monthly priority/truck tests |
| Hub-specific service penalties | `service_penalty` source penalty x shortage | `test_monthly_costs_sum_to_reported_objective`, financial reconciliation tests |
| C:D source indication | Both plausible numerators transparently monitored; no additional constraint | `test_dual_cd_indicators_opening_once_and_flags`, `test_zero_cumulative_demand_is_undefined`, capacity/downtime KPI test |
| International consolidation without fictitious freight cost | `event_upper`, `event_lower`, strict stage 5; positive quantity tie-break stage 6 | `test_event_and_lot_constraints_reject_inconsistent_orders`, `test_invalid_cost_allowance_rejected` |
| Cost/Cash/Service/Productivity dashboard | `reconciliation.calculate`, `kpis.calculate_kpis`, `reporting.generate_reports` | Reconciliation suite, KPI tests and independent exported-model audit |
| Original source preservation and input provenance | `data_loader.load_case` reads DOCX/XLSX only | `test_loading_does_not_modify_originals`, source reconciliation tests |

## Architecture for editable inputs

1. `data_loader.py`: original input adapter and source regression validation.
2. `parameters.py`: editable deep copy plus structural validation. Existing CaseData
   fields supply demand, line rates/profiles, BOM/values, opening stocks/receipts,
   salaries, hiring fees, qualification duration, lead time, lot sizes, warehouse,
   fleet, penalties and holding rates. Rebuild after editing.
3. `model.py`, `scheduling.py`, `priorities.py`: MILP construction only.
4. `solve.py`: strict lexicographic HiGHS execution and proof metadata.
5. `results.py`: checked structured extraction and raw decision export.
6. `reconciliation.py`, `kpis.py`: independent finance and operational diagnostics.
7. `reporting.py`: reproducible CSV/Markdown/JSON exports without solving.

Input loader layout is specific to the original workbook; a future interface
should edit normalized copies rather than rewrite case documents. No arbitrary
new products, lines, or daily calendars are advertised. Profiles and qualification
windows are editable within the supported formulation; fixed conventions are
validated rather than silently changed. Source regression values such as 3,095
MSU are not a generic editable-demand restriction.

## KPI definitions and financial guarantees

- Capacity: line rate × (scheduled days − qualification days − routine switch days).
- Capacity C:D: cumulative available capacity / cumulative pooled A/C + B demand.
- Supply C:D: (opening FP once + cumulative production) / cumulative demand.
- Service: shipments / demand monthly and cumulatively, with zero-demand ratios undefined.
- Capacity utilization: actual production / available capacity; actual manufacturing
  days count positive-output days and equivalent full-rate days = production/rate.
- Labor productivity: MSU produced / employed operators, including trainees.
- FP cash: sum ending product MSU × its source value; a stock, not another expense.
- AC material cash: RM kg × $5 plus PM EA × $0.40; B material value unspecified.
- FP holding: ending product MSU × product value × monthly 1.5%.
- IDE: A RM scrap × ($5/kg + $0.20/kg disposal), A PM scrap ×
  ($0.40/EA + $0.004/EA disposal), separately reported.
- Other expenses: employed salaries, one-time hiring, destination truck charges,
  service penalties and full external blocks. No independent material purchase cost.

All financial arithmetic uses unrounded solver quantities. Twelve monthly
expenses reconcile to the monetary objective; annual inventory is September's
ending balance, never a sum of monthly snapshots. Numerical audits check all
active constraints and variable bounds/integrality; they are not proof of optimality.

## Solver quality and publication

Only Scenario A, zero monetary tolerance and zero requested MILP gaps.
`solve_status.json` records each termination, mathematical bound, incumbent and
gap. `success` requires all stages proven. A secondary timeout stops later stages
but does not prevent publishing an audited monetary-optimal production plan.
Neither tests nor an incumbent justify calling an unproven event count minimal.
The V4 baseline proved 100% service and $1,215,467.50, but four events had a lower
bound of two (50% gap). See the new actual V5 analysis for the current status.

## Deliverable locations

`reports/v5/ANALYSIS.md`, `summary.txt`, `solve_status.json`, `solution_audit.json`,
`dashboard.json`, `monthly_operations.csv`, `cumulative_indicators.csv`,
`productivity.csv`, `cash.csv`, `material_valuation.csv`, monthly production/
inventory/financial CSVs, `FINANCIAL_RECONCILIATION.md`, raw daily/monthly decision
tables, `transition_ide.json`, and `v4_comparison.csv` / `plan_comparison.json`.
V4 and V2.1 historical files are preserved.

## Interface readiness checklist

- [x] Loader, editable inputs, construction, solve, extraction, KPIs and reports separated.
- [x] Rebuild-based editing supported without altering source documents.
- [x] Exact monthly family priorities cover future shortage scenarios.
- [x] Both C:D definitions and undefined/below-one flags exposed as diagnostics.
- [x] Financial stock/expense distinction and unrounded reconciliation exposed.
- [x] Strict Scenario A and truthful partial-proof handling retained.
- [x] No frontend dependency or GUI added.
- [x] Accepted expiry, B-space, calendar, sell-through and month-end assumptions centralized.
- [ ] Complete physical verification: intentionally not claimed; PM ages, B stock
      footprint, intramonth peaks, unspecified labor rules and daily delivery/transit
      remain outside this model.
- [ ] Guaranteed secondary proof within a fixed time budget: not guaranteed for MILP.

The interface should display accepted limitations and stage-level proof status,
and must not replace validation/proof with a blanket “optimal” badge.
