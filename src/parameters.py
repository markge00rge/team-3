"""Editable case copies and structural validation, separate from source regression checks.

The interface can edit this copy and rebuild. Neither source document is written.
Unsupported scheduling conventions are rejected instead of silently approximated.
"""
from copy import deepcopy
from math import isfinite
from itertools import product


def editable_case(source, *, rules=None, demand=None, lines=None, hubs=None,
                  initial_fp=None, initial_materials=None, arrivals=None, bom=None):
    case = deepcopy(source)
    if rules:
        case.rules.update(deepcopy(rules))
    for name, value in locals().copy().items():
        if name in ("demand", "lines", "hubs", "initial_fp", "initial_materials", "arrivals", "bom") and value is not None:
            setattr(case, name, deepcopy(value))
    validate_parameters(case)
    return case


def validate_parameters(data):
    if data.rules["weeks_per_month"] != 4:
        raise ValueError("Exactly four weeks / 28 planning days are required")
    if not isfinite(data.rules["training_months"]) or data.rules["training_months"] < 1 or int(data.rules['training_months']) != data.rules['training_months'] or data.rules["changeover_days"] != 1:
        raise ValueError("Training requires positive whole months; changeovers require one full day")
    for key,value in [('crew size',data.rules['upgrade_operators_per_line']),('dismissal expense',data.rules.get('dismissal_usd_per_operator',0))]:
        if not isfinite(value) or value<0 or (key=='crew size' and (value<1 or int(value)!=value)):
            raise ValueError(f'Invalid {key}')
    for prices in data.rules.get('material_unit_prices',{}).values():
        if any(not isfinite(v) or v<0 for v in prices.values()): raise ValueError('Invalid material unit price')
    if data.rules["training_output_fraction"] != 0:
        raise ValueError("Training must provide zero additional productivity")
    positive = ("truck_msu", "overflow_block_pallets", "rm_kg_per_pallet", "pm_ea_per_pallet", "fp_pallets_per_msu")
    nonnegative = ("operator_usd_per_month", "hiring_usd_per_operator", "warehouse_pallets",
        "overflow_usd_per_pallet_month", "fp_holding_fraction_month", "dedicated_trucks_month",
        "spot_surcharge_fraction", "rm_usd_per_kg", "pm_usd_per_ea", "disposal_usd_per_ton")
    for key in positive + nonnegative:
        value = data.rules[key]
        if not isfinite(value) or value < 0 or (key in positive and value == 0):
            raise ValueError(f"Invalid finite nonnegative input: {key}")
    if any(not isfinite(v) or v < 0 for v in data.initial_fp.values()):
        raise ValueError("Opening finished inventory must be finite and nonnegative")
    for frame, columns in ((data.initial_materials, ["quantity"]), (data.arrivals, ["quantity"]),
        (data.hubs,["truck_usd","unserved_usd_per_msu"]), (data.bom,["fp_usd_per_msu"])):
        if any(not isfinite(v) or v < 0 for c in columns for v in frame[c]):
            raise ValueError("Stock, receipt, valuation and cost inputs must be finite and nonnegative")
    for key in ("qualification_days", "sea_lead_months", "rm_moq_kg", "pm_moq_ea"):
        value = data.rules[key]
        if not isfinite(value) or value <= 0 or int(value) != value:
            raise ValueError(f"{key} must be a positive integer")
    expected = set(product(data.hubs.index, data.families, data.months))
    if data.demand.duplicated(["hub", "family", "month"]).any() or set(data.demand[["hub", "family", "month"]].itertuples(index=False, name=None)) != expected:
        raise ValueError("Demand must contain exactly one row per hub/family/month")
    if any(not isfinite(x) or x < 0 for x in data.demand.msu):
        raise ValueError("Demand must be finite and nonnegative")
    for l in data.lines.index:
        base = int(data.lines.loc[l, "profile"].split("/")[1])
        upgraded = int(data.rules["upgraded_profiles"][l].split("/")[1])
        if not 1 <= base <= upgraded <= 7 or data.lines.loc[l, "days_per_month"] != 4 * base:
            raise ValueError("Profiles and four-week scheduled day counts disagree")
        if not isfinite(data.lines.loc[l, "msu_per_day"]) or data.lines.loc[l, "msu_per_day"] <= 0:
            raise ValueError("Daily capacity must be finite and positive")
    for column in ("rm_kg_per_msu", "pm_ea_per_msu"):
        if any(not isfinite(v) or v <= 0 for v in data.bom[column]):
            raise ValueError("BOM consumption factors must be finite and positive")
    return data
