"""Run strict hub service, monetary cost, order consolidation and tie-breaks."""
from dataclasses import dataclass, field
from math import isfinite

import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition


@dataclass
class SolveOutcome:
    success: bool
    message: str
    stages: list[dict] = field(default_factory=list)
    minimum_cost: float | None = None
    cost_limit: float | None = None


def _procurement_warm_start(model, seconds=20):
    """Primal heuristic ONLY: optimize orders for the current daily schedule.

    The original model is never fixed or relaxed. Copy a feasible candidate
    back as starting values, then solve the original unrestricted event MILP.
    """
    candidate = model.clone()
    for name in ("daily_production", "hire", "upgraded", "qualification_start", "transitioned",
                 "l2_configuration", "l2_initial", "changeover"):
        for var in candidate.find_component(name).values():
            level = pyo.value(var)
            var.fix(round(level) if var.is_integer() else max(0, level), skip_validation=True)
    candidate.objective.set_value(candidate.additional_order_events)
    solver = pyo.SolverFactory("appsi_highs")
    solver.options["time_limit"] = seconds
    solver.options["mip_rel_gap"] = 0.0
    solver.options["mip_abs_gap"] = 0.0
    result = solver.solve(candidate, load_solutions=False, warmstart=True)
    if not len(result.solution):
        return None
    candidate.solutions.load_from(result)
    for component in model.component_objects(pyo.Var):
        other = candidate.find_component(component.name)
        for key, var in component.items():
            if other[key].value is not None:
                var.set_value(other[key].value, skip_validation=True)
    return float(pyo.value(candidate.additional_order_events))


def solve_lexicographic(model, *, cost_tolerance=0.0, tee=False, solver=None, time_limit=120, progress=False, stage_callback=None) -> SolveOutcome:
    """Advance only after proven optimality; label any fallback/incumbent report.

    Service optima are fixed by equality (subject to solver feasibility tolerance).
    No weighted penalty surrogate is used for priority ordering.
    """
    model._solve_success = False
    model._has_incumbent = False
    if not isfinite(cost_tolerance) or cost_tolerance < 0:
        raise ValueError("Cost tolerance must be a finite nonnegative fraction")
    if cost_tolerance != 0:
        raise ValueError("Strict Scenario A only: cost tolerance must be zero")
    if time_limit is not None and (not isfinite(time_limit) or time_limit <= 0):
        raise ValueError("Time limit must be positive and finite")
    if model.component("service_locks") is not None:
        model.del_component("service_locks")
    model.service_locks = pyo.ConstraintList()
    solver = solver if solver is not None else pyo.SolverFactory("appsi_highs")
    stages = []
    minimum_cost = cost_limit = None
    try:
        if not solver.available(exception_flag=False):
            return SolveOutcome(False, "HiGHS is unavailable; check the active Python environment.")
        solver.options["mip_rel_gap"] = 0.0
        solver.options["mip_abs_gap"] = 0.0
        if time_limit is not None:
            solver.options["time_limit"] = time_limit
        expressions = [(f"service_{hub}", model.shortage_by_hub[hub]) for hub in model.priority_hubs]
        expressions.append(("modeled_cost", model.total_cost))
        expressions.append(("international_order_events", model.additional_order_events))
        expressions.append(("procurement_quantity_tiebreak", model.procurement_tiebreak))
        # Cleanup only within tied event/quantity optima; all earlier locks stay.
        expressions.append(("cost_cleanup", model.total_cost))
        for name, expression in expressions:
            if stage_callback:
                stage_callback(name, "running", {})
            if progress:
                print(f"Solving {name} (per-stage limit {time_limit}s)", flush=True)
            model.objective.set_value(expression)
            if (name == "international_order_events" and getattr(model, "integrated_schedule", False)
                    and any(not var.fixed for var in model.daily_production.values())):
                try:
                    events = _procurement_warm_start(model)
                    if progress:
                        print(f"Schedule-fixed primal heuristic: {events} events; full scheduling decisions remain free", flush=True)
                except Exception as exc:
                    if progress:
                        print(f"Optional warm-start heuristic unavailable: {exc}", flush=True)
            kwargs = dict(tee=tee, load_solutions=False)
            if hasattr(solver, "warm_start_capable") and solver.warm_start_capable():
                kwargs["warmstart"] = model._has_incumbent
            result = solver.solve(model, **kwargs)
            status = result.solver.status
            termination = result.solver.termination_condition
            stage = dict(name=name, status=str(status), termination=str(termination))
            problem = result.problem[0] if hasattr(result, "problem") and len(result.problem) else None
            if problem is not None:
                for key in ("lower_bound", "upper_bound"):
                    try:
                        bound = float(getattr(problem, key))
                        if isfinite(bound):
                            stage[key] = bound
                    except (TypeError, ValueError):
                        pass
                if "lower_bound" in stage and "upper_bound" in stage:
                    stage["relative_gap"] = abs(stage["upper_bound"] - stage["lower_bound"]) / max(1e-10, abs(stage["upper_bound"]))
            stages.append(stage)
            if stage_callback:
                stage_callback(name, "completed" if termination == TerminationCondition.optimal and status == SolverStatus.ok else "stopped", stage.copy())
            if status != SolverStatus.ok or termination != TerminationCondition.optimal:
                if hasattr(result, "solution") and len(result.solution):
                    model.solutions.load_from(result)
                    model._has_incumbent = True
                    stage["incumbent_objective"] = float(pyo.value(expression))
                elif model._has_incumbent:
                    # The previous proven stage's solution remains feasible:
                    # only its attained optimum was locked before this solve.
                    stage["incumbent_objective"] = float(pyo.value(expression))
                    stage["incumbent_source"] = "previous proven stage (fallback)"
                if model._has_incumbent and "lower_bound" in stage:
                    stage["incumbent_gap"] = abs(stage["incumbent_objective"]-stage["lower_bound"]) / max(1e-10, abs(stage["incumbent_objective"]))
                return SolveOutcome(False, f"{name}: {status}, {termination}; later stages not run; any exported incumbent is not fully lexicographic optimal.", stages, minimum_cost, cost_limit)
            model.solutions.load_from(result)
            model._has_incumbent = True
            optimum = float(pyo.value(expression))
            stage["optimum"] = optimum
            if name == "modeled_cost":
                minimum_cost = optimum
                cost_limit = optimum * (1 + cost_tolerance)
                model.service_locks.add(expression <= cost_limit)
            elif name != "cost_cleanup":
                model.service_locks.add(expression == optimum)
    except Exception as exc:
        return SolveOutcome(False, f"Solver execution failed: {exc}", stages, minimum_cost, cost_limit)
    model._solve_success = True
    return SolveOutcome(True, "All service, cost, order-event and quantity stages solved to optimality.", stages, minimum_cost, cost_limit)


