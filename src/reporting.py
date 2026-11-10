"""Reproducible reporting from saved solver decisions, without optimization."""
import json
from hashlib import sha256
from pathlib import Path
import pandas as pd
from src.data_loader import load_case, ROOT
from src.reconciliation import read_saved, calculate, markdown
from src.kpis import calculate_kpis


def generate_reports(data, directory, baseline=ROOT / "reports/v4"):
    directory, baseline = Path(directory), Path(baseline)
    if directory.resolve() == baseline.resolve():
        raise ValueError("V5 reporting must not overwrite the historical V4 baseline")
    tables, status = read_saved(directory)
    if status.get('material_policy')=='explicit_abc_v7' and (directory/'effective_inputs.json').exists():
        from src.parameters import case_from_snapshot
        data=case_from_snapshot(data,json.loads((directory/'effective_inputs.json').read_text(encoding='utf-8')))
    if 'total_delivery_cost' in status['costs']:
        from src.report_v6 import generate
        return generate(data,directory)
    for name in ("daily_schedule", "line_capacity", "material_orders"):
        tables[name] = pd.read_csv(directory / f"{name}.csv", float_precision="round_trip")
    financial = calculate(data, tables, status)
    outputs = calculate_kpis(data, tables, financial)
    outputs.update(monthly_production_inventory=financial.monthly,
                   monthly_inventory_by_product=financial.products,
                   monthly_cost_breakdown=financial.costs)
    for name, frame in outputs.items():
        frame.to_csv(directory / f"{name}.csv", index=False)
    comparison = []
    old = json.loads((baseline / "solve_status.json").read_text())
    for key, value in status["costs"].items():
        comparison.append(dict(metric=key, v4=old["costs"].get(key), v5=value,
            difference=value-old["costs"][key] if value is not None and old["costs"].get(key) is not None else None))
    old_capacity = pd.read_csv(baseline / "line_capacity.csv")
    old_service = pd.read_csv(baseline / "service.csv")
    for metric, before, after in (
        ("served_msu", old_service.served_msu.sum(), tables["service"].served_msu.sum()),
        ("available_capacity_msu", old_capacity.capacity_msu.sum(), tables["line_capacity"].capacity_msu.sum()),
        ("routine_changeover_days", old_capacity.changeover_days.sum(), tables["line_capacity"].changeover_days.sum())):
        comparison.append(dict(metric=metric,v4=float(before),v5=float(after),difference=float(after-before)))
    pd.DataFrame(comparison).to_csv(directory / "v4_comparison.csv", index=False)
    old_transition = json.loads((baseline / "transition_ide.json").read_text())
    transition = json.loads((directory / "transition_ide.json").read_text())
    compare_plan = dict(v4_transition=old_transition, v5_transition=transition)
    for name, col in (("production", "msu"), ("staffing", "hired_crew"),
                       ("warehouse", "external_blocks"), ("transport", "spot_trucks")):
        before = pd.read_csv(baseline / f"{name}.csv")
        after = tables[name]
        compare_plan[name] = dict(v4_total=float(before[col].sum()), v5_total=float(after[col].sum()))
    old_orders = pd.read_csv(baseline / "material_orders.csv")
    compare_plan["material_orders"] = [dict(product=p, material=k,
        v4_quantity=float(old_orders.query("product == @p and material == @k").quantity.sum()),
        v5_quantity=float(tables["material_orders"].query("product == @p and material == @k").quantity.sum()))
        for p in ("A", "C") for k in ("RM", "PM")]
    monthly_comparisons = []
    for name, keys, values in (
        ("production", ["month", "line", "product"], ["msu"]),
        ("material_orders", ["order_month", "arrival_month", "product", "material"], ["quantity", "order_event"]),
        ("transport", ["month", "hub"], ["dedicated_trucks", "spot_trucks"]),
        ("line_capacity", ["month", "line"], ["capacity_msu", "changeover_days"]),
        ("staffing", ["month", "line"], ["hired_crew", "upgraded"]),
        ("warehouse", ["month"], ["tracked_pallets", "external_blocks"])):
        previous = pd.read_csv(baseline / f"{name}.csv").set_index(keys)
        current = tables[name].set_index(keys)
        for key in current.index:
            labels = dict(zip(keys,key if isinstance(key,tuple) else (key,)))
            for col in values:
                a,b = float(previous.loc[key,col]),float(current.loc[key,col])
                monthly_comparisons.append(dict(table=name,metric=col,**labels,v4=a,v5=b,difference=b-a))
    pd.DataFrame(monthly_comparisons).to_csv(directory / "monthly_plan_comparison.csv",index=False)
    (directory / "plan_comparison.json").write_text(json.dumps(compare_plan, indent=2))
    monetary = next((s for s in status["stages"] if s["name"] == "modeled_cost"), {})
    dashboard = dict(costs=status["costs"], all_stages_optimal=status["success"],
        monetary_stage=monetary, stages=status["stages"], annual_demand_msu=float(tables["service"].demand_msu.sum()),
        annual_shipments_msu=float(tables["service"].served_msu.sum()),
        additional_order_events=float(tables["material_orders"].order_event.sum()),
        monthly=json.loads(outputs["monthly_operations"].to_json(orient="records")),
        cash=json.loads(outputs["cash"].to_json(orient="records")))
    (directory / "dashboard.json").write_text(json.dumps(dashboard, indent=2, allow_nan=False))
    protected = list((ROOT / "data").glob("Venus_PS_*")) + list(baseline.glob("*"))
    (directory / "source_fingerprints.json").write_text(json.dumps({
        str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
        for p in protected if p.is_file()}, indent=2))
    ratios = outputs["cumulative_indicators"][["month", "available_capacity_msu", "cumulative_capacity_msu",
        "total_production_msu", "cumulative_supply_msu", "cumulative_demand_msu", "capacity_to_demand", "supply_to_demand",
        "monthly_service_fraction", "cumulative_service_fraction"]]
    text = "\n".join(["# V5 strict Scenario A: operational and financial reconciliation", "",
        f"Monetary termination: **{monetary.get('termination')}**; minimum ${status['minimum_cost']:,.2f}. "
        f"All-stage optimality: **{status['success']}**. Secondary status is not a monetary proof.", "",
        "## Solver stages", "", markdown(pd.DataFrame(status["stages"])), "",
        "## 1. Capacity and manufacturing plan", "", markdown(ratios), "",
        "Capacity is physically available line-day capacity after qualification/changeovers and training. "
        "Production is actual manufacturing. Supply includes initial FP once; shipments are actual customer deliveries. "
        "Ratios below one are flagged in cumulative_indicators.csv. Zero-demand ratios are undefined, not zero. "
        "Both C:D interpretations are diagnostics, not feasibility constraints; full service alone does not prove both ratios exceed one.", "",
        "## 2. Transition and IDE", "", "```json", json.dumps(transition, indent=2), "```", "",
        "## 3. Inventory, cash and warehouse", "", markdown(outputs["cash"]), "",
        f"Inventory value is a balance-sheet KPI and is not added to expenses. FP holding is {100 * data.rules['fp_holding_fraction_month']:g}% of product-specific "
        f"ending value. A/C RM/PM valuation uses input ${data.rules['rm_usd_per_kg']:g}/kg and ${data.rules['pm_usd_per_ea']:g}/EA. B physical material value/space is unspecified and excluded. "
        "Month-end storage is constrained; intramonth peaks are not verified. See storage_peaks.csv for a conservative dispatch diagnostic.", "",
        "## 4. Regional service and distribution", "",
        "service.csv separates hub/family/month demand, shipments and shortages; transport.csv shows dedicated/spot trucks. "
        "Exact monthly priorities apply separately to A/C and B, including every higher/lower regional pair.", "",
        "## 5. Annual costs and comparison", "", markdown(pd.DataFrame(comparison)), "",
        f"V4 qualification began {old_transition['qualification_start']['month']} planning day "
        f"{old_transition['qualification_start']['planning_day']}; this V5 plan begins "
        f"{transition['qualification_start']['month']} day {transition['qualification_start']['planning_day']}. "
        "Different equally cost-optimal daily schedules/order timings may exist; the objective does not separately "
        "prefer a particular planning day. Full service, production volume, salaries and expense components must "
        "be compared independently rather than inferring an improvement from a changed date. "
        "plan_comparison.json records these differences, including separate RM and PM quantities (never added across units).", "",
        "The selected plan consumes the available A raw material before qualification, avoiding its scrap value/disposal "
        "while leaving unavoidable unmatched A packaging visible in IDE. C then supplies the shared family without any "
        "duplicated demand or additional A manufacturing. Prebuilding FP at base profiles covers the summer peaks; "
        "the selected cost optimum does not hire crews or rent external blocks. These are integrated service/cost "
        "trade-offs, not a claim that the selected day or every procurement date is unique.", "",
        "## Monthly production / inventory", "", markdown(financial.monthly), "",
        "## Monthly financial reconciliation (USD)", "", markdown(financial.costs), "",
        "## Productivity", "", markdown(outputs["productivity"]), "",
        "Available-day utilization is production/capacity. Manufacturing days count days with positive output; equivalent "
        "full-rate days account for partial days. MSU per employed operator includes paid trainees and is a separate labor KPI.", "",
        "## Assumptions and reproduction", "",
        "See ../../ASSUMPTIONS.md and ../../FINAL_OPTIMIZER_READINESS.md. Packaging usability is unverified; no detailed expiry. "
        "No overtime/headcount ceiling is invented. No material purchase expense or daily customer dispatch is introduced.", "",
        "`python -m src.reporting --report-dir reports/v5` regenerates these derived reports without solving. "
        "`python -m src.solve --output-dir reports/v5 --time-limit 180` rebuilds and solves strict Scenario A.", ""])
    (directory / "ANALYSIS.md").write_text(text, encoding="utf-8")
    (directory / "FINANCIAL_RECONCILIATION.md").write_text(
        "# Independent monthly financial reconciliation\n\n" + markdown(financial.costs) +
        "\n\nComputed from unrounded solver quantities and loader rates, independently of model expressions. "
        f"Salaries = employed operators x ${data.rules['operator_usd_per_month']:g}/month, hiring = new operators x ${data.rules['hiring_usd_per_operator']:g}; "
        f"FP holding = ending MSU x individual product value x {data.rules['fp_holding_fraction_month']:g}; transport = integer trucks x hub rate "
        f"(spot x {1+data.rules['spot_surcharge_fraction']:g}); penalty = unserved MSU x hub penalty; storage = blocks x {data.rules['overflow_block_pallets']:g} x ${data.rules['overflow_usd_per_pallet_month']:g}. "
        f"RM IDE = scrap kg x (${data.rules['rm_usd_per_kg']:g} + ${data.rules['disposal_usd_per_ton']:g}/1000); PM IDE = scrap EA x (${data.rules['pm_usd_per_ea']:g} + {data.rules['pm_kg_per_1000_ea']/1000:g} x ${data.rules['disposal_usd_per_ton']:g}/1000). "
        "No material purchase cost, inventory-value expense or intermediate rounding.\n\n" +
        json.dumps(financial.diagnostics, indent=2), encoding="utf-8")
    summary = directory / "summary.txt"
    marker = "\n=== V5 MONTHLY RECONCILIATION ===\n"
    prefix = summary.read_text(encoding="utf-8").split(marker)[0].replace(
        "V4 integrated planning calendar.", "Integrated 28-day planning calendar.")
    summary.write_text(prefix + marker + markdown(financial.monthly) + "\n\n" + markdown(financial.costs) +
        "\n\n" + markdown(ratios) + "\n", encoding="utf-8")
    return outputs


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports/v7")
    args = parser.parse_args()
    generate_reports(load_case(), args.report_dir)
    print(f"Reports regenerated without solving: {args.report_dir}")


if __name__ == "__main__":
    main()
