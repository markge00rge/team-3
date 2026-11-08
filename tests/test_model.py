"""Integration checks using HiGHS, including scarcity and infeasibility."""
from copy import deepcopy
from math import ceil
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest
from pyomo.opt import SolverStatus, TerminationCondition

from src.data_loader import load_case
from src.model import FixedScenario, build_model as _build_model
from src.results import extract_results, write_results, write_comparison
from src.solve import solve_lexicographic

TOL = 1e-5


def build_model(data, scenario=None):
    """Historical fixed Scenario A regression adapter; never run Scenario B."""
    return _build_model(data, scenario or FixedScenario(data.rules["target_launch"]))


@pytest.fixture(scope="module")
def data():
    return load_case()


@pytest.fixture(scope="module")
def solved(data):
    model = build_model(data)
    outcome = solve_lexicographic(model)
    assert outcome.success, outcome.message
    return model, extract_results(model), outcome




def test_inventory_balances(data, solved):
    _, result, _ = solved
    for product in data.products:
        opening = data.initial_fp[product]
        for month in data.months:
            made = result.production.query("product == @product and month == @month").msu.sum()
            sent = result.shipments.query("product == @product and month == @month").msu.sum()
            closing = result.inventory.query("product == @product and month == @month").msu.item()
            assert closing >= -TOL
            assert opening + made - sent == pytest.approx(closing, abs=TOL)
            opening = closing
    assert result.production.msu.sum() == pytest.approx(3045, abs=TOL)


def test_production_limits_and_eligibility(data, solved):
    _, result, _ = solved
    for line in data.lines.index:
        for month in data.months:
            days = data.lines.loc[line, "days_per_month"] - (1 if line == "L2" else 0)
            if month == "2027-01":
                days -= 3
            made = result.production.query("line == @line and month == @month").msu.sum()
            assert made <= days * data.lines.loc[line, "msu_per_day"] + TOL
    assert result.production.query("line == 'L1' and product == 'B'").msu.sum() == 0
    assert result.production.query("product == 'C' and month < '2027-01'").msu.sum() == 0
    assert result.production.query("product == 'A' and month >= '2027-01'").msu.sum() == 0
    assert result.shipments.query("product == 'A' and month >= '2027-01'").msu.sum() == 0
    assert result.shipments.query("product == 'C' and month < '2027-01'").msu.sum() == 0


def test_demand_accounting(data, solved):
    _, result, _ = solved
    for row in result.service.itertuples():
        assert row.served_msu + row.unserved_msu == pytest.approx(row.demand_msu, abs=TOL)
        shipment = result.shipments
        shipment = shipment[(shipment.hub == row.hub) & (shipment.month == row.month) & shipment["product"].isin(data.families[row.family])]
        assert shipment.msu.sum() == pytest.approx(row.served_msu, abs=TOL)
        assert row.unserved_msu >= -TOL
    assert result.service.served_msu.sum() == pytest.approx(3070, abs=TOL)
    assert result.service.unserved_msu.sum() == pytest.approx(25, abs=TOL)
    assert result.service.query("hub != 'H3'").unserved_msu.sum() == pytest.approx(0, abs=TOL)


def test_transport_capacity_fleet_and_partial_loads(data, solved):
    _, result, _ = solved
    for row in result.transport.itertuples():
        sent = result.shipments.query("hub == @row.hub and month == @row.month").msu.sum()
        count = row.dedicated_trucks + row.spot_trucks
        assert sent <= 5 * count + TOL
        # Positive truck costs eliminate unused trucks and charge full partial loads.
        assert count == pytest.approx(ceil((sent - TOL) / 5), abs=TOL)
        for value in (row.dedicated_trucks, row.spot_trucks):
            assert value >= -TOL and abs(value - round(value)) < TOL
    assert (result.transport.groupby("month").dedicated_trucks.sum() <= 65 + TOL).all()
    assert result.transport.spot_trucks.sum() == pytest.approx(35, abs=TOL)


def test_costs_and_stages(data, solved):
    _, result, outcome = solved
    assert [s["name"] for s in outcome.stages] == ["service_H1", "service_H2", "service_H3", "modeled_cost", "international_order_events", "procurement_quantity_tiebreak", "cost_cleanup"]
    assert all(s["termination"] == "optimal" for s in outcome.stages)
    assert result.costs["labor"] == 840000
    assert result.costs["fp_holding"] == pytest.approx(58987.5, abs=0.01)
    assert result.costs["transportation"] == pytest.approx(285000, abs=0.01)
    assert result.costs["service_failure"] == pytest.approx(30000, abs=TOL)
    assert result.costs["ide"] is None and result.costs["external_storage"] == 0
    assert result.costs["total_modeled"] == pytest.approx(1213987.5, abs=0.01)
    assert result.costs["total_modeled"] == pytest.approx(outcome.stages[3]["optimum"], abs=0.01)


