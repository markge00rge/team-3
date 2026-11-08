"""Exact 28-day manufacturing, one-way qualification, crewing and A scrap MILP."""
from math import ceil

import pyomo.environ as pyo


def scheduled(day, profile):
    """Planning weekday 1..7 repeats four times; never use Gregorian lengths."""
    return (day - 1) % 7 < profile


def add_integrated_schedule(m, data):
    months = list(m.months)
    n = 28 * len(months)
    m.integrated_schedule = True
    m.days = pyo.RangeSet(1, n)
    m.day_month = {d: months[(d - 1) // 28] for d in m.days}
    m.planning_day = {d: (d - 1) % 28 + 1 for d in m.days}
    m.month_days = {t: tuple(d for d in m.days if m.day_month[d] == t) for t in months}
    m.base_profile = {"L1": 5, "L2": 6}
    m.upgrade_profile = {"L1": 6, "L2": 7}
    m.rate = {l: float(data.lines.loc[l, "msu_per_day"]) for l in m.lines}
    m.hire = pyo.Var(m.lines, m.months, domain=pyo.Binary)
    m.upgraded = pyo.Var(m.lines, m.months, domain=pyo.Binary)
    m.one_hire = pyo.Constraint(m.lines, rule=lambda m, l: sum(m.hire[l, t] for t in m.months) <= 1)
    m.upgrade_training = pyo.Constraint(m.lines, m.months, rule=lambda m, l, t:
        m.upgraded[l, t] == sum(m.hire[l, u] for u in months[:months.index(t)]))
    for l in m.lines:
        m.hire[l, months[-1]].fix(0)  # no intended activation beyond horizon
    m.employed = pyo.Expression(m.lines, m.months, rule=lambda m, l, t:
        sum(m.hire[l, u] for u in months[:months.index(t) + 1]))
    m.operating = pyo.Expression(m.lines, m.days, rule=lambda m, l, d:
        int(scheduled(d, m.base_profile[l])) +
        int(scheduled(d, m.upgrade_profile[l]) and not scheduled(d, m.base_profile[l])) * m.upgraded[l, m.day_month[d]])

    m.qualification_start = pyo.Var(m.days, domain=pyo.Binary)
    valid = {d for d in m.days if d + 2 <= n and all(scheduled(u, 5) for u in range(d, d + 3))}
    m.qualification_candidates = tuple(sorted(valid))
    for d in m.days:
        if d not in valid:
            m.qualification_start[d].fix(0)
    m.one_qualification = pyo.Constraint(expr=sum(m.qualification_start[d] for d in valid) == 1)
    m.transitioned = pyo.Var(m.days, domain=pyo.Binary)
    m.transition_flow = pyo.Constraint(m.days, rule=lambda m, d:
        m.transitioned[d] == (m.transitioned[d - 1] if d > 1 else 0) + m.qualification_start[d])
    m.qualified = pyo.Expression(m.days, rule=lambda m, d: m.transitioned[d - 3] if d > 3 else 0)
    m.shutdown = pyo.Expression(m.days, rule=lambda m, d: m.transitioned[d] - m.qualified[d])
    m.daily_production = pyo.Var(m.lines, m.products, m.days, domain=pyo.NonNegativeReals)
    for d in m.days:
        m.daily_production["L1", "B", d].fix(0)
    m.daily_schedule_capacity = pyo.Constraint(m.lines, m.days, rule=lambda m, l, d:
        sum(m.daily_production[l, p, d] for p in m.products) <= m.rate[l] * m.operating[l, d])
    m.daily_shutdown_capacity = pyo.Constraint(m.lines, m.days, rule=lambda m, l, d:
        sum(m.daily_production[l, p, d] for p in m.products) <= m.rate[l] * (1 - m.shutdown[d]))
    m.no_a_after_transition = pyo.Constraint(m.lines, m.days, rule=lambda m, l, d:
        m.daily_production[l, "A", d] <= m.rate[l] * (1 - m.transitioned[d]))
    m.no_c_before_qualification = pyo.Constraint(m.lines, m.days, rule=lambda m, l, d:
        m.daily_production[l, "C", d] <= m.rate[l] * m.qualified[d])

    m.l2_configuration = pyo.Var(m.products, m.days, domain=pyo.Binary)
    m.l2_initial = pyo.Var(m.products, domain=pyo.Binary)
    m.l2_initial["C"].fix(0)
    m.initial_configuration = pyo.Constraint(expr=sum(m.l2_initial[p] for p in m.products) == 1)
    m.one_configuration = pyo.Constraint(m.days, rule=lambda m, d:
        sum(m.l2_configuration[p, d] for p in m.products) == 1)
    m.no_a_configuration = pyo.Constraint(m.days, rule=lambda m, d: m.l2_configuration["A", d] <= 1 - m.transitioned[d])
    m.no_early_c_configuration = pyo.Constraint(m.days, rule=lambda m, d: m.l2_configuration["C", d] <= m.transitioned[d])
    m.changeover = pyo.Var(m.days, domain=pyo.Binary)
    def prior(p, d):
        return m.l2_configuration[p, d - 1] if d > 1 else m.l2_initial[p]
    # Only A -> C at qualification start is exempt. B never gets a free switch.
    m.config_enter = pyo.Constraint(m.products, m.days, rule=lambda m, p, d:
        m.l2_configuration[p, d] - prior(p, d) <= m.changeover[d] + (m.qualification_start[d] if p == "C" else 0))
    m.config_leave = pyo.Constraint(m.products, m.days, rule=lambda m, p, d:
        prior(p, d) - m.l2_configuration[p, d] <= m.changeover[d] + (m.qualification_start[d] if p == "A" else 0))
    m.no_fake_changeover = pyo.Constraint(m.products, m.days, rule=lambda m, p, d:
        m.changeover[d] <= 2 - prior(p, d) - m.l2_configuration[p, d])
    m.changeover_scheduled = pyo.Constraint(m.days, rule=lambda m, d: m.changeover[d] <= m.operating["L2", d])
    m.no_double_downtime = pyo.Constraint(m.days, rule=lambda m, d: m.changeover[d] <= 1 - m.shutdown[d])
    m.monthly_changeovers = pyo.Constraint(m.months, rule=lambda m, t: sum(m.changeover[d] for d in m.month_days[t]) <= data.rules["l2_max_changeovers"])
    m.changeover_capacity = pyo.Constraint(m.days, rule=lambda m, d:
        sum(m.daily_production["L2", p, d] for p in m.products) <= m.rate["L2"] * (1 - m.changeover[d]))
    m.config_production = pyo.Constraint(m.products, m.days, rule=lambda m, p, d:
        m.daily_production["L2", p, d] <= m.rate["L2"] * m.l2_configuration[p, d])
    m.monthly_production_link = pyo.Constraint(m.lines, m.products, m.months, rule=lambda m, l, p, t:
        m.production[l, p, t] == sum(m.daily_production[l, p, d] for d in m.month_days[t]))
    m.del_component("production_limit")
    m.del_component("capacity")
    m.capacity = pyo.Expression(m.lines, m.months, rule=lambda m, l, t:
        m.rate[l] * sum(m.operating[l, d] - m.shutdown[d] - (m.changeover[d] if l == "L2" else 0) for d in m.month_days[t]))
    m.integrated_month_capacity = pyo.Constraint(m.lines, m.months, rule=lambda m, l, t:
        sum(m.production[l, p, t] for p in m.products) <= m.capacity[l, t])

    # Bound total useful purchases by full upgraded capacity, rounded to lots.
    m.total_order_bound = pyo.ConstraintList()
    stock_bound = {}
    for p in m.material_products:
        maximum = sum(m.rate[l] * m.upgrade_profile[l] * 4 * len(months)
                      for l in m.lines if p in data.lines.loc[l, "products"])
        for k in m.materials:
            lots = ceil(maximum * pyo.value(m.bom_quantity[p, k]) / pyo.value(m.lot_size[k]))
            m.total_order_bound.add(sum(m.integer_lots[p, k, t] for t in months) <= lots)
            stock_bound[p, k] = float(pyo.value(m.initial_material[p, k])) + sum(pyo.value(m.fixed_material_arrival[p, k, t]) for t in months) + lots * pyo.value(m.lot_size[k])
    m.material_stock_bound = stock_bound
    m.material_balance.deactivate()
    m.daily_material_inventory = pyo.Var(m.material_products, m.materials, m.days, domain=pyo.NonNegativeReals)
    m.a_scrap = pyo.Var(m.materials, m.days, domain=pyo.NonNegativeReals)
    m.scrap_only_at_start = pyo.Constraint(m.materials, m.days, rule=lambda m, k, d:
        m.a_scrap[k, d] <= stock_bound["A", k] * m.qualification_start[d])
    m.no_usable_a_after_transition = pyo.Constraint(m.materials, m.days, rule=lambda m, k, d:
        m.daily_material_inventory["A", k, d] <= stock_bound["A", k] * (1 - m.transitioned[d]))
    def receipts(p, k, d):
        t = m.day_month[d]
        return m.fixed_material_arrival[p, k, t] + m.additional_material_arrival[p, k, t] if m.planning_day[d] == 1 else 0
    def material_balance(m, p, k, d):
        opening = m.initial_material[p, k] if d == 1 else m.daily_material_inventory[p, k, d - 1]
        return m.daily_material_inventory[p, k, d] == opening + receipts(p, k, d) - m.bom_quantity[p, k] * sum(m.daily_production[l, p, d] for l in m.lines) - (m.a_scrap[k, d] if p == "A" else 0)
    m.daily_material_balance = pyo.Constraint(m.material_products, m.materials, m.days, rule=material_balance)
    m.material_month_end = pyo.Constraint(m.material_products, m.materials, m.months, rule=lambda m, p, k, t:
        m.material_inventory[p, k, t] == m.daily_material_inventory[p, k, m.month_days[t][-1]])
    m.no_late_a_receipts = pyo.ConstraintList()
    for t in months:
        d = m.month_days[t][0]
        if d > 1:
            for k in m.materials:
                m.no_late_a_receipts.add(m.additional_material_arrival["A", k, t] <= stock_bound["A", k] * (1 - m.transitioned[d - 1]))
    m.monthly_a_scrap = pyo.Expression(m.materials, m.months, rule=lambda m, k, t: sum(m.a_scrap[k, d] for d in m.month_days[t]))
    m.rm_scrap_value = pyo.Expression(expr=sum(m.a_scrap["RM", d] for d in m.days) * data.rules["rm_usd_per_kg"])
    m.pm_scrap_value = pyo.Expression(expr=sum(m.a_scrap["PM", d] for d in m.days) * data.rules["pm_usd_per_ea"])
    m.rm_disposal = pyo.Expression(expr=sum(m.a_scrap["RM", d] for d in m.days) / 1000 * data.rules["disposal_usd_per_ton"])
    m.pm_disposal = pyo.Expression(expr=sum(m.a_scrap["PM", d] for d in m.days) * data.rules["pm_kg_per_1000_ea"] / 1000 / 1000 * data.rules["disposal_usd_per_ton"])
    m.ide_cost = pyo.Expression(expr=m.rm_scrap_value + m.pm_scrap_value + m.rm_disposal + m.pm_disposal)
    crew = data.rules["upgrade_operators_per_line"]
    m.crew_salary = pyo.Param(initialize=crew * data.rules["operator_usd_per_month"])
    m.crew_hiring_fee = pyo.Param(initialize=crew * data.rules["hiring_usd_per_operator"])
    m.base_labor_cost = pyo.Expression(expr=len(months) * data.lines.operators.sum() * data.rules["operator_usd_per_month"])
    m.new_salary_cost = pyo.Expression(expr=crew * data.rules["operator_usd_per_month"] * sum(m.employed[l, t] for l in m.lines for t in months))
    m.hiring_cost = pyo.Expression(expr=crew * data.rules["hiring_usd_per_operator"] * sum(m.hire[l, t] for l in m.lines for t in months))
    m.labor_cost.set_value(m.base_labor_cost + m.new_salary_cost + m.hiring_cost)
    m.total_cost.set_value(m.total_cost.expr + m.ide_cost)
