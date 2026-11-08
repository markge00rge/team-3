"""Independent reporting checks; no optimizer calls or decision changes."""
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil

import pandas as pd
import pytest

from src.data_loader import ROOT, load_case
from src.reconciliation import COST_COLUMNS, INPUT_TABLES, MARKER, calculate, read_saved, write_reconciliation


@pytest.fixture(scope="module")
def inputs():
    data = load_case()
    tables, status = read_saved(ROOT / "reports/v4")
    return data, tables, status


@pytest.fixture(scope="module")
def report(inputs):
    return calculate(*inputs)


def test_annual_demand_opening_and_flows(report):
    annual = report.monthly.iloc[-1]
    assert annual.month == "ANNUAL"
    assert annual.ac_demand_msu == 1560
    assert annual.b_demand_msu == 1535
    assert annual.total_demand_msu == 3095
    assert annual.opening_fp_msu == 25
    assert annual.total_production_msu == pytest.approx(3070)
    assert annual.shipments_msu == 3095
    assert annual.unserved_msu == 0
    assert annual.net_fp_change_msu == pytest.approx(-25)
    assert annual.ending_fp_msu == pytest.approx(0, abs=1e-8)
    assert annual.fp_pallets == pytest.approx(report.monthly.iloc[-2].fp_pallets)
    assert annual.ending_fp_msu != pytest.approx(report.monthly.iloc[:-1].ending_fp_msu.sum())


@pytest.mark.parametrize("product,initial,valuation", [("A", 10, 4000), ("B", 15, 5500), ("C", 0, 4200)])
def test_product_inventory_and_valuation(report, product, initial, valuation):
    rows = report.products.query("product == @product")
    assert len(rows) == 12
    assert rows.iloc[0].opening_fp_msu == initial
    assert rows.opening_fp_msu.iloc[1:].tolist() == pytest.approx(rows.ending_fp_msu.iloc[:-1].tolist())
    for row in rows.itertuples():
        assert row.opening_fp_msu + row.production_msu - row.shipments_msu == pytest.approx(row.ending_fp_msu, abs=1e-8)
        assert row.valuation_usd_per_msu == valuation
        assert row.ending_fp_value_usd == pytest.approx(row.ending_fp_msu * valuation, abs=1e-8)
        assert row.holding_expense_usd == pytest.approx(row.ending_fp_msu * valuation * .015, abs=1e-8)


def test_monthly_aggregate_and_drawdowns(report):
    for row in report.monthly.iloc[:-1].itertuples():
        products = report.products.query("month == @row.month")
        assert row.opening_fp_msu == pytest.approx(products.opening_fp_msu.sum(), abs=1e-8)
        assert row.net_fp_change_msu == pytest.approx(row.total_production_msu-row.shipments_msu, abs=1e-8)
        assert row.ending_fp_msu == pytest.approx(row.opening_fp_msu+row.net_fp_change_msu, abs=1e-8)
        assert row.fp_pallets == pytest.approx(4*row.ending_fp_msu, abs=1e-8)
        assert row.ending_fp_msu >= -1e-8
    assert report.monthly.query("month == '2027-06'").net_fp_change_msu.item() == -93
    assert report.monthly.query("month == '2027-06'").ending_fp_msu.item() == pytest.approx(86)


def test_annual_holding_independently(inputs, report):
    _, tables, status = inputs
    prices = {"A": 4000, "B": 5500, "C": 4200}
    expected = math.fsum(row.msu * prices[row.product] * .015 for row in tables["inventory"].itertuples())
    assert expected == pytest.approx(56167.5, abs=1e-7)
    assert report.costs.fp_holding_usd.iloc[:-1].sum() == pytest.approx(expected, abs=1e-7)
    assert expected == pytest.approx(status["costs"]["fp_holding"], abs=1e-7)
    assert report.products.query("product == 'B'").holding_expense_usd.sum() == pytest.approx(7342.5, abs=1e-7)
    assert report.products.query("product == 'C'").holding_expense_usd.sum() == pytest.approx(48825, abs=1e-7)


def test_monthly_costs_sum_to_reported_objective(inputs, report):
    _, _, status = inputs
    assert len(report.costs) == 13
    for row in report.costs.iloc[:-1].itertuples():
        assert math.fsum(getattr(row, name) for name in COST_COLUMNS) == pytest.approx(row.total_modeled_cost_usd, abs=1e-8)
    annual = report.costs.iloc[-1]
    assert report.costs.total_modeled_cost_usd.iloc[:-1].sum() == pytest.approx(status["minimum_cost"], abs=1e-7)
    assert annual.dedicated_transport_usd == 272200
    assert annual.spot_transport_usd == 16800
    assert annual.a_pm_scrap_value_usd == pytest.approx(30000, abs=1e-7)
    assert annual.a_pm_disposal_usd == pytest.approx(300, abs=1e-7)
    assert annual.total_modeled_cost_usd == pytest.approx(1215467.5, abs=1e-7)


