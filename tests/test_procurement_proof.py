"""Event-cap proof semantics and integer-rounded, full-service cover cuts."""
import pyomo.environ as pyo
from src.procurement_proof import check_cap, strengthen_procurement


def tiny(required):
    m=pyo.ConcreteModel()
    m.events=pyo.Var(range(3),domain=pyo.Binary,initialize=1)
    m.additional_order_events=pyo.Expression(expr=sum(m.events.values()))
    m.need=pyo.Constraint(expr=m.additional_order_events>=required)
    m.total_cost=pyo.Expression(expr=100)
    m.objective=pyo.Objective(expr=m.additional_order_events)
    return m


def test_feasible_cap_is_candidate_not_minimum_certificate(tmp_path):
    m=tiny(2)
    result=check_cap(m,2,seconds=10,log_path=tmp_path/'feasible.log',threads=0)
    assert result['has_solution'] and result['audit']['passed']
    assert result['events']==2 and result['monetary_cost']==100
    assert all(not v.fixed for v in m.events.values())


def test_one_fewer_event_proven_infeasible(tmp_path):
    result=check_cap(tiny(2),1,seconds=10,log_path=tmp_path/'infeasible.log',threads=0)
    assert result['termination']=='infeasible'
    assert not result['has_solution']


def test_timeout_is_not_an_infeasibility_certificate(tmp_path,monkeypatch):
    from types import SimpleNamespace
    fake=SimpleNamespace(options={},solve=lambda *a,**kw:SimpleNamespace(
        solver=SimpleNamespace(status='aborted',termination_condition='maxTimeLimit'),solution=[]))
    monkeypatch.setattr(pyo,'SolverFactory',lambda *a,**kw:fake)
    result=check_cap(tiny(2),1,seconds=10,log_path=tmp_path/'timeout.log')
    assert result['termination']=='maxTimeLimit'
    assert not result['has_solution']


def test_prefix_cover_rounds_cumulative_lots_without_fixing_orders():
    m=pyo.ConcreteModel()
    m.months=pyo.Set(initialize=['2026-10','2026-11','2026-12','2027-01'],ordered=True)
    m.hubs=pyo.Set(initialize=['H1'])
    m.materials=pyo.Set(initialize=['RM','PM'])
    m.demand=pyo.Param(m.hubs,['B'],m.months,initialize=100)
    m.initial_fp=pyo.Param(['B'],initialize=15)
    m.bom_quantity=pyo.Param(['B'],m.materials,initialize={('B','RM'):600,('B','PM'):2000})
    m.initial_material=pyo.Param(['B'],m.materials,initialize={('B','RM'):200000,('B','PM'):750000})
    m.fixed_material_arrival=pyo.Param(['B'],m.materials,m.months,initialize=0)
    m.lot_size=pyo.Param(m.materials,initialize={'RM':50000,'PM':125000})
    m.order_arrival_month={t:('2027-01' if t=='2026-10' else '2028-01') for t in m.months}
    m.integer_lots=pyo.Var(['B'],m.materials,m.months,domain=pyo.NonNegativeIntegers,initialize=0)
    assert strengthen_procurement(m)==2
    assert pyo.value(m.proof_b_cover[1].lower)==1  # (385*600-200000)/50000 -> 1
    assert pyo.value(m.proof_b_cover[2].lower)==1  # (385*2000-750000)/125000 -> 1
    assert not any(v.fixed for v in m.integer_lots.values())
    assert strengthen_procurement(m)==0
