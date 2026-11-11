"""Extract structured outputs only after the checked lexicographic solve."""
from dataclasses import dataclass, field

import pandas as pd
import pyomo.environ as pyo


@dataclass
class ModelResults:
    production: pd.DataFrame
    inventory: pd.DataFrame
    shipments: pd.DataFrame
    service: pd.DataFrame
    transport: pd.DataFrame
    costs: dict[str, float | None]
    material_balances: pd.DataFrame
    material_orders: pd.DataFrame
    b_material_consumption: pd.DataFrame
    warehouse: pd.DataFrame
    fixed_receipts: pd.DataFrame
    daily_schedule: pd.DataFrame = field(default_factory=pd.DataFrame)
    daily_material: pd.DataFrame = field(default_factory=pd.DataFrame)
    staffing: pd.DataFrame = field(default_factory=pd.DataFrame)
    line_capacity: pd.DataFrame = field(default_factory=pd.DataFrame)
    transition: dict = field(default_factory=dict)
    storage_peaks: pd.DataFrame = field(default_factory=pd.DataFrame)
    material_policy: str = 'legacy_ac_smooth_b'
    shipment_consolidation_policy: str = 'independent_materials'
    international_shipment_schedule: pd.DataFrame = field(default_factory=pd.DataFrame)


def extract_results(model, *, allow_incumbent=False) -> ModelResults:
    if not getattr(model, "_solve_success", False) and not (allow_incumbent and getattr(model, "_has_incumbent", False)):
        raise RuntimeError("Results require a successful, optimal lexicographic solve.")
    m = model
    value = pyo.value
    result = ModelResults(
        pd.DataFrame([dict(line=l, product=p, month=t, msu=value(m.production[l, p, t])) for l in m.lines for p in m.products for t in m.months]),
        pd.DataFrame([dict(product=p, month=t, msu=value(m.inventory[p, t])) for p in m.products for t in m.months]),
        pd.DataFrame([dict(product=p, hub=h, month=t, msu=value(m.shipment[p, h, t])) for p in m.products for h in m.hubs for t in m.months]),
        pd.DataFrame([dict(hub=h, family=f, month=t, demand_msu=value(m.demand[h, f, t]),
                           served_msu=sum(value(m.shipment[p, h, t]) for p in m.family_members[f]),
                           unserved_msu=value(m.unserved[h, f, t])) for h in m.hubs for f in m.families for t in m.months]),
        pd.DataFrame([dict(hub=h, month=t, dedicated_trucks=value(m.dedicated[h, t]), spot_trucks=value(m.spot[h, t])) for h in m.hubs for t in m.months]),
        dict(labor=float(value(m.labor_cost)), fp_holding=float(value(m.holding_cost)),
             transportation=float(value(m.transport_cost)), service_failure=float(value(m.service_penalty)),
             ide=float(value(m.ide_cost)) if hasattr(m, "ide_cost") else None, external_storage=float(value(m.external_storage_cost)), total_modeled=float(value(m.total_cost))),
        pd.DataFrame([dict(product=p, material=k, unit="kg" if k == "RM" else "EA", month=t,
            opening=value(m.initial_material[p, k]) if i == 0 else value(m.material_inventory[p, k, list(m.months)[i-1]]),
            fixed_arrival=value(m.fixed_material_arrival[p, k, t]),
            additional_arrival=value(m.additional_material_arrival[p, k, t]),
            consumption=value(m.material_consumption[p, k, t]),
            scrap=value(m.monthly_a_scrap[k, t]) if p == "A" and hasattr(m, "monthly_a_scrap") else 0,
            ending=value(m.material_inventory[p, k, t]))
            for p in m.material_products for k in m.materials for i, t in enumerate(m.months)]),
        pd.DataFrame([dict(product=p, material=k, unit="kg" if k == "RM" else "EA", order_month=t,
            arrival_month=m.order_arrival_month[t], quantity=value(m.material_order[p, k, t]),
            integer_lots=value(m.integer_lots[p, k, t]), order_event=value(m.order_event[p, k, t]))
            for p in m.material_products for k in m.materials for t in m.months]),
        pd.DataFrame([dict(month=t, rm_kg=value(m.b_material_consumption["RM", t]),
                           pm_ea=value(m.b_material_consumption["PM", t])) for t in m.months]),
        pd.DataFrame([dict(month=t, fp_pallets=value(m.fp_pallets[t]), rm_pallets=value(m.rm_pallets[t]),
            pm_pallets=value(m.pm_pallets[t]), tracked_pallets=value(m.tracked_pallets[t]),
            onsite_capacity=value(m.onsite_capacity),
            minimum_external_pallets=max(0, value(m.tracked_pallets[t] - m.onsite_capacity)),
            onsite_pallets=min(value(m.tracked_pallets[t]), value(m.onsite_capacity)),
            external_blocks=value(m.external_blocks[t]),
            external_storage_usd=value(m.external_blocks[t] * m.external_block_usd)) for t in m.months]),
        pd.DataFrame([dict(product=p, material=k, unit="kg" if k == "RM" else "EA",
            arrival_month=t, quantity=value(m.fixed_material_arrival[p, k, t]))
            for p in m.material_products for k in m.materials for t in m.months
            if value(m.fixed_material_arrival[p, k, t]) > 0]),
    )
    if getattr(m, "integrated_schedule", False):
        _schedule_results(m, result)
    result.material_policy='explicit_abc_v7' if getattr(m,'explicit_b_materials',False) else 'legacy_ac_smooth_b'
    for p in m.products:
        result.warehouse[f'{p.lower()}_fp_pallets']=[value(m.inventory[p,t])*m.inventory_pallet_factors['FP'] for t in m.months]
    for p in m.material_products:
        for k in m.materials:
            result.warehouse[f'{p.lower()}_{k.lower()}_pallets']=[value(m.material_inventory[p,k,t])*m.inventory_pallet_factors[k] for t in m.months]
    if getattr(m,'material_financial_model',False):
        result.costs.update(operating_full_ide=value(m.operating_cost_full_ide),
            ide_overlap_adjustment=value(m.ide_overlap),operating_expenses=value(m.reconciled_operating_cost),
            a_materials=value(m.a_material_cost),c_materials=value(m.c_material_cost),b_materials=value(m.b_material_cost),
            total_delivery_cost=value(m.total_cost),dismissal=value(m.dismissal_cost))
        result.material_balances['new_purchased_scrap']=[value(m.a_new_scrap_month[r.material,r.month]) if r.product=='A' else 0
            for r in result.material_balances.itertuples()]
        result.material_orders['unit_price_usd']=[value(m.material_unit_price[r.product,r.material]) for r in result.material_orders.itertuples()]
        result.material_orders['purchase_expense_usd']=result.material_orders.quantity*result.material_orders.unit_price_usd
        if not m.explicit_b_materials:
            result.b_material_consumption['rm_expense_usd']=result.b_material_consumption.rm_kg*value(m.material_unit_price['B','RM'])
            result.b_material_consumption['pm_expense_usd']=result.b_material_consumption.pm_ea*value(m.material_unit_price['B','PM'])
            result.b_material_consumption['material_expense_usd']=result.b_material_consumption.rm_expense_usd+result.b_material_consumption.pm_expense_usd
    from src.shipment_policy import shipment_schedule
    result.shipment_consolidation_policy=m.shipment_consolidation_policy
    result.international_shipment_schedule=shipment_schedule(result.material_orders,m.shipment_consolidation_policy,
        rm_kg_per_pallet=1/m.inventory_pallet_factors['RM'],pm_ea_per_pallet=1/m.inventory_pallet_factors['PM'])
    if len(result.international_shipment_schedule)!=round(value(m.international_shipments)):
        raise ValueError('Shipment groups do not reconcile to the MILP indicators')
    return result


