"""V7 explicit B procurement: known-outcome MILPs and independent accounting."""
from copy import deepcopy
import json
from pathlib import Path
import pandas as pd
import pyomo.environ as pyo
import pytest
from app.scenarios import original_scenario,Scenario
from src.data_loader import load_case,ROOT
from src.material_policy import planning_case
from src.model import build_model
from src.results import extract_results,write_results
from src.solve import solve_lexicographic
from src.reconciliation import calculate,read_saved
from src.validation import audit_solution


@pytest.fixture(scope='module')
def model(): return build_model(original_scenario().to_case())


def zero(m,name):
    for v in getattr(m,name).values(): v.set_value(0,skip_validation=True)


def test_default_stock_assumptions_and_unchanged_sources(model):
    source=load_case();case=original_scenario().to_case()
    assert original_scenario().schema_version==3
    assert set(model.material_products)=={'A','B','C'}
    assert pyo.value(model.initial_material['B','RM'])==200000
    assert pyo.value(model.initial_material['B','PM'])==750000
    assert pyo.value(model.initial_fp['B'])==15
    assert pyo.value(model.initial_material['A','RM'])==115000
    assert pyo.value(model.initial_material['A','PM'])==400000
    assert set(source.initial_materials['product'])=={'A','C'}
    pd.testing.assert_frame_equal(source.arrivals,case.arrivals)
    assert 'not numerical stocks' in case.rules['b_opening_stock_provenance']


@pytest.mark.parametrize('material,quantity',[('RM',0),('RM',123456),('PM',0),('PM',987654)])
def test_custom_b_opening_stock_reaches_real_inventory_parameter(material,quantity):
    s=original_scenario();s.values[f'stock.B.{material}']=quantity
    m=build_model(s.to_case())
    assert pyo.value(m.initial_material['B',material])==quantity
    assert Scenario.from_json(s.to_json())==s


@pytest.mark.parametrize('quantity',[-1,float('nan'),float('inf'),True])
@pytest.mark.parametrize('material',['RM','PM'])
def test_invalid_b_inventory_rejected(material,quantity):
    s=original_scenario();s.values[f'stock.B.{material}']=quantity
    with pytest.raises(ValueError):s.to_case()


def test_b_bom_edits_and_line_eligibility():
    s=original_scenario();s.values['bom.B.rm_kg_per_msu']=650;s.values['bom.B.pm_ea_per_msu']=2100
    m=build_model(s.to_case());zero(m,'production')
    m.production['L2','B','2026-10'].set_value(2)
    assert pyo.value(m.material_consumption['B','RM','2026-10'])==1300
    assert pyo.value(m.material_consumption['B','PM','2026-10'])==4200
    assert m.production['L1','B','2026-10'].fixed


def test_b_purchase_cost_not_production_or_opening_stock(model):
    m=model;zero(m,'material_order');zero(m,'production')
    assert pyo.value(m.b_material_cost)==0
    m.production['L2','B','2027-06'].set_value(150)
    assert pyo.value(m.material_consumption['B','RM','2027-06'])==90000
    assert pyo.value(m.material_consumption['B','PM','2027-06'])==300000
    assert pyo.value(m.b_material_cost)==0  # no former $570,000 consumption expense
    m.material_order['B','RM','2026-10'].set_value(50000)
    assert pyo.value(m.b_material_cost)==250000
    m.material_order['B','PM','2026-10'].set_value(125000)
    assert pyo.value(m.b_material_cost)==300000
    m.material_order['B','RM','2026-10'].set_value(0)
    assert pyo.value(m.b_material_cost)==50000


def test_b_price_changes_actual_total_objective_coefficients():
    from pyomo.repn import generate_standard_repn
    s=original_scenario();s.values['price.B.RM']=7;s.values['price.B.PM']=.6
    m=build_model(s.to_case());rep=generate_standard_repn(m.total_cost)
    coefficients={v.name:float(c) for v,c in zip(rep.linear_vars,rep.linear_coefs)}
    assert coefficients[m.material_order['B','RM','2026-10'].name]==7
    assert coefficients[m.material_order['B','PM','2026-10'].name]==.6
    assert m.production['L2','B','2026-10'].name not in coefficients


