"""Numerical audit of the exact active MILP, independent of solver status claims."""
import pyomo.environ as pyo


def audit_solution(model, tolerance=1e-5):
    violations = []
    constraints = variables = 0
    maximum = 0.0
    for var in model.component_data_objects(pyo.Var):
        variables += 1
        if var.value is None:
            violations.append(dict(name=var.name, error="uninitialized"))
            continue
        error = 0.0
        if var.lb is not None:
            error = max(error, pyo.value(var.lb)-var.value)
        if var.ub is not None:
            error = max(error, var.value-pyo.value(var.ub))
        if var.is_integer():
            error = max(error, abs(var.value-round(var.value)))
        maximum = max(maximum, error)
        if error > tolerance:
            violations.append(dict(name=var.name, violation=error))
    for con in model.component_data_objects(pyo.Constraint, active=True):
        constraints += 1
        body = pyo.value(con.body, exception=False)
        if body is None:
            violations.append(dict(name=con.name, error="uninitialized body"))
            continue
        error = 0.0
        if con.lower is not None:
            error = max(error, pyo.value(con.lower)-body)
        if con.upper is not None:
            error = max(error, body-pyo.value(con.upper))
        maximum = max(maximum, error)
        if error > tolerance:
            violations.append(dict(name=con.name, violation=error))
    return dict(passed=not violations, tolerance=tolerance, constraints_checked=constraints,
                variables_checked=variables, max_violation=maximum, violations=violations)


def audit_exported_schedule(data, directory):
    """Reconstruct exported variable levels in the original V4 MILP and audit.

    Does not optimize, infer missing levels or change proof status. Useful for
    independently checking a saved incumbent or an earlier export.
    """
    import json
    from pathlib import Path
    import pandas as pd
    from src.model import build_model
    directory = Path(directory)
    m = build_model(data)
    def read(name):
        return pd.read_csv(directory / f"{name}.csv")
    def assign(var, level):
        var.set_value(float(level), skip_validation=True)
    transition = json.loads((directory / "transition_ide.json").read_text())
    start = transition["qualification_start"]["horizon_day"]
    for d in m.days:
        assign(m.qualification_start[d], int(d == start))
        assign(m.transitioned[d], int(d >= start))
    for p in m.products:
        assign(m.l2_initial[p], int(p == transition["initial_l2_configuration"]))
    for r in read("daily_schedule").itertuples():
        d = r.horizon_day
        for p, col in (("A", "production_a"), ("B", "production_b"), ("C", "production_c")):
            assign(m.daily_production[r.line, p, d], getattr(r, col))
            if r.line == "L2":
                assign(m.l2_configuration[p, d], int(p == r.configuration))
        if r.line == "L2":
            assign(m.changeover[d], r.changeover)
    for r in read("staffing").itertuples():
        assign(m.hire[r.line, r.month], r.hired_crew)
        assign(m.upgraded[r.line, r.month], r.upgraded)
    for r in read("daily_material").itertuples():
        assign(m.daily_material_inventory[r.product, r.material, r.horizon_day], r.ending)
        if r.product == "A":
            assign(m.a_scrap[r.material, r.horizon_day], r.scrap)
    for r in read("material_balances").itertuples():
        assign(m.material_inventory[r.product, r.material, r.month], r.ending)
    for r in read("material_orders").itertuples():
        key = r.product, r.material, r.order_month
        assign(m.material_order[key], r.quantity)
        assign(m.integer_lots[key], r.integer_lots)
        assign(m.order_event[key], r.order_event)
    for r in read("production").itertuples():
        assign(m.production[r.line, r.product, r.month], r.msu)
    for r in read("inventory").itertuples():
        assign(m.inventory[r.product, r.month], r.msu)
    for r in read("shipments").itertuples():
        assign(m.shipment[r.product, r.hub, r.month], r.msu)
    for r in read("service").itertuples():
        assign(m.unserved[r.hub, r.family, r.month], r.unserved_msu)
    for r in read("transport").itertuples():
        assign(m.dedicated[r.hub, r.month], r.dedicated_trucks)
        assign(m.spot[r.hub, r.month], r.spot_trucks)
    for r in read("warehouse").itertuples():
        assign(m.external_blocks[r.month], r.external_blocks)
    status = json.loads((directory / "solve_status.json").read_text())
    m.exported_objective_locks = pyo.ConstraintList()
    if status["cost_limit"] is not None:
        m.exported_objective_locks.add(m.total_cost <= status["cost_limit"])
    for stage in status["stages"]:
        if stage["name"].startswith("service_") and stage["termination"] == "optimal":
            hub = stage["name"].split("service_", 1)[1]
            m.exported_objective_locks.add(m.shortage_by_hub[hub] == stage["optimum"])
    result = audit_solution(m)
    result["reported_monetary_cost"] = pyo.value(m.total_cost)
    result["reported_international_events"] = pyo.value(m.additional_order_events)
    result["all_lexicographic_stages_optimal"] = status["success"]
    return result


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    from src.data_loader import load_case
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/v4"))
    args = parser.parse_args()
    result = audit_exported_schedule(load_case(), args.report_dir)
    (args.report_dir / "solution_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
