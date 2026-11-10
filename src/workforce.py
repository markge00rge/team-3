"""Exact monthly additional-crew employment, qualification, dismissal and rehire."""
import pyomo.environ as pyo


def add_flexible_workforce(m,data,months):
    training = int(data.rules['training_months'])
    m.flexible_workforce_model = True
    m.employed = pyo.Var(m.lines,m.months,domain=pyo.Binary)
    m.dismiss = pyo.Var(m.lines,m.months,domain=pyo.Binary)
    m.workforce_state = pyo.ConstraintList()
    flexible = data.rules.get('flexible_workforce',True)
    for l in m.lines:
        for i,t in enumerate(months):
            previous = m.employed[l,months[i-1]] if i else 0
            h,d,e = m.hire[l,t],m.dismiss[l,t],m.employed[l,t]
            m.workforce_state.add(e==previous+h-d)
            m.workforce_state.add(h<=1-previous)
            m.workforce_state.add(d<=previous)
            m.workforce_state.add(h+d<=1)
            recent = [m.hire[l,u] for u in months[max(0,i-training+1):i+1]]
            m.workforce_state.add(m.upgraded[l,t]<=e)
            for hire in recent: m.workforce_state.add(m.upgraded[l,t]<=1-hire)
            m.workforce_state.add(m.upgraded[l,t]>=e-sum(recent))
            if not flexible: d.fix(0)
            if i+training>=len(months): h.fix(0)
    m.training = pyo.Expression(m.lines,m.months,rule=lambda m,l,t:m.employed[l,t]-m.upgraded[l,t])