def test_material_balances_bom_and_fixed_arrivals(data, solved):
    model, result, _ = solved
    expected_fixed = {("A", "PM", "2026-10"): 250000,
                      ("C", "PM", "2026-10"): 375000,
                      ("C", "RM", "2026-11"): 150000}
    for row in result.material_balances.itertuples():
        key = row.product, row.material, row.month
        assert row.fixed_arrival == expected_fixed.get(key, 0)
        production = result.production.query("product == @row.product and month == @row.month").msu.sum()
        assert row.consumption == pytest.approx(production * (500 if row.material == "RM" else 2500), abs=TOL)
        assert row.opening + row.fixed_arrival + row.additional_arrival - row.consumption == pytest.approx(row.ending, abs=TOL)
        assert row.ending >= -TOL
    for (p, k), frame in result.material_balances.groupby(["product", "material"], sort=False):
        initial = data.initial_materials.query("product == @p and material == @k").quantity.item()
        assert frame.iloc[0].opening == initial
        assert frame.opening.iloc[1:].tolist() == pytest.approx(frame.ending.iloc[:-1].tolist(), abs=TOL)
    assert all(p != "B" for p, k, t in model.material_inventory)
    assert all(p != "B" for p, k, t in model.material_order)
    assert len(model.material_inventory) == 48
    assert len(model.material_order) == 48


def test_procurement_lead_times_moq_and_no_excess(data, solved):
    model, result, _ = solved
    for row in result.material_orders.itertuples():
        order_y, order_m = map(int, row.order_month.split("-"))
        arrival_y, arrival_m = map(int, row.arrival_month.split("-"))
        assert (arrival_y - order_y) * 12 + arrival_m - order_m == 3
        increment = 50000 if row.material == "RM" else 125000
        assert row.quantity / increment == pytest.approx(round(row.quantity / increment), abs=TOL)
        if row.arrival_month not in data.months:
            assert row.quantity == 0
        if row.arrival_month in data.months:
            arrival = result.material_balances.query("product == @row.product and material == @row.material and month == @row.arrival_month").additional_arrival.item()
            assert arrival == pytest.approx(row.quantity, abs=TOL)
    assert result.material_orders.query("product == 'A'").quantity.sum() == 0
    totals = result.material_orders.query("product == 'C'").groupby("material").quantity.sum()
    assert totals.to_dict() == pytest.approx({"RM": 500000, "PM": 2875000}, abs=TOL)
    terminal_c = result.material_balances.query("product == 'C' and month == '2027-09'")
    assert terminal_c.ending.tolist() == pytest.approx([2500, 12500], abs=TOL)
    assert model.integer_lots["C", "RM", "2026-10"].is_integer()
    assert result.material_balances.query("month < '2027-01'").additional_arrival.sum() == 0


def test_b_consumption_is_information_only(solved):
    model, result, _ = solved
    for row in result.b_material_consumption.itertuples():
        produced = result.production.query("product == 'B' and month == @row.month").msu.sum()
        assert row.rm_kg == pytest.approx(600 * produced, abs=TOL)
        assert row.pm_ea == pytest.approx(2000 * produced, abs=TOL)
    assert result.b_material_consumption.rm_kg.sum() == pytest.approx(912000, abs=TOL)
    assert result.b_material_consumption.pm_ea.sum() == pytest.approx(3040000, abs=TOL)
    assert set(model.material_products) == {"A", "C"}


@pytest.mark.parametrize("product,material", [(p, k) for p in ("A", "C") for k in ("RM", "PM")])
def test_each_missing_material_blocks_only_its_product(data, product, material):
    model = build_model(data)
    model.initial_material[product, material] = 0
    for month in model.months:
        model.fixed_material_arrival[product, material, month] = 0
        model.material_order[product, material, month].fix(0)
    outcome = solve_lexicographic(model)
    assert outcome.success, outcome.message
    result = extract_results(model)
    assert result.production.query("product == @product").msu.sum() == pytest.approx(0, abs=TOL)
    assert result.production.query("product == 'B'").msu.sum() == pytest.approx(1520, abs=TOL)
    other = "C" if product == "A" else "A"
    assert result.production.query("product == @other").msu.sum() > 0


