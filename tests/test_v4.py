"""V4 exact synthetic schedules with independently calculated balances/costs.

Synthetic quantities and fixed schedules below are diagnostics, not case inputs.
The original 12-month sources are never modified.
"""
from copy import deepcopy

import pyomo.environ as pyo
import pytest

from src.data_loader import load_case
from src.model import build_model
from src.results import extract_results, write_results
from src.scheduling import scheduled
from src.solve import solve_lexicographic
from src.validation import audit_solution, audit_exported_schedule

TOL = 1e-5


@pytest.fixture(scope="module")
def case():
    return load_case()


def diagnostic(case, start=10):
    """No production, purchases or upgrades, fixed qualification, L2 stays B."""
    m = build_model(case)
    for d in m.days:
        m.qualification_start[d].fix(int(d == start))
        m.changeover[d].fix(0)
        for p in m.products:
            m.l2_configuration[p, d].fix(int(p == "B"))
            for l in m.lines:
                m.daily_production[l, p, d].fix(0)
    for p in m.products:
        m.l2_initial[p].fix(int(p == "B"))
    for key in m.hire:
        m.hire[key].fix(0)
    for key in m.material_order:
        m.material_order[key].fix(0)
    return m


def solve(m):
    outcome = solve_lexicographic(m, time_limit=30)
    assert outcome.success, outcome.message
    return extract_results(m), outcome


def test_four_week_calendar(case):
    m = build_model(case)
    assert len(m.days) == 336
    for t in m.months:
        assert len(m.month_days[t]) == 28
        assert [m.planning_day[d] for d in m.month_days[t]] == list(range(1, 29))
        assert [sum(scheduled(d, profile) for d in m.month_days[t]) for profile in (5, 6, 7)] == [20, 24, 28]
    assert len(m.qualification_candidates) == 144
    for d in m.qualification_candidates:
        assert all(scheduled(u, 5) and scheduled(u, 6) for u in range(d, d+3))


def test_chronological_scrap_and_finished_goods_sellthrough(case, tmp_path):
    data = deepcopy(case)
    data.initial_materials.loc[data.initial_materials["product"] == "A", "quantity"] = [1000, 5000]
    data.arrivals.quantity = 0
    m = diagnostic(data, start=10)
    m.daily_production["L1", "A", 1].fix(1)
    m.shipment["A", "H1", "2026-11"].fix(1)
    result, outcome = solve(m)
    tr = result.transition
    assert tr["qualification_start"] == dict(month="2026-10", planning_day=10, horizon_day=10)
    assert [r["horizon_day"] for r in tr["shutdown_days"]] == [10, 11, 12]
    assert tr["a_rm_consumed_before_kg"] == 500
    assert tr["a_pm_consumed_before_ea"] == 2500
    assert tr["a_rm_scrap_kg"] == 500
    assert tr["a_pm_scrap_ea"] == 2500
    assert tr["rm_scrap_value_usd"] == 2500
    assert tr["rm_disposal_usd"] == 100
    assert tr["pm_scrap_value_usd"] == 1000
    assert tr["pm_disposal_usd"] == 10
    assert tr["total_ide_usd"] == 3610
    assert tr["a_fp_sellthrough_later_months_msu"] >= 1
    assert result.daily_material.query("product == 'A' and horizon_day >= 10").ending.sum() == 0
    for r in result.daily_material.itertuples():
        assert r.opening + r.fixed_arrival + r.additional_arrival - r.consumption - r.scrap == pytest.approx(r.ending, abs=TOL)
        if r.scrap > TOL:
            assert r.product == "A" and r.horizon_day == 10
    for r in result.material_balances.itertuples():
        assert r.opening+r.fixed_arrival+r.additional_arrival-r.consumption-r.scrap == pytest.approx(r.ending, abs=TOL)
    assert result.costs["total_modeled"] == pytest.approx(sum(v for k, v in result.costs.items() if k != "total_modeled"), abs=.01)
    assert result.costs["labor"] == 840000
    assert result.staffing.hired_crew.sum() == 0
    assert audit_solution(m)["passed"]
    assert result.line_capacity.query("line == 'L1' and month == '2026-10'").capacity_msu.item() == 102
    assert result.line_capacity.query("line == 'L2' and month == '2026-10'").capacity_msu.item() == 168
    assert len(result.service) == 72
    assert result.service.demand_msu.sum() == 3095
    write_results(result, outcome, tmp_path)
    assert (tmp_path / "transition_ide.json").exists()
    assert (tmp_path / "daily_schedule.csv").exists()
    assert audit_exported_schedule(data, tmp_path)["passed"]


