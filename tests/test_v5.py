"""Independent synthetic allocation and KPI tests; no invented case input values."""
from copy import deepcopy
from pathlib import Path
import pandas as pd
import pyomo.environ as pyo
import pytest

from src.data_loader import load_case, ROOT
from src.priorities import add_monthly_priorities
from src.kpis import cumulative_indicators, calculate_kpis
from src.parameters import editable_case
from src.reconciliation import read_saved, calculate
from src.validation import audit_exported_schedule


def allocation(ac, b, middle=10):
    m = pyo.ConcreteModel()
    m.hubs = pyo.Set(initialize=["H1", "H2", "H3"])
    m.priority_hubs = tuple(m.hubs)
    m.families = pyo.Set(initialize=["AC", "B"])
    m.months = pyo.Set(initialize=["first", "second"])
    m.products = pyo.Set(initialize=["A", "C", "B"])
    m.family_members = dict(AC=("A", "C"), B=("B",))
    m.demand = pyo.Param(m.hubs, m.families, m.months,
        initialize=lambda m, h, f, t: middle if h == "H2" else 10)
    m.shipment = pyo.Var(m.products, m.hubs, m.months, domain=pyo.NonNegativeReals)
    m.unserved = pyo.Var(m.hubs, m.families, m.months, domain=pyo.NonNegativeReals)
    m.balance = pyo.Constraint(m.hubs, m.families, m.months,
        rule=lambda m, h, f, t: sum(m.shipment[p, h, t] for p in m.family_members[f]) + m.unserved[h, f, t] == m.demand[h, f, t])
    m.supply = pyo.Constraint(m.families, m.months, rule=lambda m, f, t:
        sum(m.shipment[p, h, t] for p in m.family_members[f] for h in m.hubs) == min(ac if f == "AC" else b, 20 + middle))
    m.dedicated = pyo.Var(m.hubs, m.months, domain=pyo.NonNegativeIntegers)
    m.spot = pyo.Var(m.hubs, m.months, domain=pyo.NonNegativeIntegers)
    m.fleet = pyo.Constraint(m.months, rule=lambda m, t: sum(m.dedicated[h, t] for h in m.hubs) <= 1)
    m.trucks = pyo.Constraint(m.hubs, m.months, rule=lambda m, h, t:
        sum(m.shipment[p, h, t] for p in m.products) <= 5 * (m.dedicated[h, t] + m.spot[h, t]))
    add_monthly_priorities(m)
    m.objective = pyo.Objective(expr=sum(m.dedicated[k] + 2 * m.spot[k] for k in m.dedicated))
    result = pyo.SolverFactory("appsi_highs").solve(m)
    assert str(result.solver.termination_condition) == "optimal"
    return m


@pytest.mark.parametrize("ac,b", [(30,30),(10,10),(25,25),(12,30),(30,12),(4,23),(0,0)])
def test_exact_monthly_family_priorities(ac, b):
    m = allocation(ac, b)
    for t in m.months:
        for f, available in (("AC", ac), ("B", b)):
            for i, h in enumerate(m.hubs):
                expected = min(10, max(0, available - 10 * i))
                assert sum(pyo.value(m.shipment[p,h,t]) for p in m.family_members[f]) == pytest.approx(expected)
            assert sum(pyo.value(m.unserved[h,f,t]) for h in m.hubs) == pytest.approx(max(0,30-available))
        assert sum(pyo.value(m.dedicated[h,t]) for h in m.hubs) <= 1


def test_zero_middle_demand_cannot_bypass_cairo_shortage():
    m = allocation(5,20,middle=0)
    for t in m.months:
        assert sum(pyo.value(m.shipment[p,"H3",t]) for p in ("A","C")) == pytest.approx(0)
        assert pyo.value(m.shipment["B","H3",t]) == pytest.approx(10)


def test_dual_cd_indicators_opening_once_and_flags():
    frame = pd.DataFrame(dict(month=["one","two","three"],total_demand_msu=[10,20,0],
        total_production_msu=[5,20,0],shipments_msu=[10,20,0]))
    k = cumulative_indicators(frame, {"one":8,"two":30,"three":0}, 5)
    assert list(k.cumulative_supply_msu) == [10,30,30]
    assert list(k.cumulative_capacity_msu) == [8,38,38]
    assert list(k.cumulative_demand_msu) == [10,30,30]
    assert k.iloc[0].capacity_to_demand_below_one
    assert k.iloc[0].supply_to_demand == 1
    assert k.iloc[0].monthly_service_fraction == 1
    assert pd.isna(k.iloc[2].monthly_service_fraction)


def test_zero_cumulative_demand_is_undefined():
    frame = pd.DataFrame(dict(month=["one"], total_demand_msu=[0],total_production_msu=[0],shipments_msu=[0]))
    k = cumulative_indicators(frame,{"one":10},25)
    assert pd.isna(k.iloc[0].capacity_to_demand)
    assert not k.iloc[0].capacity_to_demand_defined


def v4_kpis():
    data = load_case()
    tables, status = read_saved(ROOT / "reports/v4")
    for name in ("daily_schedule","line_capacity","material_orders"):
        tables[name] = pd.read_csv(ROOT / f"reports/v4/{name}.csv",float_precision="round_trip")
    financial = calculate(data,tables,status)
    return data,tables,financial,calculate_kpis(data,tables,financial)


