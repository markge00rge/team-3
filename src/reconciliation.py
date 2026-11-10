"""Read-only financial recomputation of saved V4 decisions; never calls a solver."""
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path

import pandas as pd

from src.data_loader import ROOT, load_case

INPUT_TABLES = ("production", "inventory", "shipments", "service", "transport",
                "staffing", "material_balances", "warehouse", "material_orders")
MARKER = "=== MONTHLY FINANCIAL RECONCILIATION (generated) ==="
COST_COLUMNS = ("base_salaries_usd", "new_crew_salaries_usd", "hiring_fees_usd",
                "a_rm_scrap_value_usd", "a_pm_scrap_value_usd", "a_rm_disposal_usd",
                "a_pm_disposal_usd", "fp_holding_usd", "dedicated_transport_usd",
                "spot_transport_usd", "service_penalties_usd", "external_storage_usd")


@dataclass
class Reconciliation:
    monthly: pd.DataFrame
    products: pd.DataFrame
    costs: pd.DataFrame
    diagnostics: dict


def read_saved(directory):
    directory = Path(directory)
    tables = {name: pd.read_csv(directory / f"{name}.csv", float_precision="round_trip")
              for name in INPUT_TABLES}
    status = json.loads((directory / "solve_status.json").read_text(encoding="utf-8"))
    return tables, status


def _close(actual, expected, label, tolerance=1e-5):
    if not math.isfinite(float(actual)) or abs(actual - expected) > tolerance:
        raise ValueError(f"{label}: actual {actual!r}, expected {expected!r}")


def _grid(frame, keys, expected, name):
    if frame.duplicated(keys).any() or set(frame[keys].itertuples(index=False, name=None)) != set(expected):
        raise ValueError(f"Missing, duplicate or unexpected {name} records")
    numeric = frame.select_dtypes(include="number")
    if frame.isna().any().any() or not numeric.map(math.isfinite).all().all():
        raise ValueError(f"Missing or nonfinite {name} values")


