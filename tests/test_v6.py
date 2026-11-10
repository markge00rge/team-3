"""Exact known-outcome employment schedules and independently valued materials."""
from copy import deepcopy
import pyomo.environ as pyo
import pytest
from src.data_loader import load_case
from src.model import build_model
from src.workforce import add_flexible_workforce
from app.scenarios import original_scenario as current_scenario
from app.components.financial_cards import compact_currency,card_html


def workforce(months=6,flexible=True,training=1):
    data=load_case(); data.rules.update(flexible_workforce=flexible,training_months=training)
    m=pyo.ConcreteModel(); m.lines=pyo.Set(initialize=['L2']); m.months=pyo.RangeSet(1,months)
    m.hire=pyo.Var(m.lines,m.months,domain=pyo.Binary)
    m.upgraded=pyo.Var(m.lines,m.months,domain=pyo.Binary)
    add_flexible_workforce(m,data,list(m.months))
    m.objective=pyo.Objective(expr=sum(10000*m.employed['L2',t]+5000*m.hire['L2',t] for t in m.months))
    return m


def solve(m):
    r=pyo.SolverFactory('appsi_highs').solve(m)
    assert str(r.solver.termination_condition)=='optimal'
    return pyo.value(m.objective)


def test_temporary_crew_cheaper_than_permanent_and_base_returns():
    temporary=workforce(months=4); temporary.upgraded['L2',2].fix(1)
    permanent=workforce(months=4,flexible=False); permanent.upgraded['L2',2].fix(1)
    assert solve(temporary)==25000
    assert solve(permanent)==45000
    assert pyo.value(temporary.hire['L2',1])==1
    assert pyo.value(temporary.training['L2',1])==1
    assert pyo.value(temporary.employed['L2',1])==1
    assert pyo.value(temporary.dismiss['L2',3])==1
    assert pyo.value(temporary.employed['L2',3])==pyo.value(temporary.upgraded['L2',3])==0


def test_rehire_repeats_fee_and_training():
    m=workforce(); m.upgraded['L2',2].fix(1); m.upgraded['L2',5].fix(1)
    assert solve(m)==50000
    assert [pyo.value(m.hire['L2',t]) for t in m.months]==[1,0,0,1,0,0]
    assert pyo.value(m.training['L2',4])==1
    assert pyo.value(m.upgraded['L2',4])==0
    for t in m.months:
        assert pyo.value(m.hire['L2',t]+m.dismiss['L2',t])<=1
        assert pyo.value(m.upgraded['L2',t])<=pyo.value(m.employed['L2',t])


def test_two_full_months_of_retraining():
    m=workforce(months=7,training=2)
    m.hire['L2',1].fix(1); m.dismiss['L2',4].fix(1); m.hire['L2',5].fix(1)
    m.upgraded['L2',3].fix(1); m.upgraded['L2',7].fix(1)
    solve(m)
    for t in [1,2,5,6]: assert pyo.value(m.training['L2',t])==1 and pyo.value(m.upgraded['L2',t])==0
    assert pyo.value(m.upgraded['L2',3])==pyo.value(m.upgraded['L2',7])==1


@pytest.fixture(scope='module')
def model():
    data=load_case();data.rules['explicit_b_materials']=False
    return build_model(data)


def original_scenario():
    return current_scenario(schema_version=2)


def zero(m,name):
    for v in getattr(m,name).values(): v.set_value(0,skip_validation=True)


def test_b_cost_production_only_default_150_msu(model):
    m=model; zero(m,'production'); zero(m,'material_order')
    m.production['L2','B','2027-06'].set_value(150)
    assert pyo.value(m.b_material_cost)==570000
    m.production['L2','B','2027-06'].set_value(0)
    m.shipment['B','H1','2026-10'].set_value(15)
    assert pyo.value(m.b_material_cost)==0
    assert set(m.material_products)=={'A','C'}


@pytest.mark.parametrize('p,k,quantity,expected',[('A','RM',50000,250000),('A','PM',125000,50000),('C','RM',50000,250000),('C','PM',125000,50000)])
def test_additional_orders_cost_not_opening_or_fixed_receipts(model,p,k,quantity,expected):
    m=model; zero(m,'material_order')
    assert pyo.value(m.a_material_cost+m.c_material_cost)==0
    m.material_order[p,k,'2026-10'].set_value(quantity)
    assert pyo.value(m.a_material_cost if p=='A' else m.c_material_cost)==expected


@pytest.mark.parametrize('p,k',[('A','RM'),('A','PM'),('B','RM'),('B','PM'),('C','RM'),('C','PM')])
def test_each_product_price_maps_to_real_objective(p,k):
    s=original_scenario(); s.values[f'price.{p}.{k}']=7
    m=build_model(s.to_case())
    assert pyo.value(m.material_unit_price[p,k])==7
    zero(m,'material_order'); zero(m,'production')
    if p=='B':
        m.production['L2','B','2026-10'].set_value(1)
        other='PM' if k=='RM' else 'RM'
        assert pyo.value(m.b_material_cost)==7*pyo.value(m.bom_quantity[p,k])+pyo.value(m.material_unit_price[p,other]*m.bom_quantity[p,other])
    else:
        m.material_order[p,k,'2026-10'].set_value(100)
        assert pyo.value(m.a_material_cost if p=='A' else m.c_material_cost)==700


