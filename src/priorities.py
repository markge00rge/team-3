"""Exact monthly allocation priorities, independently for each demand family."""
import pyomo.environ as pyo


def add_monthly_priorities(m):
    hubs = tuple(m.priority_hubs)
    # All pairs are needed: adjacent pairs alone fail when intermediate demand is zero.
    m.priority_pairs = pyo.Set(dimen=2, initialize=[(a, b)
        for i, a in enumerate(hubs) for b in hubs[i + 1:]])
    m.priority_release = pyo.Var(m.priority_pairs, m.families, m.months, domain=pyo.Binary)
    m.priority_higher_served = pyo.Constraint(m.priority_pairs, m.families, m.months,
        rule=lambda m, a, b, f, t: m.unserved[a, f, t] <=
            m.demand[a, f, t] * (1 - m.priority_release[a, b, f, t]))
    m.priority_lower_shipments = pyo.Constraint(m.priority_pairs, m.families, m.months,
        rule=lambda m, a, b, f, t: sum(m.shipment[p, b, t] for p in m.family_members[f])
            <= m.demand[b, f, t] * m.priority_release[a, b, f, t])