def test_positive_a_orders_use_increments_in_diagnostic_scenario(data):
    # Artificial later transition allows an October A order to arrive in January.
    model = build_model(data, FixedScenario("2027-04"))
    for key in model.production:
        model.production[key].fix(0)
    model.production["L1", "A", "2027-01"].fix(1)
    for key in model.initial_material:
        model.initial_material[key] = 0
    for key in model.fixed_material_arrival:
        model.fixed_material_arrival[key] = 0
    outcome = solve_lexicographic(model)
    assert outcome.success, outcome.message
    orders = extract_results(model).material_orders.query("product == 'A'")
    assert orders.query("material == 'RM'").quantity.sum() == pytest.approx(50000, abs=TOL)
    assert orders.query("material == 'PM'").quantity.sum() == pytest.approx(125000, abs=TOL)
    assert orders.query("quantity > 0").order_month.tolist() == ["2026-10", "2026-10"]


def test_forcing_production_without_material_is_infeasible(data):
    model = build_model(data)
    model.initial_material["A", "RM"] = 0
    model.production["L1", "A", "2026-10"].fix(1)
    outcome = solve_lexicographic(model)
    assert not outcome.success
    assert "infeasible" in outcome.message.lower()
    with pytest.raises(RuntimeError):
        extract_results(model)


@pytest.mark.parametrize("initial_b", [15, 800, 1400])
def test_strict_hub_priority_under_scarcity(data, initial_b):
    # Synthetic stress case: no production; vary only available B stock.
    stressed = deepcopy(data)
    stressed.initial_fp["B"] = initial_b
    model = build_model(stressed)
    for key in model.capacity:
        model.capacity[key] = 0
    outcome = solve_lexicographic(model)
    assert outcome.success, outcome.message
    result = extract_results(model)
    assert result.material_orders.quantity.sum() == pytest.approx(0, abs=TOL)
    remaining = initial_b
    for hub, demand in (("H1", 745), ("H2", 515), ("H3", 275)):
        served = result.service.query("hub == @hub and family == 'B'").served_msu.sum()
        assert served == pytest.approx(min(remaining, demand), abs=TOL)
        remaining = max(0, remaining - demand)
    assert result.shipments.query("product == 'A' and hub == 'H1'").msu.sum() == pytest.approx(10, abs=TOL)
    for stage, hub in zip(outcome.stages[:3], model.priority_hubs):
        final_shortage = result.service.query("hub == @hub").unserved_msu.sum()
        assert final_shortage == pytest.approx(stage["optimum"], abs=TOL)
    expected_penalty = sum(result.service.query("hub == @h").unserved_msu.sum() * data.hubs.loc[h, "unserved_usd_per_msu"] for h in data.hubs.index)
    assert result.costs["service_failure"] == pytest.approx(expected_penalty, abs=0.01)


def test_partial_truck_is_paid_in_full(data):
    model = build_model(data)
    for key in model.capacity:
        model.capacity[key] = 0
    # Force a 1 MSU shipment in a controlled shortage scenario.
    model.shipment["B", "H1", "2026-10"].fix(1)
    model.shipment["A", "H1", "2026-10"].fix(0)
    outcome = solve_lexicographic(model)
    assert outcome.success, outcome.message
    result = extract_results(model)
    sent = result.shipments.query("hub == 'H1' and month == '2026-10'").msu.sum()
    trucks = result.transport.query("hub == 'H1' and month == '2026-10'")
    assert sent % 5 != pytest.approx(0, abs=TOL)
    assert (trucks.dedicated_trucks + trucks.spot_trucks).item() * 5 >= sent - TOL


def test_infeasibility_blocks_results_and_clears_previous_success(data):
    model = build_model(data)
    assert solve_lexicographic(model).success
    model.impossible = pyo.Constraint(expr=model.inventory["A", "2026-10"] >= 1000000)
    outcome = solve_lexicographic(model)
    assert not outcome.success
    assert "infeasible" in outcome.message.lower()
    with pytest.raises(RuntimeError, match="successful"):
        extract_results(model)


def test_unsolved_and_nonoptimal_solve_are_not_extracted(data):
    model = build_model(data)
    with pytest.raises(RuntimeError):
        extract_results(model)
    class LimitedSolver:
        options = {}
        def available(self, **kwargs):
            return True
        def solve(self, *args, **kwargs):
            return SimpleNamespace(solver=SimpleNamespace(status=SolverStatus.aborted,
                                   termination_condition=TerminationCondition.maxTimeLimit))
    outcome = solve_lexicographic(model, solver=LimitedSolver())
    assert not outcome.success
    with pytest.raises(RuntimeError):
        extract_results(model)


def test_report_export_preserves_balances_and_status(solved, tmp_path):
    import json
    import pandas as pd
    _, result, outcome = solved
    write_results(result, outcome, tmp_path)
    balances = pd.read_csv(tmp_path / "material_balances.csv")
    assert len(balances) == 48
    assert set(balances["product"]) == {"A", "C"}
    assert (balances.opening + balances.fixed_arrival + balances.additional_arrival - balances.consumption).tolist() == pytest.approx(balances.ending.tolist(), abs=TOL)
    status = json.loads((tmp_path / "solve_status.json").read_text())
    assert status["success"]
    assert len(status["stages"]) == 7
    assert status["costs"]["ide"] is None
    assert "B theoretical consumption" in (tmp_path / "summary.txt").read_text()


