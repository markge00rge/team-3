"""Read the original Venus inputs. No optimization model is constructed.

Workbook coordinates refer to the supplied 2026 workbook, not a generic template.
All quantities retain the case units: MSU, kg, EA, pallets, USD and months.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHEETS = ("Assumptions & Rules", "Line & BOM Profiles",
          "Stocks Closure (30 Sep)", "12M Demand Forecast")


def number(value):
    """First numeric quantity in a source cell; fail on absent/non-numeric data."""
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(value))
    if not match:
        raise ValueError(f"Expected numeric quantity, got {value!r}")
    return float(match.group().replace(",", ""))


@dataclass
class CaseData:
    months: tuple[str, ...]
    products: dict
    families: dict
    lines: pd.DataFrame
    hubs: pd.DataFrame
    bom: pd.DataFrame
    initial_fp: dict
    initial_materials: pd.DataFrame
    arrivals: pd.DataFrame
    demand: pd.DataFrame
    rules: dict
    raw_rules: pd.DataFrame
    word_paragraphs: list[str]
    word_tables: list[list[list[str]]]
    raw_sheets: dict[str, pd.DataFrame]
    cached_totals: list
    cached_monthly_totals: list


def read_word(path: Path):
    """Read paragraphs and tables with the standard library; never rewrite DOCX."""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(path) as archive:
        body = ET.fromstring(archive.read("word/document.xml")).find("w:body", ns)
    def text(node):
        return "".join(t.text or "" for t in node.findall(".//w:t", ns))
    paragraphs, tables = [], []
    for node in body:
        if node.tag.endswith("}p"):
            paragraphs.append(text(node))
        elif node.tag.endswith("}tbl"):
            tables.append([[text(cell) for cell in row.findall("w:tc", ns)]
                           for row in node.findall("w:tr", ns)])
    return paragraphs, tables


def load_case(data_dir: Path | str = ROOT / "data") -> CaseData:
    data_dir = Path(data_dir)
    excel = data_dir / "Venus_PS_Supporting_Data_2026.xlsx"
    word = data_dir / "Venus_PS_Case_Study_2026.docx"
    raw = pd.read_excel(excel, sheet_name=list(SHEETS), header=None, engine="openpyxl", keep_default_na=False)
    def cell(sheet, row, col):
        return raw[SHEETS[sheet]].iat[row - 1, col - 1]
    def rule(row):
        return str(cell(0, row, 2))
    def after(text, marker):
        return number(text.split(marker, 1)[1])

    products = {p: str(cell(1, 9, col)) for p, col in (("A", 2), ("C", 3), ("B", 4))}
    lines = []
    for row, key, capable in ((5, "L1", ("A", "C")), (6, "L2", ("A", "C", "B"))):
        lines.append(dict(line=key, name=cell(1, row, 1), products=capable,
                          msu_per_day=number(cell(1, row, 3)), profile=cell(1, row, 4),
                          days_per_month=number(cell(1, row, 5)),
                          base_msu=number(cell(1, row, 6)),
                          one_changeover_msu=number(cell(1, row, 7)),
                          operators=number(cell(1, row, 8))))
    bom = []
    for product, col in (("A", 2), ("C", 3), ("B", 4)):
        bom.append(dict(product=product, rm_kg_per_msu=number(cell(1, 10, col)),
                        pm_ea_per_msu=number(cell(1, 11, col)),
                        fp_usd_per_msu=number(cell(1, 12, col))))
    fp = {p: number(cell(2, r, 2)) for p, r in (("A", 5), ("B", 6), ("C", 7))}
    materials, arrivals = [], []
    for row, product, kind in ((11, "A", "RM"), (12, "A", "PM"),
                               (13, "C", "RM"), (14, "C", "PM")):
        materials.append(dict(product=product, material=kind,
                              unit="kg" if kind == "RM" else "EA",
                              quantity=number(cell(2, row, 2)),
                              stated_support_msu=number(cell(2, row, 5))))
        for col, date in ((3, "2026-10-01"), (4, "2026-11-01")):
            quantity = number(cell(2, row, col))
            if quantity:
                arrivals.append(dict(product=product, material=kind, date=date,
                                     quantity=quantity, unit="kg" if kind == "RM" else "EA"))
    months = tuple(pd.to_datetime(str(cell(3, 3, c)), format="%b-%y").strftime("%Y-%m")
                   for c in range(3, 15))
    demand, hubs = [], []
    for row in range(4, 10):
        hub = f"H{(row - 4) // 2 + 1}"
        family = "AC" if row % 2 == 0 else "B"
        for col, month in enumerate(months, 3):
            demand.append(dict(hub=hub, family=family, month=month, msu=number(cell(3, row, col))))
        if family == "AC":
            i = (row - 4) // 2
            service = rule(24 + i)
            cost_text = rule(22).split("|")[i]
            hubs.append(dict(hub=hub, name=cell(3, row, 1), priority=i + 1,
                             channel=service.split(" – ")[-1].split(" (")[0],
                             truck_usd=after(cost_text, "$"),
                             unserved_usd_per_msu=after(service, "$")))
    # Numeric rules are extracted from their source prose, with the prose retained.
    rules = dict(
        weeks_per_month=number(rule(4)), minimum_cumulative_cd=after(rule(5), "below"),
        l2_max_changeovers=number(rule(6)), changeover_days=after(rule(6), "="),
        qualification_days=number(rule(7)), target_launch="2027-01", early_launch_allowed=True,
        peak_months=("2027-05", "2027-06", "2027-07"),
        sea_lead_months=after(rule(9), "Lead Time ="),
        rm_moq_kg=number(cell(2, 18, 2)), pm_moq_ea=number(cell(2, 19, 2)),
        pm_expiry_years=after(rule(11), "expires after"),
        scrap_material_cost_fraction=after(rule(11), "IDE =") / 100,
        disposal_usd_per_ton=after(rule(11), "$"), pm_kg_per_1000_ea=after(rule(11), "weighs"),
        operator_usd_per_month=after(rule(13), "$"), base_operators=after(rule(13), "month ("),
        upgrade_extra_days=after(rule(14), "(+"), upgrade_operators_per_line=after(rule(14), "need +"),
        upgraded_profiles={"L1": "24/6", "L2": "24/7"},
        upgrade_extra_msu={"L1": after(rule(14), "= +"), "L2": after(rule(14).split("or L2", 1)[1], "= +")},
        qualification_simultaneous=True, ac_switch_exempt_from_routine_changeover=True,
        b_materials_separate=True, b_smooth_replenishment=True,
        warehouse_measurement="end-of-month FP + RM + PM", holding_cost_basis="ending FP value only",
        truck_hub_mixing_allowed=False, partial_load_pays_full_truck=True,
        a_remaining_materials_scrapped_at_phaseout=True,
        training_months=number(rule(15)), training_usd_per_operator=after(rule(15), "$"),
        training_output_fraction=after(rule(15), "at ") / 100,
        hiring_usd_per_operator=after(rule(15), "plus a $"),
        warehouse_pallets=after(rule(16), "="), overflow_usd_per_pallet_month=after(rule(17), "$"),
        overflow_block_pallets=after(rule(17), "blocks of"),
        fp_holding_fraction_month=number(rule(18)) / 100,
        truck_msu=after(rule(19), "="), truck_pallets=after(rule(19), "MSU ("),
        dedicated_trucks_month=after(rule(21), "Max"), spot_surcharge_fraction=after(rule(23), "+") / 100,
        rm_usd_per_kg=number(cell(1, 10, 5)), pm_usd_per_ea=number(cell(1, 11, 5)),
        rm_kg_per_pallet=number(cell(1, 10, 6)), pm_ea_per_pallet=number(cell(1, 11, 6)),
        fp_pallets_per_msu=after(str(cell(1, 12, 6)), "="),
        overtime_rate=None, overtime_limit=None, headcount_limit=None,
        b_opening_rm_kg=None, b_opening_pm_ea=None, pm_opening_age=None,
    )
    paragraphs, tables = read_word(word)
    with excel.open("rb") as stream:
        book = openpyxl.load_workbook(stream, read_only=True, data_only=True)
        sheet = book[SHEETS[3]]
        totals = [sheet.cell(r, 15).value for r in range(4, 13)]
        monthly = [[sheet.cell(r, c).value for c in range(3, 15)] for r in range(10, 13)]
        book.close()
    return CaseData(months, products, {"AC": ("A", "C"), "B": ("B",)},
                    pd.DataFrame(lines).set_index("line"), pd.DataFrame(hubs).set_index("hub"),
                    pd.DataFrame(bom).set_index("product"), fp, pd.DataFrame(materials),
                    pd.DataFrame(arrivals), pd.DataFrame(demand), rules,
                    raw[SHEETS[0]].iloc[3:26, :2].set_axis(["category", "rule"], axis=1),
                    paragraphs, tables, raw, totals, monthly)


KNOWN_ISSUES = [
    "INCONSISTENT: Standard sea lead time is 3 months, but Sep 1 to Oct 1 is 1 month. Fixed arrivals are preserved; future order timing needs clarification.",
    "MISSING: Overtime premium, overtime limits and strict headcount ceiling are not quantified.",
    "MISSING: Product B opening RM/PM stocks and pre-horizon pipeline are absent; smooth replenishment is stated but does not quantify these.",
    "MISSING: Opening PM ages are absent, so the one-year expiry cannot yet be dated.",
    "AMBIGUOUS: A/C demand is pooled; exact transition date, product substitution and treatment of residual A finished goods need agreement.",
    "AMBIGUOUS: C:D numerator, accumulation convention and whether opening inventory counts are not defined.",
    "AMBIGUOUS: Shutdown calendar placement and overlap with nonworking days/changeovers are unspecified.",
    "AMBIGUOUS: Service priorities are strict in prose, but their relation to monetary penalties and lost sales versus backlog is unspecified.",
    "AMBIGUOUS: Truckload MOQ may mean a minimum quantity or integer multiples; this needs clarification.",
    "MISSING: Explicit cash objective/tradeoff, target ending inventories and conversion costs beyond labor/materials are not supplied.",
]


def validate_case(data: CaseData) -> tuple[list[str], list[str]]:
    """Return data errors separately from unresolved source inputs."""
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    check(data.months == tuple(pd.date_range("2026-10-01", periods=12, freq="MS").strftime("%Y-%m")), "Planning months differ from Oct 2026–Sep 2027")
    check(len(data.demand) == 72 and not data.demand.duplicated(["hub", "family", "month"]).any(), "Demand must contain 72 unique hub/family/month records")
    expected_keys = {(hub, family, month) for hub in data.hubs.index
                     for family in data.families for month in data.months}
    check(set(data.demand[["hub", "family", "month"]].itertuples(index=False, name=None)) == expected_keys,
          "Demand keys do not cover every declared hub/family/month")
    check(data.demand.msu.sum() == 3095, "Annual demand differs from 3,095 MSU")
    check(data.lines.base_msu.sum() == 312, "Base manufacturing capacity differs from 312 MSU/month")
    check((data.lines.base_msu == data.lines.msu_per_day * data.lines.days_per_month).all(), "Line capacities do not reconcile")
    check(data.initial_fp == {"A": 10, "B": 15, "C": 0}, "Opening FP differs from documented stocks")
    expected = {("A", "PM", "2026-10-01", 250000), ("C", "PM", "2026-10-01", 375000), ("C", "RM", "2026-11-01", 150000)}
    actual = set(data.arrivals[["product", "material", "date", "quantity"]].itertuples(index=False, name=None))
    check(actual == expected, "Fixed material arrivals differ from the three documented shipments")
    check(data.lines.operators.sum() == data.rules["base_operators"], "Base operator count does not reconcile")
    check(data.rules["truck_msu"] * data.rules["fp_pallets_per_msu"] == data.rules["truck_pallets"], "Truck MSU/pallet conversion does not reconcile")
    for frame, columns in ((data.demand, ["msu"]), (data.bom, list(data.bom.columns)),
                           (data.initial_materials, ["quantity"]), (data.arrivals, ["quantity"])):
        check(frame[columns].notna().all().all() and (frame[columns] >= 0).all().all(), "Missing or negative numeric input")
    calculated = [data.demand.query("hub == @h and family == @f").msu.sum()
                  for h in ("H1", "H2", "H3") for f in ("AC", "B")]
    calculated += [data.demand.query("family == @f").msu.sum() for f in ("AC", "B")]
    calculated += [data.demand.msu.sum()]
    check(calculated == data.cached_totals, "Workbook cached annual totals are missing or inconsistent with detail")
    for i, family in enumerate(("AC", "B", None)):
        detail = data.demand if family is None else data.demand.query("family == @family")
        check(detail.groupby("month").msu.sum().reindex(data.months).tolist() == data.cached_monthly_totals[i], "Workbook cached monthly totals differ from detail")
    for row in data.initial_materials.itertuples():
        delivered = data.arrivals.query("product == @row.product and material == @row.material").quantity.sum()
        factor = data.bom.loc[row.product, "rm_kg_per_msu" if row.material == "RM" else "pm_ea_per_msu"]
        check((row.quantity + delivered) / factor == row.stated_support_msu, f"Material support does not reconcile: {row.product} {row.material}")
    # Compare every workbook business table with its corresponding Word table.
    ranges = [(0, 3, 26, 2), (1, 4, 6, 8), (1, 9, 12, 6),
              (2, 4, 7, 2), (2, 10, 14, 5), (2, 17, 19, 2), (3, 3, 12, 15)]
    check(len(data.word_tables) == 8, "Expected seven Word business tables and abbreviation appendix")
    def normalized(value):
        if pd.isna(value):
            return ""
        if isinstance(value, (int, float)):
            return f"{value:g}"
        return re.sub(r"\s+", " ", str(value).replace(",", "")).strip()
    for index, (sheet, start, end, width) in enumerate(ranges):
        if index >= len(data.word_tables):
            continue
        expected_table = data.word_tables[index]
        actual_table = data.raw_sheets[SHEETS[sheet]].iloc[start - 1:end, :width].copy()
        if sheet == 3:
            for r in range(6):
                actual_table.iat[r + 1, 14] = calculated[r]
            for r in range(3):
                actual_table.iloc[r + 7, 2:14] = data.cached_monthly_totals[r]
                actual_table.iat[r + 7, 14] = calculated[r + 6]
        check([[normalized(v) for v in row] for row in actual_table.values] ==
              [[normalized(v) for v in row] for row in expected_table],
              f"Word/workbook mismatch in business table {index + 1}")
    return errors, list(KNOWN_ISSUES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        data = load_case(args.data_dir)
        errors, issues = validate_case(data)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print(f"ERROR: Cannot load source data: {exc}")
        return 1
    print(f"Demand: {data.demand.msu.sum():,.0f} MSU | Base capacity: {data.lines.base_msu.sum():.0f} MSU/month")
    print(f"Months: {len(data.months)} | Hubs: {len(data.hubs)} | Fixed arrivals: {len(data.arrivals)}")
    print(f"Validation: {'FAIL' if errors else 'PASS'} ({len(errors)} data errors)")
    for message in errors:
        print(f"ERROR: {message}")
    print("Unresolved source inputs (require clarification before modeling):")
    for issue in issues:
        print(f"- {issue}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