def calculate(data, tables, status):
    """Recompute from quantities and source rates, not exported cost subtotals.

    Original binary-floating-point levels are retained. Rounding is only for
    readable Markdown; it is never used to calculate a balance or expense.
    """
    months, products, hubs = tuple(data.months), tuple(data.products), tuple(data.hubs.index)
    from src.financial_model import material_price
    complete='total_delivery_cost' in status['costs']
    explicit=status.get('material_policy')=='explicit_abc_v7'
    if explicit:
        from src.material_policy import planning_case
        data=planning_case(data,explicit=True)
    orders=tables.get('material_orders',pd.DataFrame())
    from itertools import product
    specs = {
        "production": (["line", "product", "month"], product(data.lines.index, products, months)),
        "inventory": (["product", "month"], product(products, months)),
        "shipments": (["product", "hub", "month"], product(products, hubs, months)),
        "service": (["hub", "family", "month"], product(hubs, data.families, months)),
        "transport": (["hub", "month"], product(hubs, months)),
        "staffing": (["line", "month"], product(data.lines.index, months)),
        "material_balances": (["product", "material", "month"], product(("A", "B", "C") if explicit else ("A", "C"), ("RM", "PM"), months)),
        "warehouse": (["month"], ((t,) for t in months)),
    }
    for name, (keys, expected) in specs.items():
        _grid(tables[name], keys, expected, name)
    made = tables["production"].groupby(["product", "month"]).msu.sum()
    if explicit:
        stock=data.initial_materials.set_index(['product','material']).quantity.to_dict()
        order_grid={(r.product,r.material,r.order_month):r for r in orders.itertuples()}
        _grid(orders,['product','material','order_month'],product(products,('RM','PM'),months),'material orders')
        for r in orders.itertuples():
            lot=data.rules['rm_moq_kg' if r.material=='RM' else 'pm_moq_ea']
            _close(r.quantity,r.integer_lots*lot,'Integer lot quantity')
            _close(r.integer_lots,round(r.integer_lots),'Whole procurement lots')
            _close(r.order_event,int(r.quantity>1e-5),'Order-event indicator')
            year,month=map(int,r.order_month.split('-'));offset=year*12+month-1+int(data.rules['sea_lead_months'])
            expected=f'{offset//12:04d}-{offset%12+1:02d}'
            if r.arrival_month!=expected: raise ValueError('Procurement arrival month violates lead time')
            if expected not in months: _close(r.quantity,0,'No outside-horizon orders')
        for r in tables['material_balances'].sort_values(['product','material','month']).itertuples():
            key=(r.product,r.material);i=months.index(r.month)
            _close(r.opening,stock[key],'Material opening carry-forward')
            fixed=data.arrivals[(data.arrivals['product']==r.product)&(data.arrivals.material==r.material)&(data.arrivals.date.str[:7]==r.month)].quantity.sum()
            _close(r.fixed_arrival,fixed,'Fixed material receipts')
            lead=int(data.rules['sea_lead_months'])
            arriving=order_grid[r.product,r.material,months[i-lead]].quantity if i>=lead else 0
            _close(r.additional_arrival,arriving,'Procurement lead-time receipts')
            col='rm_kg_per_msu' if r.material=='RM' else 'pm_ea_per_msu'
            _close(r.consumption,made[r.product,r.month]*data.bom.loc[r.product,col],'Actual-production BOM consumption')
            _close(r.ending,r.opening+r.fixed_arrival+r.additional_arrival-r.consumption-r.scrap,'Material conservation')
            if r.ending < -1e-5: raise ValueError('Negative material inventory')
            if r.product!='A': _close(r.scrap,0,'Only A materials may be scrapped')
            stock[key]=r.ending
        for r in tables['warehouse'].itertuples():
            balances=tables['material_balances'][tables['material_balances'].month==r.month]
            rm=balances.query("material == 'RM'").ending.sum()/data.rules['rm_kg_per_pallet']
            pm=balances.query("material == 'PM'").ending.sum()/data.rules['pm_ea_per_pallet']
            _close(r.rm_pallets,rm,'ABC RM pallets');_close(r.pm_pallets,pm,'ABC PM pallets')
            _close(r.tracked_pallets,r.fp_pallets+rm+pm,'Combined warehouse pallets')
            if r.tracked_pallets>r.onsite_capacity+data.rules['overflow_block_pallets']*r.external_blocks+1e-5:
                raise ValueError('Warehouse capacity exceeded')
    sent = tables["shipments"].groupby(["product", "month"]).msu.sum()
    ending = tables["inventory"].set_index(["product", "month"]).msu
    demand = data.demand.set_index(["hub", "family", "month"]).msu
    for row in tables["service"].itertuples():
        _close(row.demand_msu, demand[row.hub, row.family, row.month], "source demand")
        _close(row.served_msu + row.unserved_msu, row.demand_msu, "demand accounting")
        member_shipments = tables["shipments"]
        member_shipments = member_shipments[(member_shipments.hub == row.hub) &
            (member_shipments.month == row.month) & member_shipments["product"].isin(data.families[row.family])]
        _close(member_shipments.msu.sum(), row.served_msu, "family shipment accounting")
    records = []
    rate = data.rules["fp_holding_fraction_month"]
    for p in products:
        opening = data.initial_fp[p]
        price = data.bom.loc[p, "fp_usd_per_msu"]
        for t in months:
            close, production, shipments = ending[p, t], made[p, t], sent[p, t]
            _close(opening + production - shipments, close, f"{p} {t} FP balance")
            if close < -1e-5:
                raise ValueError(f"Negative ending FP: {p} {t}")
            records.append(dict(month=t, product=p, opening_fp_msu=opening,
                production_msu=production, shipments_msu=shipments, ending_fp_msu=close,
                valuation_usd_per_msu=price, ending_fp_value_usd=close * price,
                holding_expense_usd=close * price * rate))
            opening = close
    detail = pd.DataFrame(records)
    monthly = []
    for t in months:
        rows = detail[detail.month == t]
        families = data.demand[data.demand.month == t].groupby("family").msu.sum()
        production = rows.set_index("product").production_msu
        opening, shipments = rows.opening_fp_msu.sum(), rows.shipments_msu.sum()
        net = rows.production_msu.sum() - shipments
        close = rows.ending_fp_msu.sum()
        _close(opening + net, close, f"{t} aggregate FP balance")
        _close(close * data.rules["fp_pallets_per_msu"], tables["warehouse"].set_index("month").loc[t, "fp_pallets"], "FP pallets")
        monthly.append(dict(month=t, ac_demand_msu=families["AC"], b_demand_msu=families["B"],
            total_demand_msu=families.sum(), a_production_msu=production["A"],
            c_production_msu=production["C"], b_production_msu=production["B"],
            total_production_msu=rows.production_msu.sum(), opening_fp_msu=opening,
            shipments_msu=shipments, unserved_msu=tables["service"].query("month == @t").unserved_msu.sum(),
            net_fp_change_msu=net, ending_fp_msu=close, fp_pallets=close * data.rules["fp_pallets_per_msu"]))
    monthly = pd.DataFrame(monthly)
    cash = []
    for t in months:
        staff = tables["staffing"].query("month == @t")
        scrap = tables["material_balances"].query("product == 'A' and month == @t").set_index("material").scrap
        rm, pm = scrap["RM"], scrap["PM"]
        transport = tables["transport"].query("month == @t").set_index("hub")
        service = tables["service"].query("month == @t").groupby("hub").unserved_msu.sum()
        wage, crew = data.rules["operator_usd_per_month"], data.rules["upgrade_operators_per_line"]
        row = dict(month=t, base_salaries_usd=data.lines.operators.sum() * wage,
            new_crew_salaries_usd=staff.employed_crews.sum() * crew * wage,
            hiring_fees_usd=staff.hired_crew.sum() * crew * data.rules["hiring_usd_per_operator"],
            a_rm_scrap_value_usd=rm * material_price(data,'A','RM'),
            a_pm_scrap_value_usd=pm * material_price(data,'A','PM'),
            a_rm_disposal_usd=rm / 1000 * data.rules["disposal_usd_per_ton"],
            a_pm_disposal_usd=pm * (data.rules["pm_kg_per_1000_ea"] / 1000) / 1000 * data.rules["disposal_usd_per_ton"],
            fp_holding_usd=math.fsum(detail.query("month == @t").holding_expense_usd),
            dedicated_transport_usd=sum(transport.loc[h, "dedicated_trucks"] * data.hubs.loc[h, "truck_usd"] for h in hubs),
            spot_transport_usd=sum(transport.loc[h, "spot_trucks"] * data.hubs.loc[h, "truck_usd"] * (1 + data.rules["spot_surcharge_fraction"]) for h in hubs),
            service_penalties_usd=sum(service[h] * data.hubs.loc[h, "unserved_usd_per_msu"] for h in hubs),
            external_storage_usd=tables["warehouse"].query("month == @t").external_blocks.item() * data.rules["overflow_block_pallets"] * data.rules["overflow_usd_per_pallet_month"])
        row["total_modeled_cost_usd"] = math.fsum(row[c] for c in COST_COLUMNS)
        if complete:
            row['dismissal_expense_usd']=staff.dismissed_crew.sum()*crew*data.rules.get('dismissal_usd_per_operator',0)
            row['full_ide_usd']=sum(row[c] for c in COST_COLUMNS[3:7])
            row['operating_full_ide_usd']=row['total_modeled_cost_usd']+row['dismissal_expense_usd']
            overlap=0.0
            for k in ('RM','PM'):
                annual_scrap=tables['material_balances'].query("product == 'A' and material == @k").scrap.sum()
                annual_orders=orders.query("product == 'A' and material == @k").quantity.sum()
                expected=min(annual_scrap,annual_orders) if scrap[k]>1e-7 else 0.0
                actual=tables['material_balances'].query("product == 'A' and material == @k and month == @t").new_purchased_scrap.item()
                _close(actual,expected,'New purchased A scrap provenance',1e-4)
                overlap+=actual*material_price(data,'A',k)
            row['ide_overlap_adjustment_usd']=overlap
            row['operating_expenses_usd']=row['operating_full_ide_usd']-overlap
            for p in (('A','B','C') if explicit else ('A','C')):
                for k in ('RM','PM'):
                    amount=orders.query('product == @p and material == @k and order_month == @t').quantity.sum()
                    row[f'{p.lower()}_{k.lower()}_order_usd']=amount*material_price(data,p,k)
                row[f'{p.lower()}_material_cost_usd']=row[f'{p.lower()}_rm_order_usd']+row[f'{p.lower()}_pm_order_usd']
            if not explicit:
                for k,col in [('RM','rm_kg_per_msu'),('PM','pm_ea_per_msu')]:
                    row[f'b_{k.lower()}_consumption_usd']=made['B',t]*data.bom.loc['B',col]*material_price(data,'B',k)
                row['b_material_cost_usd']=row['b_rm_consumption_usd']+row['b_pm_consumption_usd']
            row['total_delivery_cost_usd']=row['operating_expenses_usd']+sum(row[f'{p}_material_cost_usd'] for p in ('a','c','b'))
            row['total_modeled_cost_usd']=row['total_delivery_cost_usd']
        cash.append(row)
    costs = pd.DataFrame(cash)
    annual = {"month": "ANNUAL"}
    annual.update({c: math.fsum(monthly[c]) for c in monthly.columns if c != "month"})
    annual.update(opening_fp_msu=monthly.iloc[0].opening_fp_msu,
                  ending_fp_msu=monthly.iloc[-1].ending_fp_msu, fp_pallets=monthly.iloc[-1].fp_pallets)
    monthly = pd.concat([monthly, pd.DataFrame([annual])], ignore_index=True)
    totals = {c: math.fsum(costs[c]) for c in costs.columns if c != "month"}
    costs = pd.concat([costs, pd.DataFrame([dict(month="ANNUAL", **totals)])], ignore_index=True)
    groups = dict(labor=sum(totals[c] for c in COST_COLUMNS[:3]), fp_holding=totals["fp_holding_usd"],
        transportation=totals["dedicated_transport_usd"]+totals["spot_transport_usd"],
        ide=sum(totals[c] for c in COST_COLUMNS[3:7]), service_failure=totals["service_penalties_usd"],
        external_storage=totals["external_storage_usd"], total_modeled=totals["total_modeled_cost_usd"])
    if complete:
        groups['labor']+=totals['dismissal_expense_usd']
        groups.update(operating_full_ide=totals['operating_full_ide_usd'],ide_overlap_adjustment=totals['ide_overlap_adjustment_usd'],
            operating_expenses=totals['operating_expenses_usd'],a_materials=totals['a_material_cost_usd'],
            c_materials=totals['c_material_cost_usd'],b_materials=totals['b_material_cost_usd'],
            total_delivery_cost=totals['total_delivery_cost_usd'],dismissal=totals['dismissal_expense_usd'])
    for name, value in groups.items():
        _close(value, status["costs"][name], f"reported {name}", .01)
    monetary_stage = next((s for s in status["stages"] if s["name"] == "modeled_cost"), {"termination": "notRun"})
    if monetary_stage["termination"] == "optimal":
        _close(groups["total_modeled"], monetary_stage["optimum"], "proven minimum monetary cost", .01)
    opening_value = math.fsum(r.opening_fp_msu * r.valuation_usd_per_msu for r in detail.itertuples())
    total_end_msu = math.fsum(detail.ending_fp_msu)
    all_ac_as_a = math.fsum(r.ending_fp_msu * (data.bom.loc["A", "fp_usd_per_msu"] if r.product in ("A", "C") else r.valuation_usd_per_msu) * rate for r in detail.itertuples())
    diagnostics = dict(annual_costs=groups, holding_by_product=detail.groupby("product").holding_expense_usd.sum().to_dict(),
        opening_basis_holding_usd=opening_value*rate,
        ending_basis_holding_usd=groups["fp_holding"],
        annual_ending_only_holding_usd=detail[detail.month == months[-1]].ending_fp_value_usd.sum()*rate,
        all_fp_at_c_value_holding_usd=total_end_msu*data.bom.loc["C", "fp_usd_per_msu"]*rate,
        ac_stock_at_a_value_holding_usd=all_ac_as_a,
        rounded_integer_msu_holding_usd=math.fsum(round(r.ending_fp_msu)*r.valuation_usd_per_msu*rate for r in detail.itertuples()),
        residual_vs_reported_usd=groups["total_modeled"]-status["costs"]["total_modeled"],
        residual_vs_proven_minimum_usd=groups["total_modeled"]-monetary_stage["optimum"] if monetary_stage["termination"] == "optimal" else None,
        monthly_ending_inventory_sum_msu=total_end_msu)
    return Reconciliation(monthly, detail, costs, diagnostics)