def _schedule_results(m, result):
    v = pyo.value
    start = next(d for d in m.days if v(m.qualification_start[d]) > 0.5)
    def date(d):
        return dict(month=m.day_month[d], planning_day=m.planning_day[d], horizon_day=d)
    result.daily_schedule = pd.DataFrame([dict(line=l, **date(d),
        scheduled=v(m.operating[l, d]), qualified=v(m.qualified[d]), transitioned=v(m.transitioned[d]),
        shutdown=v(m.shutdown[d]), changeover=v(m.changeover[d]) if l == "L2" else 0,
        configuration=next(p for p in m.products if v(m.l2_configuration[p, d]) > .5) if l == "L2" else ("C" if v(m.transitioned[d]) > .5 else "A"),
        production_a=v(m.daily_production[l, "A", d]), production_b=v(m.daily_production[l, "B", d]),
        production_c=v(m.daily_production[l, "C", d])) for l in m.lines for d in m.days])
    records = []
    for p in m.material_products:
        for k in m.materials:
            for d in m.days:
                t = m.day_month[d]
                opening = v(m.initial_material[p, k]) if d == 1 else v(m.daily_material_inventory[p, k, d-1])
                fixed = v(m.fixed_material_arrival[p, k, t]) if m.planning_day[d] == 1 else 0
                added = v(m.additional_material_arrival[p, k, t]) if m.planning_day[d] == 1 else 0
                records.append(dict(product=p, material=k, **date(d), opening=opening,
                    fixed_arrival=fixed, additional_arrival=added,
                    consumption=v(m.bom_quantity[p, k]) * sum(v(m.daily_production[l, p, d]) for l in m.lines),
                    scrap=v(m.a_scrap[k, d]) if p == "A" else 0,
                    ending=v(m.daily_material_inventory[p, k, d])))
    result.daily_material = pd.DataFrame(records)
    result.staffing = pd.DataFrame([dict(line=l, month=t, hired_crew=v(m.hire[l, t]),
        training=v(m.training[l,t]) if hasattr(m,'training') else v(m.hire[l, t]),
        dismissed_crew=v(m.dismiss[l,t]) if hasattr(m,'dismiss') else 0,
        qualified_crew=v(m.upgraded[l,t]),upgraded=v(m.upgraded[l, t]), employed_crews=v(m.employed[l, t]),
        dismissal_usd=v(m.crew_dismissal_fee)*v(m.dismiss[l,t]) if hasattr(m,'dismiss') else 0,
        employed_operators=v(m.employed[l,t])*m._crew_size,
        additional_salary_usd=v(m.crew_salary*m.employed[l, t]), hiring_usd=v(m.crew_hiring_fee*m.hire[l, t])) for l in m.lines for t in m.months])
    result.line_capacity = pd.DataFrame([dict(line=l, month=t, scheduled_days=sum(v(m.operating[l, d]) for d in m.month_days[t]),
        qualification_days=sum(v(m.shutdown[d]) for d in m.month_days[t]),
        changeover_days=sum(v(m.changeover[d]) for d in m.month_days[t]) if l == "L2" else 0,
        capacity_msu=v(m.capacity[l, t]), production_msu=sum(v(m.production[l, p, t]) for p in m.products)) for l in m.lines for t in m.months])
    c_days = [d for d in m.days if sum(v(m.daily_production[l, "C", d]) for l in m.lines) > 1e-5]
    a_days = [d for d in m.days if sum(v(m.daily_production[l, "A", d]) for l in m.lines) > 1e-5]
    pre = result.daily_material.query("product == 'A' and horizon_day == @start")
    result.transition = dict(qualification_start=date(start), shutdown_days=[date(d) for d in range(start, start+m.qualification_duration)],
        c_first_production=date(min(c_days)) if c_days else None,
        a_last_production=date(max(a_days)) if a_days else None,
        a_fp_sellthrough_later_months_msu=sum(v(m.shipment["A", h, t]) for h in m.hubs for t in m.months if t > m.day_month[start]),
        a_fp_shipments_in_transition_month_msu=sum(v(m.shipment["A", h, m.day_month[start]]) for h in m.hubs),
        a_rm_consumed_before_kg=result.daily_material.query("product == 'A' and material == 'RM' and horizon_day < @start").consumption.sum(),
        a_pm_consumed_before_ea=result.daily_material.query("product == 'A' and material == 'PM' and horizon_day < @start").consumption.sum(),
        a_rm_before_scrap_kg=pre.query("material == 'RM'").eval("opening + fixed_arrival + additional_arrival").sum(),
        a_pm_before_scrap_ea=pre.query("material == 'PM'").eval("opening + fixed_arrival + additional_arrival").sum(),
        a_rm_scrap_kg=sum(v(m.a_scrap["RM", d]) for d in m.days),
        a_pm_scrap_ea=sum(v(m.a_scrap["PM", d]) for d in m.days),
        rm_scrap_value_usd=v(m.rm_scrap_value), pm_scrap_value_usd=v(m.pm_scrap_value),
        rm_disposal_usd=v(m.rm_disposal), pm_disposal_usd=v(m.pm_disposal), total_ide_usd=v(m.ide_cost),
        base_salary_usd=v(m.base_labor_cost), new_salary_usd=v(m.new_salary_cost), hiring_usd=v(m.hiring_cost),
        initial_l2_configuration=next(p for p in m.products if v(m.l2_initial[p]) > .5))
    # Conservative diagnostic only: assume all dispatch occurs at month-end.
    # This does not add warehouse constraints or invent a daily delivery schedule.
    fp = sum(v(m.initial_fp[p]) for p in m.products)
    pallet_factors = m.inventory_pallet_factors
    peaks = []
    for d in m.days:
        rows = result.daily_material.query("horizon_day == @d")
        before = fp*pallet_factors["FP"] + sum((r.opening+r.fixed_arrival+r.additional_arrival)*pallet_factors[r.material] for r in rows.itertuples())
        fp += sum(v(m.daily_production[l, p, d]) for l in m.lines for p in m.products)
        after = fp*pallet_factors["FP"] + sum(r.ending*pallet_factors[r.material] for r in rows.itertuples())
        t = m.day_month[d]
        peaks.append(dict(**date(d), tracked_pallets=max(before, after),
            exceeds_booked_monthend_capacity=max(before, after) > v(m.onsite_capacity + m.external_block_pallets*m.external_blocks[t]) + 1e-5))
        if m.planning_day[d] == 28:
            fp -= sum(v(m.shipment[p, h, t]) for p in m.products for h in m.hubs)
    result.storage_peaks = pd.DataFrame(peaks)