def test_lots_events_lead_time_and_no_fixed_b_receipts(model):
    m=model
    assert pyo.value(m.lot_size['RM'])==50000
    assert pyo.value(m.lot_size['PM'])==125000
    assert m.order_arrival_month['2026-10']=='2027-01'
    assert m.order_arrival_month['2026-11']=='2027-02'
    assert all(pyo.value(m.fixed_material_arrival['B',k,t])==0 for k in m.materials for t in m.months)
    assert m.material_order['B','RM','2027-07'].fixed
    assert m.integer_lots['B','PM','2026-10'].is_integer()
    for k in m.materials:
        assert pyo.value(m.additional_material_arrival['B',k,'2026-12'])==0
    zero(m,'order_event');m.order_event['B','RM','2026-10'].set_value(1)
    assert pyo.value(m.additional_order_events)==1
    zero(m,'material_order');m.material_order['B','RM','2026-10'].set_value(50000)
    assert pyo.value(m.procurement_tiebreak)==pytest.approx(50000/600)


def test_warehouse_b_footprint_no_double_fp_or_material_holding(model):
    m=model;zero(m,'inventory');zero(m,'material_inventory');zero(m,'external_blocks')
    initial_rm=pyo.value(m.initial_material['B','RM'])/1000
    initial_pm=pyo.value(m.initial_material['B','PM'])/5000
    initial_fp=pyo.value(m.initial_fp['B'])*4
    assert (initial_rm,initial_pm,initial_fp)==(200,150,60)
    assert initial_rm+initial_pm==350
    assert initial_rm+initial_pm+initial_fp==410
    m.material_inventory['B','RM','2026-10'].set_value(200000)
    m.material_inventory['B','PM','2026-10'].set_value(750000)
    m.inventory['B','2026-10'].set_value(15)
    assert pyo.value(m.tracked_pallets['2026-10'])==410
    assert pyo.value(m.holding_cost)==pytest.approx(15*5500*.015)
    m.material_inventory['B','RM','2026-10'].set_value(400000)
    assert pyo.value(m.tracked_pallets['2026-10'])==610
    assert pyo.value(m.holding_cost)==pytest.approx(15*82.5)


def synthetic_case(rm=600,pm=2000,*,demand=1):
    """Four-month diagnostic; no source file changes or assumed case values."""
    data=planning_case(load_case())
    data.months=data.months[:4]
    data.demand=data.demand[data.demand.month.isin(data.months)].copy();data.demand.msu=0.
    data.demand.loc[(data.demand.hub=='H1')&(data.demand.family=='B'),'msu']=float(demand)
    data.initial_fp={p:0 for p in data.products}
    data.initial_materials.quantity=0.
    for k,q in [('RM',rm),('PM',pm)]:
        data.initial_materials.loc[(data.initial_materials['product']=='B')&(data.initial_materials.material==k),'quantity']=q
    data.arrivals.quantity=0.
    from test_v4 import diagnostic
    m=diagnostic(data,start=1)
    if demand:
        for day in m.days:m.daily_production['L2','B',day].unfix()
        for k in m.materials:m.material_order['B',k,data.months[0]].unfix()
    return data,m


@pytest.fixture(scope='module')
def low_stock_result():
    data,m=synthetic_case()
    outcome=solve_lexicographic(m,time_limit=30)
    assert outcome.success,outcome.message
    result=extract_results(m)
    assert audit_solution(m)['passed']
    return data,m,result,outcome


