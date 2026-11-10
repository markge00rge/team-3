"""Input allowlist, real model expressions, UI state and Streamlit smoke tests."""
from copy import deepcopy
from io import BytesIO
import json
import math
import pandas as pd
import pyomo.environ as pyo
import pytest
from app.scenarios import original_scenario,Scenario,apply_demand,demand_frame,RULE_FIELDS
from app.state import initialize,navigate,reset,load_scenario
from src.data_loader import load_case,ROOT
from src.model import build_model


@pytest.fixture(scope="module")
def source(): return load_case()


def test_original_defaults_and_json_round_trip(source):
    s=original_scenario(source)
    case=s.to_case(source)
    assert s.changes(source).empty
    assert case.demand.msu.sum()==3095
    pd.testing.assert_frame_equal(case.bom,source.bom)
    pd.testing.assert_frame_equal(case.arrivals,source.arrivals)
    assert Scenario.from_json(s.to_json())==s


def test_original_adapter_preserves_every_mathematical_constraint(source):
    from pyomo.repn import generate_standard_repn
    def signature(model):
        rows=[]
        for con in model.component_data_objects(pyo.Constraint,active=True):
            r=generate_standard_repn(con.body)
            assert r.is_linear()
            terms=tuple(sorted((v.name,float(c)) for v,c in zip(r.linear_vars,r.linear_coefs)))
            rows.append((con.name,terms,float(r.constant),
                pyo.value(con.lower) if con.lower is not None else None,
                pyo.value(con.upper) if con.upper is not None else None))
        variables=[(v.name,v.is_integer(),v.fixed,pyo.value(v.lb) if v.lb is not None else None,
            pyo.value(v.ub) if v.ub is not None else None,v.value if v.fixed else None)
            for v in model.component_data_objects(pyo.Var)]
        return rows,variables
    assert signature(build_model(source))==signature(build_model(original_scenario(source).to_case(source)))


def test_navigation_and_resets_preserve_durable_edits(source):
    state={}; initialize(state,source)
    state["scenario"].values["rate.L1"]=9
    for page in [4,6,1,0,5]:
        navigate(state,page)
        assert state["scenario"].values["rate.L1"]==9
    reset(state,source,"rate.L1")
    assert state["scenario"].values["rate.L1"]==6
    state["scenario"].values["rule.warehouse_pallets"]=100
    reset(state,source)
    assert state["scenario"]==original_scenario(source)


@pytest.mark.parametrize("field",["products","training_months","lines","family.A","rule.cost_tolerance","new_hub"])
def test_structural_or_unsupported_edits_rejected(source,field):
    s=original_scenario(source); s.values[field]=2
    with pytest.raises(ValueError,match="structural"): s.to_case(source)


@pytest.mark.parametrize("value",[-1,float('nan'),float('inf'),True,"20",None])
def test_invalid_numerical_inputs_rejected(source,value):
    s=original_scenario(source); s.values["demand.H1.AC.2027-06"]=value
    with pytest.raises(ValueError): s.validate(source)


@pytest.mark.parametrize("key",list(RULE_FIELDS))
def test_every_allowed_rule_maps_to_source_parameter(source,key):
    s=original_scenario(source)
    s.values["rule."+key]+=1
    case=s.to_case(source)
    assert case.rules[key]==source.rules.get(key,0)+1
    assert source.rules.get(key,0)==original_scenario(source).values["rule."+key]


def test_all_nonrule_fields_map_and_original_is_unchanged(source):
    s=original_scenario(source)
    for key in s.values:
        if key.startswith("rule."): continue
        if key.startswith("upgrade.") or key=='flexible_workforce': s.values[key]=False
        elif key=="qualification_month": s.values[key]="2027-02"
        else: s.values[key]+=1
    c=s.to_case(source)
    for l in c.lines.index:
        assert c.lines.loc[l,"msu_per_day"]==source.lines.loc[l,"msu_per_day"]+1
        assert not c.rules["upgrade_permissions"][l]
    assert c.rules["qualification_allowed_months"]==["2027-02"]
    assert c.initial_fp["A"]==11
    from src.material_policy import planning_case
    expected=planning_case(source)
    assert (c.initial_materials.quantity==expected.initial_materials.quantity+1).all()
    assert (c.arrivals.quantity==source.arrivals.quantity+1).all()
    assert (c.bom.fp_usd_per_msu==source.bom.fp_usd_per_msu+1).all()
    for p in ("A","C"):
        for col in ("rm_kg_per_msu","pm_ea_per_msu"):
            assert c.bom.loc[p,col]==source.bom.loc[p,col]+1
    assert (c.hubs.truck_usd==source.hubs.truck_usd+1).all()
    assert (c.hubs.unserved_usd_per_msu==source.hubs.unserved_usd_per_msu+1).all()
    assert all(c.initial_fp[p]==source.initial_fp[p]+1 for p in source.products)
    assert c.demand.msu.sum()==3095+72
    assert source.initial_fp["A"]==10 and source.demand.msu.sum()==3095