def format_summary(results: ModelResults) -> str:
    service = results.service.groupby("hub")[["demand_msu", "served_msu", "unserved_msu"]].sum()
    monthly = results.service.groupby("month")[["demand_msu", "served_msu", "unserved_msu"]].sum()
    service["service_percent"] = 100 * service.served_msu / service.demand_msu.where(service.demand_msu > 0)
    monthly["service_percent"] = 100 * monthly.served_msu / monthly.demand_msu.where(monthly.demand_msu > 0)
    production = results.production.groupby("month").msu.sum().rename("production_msu")
    inventory = results.inventory.groupby("month").msu.sum().rename("ending_fp_msu")
    trucks = results.transport.groupby("month")[["dedicated_trucks", "spot_trucks"]].sum()
    lines = ["Annual hub service (MSU):", service.to_string(float_format=lambda x: f"{x:,.3f}"),
             "Monthly plan:", monthly.join([production, inventory, trucks]).to_string(float_format=lambda x: f"{x:,.3f}"),
             "Modeled costs (USD):"]
    lines.extend(f"  {key}: {'omitted' if amount is None else f'{amount:,.2f}'}" for key, amount in results.costs.items())
    if results.transition:
        import json
        lines.extend(["V4 qualification, sell-through, staffing costs and IDE:", json.dumps(results.transition, indent=2),
            "Staffing (full training salary included):", results.staffing.to_string(index=False),
            "Monthly line capacity after actual shutdown/changeovers:", results.line_capacity.to_string(index=False),
            "L2 actual changeover planning days:", results.daily_schedule.query("line == 'L2' and changeover > 0.5").to_string(index=False),
            "Conservative storage diagnostic: all shipments at month-end; not a verified daily delivery plan.",
            results.storage_peaks.groupby("month").tracked_pallets.max().to_string()])
    lines.extend([f"International dispatch batches ({results.shipment_consolidation_policy}): {len(results.international_shipment_schedule)}",
        f"Material Order Lines (positive material-category orders): {results.material_orders.order_event.sum():.0f}",
        "Fixed incoming shipments (not optimized/new events):", results.fixed_receipts.to_string(index=False),
        "Monthly production by product (MSU):", results.production.groupby(["month", "product"]).msu.sum().unstack().to_string(),
        "Monthly service by hub (MSU):", results.service.groupby(["month", "hub"])[["demand_msu", "served_msu", "unserved_msu"]].sum().to_string(),
        "Month-end tracked warehouse (B physical materials excluded, not zero; intramonth peaks unverified):",
        results.warehouse.to_string(index=False, float_format=lambda x: f"{x:,.3f}")])
    lines.extend(["A/C monthly physical material balances (kg RM; EA PM):",
                  results.material_balances.to_string(index=False, float_format=lambda x: f"{x:,.3f}"),
                  "Additional material orders (positive quantities only):",
                  results.material_orders.query("order_event > 0.5").to_string(index=False, float_format=lambda x: f"{x:,.3f}"),
                  "B theoretical consumption only (physical stock unspecified):",
                  results.b_material_consumption.to_string(index=False, float_format=lambda x: f"{x:,.3f}"),
                  "Year-end A/C materials:", results.material_balances.query("month == month.max()").to_string(index=False),
                  "No negative tracked material stock or material shortage slack is permitted. Unserved customer demand is shown above."])
    return "\n".join(lines)