@pytest.mark.parametrize("start", [5, 6, 7, 27, 28, 336])
def test_qualification_cannot_use_nonworking_days(case, start):
    m = diagnostic(case, start)
    outcome = solve_lexicographic(m, time_limit=10)
    assert not outcome.success
    assert "infeasible" in outcome.message.lower()


@pytest.mark.parametrize("line,product,day", [("L1", "A", 10), ("L2", "B", 11), ("L1", "A", 29), ("L1", "C", 8)])
def test_transition_and_shutdown_block_forbidden_production(case, line, product, day):
    m = diagnostic(case, 10)
    m.daily_production[line, product, day].fix(1)
    outcome = solve_lexicographic(m, time_limit=10)
    assert not outcome.success


def configure(m, product_for_day, initial="B"):
    for p in m.products:
        m.l2_initial[p].fix(int(p == initial))
    for d in m.days:
        m.changeover[d].unfix()
        for p in m.products:
            m.l2_configuration[p, d].fix(int(p == product_for_day(d)))


@pytest.mark.parametrize("mode,feasible,expected_changes", [
    ("same", True, 0), ("boundary", True, 1), ("weekend", False, None),
    ("two_in_month", False, None), ("a_to_c_qualification", True, 0),
    ("b_to_c_qualification", False, None), ("b_to_c_after", True, 1)])
def test_exact_l2_configuration_carry_and_changeovers(case, mode, feasible, expected_changes):
    m = diagnostic(case, 1)
    if mode == "same":
        configure(m, lambda d: "B")
    elif mode == "boundary":
        configure(m, lambda d: "B" if d < 29 else "C")
    elif mode == "weekend":
        configure(m, lambda d: "B" if d < 7 else "C")
    elif mode == "two_in_month":
        configure(m, lambda d: "C" if 8 <= d < 15 else "B")
    elif mode == "a_to_c_qualification":
        configure(m, lambda d: "C", initial="A")
    elif mode == "b_to_c_qualification":
        configure(m, lambda d: "C", initial="B")
    else:
        configure(m, lambda d: "B" if d < 4 else "C")
    outcome = solve_lexicographic(m, time_limit=20)
    assert outcome.success == feasible, outcome.message
    if feasible:
        assert sum(pyo.value(m.changeover[d]) for d in m.days) == expected_changes
        assert all(pyo.value(m.changeover[d]) + pyo.value(m.shutdown[d]) <= 1 for d in m.days)
        if mode == "boundary":
            assert pyo.value(m.changeover[29]) == 1


@pytest.mark.parametrize("line,month,feasible", [(l, t, ok) for l in ("L1", "L2") for t, ok in (("2026-11", False), ("2026-12", True))])
def test_training_blocks_extra_days_until_next_month(case, line, month, feasible):
    m = diagnostic(case, 1)
    m.hire[line, "2026-11"].fix(1)
    d = m.month_days[month][5 if line == "L1" else 6]
    m.daily_production[line, "C" if line == "L1" else "B", d].fix(1)
    outcome = solve_lexicographic(m, time_limit=20)
    assert outcome.success == feasible, outcome.message
    if feasible:
        r = extract_results(m)
        assert pyo.value(m.new_salary_cost) == 110000  # Nov through Sep, including training
        assert pyo.value(m.hiring_cost) == 5000
        assert pyo.value(m.labor_cost) == 955000
        assert pyo.value(m.upgraded[line, "2026-11"]) == 0
        assert all(pyo.value(m.upgraded[line, t]) == 1 for t in list(m.months)[2:])
        assert r.staffing.query("line == @line and month == '2026-11'").additional_salary_usd.item() == 10000


def test_both_or_neither_upgrades_are_feasible(case):
    m = diagnostic(case, 10)
    for line in m.lines:
        m.hire[line, "2026-10"].fix(1)
    result, _ = solve(m)
    assert pyo.value(m.new_salary_cost) == 240000
    assert pyo.value(m.hiring_cost) == 10000
    assert result.staffing.hired_crew.sum() == 2
    assert pyo.value(m.capacity["L1", "2026-11"]) == 144
    assert pyo.value(m.capacity["L2", "2026-11"]) == 224


def test_new_a_receipts_after_transition_are_not_allowed(case):
    m = diagnostic(case, 10)
    m.material_order["A", "RM", "2026-10"].fix(50000)
    outcome = solve_lexicographic(m, time_limit=10)
    assert not outcome.success


def test_no_b_material_variables_and_no_scenario_b(case):
    m = build_model(case)
    assert set(m.material_products) == {"A", "C"}
    assert not m.material_balance.active
    assert m.daily_material_balance.active
    with pytest.raises(ValueError, match="Scenario A"):
        solve_lexicographic(m, cost_tolerance=.02)