@pytest.mark.parametrize('scrap,purchases,overlap',[(20,0,0),(20,10,10),(5,10,5),(10,10,10)])
def test_exact_new_a_scrap_min_linearization(model,scrap,purchases,overlap):
    m=model.clone(); m.objective.set_value(m.ide_overlap)
    # Isolate provenance constraints to test exact equality regardless of objective.
    for c in list(m.component_objects(pyo.Constraint,active=True)):
        if c.name!='scrap_provenance': c.deactivate()
    for v in m.a_scrap.values(): v.fix(0)
    m.a_scrap['RM',1].fix(scrap)
    for v in m.material_order.values(): v.fix(0)
    m.material_order['A','RM','2026-10'].fix(purchases)
    for sign in (1,-1):
        m.objective.set_value(sign*m.a_new_scrap['RM'])
        r=pyo.SolverFactory('appsi_highs').solve(m)
        assert str(r.solver.termination_condition)=='optimal'
        assert pyo.value(m.a_new_scrap['RM'])==pytest.approx(overlap)
    assert pyo.value(m.ide_overlap)==pytest.approx(overlap*5)


def test_responsive_financial_cards_exact_values():
    costs=dict(operating_expenses=1.234567890123e9,a_materials=0,c_materials=12e6,b_materials=950000,total_delivery_cost=1.247517890123e9)
    html=card_html(costs)
    assert html.count('data-finance-key=')==5
    assert '1247517890.123' in html and 'TOTAL DELIVERY COST' in html
    assert len(compact_currency(1.234567890123e15))<16
    assert compact_currency(1220000)=='$1.22M'

def test_saved_real_v6_five_kpis_independently_reconcile():
    from pathlib import Path
    import math
    from src.reconciliation import read_saved, calculate
    directory=Path('reports/v6')
    tables,status=read_saved(directory)
    financial=calculate(load_case(),tables,status)
    annual=financial.costs.iloc[-1]
    keys=['operating_expenses_usd','a_material_cost_usd','c_material_cost_usd','b_material_cost_usd']
    assert math.fsum(annual[k] for k in keys)==pytest.approx(status['minimum_cost'],abs=.01)
    assert annual['total_delivery_cost_usd']==pytest.approx(status['costs']['total_delivery_cost'],abs=.01)
    assert annual['b_material_cost_usd']==pytest.approx(tables['production'].query("product == 'B'").msu.sum()*3800,abs=.01)
    assert status['stages'][3]['termination']=='optimal'
    assert tables['service'].unserved_msu.sum()==pytest.approx(0,abs=1e-5)


def test_integrated_new_a_scrap_overlap_and_order_month_reporting(tmp_path):
    from test_v4 import diagnostic
    from src.solve import solve_lexicographic
    from src.results import extract_results,write_results
    from src.reconciliation import read_saved,calculate
    from src.validation import audit_solution
    data=load_case()
    data.rules['explicit_b_materials']=False  # historical V6 accounting contract
    data.initial_materials.quantity=0
    data.arrivals.quantity=0
    data.demand.msu=0
    data.initial_fp={p:0 for p in data.products}
    m=diagnostic(data,start=113)  # February day 1; October orders arrive January.
    m.material_order['A','RM','2026-10'].fix(50000)
    m.material_order['A','PM','2026-10'].fix(125000)
    outcome=solve_lexicographic(m,time_limit=30)
    assert outcome.success,outcome.message
    result=extract_results(m)
    assert result.costs['a_materials']==pytest.approx(300000)
    assert result.costs['ide']==pytest.approx(310500)
    assert result.costs['ide_overlap_adjustment']==pytest.approx(300000)
    assert result.costs['operating_expenses']==pytest.approx(850500)
    assert result.costs['total_delivery_cost']==pytest.approx(1150500)
    assert audit_solution(m)['passed']
    write_results(result,outcome,tmp_path)
    tables,status=read_saved(tmp_path)
    costs=calculate(data,tables,status).costs.set_index('month')
    assert costs.loc['2026-10','a_material_cost_usd']==pytest.approx(300000)
    assert costs.loc['2027-01','a_material_cost_usd']==0
    assert costs.loc['2027-02','ide_overlap_adjustment_usd']==pytest.approx(300000)


def test_workforce_ui_parameters_reach_financial_expressions():
    s=original_scenario()
    for k,v in [('upgrade_operators_per_line',12),('operator_usd_per_month',1200),('hiring_usd_per_operator',600),('dismissal_usd_per_operator',200),('training_months',2)]:
        s.values['rule.'+k]=v
    m=build_model(s.to_case())
    for name in ('hire','dismiss','employed','upgraded'): zero(m,name)
    m.hire['L2','2026-10'].set_value(1)
    for t in ('2026-10','2026-11','2026-12'): m.employed['L2',t].set_value(1)
    m.upgraded['L2','2026-12'].set_value(1)
    m.dismiss['L2','2027-01'].set_value(1)
    assert pyo.value(m.labor_cost)==pytest.approx(70*1200*12+12*1200*3+12*600+12*200)


def test_schema_boolean_version_rejected():
    import json
    obj=json.loads(original_scenario().to_json());obj['schema_version']=True
    from app.scenarios import Scenario
    with pytest.raises(ValueError): Scenario.from_json(json.dumps(obj))