def write_results(results: ModelResults, outcome, output_dir, *, allow_incumbent=False):
    """Write decision tables only after checked solve/extraction."""
    import json
    from pathlib import Path
    if not outcome.success and not allow_incumbent:
        raise RuntimeError("Cannot export results for an unsuccessful solve.")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("production", "inventory", "shipments", "service", "transport",
                 "material_balances", "material_orders", "b_material_consumption", "warehouse", "fixed_receipts",
                 "daily_schedule", "daily_material", "staffing", "line_capacity", "storage_peaks", "international_shipment_schedule"):
        getattr(results, name).to_csv(directory / f"{name}.csv", index=False)
    service_monthly = results.service.groupby(["hub", "month"])[["demand_msu", "served_msu", "unserved_msu"]].sum()
    service_monthly["service_percent"] = 100 * service_monthly.served_msu / service_monthly.demand_msu.where(service_monthly.demand_msu > 0)
    service_monthly.to_csv(directory / "service_by_hub_month.csv")
    results.production.groupby(["product", "month"]).msu.sum().to_csv(directory / "production_by_product_month.csv")
    (directory / "summary.txt").write_text(
        ("OPTIMAL ALL LEXICOGRAPHIC STAGES\n" if outcome.success else "INCUMBENT ONLY: NOT PROVEN LEXICOGRAPHIC OPTIMAL\n") +
        ("Integrated 28-day planning calendar.\n" if results.transition else "Historical fixed qualification scenario.\n") +
        ("A/B/C materials explicitly balanced and ordered; purchase expense at order placement.\nMonth-end warehouse includes ABC FP, RM and PM; intramonth peaks unverified.\n" if results.material_policy=='explicit_abc_v7' else
         "B materials smoothly replenished; physical stock unspecified.\nMonth-end warehouse includes tracked FP and A/C materials only; intramonth peaks unverified.\n") +
        "PM expiry unverified; C:D is diagnostic, not constrained. See ASSUMPTIONS.md.\n"
        f"Minimum monetary cost: {outcome.minimum_cost}; allowed maximum: {outcome.cost_limit}\n\n"
        f"Shipment policy: {results.shipment_consolidation_policy}; international dispatch batches: {len(results.international_shipment_schedule)}; material order lines: {int((results.material_orders.quantity>1e-5).sum())}\n"
        + format_summary(results), encoding="utf-8")
    (directory / "solve_status.json").write_text(json.dumps(
        dict(success=outcome.success, message=outcome.message, stages=outcome.stages,
             minimum_cost=outcome.minimum_cost, cost_limit=outcome.cost_limit,
             shipment_consolidation_policy=results.shipment_consolidation_policy,
             international_shipments=len(results.international_shipment_schedule),
             material_order_lines=int((results.material_orders.quantity>1e-5).sum()),
             material_policy=results.material_policy,costs=results.costs), indent=2), encoding="utf-8")
    if results.transition:
        (directory / "transition_ide.json").write_text(json.dumps(results.transition, indent=2), encoding="utf-8")
        baseline = Path(__file__).resolve().parents[1] / "reports/v2_1/scenario_a/solve_status.json"
        if baseline.exists():
            historical = json.loads(baseline.read_text(encoding="utf-8"))
            comparison = dict(v4_all_stages_optimal=outcome.success,
                historical_v2_1_scenario_a=historical["costs"], v4_reported=results.costs,
                cost_difference_usd=results.costs["total_modeled"]-historical["costs"]["total_modeled"],
                annual_demand_msu=float(results.service.demand_msu.sum()),
                annual_served_msu=float(results.service.served_msu.sum()),
                annual_service_percent=(float(100*results.service.served_msu.sum()/results.service.demand_msu.sum()) if results.service.demand_msu.sum()>0 else None),
                additional_international_events=float(results.material_orders.order_event.sum()))
            (directory / "historical_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")