def test_c_cannot_consume_november_arrival_in_october(case):
    m = diagnostic(case, 1)
    m.daily_production["L1", "C", 8].fix(1)
    outcome = solve_lexicographic(m, time_limit=10)
    assert not outcome.success


def test_changeover_day_cannot_also_produce(case):
    m = diagnostic(case, 1)
    configure(m, lambda d: "B" if d < 29 else "C")
    m.daily_production["L2", "C", 29].fix(1)
    outcome = solve_lexicographic(m, time_limit=10)
    assert not outcome.success


def test_incumbent_is_labeled_when_a_later_stage_times_out(case):
    from types import SimpleNamespace
    from pyomo.opt import SolverStatus, TerminationCondition
    class StopAfterCost:
        options = {}
        calls = 0
        def __init__(self):
            self.delegate = pyo.SolverFactory("appsi_highs")
        def available(self, **kwargs):
            return True
        def solve(self, model, **kwargs):
            self.calls += 1
            if self.calls <= 4:
                return self.delegate.solve(model, **kwargs)
            return SimpleNamespace(solver=SimpleNamespace(status=SolverStatus.aborted,
                termination_condition=TerminationCondition.maxTimeLimit), solution=[],
                problem=[SimpleNamespace(lower_bound=0, upper_bound=float("inf"))])
    m = diagnostic(case)
    outcome = solve_lexicographic(m, solver=StopAfterCost(), time_limit=10)
    assert not outcome.success and m._has_incumbent
    assert outcome.minimum_cost is not None
    assert outcome.stages[-1]["incumbent_source"] == "previous proven stage (fallback)"
    with pytest.raises(RuntimeError):
        extract_results(m)
    reported = extract_results(m, allow_incumbent=True)
    assert reported.costs["total_modeled"] == pytest.approx(outcome.minimum_cost, abs=.01)
    assert audit_solution(m)["passed"]


def small_case(case):
    """Two synthetic four-week months; no pipeline or opening FP/materials."""
    data = deepcopy(case)
    data.months = case.months[:2]
    data.demand = data.demand[data.demand.month.isin(data.months)].copy()
    data.demand.msu = 0
    data.initial_fp = {p: 0 for p in case.products}
    data.initial_materials.quantity = 0
    data.arrivals.quantity = 0
    return data


def test_optimizer_chooses_to_consume_a_before_qualification(case):
    data = small_case(case)
    data.initial_materials.loc[(data.initial_materials["product"] == "A") & (data.initial_materials.material == "RM"), "quantity"] = 500
    data.initial_materials.loc[(data.initial_materials["product"] == "A") & (data.initial_materials.material == "PM"), "quantity"] = 2500
    data.demand.loc[(data.demand.hub == "H1") & (data.demand.family == "AC") & (data.demand.month == "2026-10"), "msu"] = 1
    m = build_model(data)
    result, _ = solve(m)
    assert result.service.unserved_msu.sum() == 0
    assert result.transition["qualification_start"]["horizon_day"] > 1
    assert result.transition["a_rm_consumed_before_kg"] == pytest.approx(500, abs=TOL)
    assert result.transition["a_pm_consumed_before_ea"] == pytest.approx(2500, abs=TOL)
    assert result.costs["ide"] == pytest.approx(0, abs=TOL)
    assert result.staffing.hired_crew.sum() == 0
    assert result.costs["total_modeled"] == pytest.approx(140300, abs=.01)
    assert audit_solution(m)["passed"]


def test_optimizer_selects_only_l2_hire_when_required_for_service(case):
    data = small_case(case)
    for month, demand in (("2026-10", 160), ("2026-11", 220)):
        data.demand.loc[(data.demand.hub == "H1") & (data.demand.family == "B") & (data.demand.month == month), "msu"] = demand
    # No-hire L2 offers only 384 - 24 shutdown loss = 360 MSU over two months.
    # Training in October enables 192 + 224 - 24 = 392 MSU, enough for 380.
    m = build_model(data)
    result, _ = solve(m)
    assert result.service.served_msu.sum() == pytest.approx(380, abs=TOL)
    assert result.staffing.query("line == 'L1'").hired_crew.sum() == 0
    assert pyo.value(m.hire["L2", "2026-10"]) == 1
    assert result.transition["qualification_start"]["month"] == "2026-10"
    assert result.transition["new_salary_usd"] == 20000
    assert result.transition["hiring_usd"] == 5000
    assert result.costs["total_modeled"] == pytest.approx(187800, abs=.01)
    assert audit_solution(m)["passed"]