def changed_model(source,changes):
    s=original_scenario(source); s.values.update(changes)
    return build_model(s.to_case(source))


def test_capacity_demand_and_qualification_change_actual_constraints(source):
    m=changed_model(source,{"rate.L1":9,"upgrade.L1":False,"qualification_month":"2027-02","demand.H1.AC.2027-06":115})
    assert m.rate["L1"]==9
    assert pyo.value(m.demand["H1","AC","2027-06"])==115
    assert all(m.day_month[d]=="2027-02" for d in m.qualification_candidates)
    assert all(m.hire["L1",t].fixed and m.hire["L1",t].value==0 for t in m.months)
    m.daily_production["L1","C",1].set_value(9)
    for p in ("A","B"): m.daily_production["L1",p,1].set_value(0)
    assert pyo.value(m.daily_production["L1","C",1].ub)==9
    # Procurement bounds are rebuilt from changed eligible upgraded capacities.
    base=build_model(source)
    assert pyo.value(m.max_order_lots["C","RM","2026-10"])>pyo.value(base.max_order_lots["C","RM","2026-10"])


def test_financial_controls_reach_actual_objective_expressions(source):
    m=changed_model(source,{"rule.fp_holding_fraction_month":.02,"bom.C.fp_usd_per_msu":4500,
        "rule.operator_usd_per_month":1100,"rule.hiring_usd_per_operator":700,
        "rule.overflow_usd_per_pallet_month":55,"rule.overflow_block_pallets":50,
        "rule.warehouse_pallets":900,"rule.truck_msu":4,"rule.dedicated_trucks_month":60,
        "rule.spot_surcharge_fraction":.8,"hub.H1.truck_usd":350,"hub.H1.unserved_usd_per_msu":4000})
    for var in m.inventory.values(): var.set_value(0)
    m.inventory["C","2026-10"].set_value(2)
    assert pyo.value(m.holding_cost)==180
    assert pyo.value(m.base_labor_cost)==924000
    for var in m.hire.values(): var.set_value(0)
    m.hire["L1","2026-10"].set_value(1)
    if hasattr(m,'dismiss'):
        for l,t in m.employed: m.employed[l,t].set_value(int(l=='L1'))
    assert pyo.value(m.new_salary_cost)==132000
    assert pyo.value(m.hiring_cost)==7000
    assert pyo.value(m.onsite_capacity)==900
    assert pyo.value(m.truck_msu)==4 and pyo.value(m.fleet_limit)==60
    for var in m.external_blocks.values(): var.set_value(0)
    m.external_blocks["2026-10"].set_value(1)
    assert pyo.value(m.external_storage_cost)==2750
    for var in list(m.dedicated.values())+list(m.spot.values()): var.set_value(0)
    m.spot["H1","2026-10"].set_value(1)
    assert pyo.value(m.transport_cost)==pytest.approx(630)
    for var in m.unserved.values(): var.set_value(0)
    m.unserved["H1","AC","2026-10"].set_value(2)
    assert pyo.value(m.service_penalty)==8000


def test_material_edits_reach_lots_receipts_bom_and_ide(source):
    m=changed_model(source,{"rule.rm_moq_kg":25000,"rule.pm_moq_ea":100000,"rule.sea_lead_months":2,
        "stock.A.RM":100000,"receipt.0":200000,"bom.A.rm_kg_per_msu":400,
        "price.A.RM":6,"price.A.PM":.5,"rule.disposal_usd_per_ton":300,
        "rule.pm_kg_per_1000_ea":30,"rule.rm_kg_per_pallet":2000,"rule.pm_ea_per_pallet":10000})
    assert pyo.value(m.lot_size["RM"])==25000 and pyo.value(m.lot_size["PM"])==100000
    assert m.order_arrival_month["2026-10"]=="2026-12"
    assert pyo.value(m.initial_material["A","RM"])==100000
    assert pyo.value(m.fixed_material_arrival["A","PM","2026-10"])==200000
    assert pyo.value(m.bom_quantity["A","RM"])==400
    for var in m.a_scrap.values(): var.set_value(0)
    m.a_scrap["RM",1].set_value(1000); m.a_scrap["PM",1].set_value(1000)
    assert pyo.value(m.ide_cost)==pytest.approx(6000+300+500+9)
    for var in m.material_inventory.values(): var.set_value(0)
    m.material_inventory["C","RM","2026-10"].set_value(2000)
    m.material_inventory["C","PM","2026-10"].set_value(10000)
    assert pyo.value(m.rm_pallets["2026-10"])==1
    assert pyo.value(m.pm_pallets["2026-10"])==1
    m.integer_lots["C","RM","2026-10"].set_value(2)
    m.material_order["C","RM","2026-10"].set_value(50000)
    assert pyo.value(m.order_lot_link["C","RM","2026-10"].body)==0