def test_v4_capacity_downtime_cash_and_productivity():
    data,tables,financial,k = v4_kpis()
    p = k["productivity"]
    dec = p.query("month == '2026-12'").set_index("line")
    assert dec.loc["L1","available_capacity_msu"] == pytest.approx(102)
    assert dec.loc["L2","available_capacity_msu"] == pytest.approx(160)
    assert p.qualification_days.sum() == pytest.approx(6)
    assert k["cumulative_indicators"].iloc[-1].cumulative_supply_msu == pytest.approx(3095)
    assert k["cash"].working_capital_holding_expense_usd.sum() == pytest.approx(56167.5)
    assert (k["monthly_operations"].employed_operators == 70).all()
    assert k["cash"].ending_fp_value_usd.equals(k["cash"].cash_tied_up_fp_usd)


def test_independent_v4_audit_including_new_monthly_priorities():
    audit = audit_exported_schedule(load_case(), ROOT / "reports/v4")
    assert audit["passed"], audit["violations"]
    assert audit["reported_monetary_cost"] == pytest.approx(1215467.5)
    assert not audit["all_lexicographic_stages_optimal"]


def test_editable_inputs_do_not_change_source_and_rebuild():
    from src.model import build_model
    source = load_case()
    changed = source.demand.copy()
    changed.loc[0,"msu"] += 7
    copy = editable_case(source, demand=changed, rules={"upgrade_permissions":{"L1":False}})
    m = build_model(copy)
    assert copy.demand.msu.sum() == source.demand.msu.sum() + 7
    assert all(m.hire["L1",t].fixed and m.hire["L1",t].value == 0 for t in m.months)
    assert source.rules.get("upgrade_permissions") is None
    assert sum(m.demand[k] for k in m.demand) == pytest.approx(3102)


@pytest.mark.parametrize("rules",[{"weeks_per_month":4.5},{"sea_lead_months":0},{"rm_moq_kg":-1},{"training_months":1.5}])
def test_invalid_editable_parameters_are_rejected(rules):
    with pytest.raises(ValueError):
        editable_case(load_case(),rules=rules)


def test_loader_extracts_four_weeks_from_source_equation():
    assert load_case().rules["weeks_per_month"] == 4


def test_service_penalties_apply_to_both_families_at_source_hub_rates():
    from src.model import build_model
    data = load_case()
    m = build_model(data)
    for var in m.unserved.values():
        var.set_value(0)
    for h in m.hubs:
        for f in m.families:
            for t in m.months:
                m.unserved[h,f,t].set_value(0.5)
                assert pyo.value(m.service_penalty) == pytest.approx(data.hubs.loc[h,"unserved_usd_per_msu"] * 0.5)
                m.unserved[h,f,t].set_value(0)


def test_kpi_capacity_includes_upgraded_days_but_not_training_days():
    data,tables,financial,_ = v4_kpis()
    tables = deepcopy(tables)
    # Synthetic reporting fixture: add L1 Saturday availability in November,
    # after an October training month; production and financial decisions untouched.
    days = tables["daily_schedule"]
    saturday = (days.planning_day - 1) % 7 == 5
    days.loc[(days.line == "L1") & (days.month == "2026-11") & saturday,"scheduled"] = 1
    capacities = tables["line_capacity"]
    capacities.loc[(capacities.line == "L1") & (capacities.month == "2026-11"),"capacity_msu"] += 24
    staff = tables["staffing"]
    staff.loc[(staff.line == "L1") & (staff.month == "2026-10"),"training"] = 1
    staff.loc[(staff.line == "L1") & (staff.month == "2026-11"),"upgraded"] = 1
    k = calculate_kpis(data,tables,financial)["productivity"].query("line == 'L1'").set_index("month")
    assert k.loc["2026-10","scheduled_days"] == 20
    assert k.loc["2026-11","scheduled_days"] == 24
    assert k.loc["2026-11","upgrade_theoretical_gain_msu"] == 24


def test_saved_v5_financial_priority_and_numerical_audit():
    path = ROOT / "reports/v5"
    if not (path / "solve_status.json").exists():
        pytest.skip("Generate the V5 solution to run its saved-plan regression audit")
    data = load_case()
    audit = audit_exported_schedule(data,path)
    assert audit["passed"], audit["violations"]
    tables,status = read_saved(path)
    financial = calculate(data,tables,status)
    assert financial.costs.iloc[-1].total_modeled_cost_usd == pytest.approx(1215467.5,abs=.01)
    assert tables["service"].unserved_msu.sum() == pytest.approx(0,abs=1e-5)
    assert status["cost_limit"] == status["minimum_cost"]
    for family in data.families:
        for month in data.months:
            regional = tables["service"].query("family == @family and month == @month").set_index("hub")
            for i,a in enumerate(data.hubs.sort_values("priority").index):
                if regional.loc[a,"unserved_msu"] > 1e-5:
                    for b in list(data.hubs.sort_values("priority").index)[i+1:]:
                        assert regional.loc[b,"served_msu"] <= 1e-5


def test_v5_reports_reproduce_without_modifying_saved_decisions(tmp_path):
    import shutil
    from hashlib import sha256
    from src.reporting import generate_reports
    source = ROOT / "reports/v5"
    if not (source / "solve_status.json").exists():
        pytest.skip("Generate V5 outputs first")
    for p in source.iterdir():
        if p.is_file():
            shutil.copy2(p,tmp_path / p.name)
    raw = ["solve_status.json","daily_schedule.csv","production.csv","inventory.csv","material_orders.csv"]
    before = {name:sha256((tmp_path/name).read_bytes()).hexdigest() for name in raw}
    generate_reports(load_case(),tmp_path)
    outputs = ["monthly_operations.csv","monthly_cost_breakdown.csv","dashboard.json","ANALYSIS.md","summary.txt"]
    first = {name:(tmp_path/name).read_bytes() for name in outputs}
    generate_reports(load_case(),tmp_path)
    assert all((tmp_path/name).read_bytes() == value for name,value in first.items())
    assert all(sha256((tmp_path/name).read_bytes()).hexdigest() == value for name,value in before.items())
