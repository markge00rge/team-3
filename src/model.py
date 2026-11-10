"""Integrated V5 model; explicit FixedScenario retains historical regression support."""
from dataclasses import dataclass
from math import ceil

import pyomo.environ as pyo

from src.data_loader import CaseData


@dataclass(frozen=True)
class FixedScenario:
    """Test policy, not a newly inferred case-study fact."""
    transition_month: str
    reserve_l2_changeover: bool = True
    name: str = "January qualification, base crews, fixed L2 changeover allowance"


def build_model(data: CaseData, scenario: FixedScenario | None = None):
    """Default: daily integrated V5. Explicit scenario: historical monthly adapter."""
    integrated = scenario is None
    if integrated:
        from src.parameters import validate_parameters
        validate_parameters(data)
    scenario = scenario or FixedScenario(data.rules["target_launch"])
    if not integrated and scenario.transition_month not in data.months:
        raise ValueError("Transition month must be in the planning horizon")
    m = pyo.ConcreteModel(name="Venus V5 integrated 28-day supply chain" if integrated else "Venus historical fixed monthly scenario")
    m.scenario = None if integrated else scenario
    m._solve_success = False
    m.months = pyo.Set(initialize=data.months, ordered=True)
    m.lines = pyo.Set(initialize=data.lines.index)
    m.products = pyo.Set(initialize=tuple(data.products))
    m.families = pyo.Set(initialize=tuple(data.families))
    m.hubs = pyo.Set(initialize=data.hubs.index)
    m.priority_hubs = tuple(data.hubs.sort_values("priority").index)
    m.family_members = {f: tuple(ps) for f, ps in data.families.items()}
    demand = data.demand.set_index(["hub", "family", "month"]).msu.to_dict()
    m.demand = pyo.Param(m.hubs, m.families, m.months, initialize=demand)
    m.initial_fp = pyo.Param(m.products, initialize=data.initial_fp)

    capacities = {}
    for line in m.lines:
        for month in m.months:
            days = float(data.lines.loc[line, "days_per_month"])
            if integrated:
                days = 4 * int(data.rules["upgraded_profiles"][line].split("/")[1])
            elif line == "L2" and scenario.reserve_l2_changeover:
                days -= data.rules["changeover_days"]
            if not integrated and month == scenario.transition_month:
                days -= data.rules["qualification_days"]
            if days < 0:
                raise ValueError("Fixed downtime exceeds available scheduled days")
            capacities[line, month] = days * float(data.lines.loc[line, "msu_per_day"])
    m.capacity = pyo.Param(m.lines, m.months, initialize=capacities,
                           within=pyo.NonNegativeReals, mutable=True)
    m.fleet_limit = pyo.Param(initialize=data.rules["dedicated_trucks_month"],
                              within=pyo.NonNegativeIntegers, mutable=True)
    m.truck_msu = pyo.Param(initialize=data.rules["truck_msu"])
    m.production = pyo.Var(m.lines, m.products, m.months, domain=pyo.NonNegativeReals)
    m.inventory = pyo.Var(m.products, m.months, domain=pyo.NonNegativeReals)
    m.shipment = pyo.Var(m.products, m.hubs, m.months, domain=pyo.NonNegativeReals)
    m.unserved = pyo.Var(m.hubs, m.families, m.months, domain=pyo.NonNegativeReals)
    m.dedicated = pyo.Var(m.hubs, m.months, domain=pyo.NonNegativeIntegers)
    m.spot = pyo.Var(m.hubs, m.months, domain=pyo.NonNegativeIntegers)
    # Redundant, tight source-demand bounds improve presolve without restricting
    # any solution allowed by nonnegative family demand conservation.
    for h in m.hubs:
        for f in m.families:
            for t in m.months:
                limit = float(pyo.value(m.demand[h, f, t]))
                m.unserved[h, f, t].setub(limit)
                for p in m.family_members[f]:
                    m.shipment[p, h, t].setub(limit)
    for line in m.lines:
        for product in m.products:
            for month in m.months:
                active = (product == "B" or
                          (product == "A" and month < scenario.transition_month) or
                          (product == "C" and month >= scenario.transition_month))
                if product not in data.lines.loc[line, "products"] or (not integrated and not active):
                    m.production[line, product, month].fix(0)
    # A cannot satisfy demand after the fixed transition, nor C before it.
    for product in ("A", "C"):
        for month in m.months:
            if not integrated and ((product == "A" and month >= scenario.transition_month) or
                    (product == "C" and month < scenario.transition_month)):
                for hub in m.hubs:
                    m.shipment[product, hub, month].fix(0)

    m.production_limit = pyo.Constraint(m.lines, m.months, rule=lambda m, l, t:
                                      sum(m.production[l, p, t] for p in m.products) <= m.capacity[l, t])
    previous = {t: data.months[i - 1] if i else None for i, t in enumerate(data.months)}
    def balance(m, p, t):
        opening = m.initial_fp[p] if previous[t] is None else m.inventory[p, previous[t]]
        return m.inventory[p, t] == opening + sum(m.production[l, p, t] for l in m.lines) - sum(m.shipment[p, h, t] for h in m.hubs)
    m.inventory_balance = pyo.Constraint(m.products, m.months, rule=balance)
    # Only A/C have detailed physical stocks. B remains smoothly replenished.
    m.material_products = pyo.Set(initialize=("A", "C"))
    m.materials = pyo.Set(initialize=("RM", "PM"))
    m.bom_quantity = pyo.Param(m.products, m.materials, initialize={
        (p, k): float(data.bom.loc[p, "rm_kg_per_msu" if k == "RM" else "pm_ea_per_msu"])
        for p in m.products for k in m.materials})
    opening_materials = data.initial_materials.set_index(["product", "material"]).quantity.to_dict()
    m.initial_material = pyo.Param(m.material_products, m.materials, initialize=opening_materials,
                                   within=pyo.NonNegativeReals, mutable=True)
    fixed = {(p, k, t): 0.0 for p in m.material_products for k in m.materials for t in m.months}
    for row in data.arrivals.itertuples():
        fixed[row.product, row.material, row.date[:7]] += row.quantity
    m.fixed_material_arrival = pyo.Param(m.material_products, m.materials, m.months,
                                        initialize=fixed, within=pyo.NonNegativeReals, mutable=True)
    lead = data.rules["sea_lead_months"]
    if lead != int(lead) or lead < 1:
        raise ValueError("Sea lead time must be a positive integer number of months")
    lead = int(lead)
    m.order_arrival_month = {}
    for i, t in enumerate(data.months):
        year, month = map(int, t.split("-"))
        offset = year * 12 + month - 1 + lead
        m.order_arrival_month[t] = f"{offset // 12:04d}-{offset % 12 + 1:02d}"
    m.material_inventory = pyo.Var(m.material_products, m.materials, m.months, domain=pyo.NonNegativeReals)
    m.material_order = pyo.Var(m.material_products, m.materials, m.months, domain=pyo.NonNegativeReals)
    moq = {"RM": data.rules["rm_moq_kg"], "PM": data.rules["pm_moq_ea"]}
    m.lot_size = pyo.Param(m.materials, initialize=moq)
    # Bound useful lots by maximum eligible production after receipt, rounded
    # up to one complete lot. No legitimate consumption needs a larger order.
    lot_bounds = {}
    for p in m.material_products:
        for k in m.materials:
            for t in m.months:
                arrival = m.order_arrival_month[t]
                max_msu = sum(capacities[l, u] for l in m.lines for u in m.months
                    if u >= arrival and not m.production[l, p, u].fixed)
                lot_bounds[p, k, t] = ceil(max_msu * pyo.value(m.bom_quantity[p, k]) / moq[k])
    m.max_order_lots = pyo.Param(m.material_products, m.materials, m.months, initialize=lot_bounds)
    m.integer_lots = pyo.Var(m.material_products, m.materials, m.months,
                            domain=pyo.NonNegativeIntegers, bounds=lambda m, p, k, t: (0, m.max_order_lots[p, k, t]))
    for p, k, t in m.material_order:
        m.material_order[p, k, t].setub(moq[k] * lot_bounds[p, k, t])
    m.order_event = pyo.Var(m.material_products, m.materials, m.months, domain=pyo.Binary)
    m.order_lot_link = pyo.Constraint(m.material_products, m.materials, m.months,
        rule=lambda m, p, k, t: m.material_order[p, k, t] == m.lot_size[k] * m.integer_lots[p, k, t])
    m.event_upper = pyo.Constraint(m.material_products, m.materials, m.months,
        rule=lambda m, p, k, t: m.integer_lots[p, k, t] <= m.max_order_lots[p, k, t] * m.order_event[p, k, t])
    m.event_lower = pyo.Constraint(m.material_products, m.materials, m.months,
        rule=lambda m, p, k, t: m.integer_lots[p, k, t] >= m.order_event[p, k, t])
    m.additional_order_events = pyo.Expression(expr=sum(m.order_event[key] for key in m.order_event))
    # No pre-horizon invented orders, no purchases arriving beyond the horizon,
    # and no new A deliveries after its fixed production window closes.
    for p in m.material_products:
        for k in m.materials:
            for t in m.months:
                arrival = m.order_arrival_month[t]
                if arrival not in m.months or (not integrated and p == "A" and arrival >= scenario.transition_month):
                    m.material_order[p, k, t].fix(0)
                    m.integer_lots[p, k, t].fix(0)
                    m.order_event[p, k, t].fix(0)
    placed = {arrival: t for t, arrival in m.order_arrival_month.items() if arrival in m.months}
    m.additional_material_arrival = pyo.Expression(m.material_products, m.materials, m.months,
        rule=lambda m, p, k, t: m.material_order[p, k, placed[t]] if t in placed else 0)
    m.material_consumption = pyo.Expression(m.material_products, m.materials, m.months,
        rule=lambda m, p, k, t: m.bom_quantity[p, k] * sum(m.production[l, p, t] for l in m.lines))
    # Information only: no B stock/procurement variables or availability constraint.
    m.b_material_consumption = pyo.Expression(m.materials, m.months,
        rule=lambda m, k, t: m.bom_quantity["B", k] * sum(m.production[l, "B", t] for l in m.lines))
    def material_balance(m, p, k, t):
        opening = m.initial_material[p, k] if previous[t] is None else m.material_inventory[p, k, previous[t]]
        return m.material_inventory[p, k, t] == opening + m.fixed_material_arrival[p, k, t] + m.additional_material_arrival[p, k, t] - m.material_consumption[p, k, t]
    m.material_balance = pyo.Constraint(m.material_products, m.materials, m.months, rule=material_balance)
    # Nonmonetary quantity tie-break, within the cost ceiling: minimize purchased
    # MSU-equivalent quantities, normalizing kg and EA by their BOM factors.
    m.procurement_tiebreak = pyo.Expression(expr=sum(m.material_order[p, k, t] / m.bom_quantity[p, k]
        for p in m.material_products for k in m.materials for t in m.months))
    m.demand_balance = pyo.Constraint(m.hubs, m.families, m.months, rule=lambda m, h, f, t:
        sum(m.shipment[p, h, t] for p in m.family_members[f]) + m.unserved[h, f, t] == m.demand[h, f, t])
    m.transport_capacity = pyo.Constraint(m.hubs, m.months, rule=lambda m, h, t:
        sum(m.shipment[p, h, t] for p in m.products) <= m.truck_msu * (m.dedicated[h, t] + m.spot[h, t]))
    m.fleet_capacity = pyo.Constraint(m.months, rule=lambda m, t:
                                     sum(m.dedicated[h, t] for h in m.hubs) <= m.fleet_limit)
    m.shortage_by_hub = pyo.Expression(m.hubs, rule=lambda m, h:
                                      sum(m.unserved[h, f, t] for f in m.families for t in m.months))
    m.labor_cost = pyo.Expression(expr=len(data.months) * data.lines.operators.sum() * data.rules["operator_usd_per_month"])
    m.holding_cost = pyo.Expression(expr=sum(m.inventory[p, t] * data.bom.loc[p, "fp_usd_per_msu"] * data.rules["fp_holding_fraction_month"] for p in m.products for t in m.months))
    m.transport_cost = pyo.Expression(expr=sum(data.hubs.loc[h, "truck_usd"] * (m.dedicated[h, t] + (1 + data.rules["spot_surcharge_fraction"]) * m.spot[h, t]) for h in m.hubs for t in m.months))
    m.service_penalty = pyo.Expression(expr=sum(data.hubs.loc[h, "unserved_usd_per_msu"] * m.shortage_by_hub[h] for h in m.hubs))
    m.onsite_capacity = pyo.Param(initialize=data.rules["warehouse_pallets"], mutable=True)
    m.external_block_pallets = pyo.Param(initialize=data.rules["overflow_block_pallets"])
    m.fp_pallets = pyo.Expression(m.months, rule=lambda m, t:
        data.rules["fp_pallets_per_msu"] * sum(m.inventory[p, t] for p in m.products))
    m.rm_pallets = pyo.Expression(m.months, rule=lambda m, t:
        sum(m.material_inventory[p, "RM", t] for p in m.material_products) / data.rules["rm_kg_per_pallet"])
    m.pm_pallets = pyo.Expression(m.months, rule=lambda m, t:
        sum(m.material_inventory[p, "PM", t] for p in m.material_products) / data.rules["pm_ea_per_pallet"])
    m.tracked_pallets = pyo.Expression(m.months, rule=lambda m, t: m.fp_pallets[t] + m.rm_pallets[t] + m.pm_pallets[t])
    m.external_blocks = pyo.Var(m.months, domain=pyo.NonNegativeIntegers)
    m.warehouse_capacity = pyo.Constraint(m.months, rule=lambda m, t:
        m.tracked_pallets[t] <= m.onsite_capacity + m.external_block_pallets * m.external_blocks[t])
    m.external_storage_cost = pyo.Expression(expr=sum(m.external_blocks[t] * m.external_block_pallets *
        data.rules["overflow_usd_per_pallet_month"] for t in m.months))
    m.external_block_usd = pyo.Param(initialize=data.rules["overflow_block_pallets"] * data.rules["overflow_usd_per_pallet_month"])
    # Reporting metadata only: source conversions also drive the warehouse
    # expressions above. Keep conservative peak diagnostics in the same units.
    m.inventory_pallet_factors = dict(FP=data.rules["fp_pallets_per_msu"],
        RM=1 / data.rules["rm_kg_per_pallet"], PM=1 / data.rules["pm_ea_per_pallet"])
    # IDE is omitted. B physical material footprint is unspecified/excluded.
    # No material purchasing term is included.
    m.total_cost = pyo.Expression(expr=m.labor_cost + m.holding_cost + m.transport_cost + m.service_penalty + m.external_storage_cost)
    m.objective = pyo.Objective(expr=0, sense=pyo.minimize)
    if integrated:
        from src.scheduling import add_integrated_schedule
        add_integrated_schedule(m, data)
        from src.priorities import add_monthly_priorities
        add_monthly_priorities(m)
        if not data.rules.get('legacy_v5',False):
            from src.financial_model import add_material_financials
            add_material_financials(m,data)
    return m