def test_low_stocks_block_b_until_january_and_no_substitution(low_stock_result):
    data,m,result,outcome=low_stock_result
    pre=result.service.query("month < '2027-01' and family == 'B'")
    assert pre.served_msu.sum()==pytest.approx(1)
    assert pre.unserved_msu.sum()==pytest.approx(2)
    assert result.service.query("month == '2027-01'").unserved_msu.sum()==pytest.approx(0)
    assert result.material_balances.ending.min()>=-1e-5
    assert result.material_orders.query("product == 'B'").order_event.sum()==2
    assert result.costs['b_materials']==pytest.approx(300000)
    assert result.material_balances.query("product == 'B'").scrap.sum()==0
    shutdown=result.daily_material.query("product == 'B' and horizon_day <= 3")
    assert shutdown.query("material == 'RM'").ending.tolist()==[600]*3
    assert shutdown.query("material == 'PM'").ending.tolist()==[2000]*3
    for r in result.material_balances.itertuples():
        assert r.ending==pytest.approx(r.opening+r.fixed_arrival+r.additional_arrival-r.consumption-r.scrap,abs=1e-5)
        if r.product=='B':
            made=result.production.query("product == 'B' and month == @r.month").msu.sum()
            assert r.consumption==pytest.approx(made*(600 if r.material=='RM' else 2000))
            if r.month<'2027-01':assert r.additional_arrival==0
    # A/C material supplies cannot replace missing B material stocks.
    _,blocked=synthetic_case(rm=0,pm=0)
    blocked.initial_material['C','RM']=10000;blocked.initial_material['C','PM']=10000
    stopped=solve_lexicographic(blocked,time_limit=30)
    assert stopped.success
    assert extract_results(blocked).production.query("product == 'B' and month < '2027-01'").msu.sum()==0


def test_more_opening_b_materials_eliminate_early_shortage():
    _,m=synthetic_case(rm=1800,pm=6000)
    outcome=solve_lexicographic(m,time_limit=30);assert outcome.success
    r=extract_results(m)
    assert r.service.query("month < '2027-01'").unserved_msu.sum()==pytest.approx(0)


def test_b_orders_and_scrap_reconcile_monthly_financials(low_stock_result,tmp_path):
    data,m,result,outcome=low_stock_result
    write_results(result,outcome,tmp_path)
    tables,status=read_saved(tmp_path)
    financial=calculate(data,tables,status)
    costs=financial.costs.set_index('month')
    assert costs.loc['2026-10','b_rm_order_usd']==pytest.approx(250000)
    assert costs.loc['2026-10','b_pm_order_usd']==pytest.approx(50000)
    assert costs.loc['2027-01','b_material_cost_usd']==0
    assert 'b_rm_consumption_usd' not in costs
    assert costs.loc['ANNUAL','b_material_cost_usd']==pytest.approx(result.costs['b_materials'])
    assert financial.costs.iloc[:-1].total_delivery_cost_usd.sum()==pytest.approx(result.costs['total_delivery_cost'])
    assert sum(result.costs[k] for k in ('operating_expenses','a_materials','b_materials','c_materials'))==pytest.approx(result.costs['total_delivery_cost'])


def test_b_stock_can_force_optimized_external_storage():
    data,m=synthetic_case(rm=2500000,pm=0,demand=0)
    outcome=solve_lexicographic(m,time_limit=30);assert outcome.success
    r=extract_results(m)
    assert r.warehouse.external_blocks.tolist()==[13]*4
    assert r.costs['external_storage']==pytest.approx(13*4500*4)
    assert r.costs['b_materials']==0  # opening stock is not a purchase
    assert (r.warehouse.b_fp_pallets==0).all()
    assert (r.warehouse.b_rm_pallets==2500).all()
    assert r.costs['fp_holding']==0


def test_legacy_v6_inputs_remain_reproducible_not_silently_converted():
    old=original_scenario(schema_version=2)
    restored=Scenario.from_json(old.to_json())
    assert restored.schema_version==2
    assert set(build_model(restored.to_case()).material_products)=={'A','C'}
    upgraded=restored.upgrade()
    assert upgraded.schema_version==3 and upgraded.values['stock.B.RM']==200000
    assert 'stock.B.RM' not in old.values