def write_comparison(a: ModelResults, a_status, b: ModelResults, b_status, output_dir):
    """Summarize two checked runs; full monthly detail remains in their folders."""
    from pathlib import Path
    if not a_status.success or not b_status.success:
        raise RuntimeError("Comparison requires both scenarios to solve optimally")
    rows = []
    for key in a.costs:
        if key != "ide":
            rows.append((key + " USD", a.costs[key], b.costs[key]))
    rows += [("Minimum monetary cost USD", a_status.minimum_cost, b_status.minimum_cost),
             ("Allowed cost ceiling USD", a_status.cost_limit, b_status.cost_limit),
             ("Additional material-specific events", a.material_orders.order_event.sum(), b.material_orders.order_event.sum()),
             ("Fixed incoming shipments (separate)", len(a.fixed_receipts), len(b.fixed_receipts)),
             ("Served MSU", a.service.served_msu.sum(), b.service.served_msu.sum()),
             ("Service %", 100 * a.service.served_msu.sum() / a.service.demand_msu.sum(), 100 * b.service.served_msu.sum() / b.service.demand_msu.sum()),
             ("External block-months", a.warehouse.external_blocks.sum(), b.warehouse.external_blocks.sum()),
             ("Peak tracked month-end pallets", a.warehouse.tracked_pallets.max(), b.warehouse.tracked_pallets.max())]
    for p in ("A", "C"):
        for k in ("RM", "PM"):
            rows.append((f"Additional {p} {k} total (kg/EA)",
                a.material_orders.query("product == @p and material == @k").quantity.sum(),
                b.material_orders.query("product == @p and material == @k").quantity.sum()))
            rows.append((f"Year-end {p} {k} (kg/EA)",
                a.material_balances.query("product == @p and material == @k").iloc[-1].ending,
                b.material_balances.query("product == @p and material == @k").iloc[-1].ending))
    comparison = pd.DataFrame(rows, columns=["metric", "scenario_a", "scenario_b"])
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(directory / "comparison.csv", index=False)
    lines = ["# V2.1 strict-cost versus 2% consolidation sensitivity", "",
             "Both scenarios solved all service, cost, event and quantity stages to optimality.", "",
             "| Metric | Scenario A: zero tolerance | Scenario B: 2% tolerance |",
             "| --- | ---: | ---: |"]
    lines += [f"| {name} | {va:,.4f} | {vb:,.4f} |" for name, va, vb in rows]
    extra_storage = b.costs["external_storage"] - a.costs["external_storage"]
    delta = b.costs["total_modeled"] - a.costs["total_modeled"]
    lines += ["", f"The more consolidated plan adds ${delta:,.2f} in total modeled cost, "
              f"including ${extra_storage:,.2f} in external storage. "
              "This expense is induced by the consolidated procurement plan; Scenario A needs no paid overflow for this case.",
              "", "The final cost cleanup removes gratuitous spending after event count and procurement quantity are fixed. "
              "Alternative monthly schedules can remain optimal.",
              "", "Each scenario folder contains summary.txt plus CSVs for hub/month service, production, "
              "orders and arrival months, material balances, warehouse blocks/costs, fixed receipts and B theoretical usage.",
              "", "B physical material footprint is unspecified/excluded, not zero. Month-end storage does not verify intramonth peaks. "
              "IDE, expiry, optimized hiring/qualification and daily sequencing remain omitted; see ../../MODEL_SCOPE.md."]
    (directory / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    # Reporting-only entry point: consumes existing saved V4 decisions, no solve.
    from src.reconciliation import main
    raise SystemExit(main())