def main():
    import argparse
    from pathlib import Path
    from src.data_loader import load_case, validate_case
    from src.model import build_model
    from src.results import extract_results, format_summary, write_results
    parser = argparse.ArgumentParser(description="V7 strict Scenario A / explicit ABC procurement")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/v7"))
    parser.add_argument("--time-limit", type=float, default=120, help="Seconds per stage; nonoptimal stages are reported honestly")
    parser.add_argument("--tee", action="store_true")
    args = parser.parse_args()
    from src.data_loader import ROOT
    for name in ("v2", "v2_1", "v4", "v5", "v6"):
        historical = (ROOT / "reports" / name).resolve()
        target = args.output_dir.resolve()
        if target == historical or historical in target.parents:
            parser.error("Use a new output directory; historical V2/V2.1/V4 reports are preserved")
    data = load_case()
    errors, _ = validate_case(data)
    if errors:
        print("Input validation failed: " + str(errors))
        return 1
    if (args.output_dir/'solve_status.json').exists(): parser.error('Use a fresh directory; existing solver results are immutable.')
    from src.material_policy import planning_case
    data=planning_case(data)
    model = build_model(data)
    print("V7 Scenario A only: explicit ABC materials; 12 months x 28 planning days", flush=True)
    outcome = solve_lexicographic(model, time_limit=args.time_limit, progress=True, tee=args.tee)
    print(outcome.message)
    for stage in outcome.stages:
        print(stage)
    if outcome.success or model._has_incumbent:
        import json
        from src.validation import audit_solution
        audit = audit_solution(model)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "solution_audit.json").write_text(json.dumps(audit, indent=2))
        if not audit["passed"]:
            print(f"Solution audit failed: {audit}")
            return 1
        results = extract_results(model, allow_incumbent=not outcome.success)
        print(format_summary(results))
        write_results(results, outcome, args.output_dir, allow_incumbent=not outcome.success)
        # A feasible monetary optimum remains publishable if a secondary stage times out.
        if outcome.minimum_cost is not None:
            from src.reporting import generate_reports
            generate_reports(data, args.output_dir)
    else:
        import json
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "solve_status.json").write_text(json.dumps(outcome.__dict__, indent=2))
    print("ABC material space tracked; PM expiry unverified; both C:D diagnostics reported.")
    print("Month-end warehouse checks do not verify intramonth peaks. See MODEL_SCOPE.md.")
    return 0 if outcome.success or (outcome.minimum_cost is not None and model._has_incumbent and audit["passed"]) else 1



if __name__ == "__main__":
    raise SystemExit(main())