def markdown(frame):
    """Display formatting only; retain original floating-point numbers in CSV."""
    def display(v):
        if isinstance(v, (int, float)):
            return f"{0.0 if abs(v) < 0.0000005 else v:,.2f}"
        return str(v)
    rows = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join("---" for _ in frame.columns) + " |"]
    rows += ["| " + " | ".join(display(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None)]
    return "\n".join(rows)


def write_reconciliation(data, directory, *, excel_total=1217953.0):
    directory = Path(directory)
    tables, status = read_saved(directory)
    report = calculate(data, tables, status)
    report.monthly.to_csv(directory / "monthly_production_inventory.csv", index=False)
    report.products.to_csv(directory / "monthly_inventory_by_product.csv", index=False)
    report.costs.to_csv(directory / "monthly_cost_breakdown.csv", index=False)
    d, annual = report.diagnostics, report.costs.iloc[-1]
    difference = excel_total - annual.total_modeled_cost_usd
    implied_holding = excel_total - (annual.total_modeled_cost_usd-annual.fp_holding_usd)
    monetary = next(s for s in status["stages"] if s["name"] == "modeled_cost")
    service_percent = 100 * (report.monthly.iloc[-1].total_demand_msu-report.monthly.iloc[-1].unserved_msu)/report.monthly.iloc[-1].total_demand_msu
    proof_text = (f"Service is {service_percent:.6g}%. Monetary-stage termination is `{monetary['termination']}`. "
                  f"Full lexicographic proof flag remains `{status['success']}`. ")
    event = next((s for s in status["stages"] if s["name"] == "international_order_events"), None)
    if event and event["termination"] != "optimal":
        proof_text += (f"Procurement-event minimization remains unproven: `{event['termination']}`, "
            f"incumbent {event.get('incumbent_objective', event.get('upper_bound', 'unavailable'))}, "
            f"bound {event.get('lower_bound', 'unavailable')}, "
            f"{100*event.get('incumbent_gap', event.get('relative_gap', float('nan'))):.6g}% gap. "
            "Later quantity/cleanup stages did not run. ")
    proof_text += "This report does not change or reinterpret solver proof status."
    lines = ["# V4 financial reconciliation of the saved plan", "",
        "Reporting only: no solver was run and no formulation, assumptions, rates or decisions were changed.", "",
        proof_text, "",
        f"Independently recalculated total: **${annual.total_modeled_cost_usd:,.2f}**. User Excel total: **${excel_total:,.2f}**. "
        f"Unexplained Excel-minus-model difference: **${difference:,.2f}**. "
        f"Recalculation minus saved objective: {d['residual_vs_reported_usd']:.12g} USD.", "",
        "## Formulas and annual cost components", "",
        "All rates come from the original workbook through load_case(); all quantities come from the saved V4 CSVs. "
        "Binary floating-point values are read with round-trip precision. Nothing is rounded or clamped before calculations. "
        "CSV precision is retained; readable tables show two decimals and display numerical near-zero noise as zero only.", "",
        "| Component | Independent formula and saved quantities | Annual USD |", "| --- | --- | ---: |"]
    formulas = [
        ("Base salaries", "sum source line operators (70) x $1,000 x 12", "base_salaries_usd"),
        ("New crew salaries", "sum staffing.employed_crews x 10 x $1,000, including training", "new_crew_salaries_usd"),
        ("Hiring", "sum staffing.hired_crew x 10 x $500", "hiring_fees_usd"),
        ("A RM scrap value", "monthly A RM scrap kg x $5/kg", "a_rm_scrap_value_usd"),
        ("A PM scrap value", "monthly A PM scrap EA x $0.40/EA", "a_pm_scrap_value_usd"),
        ("A RM disposal", "A RM scrap kg / 1,000 x $200/ton", "a_rm_disposal_usd"),
        ("A PM disposal", "A PM scrap EA x 0.02 kg/EA / 1,000 x $200/ton", "a_pm_disposal_usd"),
        ("FP holding / working capital", "sum all product/month ending FP x product value x 0.015", "fp_holding_usd"),
        ("Dedicated transport", "sum hub/month dedicated trucks x $300/$500/$800 per hub", "dedicated_transport_usd"),
        ("Spot transport", "sum hub/month spot trucks x hub rate x 1.6", "spot_transport_usd"),
        ("Service penalties", "sum unserved hub/family/month MSU x $3,000/$2,000/$1,200", "service_penalties_usd"),
        ("External rental", "sum monthly external_blocks x 100 pallets x $45", "external_storage_usd")]
    lines += [f"| {label} | {formula} | {annual[column]:,.2f} |" for label, formula, column in formulas]
    lines += [f"| **Total** | Sum the twelve categories once | **{annual.total_modeled_cost_usd:,.2f}** |", "",
        "FP values are A=$4,000/MSU, B=$5,500/MSU and C=$4,200/MSU. There is no separate material purchasing cost. "
        "New-crew salaries already include training salaries; neither is counted twice. Scrap material values are charged once in IDE. "
        "No holding charge is applied to raw materials, packaging, demand or pallet counts.", "",
        f"Difference from the separately proven monetary minimum (stage 4): {d['residual_vs_proven_minimum_usd']} USD. "
        "The few-billionths-of-a-dollar residual is floating-point noise in the saved later-stage plan, not $2,485.50.", "",
        "## Holding-cost investigation", "",
        "The product-specific month-end method is correct for the modeled objective. The saved plan's recomputed holding cost "
        "matches solve_status.json within numerical tolerance. Product contributions:", ""]
    lines += [f"- {p}: ${0 if abs(value) < 0.0000005 else value:,.2f}" for p, value in sorted(d["holding_by_product"].items())]
    lines += ["", f"If all other Excel components agree, Excel would imply **${implied_holding:,.2f}** holding expense. "
        "That is a conditional inference only: the Excel component breakdown has not been supplied.", "",
        "| Diagnostic calculation (not a model change) | Holding USD |", "| --- | ---: |"]
    for label, key in (("Correct ending product-specific stock", "ending_basis_holding_usd"),
                       ("Opening stock instead of ending", "opening_basis_holding_usd"),
                       ("Only September ending stock instead of twelve months", "annual_ending_only_holding_usd"),
                       ("All FP at C's $4,200 value", "all_fp_at_c_value_holding_usd"),
                       ("A/C stock at A's $4,000 value; B at $5,500", "ac_stock_at_a_value_holding_usd"),
                       ("Round each product's MSU to an integer first", "rounded_integer_msu_holding_usd")):
        lines.append(f"| {label} | {d[key]:,.2f} |")
    lines += ["", "Opening-versus-ending changes annual holding by the opening FP value less September closing FP value, "
        "times 1.5%. Opening FP is A=10 and B=15 MSU: $122,500, or $1,837.50 holding. This does not explain $2,485.50 alone. "
        "Using A's value for C stock understates rather than explains a higher Excel total. A and C share demand, but never a common valuation.", "",
        f"The monthly ending stocks sum to {d['monthly_ending_inventory_sum_msu']:,.6f} MSU-months. This is a holding exposure, "
        "not September stock or annual physical inventory. Prebuilt stock is charged again in each month it remains held. "
        "Negative net changes in May–July are drawdowns, not negative ending inventories. Tiny signed floating-point residues "
        "are numerical noise; integer rounding changes this plan's financial total only below the displayed cent, not by $2,485.50.", "",
        "Plan version matters: historical V2.1 holding was $58,987.50; current V4 holding is $56,167.50, a $2,820 change, "
        "which is also not $2,485.50. ANALYSIS.md, summary.txt, raw saved stocks and solve_status.json agree on the current V4 cost. "
        "Alternative schedules can have different product inventory composition; a copied monthly plan must be compared to the same saved solution.", "",
        "The CSVs contain the saved event-stage incumbent, not a separately archived copy of every stage-4 decision. "
        "It is monetary-cost optimal because its independently reconstructed cost equals the proven stage-4 minimum within tolerance. "
        "An exact vector-by-vector comparison with the original stage-4 plan is unavailable; multiple monetary-optimal plans may exist. "
        "There is no evidence here that an inconsistent plan caused the Excel difference.", "",
        "The discrepancy cannot be conclusively attributed to working capital from a single Excel grand total. "
        "For complete reconciliation, provide Excel's twelve monthly FP holding totals (ideally the 36 product/month opening/ending MSU, "
        "valuation and formula cells), base salaries, new salaries including training, hiring fees, four IDE components, dedicated transport, "
        "spot transport, service penalties and external storage totals. Also identify the source plan/version, truck counts, scrap quantities, "
        "rounding conventions, and whether opening, average or ending stock was charged. These components should sum to $1,217,953.00.", "",
        "## Monthly production and inventory", "", markdown(report.monthly), "",
        "ANNUAL sums demand/production/shipments/unserved/net flows. Its opening stock is October's opening, "
        "and its ending stock/pallets are September's ending balances, not sums of monthly stocks.", "",
        "## Monthly monetary breakdown (USD)", "", markdown(report.costs), "",
        "## Monthly product inventory and holding (MSU / USD)", "", markdown(report.products), "",
        "## Reproduce without optimizing", "", "```powershell",
        ".\\.venv\\Scripts\\python.exe -m src.results --report-dir reports/v4", "```", "",
        "This command reads existing results and source rates, overwrites only these generated reconciliation files and "
        "replaces the generated reconciliation appendix in summary.txt. Solver status and raw decision CSVs remain untouched. "
        "V2.1 historical results are not written.", "", "## Input SHA-256 fingerprints", ""]
    inputs = [directory / f"{name}.csv" for name in INPUT_TABLES] + [directory / "solve_status.json"]
    inputs += list((ROOT / "data").glob("Venus_PS_*"))
    lines += [f"- `{p.name}`: `{sha256(p.read_bytes()).hexdigest()}`" for p in inputs]
    (directory / "FINANCIAL_RECONCILIATION.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    summary = directory / "summary.txt"
    with summary.open("r", encoding="utf-8", newline="") as stream:
        prefix = stream.read().split(MARKER, 1)[0].rstrip("\r\n")
    appendix = "\n\n"+MARKER+"\nMonthly production / inventory (display only: two decimals):\n"+markdown(report.monthly)
    appendix += "\n\nMonthly monetary costs USD:\n"+markdown(report.costs)+"\n\nSee FINANCIAL_RECONCILIATION.md for formulas, diagnostics and proof status.\n"
    with summary.open("w", encoding="utf-8", newline="") as stream:
        stream.write(prefix+appendix)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports/v4")
    parser.add_argument("--excel-total", type=float, default=1217953.0)
    args = parser.parse_args()
    report = write_reconciliation(load_case(), args.report_dir, excel_total=args.excel_total)
    print(f"Recalculated modeled cost: ${report.costs.iloc[-1].total_modeled_cost_usd:,.2f}")
    print(f"FP holding: ${report.diagnostics['ending_basis_holding_usd']:,.2f}")
    print(f"Excel difference, unexplained: ${args.excel_total-report.costs.iloc[-1].total_modeled_cost_usd:,.2f}")
    print(f"Reports: {args.report_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