@pytest.mark.parametrize("scenario_fixture", ["solved"])
def test_lots_events_storage_and_service(request, scenario_fixture, data):
    model, result, outcome = request.getfixturevalue(scenario_fixture)
    for row in result.material_orders.itertuples():
        increment = 50000 if row.material == "RM" else 125000
        assert row.integer_lots >= -TOL
        assert row.integer_lots == pytest.approx(round(row.integer_lots), abs=TOL)
        assert row.quantity == pytest.approx(increment * row.integer_lots, abs=TOL)
        assert row.order_event == pytest.approx(int(row.quantity > TOL), abs=TOL)
        upper = pyo.value(model.max_order_lots[row.product, row.material, row.order_month])
        assert 0 <= upper < float("inf")
        assert row.integer_lots <= upper * row.order_event + TOL
        assert row.integer_lots >= row.order_event - TOL
        # Bounds are derived from eligible post-receipt production capacity.
        capacity = sum(pyo.value(model.capacity[l, t]) for l in model.lines for t in model.months
                       if t >= row.arrival_month and not model.production[l, row.product, t].fixed)
        assert upper == ceil(capacity * (500 if row.material == "RM" else 2500) / increment)
        if row.arrival_month not in data.months:
            assert abs(row.quantity) < TOL and abs(row.order_event) < TOL
        assert (int(row.arrival_month[:4]) - int(row.order_month[:4])) * 12 + int(row.arrival_month[-2:]) - int(row.order_month[-2:]) == 3
    assert len(result.fixed_receipts) == 3
    assert result.fixed_receipts.quantity.sum() == 775000
    for row in result.material_balances.itertuples():
        assert row.ending >= -TOL
        assert row.opening + row.fixed_arrival + row.additional_arrival - row.consumption == pytest.approx(row.ending, abs=TOL)
    for row in result.warehouse.itertuples():
        fp = result.inventory.query("month == @row.month").msu.sum() * 4
        rm = result.material_balances.query("month == @row.month and material == 'RM'").ending.sum() / 1000
        pm = result.material_balances.query("month == @row.month and material == 'PM'").ending.sum() / 5000
        assert row.tracked_pallets == pytest.approx(fp + rm + pm, abs=TOL)
        assert row.tracked_pallets <= 1200 + 100 * row.external_blocks + TOL
        assert row.external_blocks == pytest.approx(ceil(max(0, row.tracked_pallets - 1200 - TOL) / 100), abs=TOL)
        assert row.external_storage_usd == pytest.approx(row.external_blocks * 4500, abs=0.01)
    assert result.costs["external_storage"] == pytest.approx(result.warehouse.external_storage_usd.sum(), abs=0.01)
    assert result.costs["total_modeled"] <= outcome.cost_limit + 0.01
    assert result.service.groupby("hub").unserved_msu.sum().tolist() == pytest.approx([0, 0, 25], abs=TOL)
    assert set(model.material_products) == {"A", "C"}
    assert all(p != "B" for p, k, t in model.integer_lots)
    assert all(p != "B" for p, k, t in model.order_event)




@pytest.mark.parametrize("tolerance", [-0.01, float("nan"), float("inf")])
def test_invalid_cost_allowance_rejected(data, tolerance):
    model = build_model(data)
    with pytest.raises(ValueError, match="finite nonnegative"):
        solve_lexicographic(model, cost_tolerance=tolerance)
    with pytest.raises(RuntimeError):
        extract_results(model)


@pytest.mark.parametrize("violation", ["zero_quantity_with_event", "positive_quantity_without_event", "fractional_lot"])
def test_event_and_lot_constraints_reject_inconsistent_orders(data, violation):
    model = build_model(data)
    key = ("C", "RM", "2026-10")
    if violation == "zero_quantity_with_event":
        model.material_order[key].fix(0)
        model.order_event[key].fix(1)
    elif violation == "positive_quantity_without_event":
        model.material_order[key].fix(50000)
        model.order_event[key].fix(0)
    else:
        # Force half a lot via quantity; do not fix an integer variable to an
        # out-of-domain value (which Pyomo could substitute during presolve).
        model.material_order[key].fix(25000)
    outcome = solve_lexicographic(model)
    assert not outcome.success
    assert "infeasible" in outcome.message.lower()
    with pytest.raises(RuntimeError):
        extract_results(model)


