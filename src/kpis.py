"""Pure operational/cash diagnostics. None of these metrics constrain the MILP."""
import math
import pandas as pd


def ratio(numerator, denominator):
    return numerator / denominator if denominator > 0 else float("nan")


def cumulative_indicators(monthly, capacity, initial_fp):
    """Capacity excludes opening stock; supply includes it exactly once."""
    frame = monthly[monthly.month != "ANNUAL"].copy().reset_index(drop=True)
    frame["available_capacity_msu"] = frame.month.map(capacity)
    for source, target in (("total_demand_msu", "cumulative_demand_msu"),
                           ("total_production_msu", "cumulative_production_msu"),
                           ("available_capacity_msu", "cumulative_capacity_msu"),
                           ("shipments_msu", "cumulative_shipments_msu")):
        frame[target] = frame[source].cumsum()
    frame["initial_fp_msu"] = initial_fp
    frame["cumulative_supply_msu"] = initial_fp + frame.cumulative_production_msu
    for numerator, name in (("cumulative_capacity_msu", "capacity_to_demand"),
                            ("cumulative_supply_msu", "supply_to_demand")):
        frame[name] = [ratio(n, d) for n, d in zip(frame[numerator], frame.cumulative_demand_msu)]
        frame[name + "_below_one"] = frame[name] < 1 - 1e-8
        frame[name + "_defined"] = frame.cumulative_demand_msu > 0
    frame["monthly_service_fraction"] = [ratio(s, d) for s, d in zip(frame.shipments_msu, frame.total_demand_msu)]
    frame["cumulative_service_fraction"] = [ratio(s, d) for s, d in zip(frame.cumulative_shipments_msu, frame.cumulative_demand_msu)]
    return frame


def calculate_kpis(data, tables, financial):
    daily = tables["daily_schedule"].copy()
    daily["production"] = daily[["production_a", "production_b", "production_c"]].sum(axis=1)
    rows = []
    for l in data.lines.index:
        rate = float(data.lines.loc[l, "msu_per_day"])
        for t in data.months:
            days = daily[(daily.line == l) & (daily.month == t)]
            if len(days) != 28 or set(days.planning_day) != set(range(1, 29)):
                raise ValueError("Daily schedule must contain exactly 28 distinct planning days")
            scheduled = days.scheduled.sum()
            shutdown, changes = days.shutdown.sum(), days.changeover.sum()
            available = scheduled - shutdown - changes
            capacity, production = available * rate, days.production.sum()
            exported = tables["line_capacity"].query("line == @l and month == @t").iloc[0]
            if abs(capacity - exported.capacity_msu) > 1e-5 or abs(production - exported.production_msu) > 1e-5:
                raise ValueError("Capacity or daily/monthly production does not reconcile")
            staff = tables["staffing"].query("line == @l and month == @t").iloc[0]
            rows.append(dict(month=t, line=l, scheduled_days=scheduled, available_days=available,
                actual_manufacturing_days=int((days.production > 1e-5).sum()),
                equivalent_full_rate_days=production / rate, qualification_days=shutdown,
                changeover_days=changes, available_capacity_msu=capacity, production_msu=production,
                capacity_utilization=ratio(production, capacity), hired_crew=staff.hired_crew,
                training=staff.training, upgraded=staff.upgraded,
                upgrade_theoretical_gain_msu=(scheduled - data.lines.loc[l, "days_per_month"]) * rate,
                employed_operators=data.lines.loc[l, "operators"] + staff.employed_crews * data.rules["upgrade_operators_per_line"]))
    productivity = pd.DataFrame(rows)
    capacity = productivity.groupby("month").available_capacity_msu.sum()
    indicators = cumulative_indicators(financial.monthly, capacity, sum(data.initial_fp.values()))
    cash = financial.products.groupby("month").ending_fp_value_usd.sum()
    material = tables["material_balances"].copy()
    from src.financial_model import material_price
    material["inventory_value_usd"] = [r.ending*material_price(data,r.product,r.material) for r in material.itertuples()]
    cash_rows = []
    for t in data.months:
        cash_rows.append(dict(month=t, ending_fp_value_usd=cash[t],
            cash_tied_up_fp_usd=cash[t], **{('tracked_abc_material_value_usd' if data.rules.get('explicit_b_materials',False) else 'tracked_ac_material_value_usd'):material.query("month == @t").inventory_value_usd.sum()},
            working_capital_holding_expense_usd=financial.costs.query("month == @t").fp_holding_usd.item()))
    operations = indicators.copy().set_index("month")
    def attach(frame, index, columns, prefix):
        wide = frame.pivot(index="month", columns=index, values=columns)
        wide.columns = [prefix + "_".join(map(str, c if isinstance(c, tuple) else (c,))) for c in wide.columns]
        return wide
    for frame, index, columns, prefix in (
        (tables["service"], ["hub", "family"], ["served_msu", "unserved_msu"], "service_"),
        (tables["production"], ["line", "product"], ["msu"], "production_"),
        (tables["inventory"], ["product"], ["msu"], "ending_fp_"),
        (tables["material_balances"], ["product", "material"], ["ending", "additional_arrival"], "material_"),
        (tables["transport"], ["hub"], ["dedicated_trucks", "spot_trucks"], "transport_"),
        (productivity, ["line"], ["available_capacity_msu", "scheduled_days", "available_days", "actual_manufacturing_days",
           "qualification_days", "changeover_days", "hired_crew", "training", "upgraded", "capacity_utilization"], "line_")):
        operations = operations.join(attach(frame, index, columns, prefix))
    operations = operations.join(tables["warehouse"].set_index("month").drop(columns=["fp_pallets"]))
    operations["additional_order_events"] = tables["material_orders"].groupby("order_month").order_event.sum()
    operations["employed_operators"] = productivity.groupby("month").employed_operators.sum()
    operations["production_msu_per_employed_operator"] = operations.total_production_msu / operations.employed_operators
    return dict(cumulative_indicators=indicators, productivity=productivity,
                cash=pd.DataFrame(cash_rows), material_valuation=material,
                monthly_operations=operations.reset_index())
