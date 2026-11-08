"""Regression checks against original case facts and validation failure paths."""
from copy import deepcopy
from hashlib import sha256
import pytest

from src.data_loader import ROOT, load_case, validate_case


@pytest.fixture(scope="module")
def case():
    return load_case()


def test_sources_reconcile(case):
    errors, issues = validate_case(case)
    assert errors == []
    assert any("sea lead time" in item for item in issues)
    assert len(case.word_tables) == 8
    assert len(case.raw_rules) == 23


def test_demand(case):
    assert case.demand.msu.sum() == 3095
    assert case.demand.groupby("family").msu.sum().to_dict() == {"AC": 1560, "B": 1535}
    assert case.demand.groupby("month").msu.sum().tolist() == [190, 185, 225, 180, 200, 240, 285, 355, 405, 390, 255, 185]
    assert len(case.months) == 12
    assert case.months[0] == "2026-10" and case.months[-1] == "2027-09"


def test_lines_and_labor(case):
    assert case.lines.base_msu.to_dict() == {"L1": 120, "L2": 192}
    assert case.lines.base_msu.sum() == 312
    assert case.lines.one_changeover_msu.to_dict() == {"L1": 120, "L2": 184}
    assert case.lines.operators.sum() == 70
    assert case.rules["qualification_days"] == 3
    assert case.rules["upgrade_extra_msu"] == {"L1": 24, "L2": 32}
    assert case.rules["training_months"] == 1
    assert case.rules["training_output_fraction"] == 0
    assert case.rules["operator_usd_per_month"] == 1000
    assert case.rules["hiring_usd_per_operator"] == 500


def test_initial_inventories(case):
    assert case.initial_fp == {"A": 10, "B": 15, "C": 0}
    assert case.initial_materials.set_index(["product", "material"]).quantity.to_dict() == {
        ("A", "RM"): 115000, ("A", "PM"): 400000, ("C", "RM"): 0, ("C", "PM"): 0}
    assert case.rules["b_opening_rm_kg"] is None
    assert case.rules["headcount_limit"] is None


def test_exact_fixed_arrivals(case):
    assert case.arrivals.to_dict("records") == [
        dict(product="A", material="PM", date="2026-10-01", quantity=250000, unit="EA"),
        dict(product="C", material="RM", date="2026-11-01", quantity=150000, unit="kg"),
        dict(product="C", material="PM", date="2026-10-01", quantity=375000, unit="EA"),
    ]


def test_bom_storage_transport_service(case):
    assert case.bom.rm_kg_per_msu.to_dict() == {"A": 500, "C": 500, "B": 600}
    assert case.bom.pm_ea_per_msu.to_dict() == {"A": 2500, "C": 2500, "B": 2000}
    assert case.bom.fp_usd_per_msu.to_dict() == {"A": 4000, "C": 4200, "B": 5500}
    assert case.rules["warehouse_pallets"] == 1200
    assert case.rules["overflow_block_pallets"] == 100
    assert case.rules["overflow_usd_per_pallet_month"] == 45
    assert case.rules["fp_holding_fraction_month"] == 0.015
    assert case.rules["dedicated_trucks_month"] == 65
    assert case.rules["spot_surcharge_fraction"] == 0.6
    assert case.hubs.truck_usd.tolist() == [300, 500, 800]
    assert case.hubs.unserved_usd_per_msu.tolist() == [3000, 2000, 1200]
    assert case.rules["rm_moq_kg"] == 50000
    assert case.rules["pm_moq_ea"] == 125000


@pytest.mark.parametrize("fault,expected", [
    ("demand", "Annual demand"), ("arrival", "Fixed material arrivals"),
    ("capacity", "Base manufacturing capacity"), ("cache", "cached annual totals"),
    ("word", "Word/workbook mismatch"),
])
def test_validator_rejects_corrupted_data(case, fault, expected):
    changed = deepcopy(case)
    if fault == "demand":
        changed.demand.loc[0, "msu"] += 1
    elif fault == "arrival":
        changed.arrivals.loc[0, "date"] = "2026-11-01"
    elif fault == "capacity":
        changed.lines.loc["L1", "base_msu"] = 119
    elif fault == "cache":
        changed.cached_totals[0] = None
    else:
        changed.word_tables[0][1][1] = "Different rule"
    errors, _ = validate_case(changed)
    assert any(expected in error for error in errors)


def test_loading_does_not_modify_originals():
    sources = list((ROOT / "data").glob("Venus_PS_*"))
    before = {p: sha256(p.read_bytes()).hexdigest() for p in sources}
    load_case()
    assert before == {p: sha256(p.read_bytes()).hexdigest() for p in sources}