def test_edited_material_footprints_reach_conservative_peak_export(source):
    from app.optimizer_adapter import read_run
    from src.results import extract_results
    from src.validation import audit_exported_schedule
    # Independent receipt-day arithmetic: October has 25 FP, 115,000 kg A RM,
    # 650,000 EA A PM and 375,000 EA C PM before any manufacturing.
    s=original_scenario(source)
    s.values.update({"rule.rm_kg_per_pallet":2000,"rule.pm_ea_per_pallet":10000})
    m=build_model(s.to_case(source))
    assert m.inventory_pallet_factors==dict(FP=4,RM=1/2000,PM=1/10000)
    expected=25*4+115000/2000+(650000+375000)/10000
    assert expected==260
    # Exercise the actual extraction against the saved V5 schedule. Load exact
    # levels using a capture of the existing exported-schedule reconstruction.
    from unittest.mock import patch
    import src.validation as validation
    captured=[]
    original=validation.audit_solution
    def capture(model,*args,**kwargs):
        captured.append(model)
        return original(model,*args,**kwargs)
    with patch.object(validation,"audit_solution",capture):
        audit_exported_schedule(source,ROOT/"reports/v5")
    restored=captured[0]
    restored.inventory_pallet_factors=m.inventory_pallet_factors
    restored._solve_success=True
    exported=extract_results(restored)
    first=exported.storage_peaks.iloc[0]
    # The peak is max(before receipt-day production, after production), so both
    # sides use the edited conversion; calculate from independently exported rows.
    rows=exported.daily_material.query("horizon_day == 1")
    made=exported.daily_schedule.query("horizon_day == 1")[["production_a","production_b","production_c"]].sum().sum()
    after=(25+made)*4+sum(r.ending*(1/2000 if r.material=="RM" else 1/10000) for r in rows.itertuples())
    assert first.tracked_pallets==pytest.approx(max(expected,after))


def test_demand_csv_exact_grid_and_no_double_counting(source):
    s=original_scenario(source); frame=demand_frame(s,source)
    frame.loc[(frame.month=="2027-06") & (frame.hub=="H1") & (frame.family=="AC"),"msu"]+=10
    edited=apply_demand(s,frame,source)
    assert edited.to_case(source).demand.msu.sum()==3105
    assert s.to_case(source).demand.msu.sum()==3095
    for bad in [frame.iloc[:-1],pd.concat([frame,frame.iloc[:1]]),frame.assign(family="A")]:
        with pytest.raises(ValueError): apply_demand(s,bad,source)


def button(at,label): return next(b for b in at.button if b.label==label)


def test_streamlit_home_venus_future_and_prefilled_navigation():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(ROOT/"app/main.py"),default_timeout=25).run()
    assert not at.exception
    button(at,"Explore what’s coming →").click().run()
    assert not at.exception and any("under development" in x.value for x in at.info)
    button(at,"Back to Venus").click().run()
    assert any(b.label=="Run Original Case" for b in at.button)
    button(at,"Customize Parameters").click().run()
    assert not at.exception
    next(x for x in at.selectbox if x.key=="section_navigation").select_index(1).run()
    field=next(x for x in at.number_input if x.label.startswith("Daily output") and "L1" in x.label)
    field.set_value(7.0).run()
    assert at.session_state.scenario.values["rate.L1"]==7
    next(x for x in at.selectbox if x.key=="section_navigation").select_index(4).run()
    next(x for x in at.selectbox if x.key=="section_navigation").select_index(1).run()
    assert next(x for x in at.number_input if x.label.startswith("Daily output") and "L1" in x.label).value==7
    button(at,"Reset entire scenario").click().run()
    assert at.session_state.scenario.values["rate.L1"]==6
    assert not at.exception


def test_original_entry_runs_fresh_defaults_without_questionnaire(monkeypatch,tmp_path):
    from streamlit.testing.v1 import AppTest
    captured=[]
    class Process:
        def poll(self): return None
    def start(scenario,time_limit,**kwargs):
        captured.append(scenario)
        return dict(process=Process(),directory=str(tmp_path),name=scenario.name)
    monkeypatch.setattr("app.jobs.start_job",start)
    at=AppTest.from_file(str(ROOT/"app/main.py"),default_timeout=25).run()
    at.session_state.scenario.values["rate.L1"]=99
    button(at,"Open Venus Case Study →").click().run()
    button(at,"Run Original Case").click().run()
    assert at.session_state.screen=='name_original' and not captured
    next(x for x in at.text_input if x.label=='Scenario Run Name').set_value('  Named Original  ').run()
    button(at,'Run Optimization').click().run()
    assert captured[0].name=='Named Original'
    assert captured[0].values["rate.L1"]==6
    assert at.session_state.scenario.values["rate.L1"]==99
    assert at.session_state.screen=="running" and not at.exception