def test_no_arbitrary_ac_demand_split(report):
    assert "demand" not in report.products.columns
    assert not any("a_demand" in c or "c_demand" in c and c != "ac_demand_msu" for c in report.monthly.columns)
    rows = report.monthly.iloc[:-1]
    assert rows.total_demand_msu.tolist() == pytest.approx((rows.ac_demand_msu+rows.b_demand_msu).tolist())


def test_fractional_msu_is_not_rounded_before_finance(inputs):
    data, original, saved = inputs
    tables, status = deepcopy(original), deepcopy(saved)
    delta = 0.123456789
    tables["inventory"].loc[(tables["inventory"]["product"] == "C") & (tables["inventory"].month == "2027-01"), "msu"] += delta
    for month, amount in (("2027-01", delta), ("2027-02", -delta)):
        tables["production"].loc[(tables["production"].line == "L1") & (tables["production"]["product"] == "C") & (tables["production"].month == month), "msu"] += amount
    tables["warehouse"].loc[tables["warehouse"].month == "2027-01", "fp_pallets"] += delta*4
    financial_delta = delta * 4200 * .015
    status["costs"]["fp_holding"] += financial_delta
    status["costs"]["total_modeled"] += financial_delta
    for stage in status["stages"]:
        if stage["name"] == "modeled_cost":
            stage["optimum"] += financial_delta
    result = calculate(data, tables, status)
    january = result.products.query("product == 'C' and month == '2027-01'").iloc[0]
    assert january.ending_fp_msu == 30+delta
    assert january.holding_expense_usd == pytest.approx((30+delta)*4200*.015, abs=1e-10)
    assert abs(january.holding_expense_usd-round(january.holding_expense_usd, 2)) > .001


@pytest.mark.parametrize("fault", ["missing_stock", "bad_stock", "duplicate_demand", "wrong_objective"])
def test_inconsistent_saved_data_fails_instead_of_fabricating(inputs, fault):
    data, original, saved = inputs
    tables, status = deepcopy(original), deepcopy(saved)
    if fault == "missing_stock":
        tables["inventory"] = tables["inventory"].iloc[1:]
    elif fault == "bad_stock":
        tables["inventory"].loc[0, "msu"] += 1
    elif fault == "duplicate_demand":
        tables["service"] = pd.concat([tables["service"], tables["service"].iloc[:1]])
    else:
        status["costs"]["total_modeled"] += 100
    with pytest.raises(ValueError):
        calculate(data, tables, status)


def test_export_is_reproducible_preserves_inputs_and_status(inputs, tmp_path):
    data, _, _ = inputs
    source = ROOT / "reports/v4"
    files = [source/f"{name}.csv" for name in INPUT_TABLES] + [source/"solve_status.json", source/"summary.txt"]
    for path in files:
        shutil.copyfile(path, tmp_path/path.name)
    preserved = [tmp_path/f"{name}.csv" for name in INPUT_TABLES] + [tmp_path/"solve_status.json"]
    preserved += [ROOT/"src"/name for name in ("model.py", "scheduling.py", "solve.py", "data_loader.py")]
    preserved += list((ROOT/"data").glob("Venus_PS_*"))
    before = {p: sha256(p.read_bytes()).hexdigest() for p in preserved}
    write_reconciliation(data, tmp_path)
    output_names = ["monthly_production_inventory.csv", "monthly_inventory_by_product.csv", "monthly_cost_breakdown.csv", "FINANCIAL_RECONCILIATION.md", "summary.txt"]
    output_hashes = {name: sha256((tmp_path/name).read_bytes()).hexdigest() for name in output_names}
    write_reconciliation(data, tmp_path)
    assert output_hashes == {name: sha256((tmp_path/name).read_bytes()).hexdigest() for name in output_names}
    assert before == {p: sha256(p.read_bytes()).hexdigest() for p in preserved}
    assert (tmp_path/"summary.txt").read_text().count(MARKER) == 1
    text = (tmp_path/"FINANCIAL_RECONCILIATION.md").read_text()
    assert "$2,485.50" in text and "$58,653.00" in text
    assert "cannot be conclusively attributed" in text
    assert "50% gap" in text
    assert not json.loads((tmp_path/"solve_status.json").read_text())["success"]
    assert len(pd.read_csv(tmp_path/"monthly_inventory_by_product.csv")) == 36
