"""Immutable local history and pure saved-data comparisons; real V6 artifacts."""
from copy import deepcopy
from datetime import datetime,timezone
import json
import sqlite3
from uuid import uuid4
import pandas as pd
import pytest
from src.data_loader import ROOT
from app.scenarios import Scenario
from app.optimizer_adapter import read_run
from app.run_store import (RunStore,RunStoreError,make_record,snapshot_case,
    unpack_results,restore_frame,validate_name)
from app.comparisons import (choose_pair,difference,percentage,changed_inputs,
    demand_comparison,financial_comparison,service_comparison,paired_table,warnings)


@pytest.fixture(scope='module')
def real_record():
    directory=ROOT/'reports/app_runs/v6_original_resumed'
    completion,tables,transition=read_run(directory)
    cfg=json.loads((directory/'scenario.json').read_text())
    scenario=Scenario.from_json(json.dumps(cfg))
    effective=snapshot_case(scenario.to_case())
    audit=json.loads((directory/'solution_audit.json').read_text())
    return make_record('Original Venus Plan',cfg,effective,completion,tables,transition,audit,scenario_type='Original')


@pytest.fixture
def store(tmp_path,monkeypatch):
    path=tmp_path/'local/runs.sqlite3'
    monkeypatch.setenv('CAIRO_RUN_DB',str(path))
    return RunStore()


def changed(record,name='Higher June Demand'):
    out=deepcopy(record); out.update(run_id=uuid4().hex,name=name,scenario_type='Customized')
    return out


def test_atomic_save_reopen_new_instance_complete_snapshot(store,real_record,monkeypatch):
    store.save_run(real_record)
    monkeypatch.setattr('app.scenarios.load_case',lambda:pytest.fail('Historical reads must not load defaults'))
    another=RunStore(store.path)
    assert another.get_run(real_record['run_id'])==real_record
    assert another.validate_integrity(real_record['run_id'])
    assert another.get_inputs(real_record['run_id'])==real_record['effective_inputs']
    assert another.get_results(real_record['run_id'])==real_record['results']
    inputs=another.get_inputs(real_record['run_id'])
    assert restore_frame(inputs['demand']).msu.sum()==3095
    assert sum(inputs['initial_fp'].values())==25
    assert inputs['rules']['weeks_per_month']==4
    assert inputs['rules']['material_unit_prices']['B']['RM']==5
    assert len(another.get_results(real_record['run_id'])['tables']['daily_schedule']['data'])==672


def test_duplicate_display_names_coexist_and_cannot_overwrite(store,real_record):
    a=deepcopy(real_record);b=changed(a,a['name'])
    store.save_run(a);store.save_run(b)
    assert len(store.list_runs())==2 and store.name_in_use(' original venus plan ')
    assert store.save_run(a)==a['run_id']
    modified=deepcopy(a);modified['name']='Replacement'
    with pytest.raises(RunStoreError,match='immutable'):store.save_run(modified)
    assert store.get_run(a['run_id'])==a


def test_categories_types_and_incumbent_status_preserved(store,real_record):
    incumbent=changed(real_record);incumbent['category']='General Plant'
    c=incumbent['results']['completion'];c['outcome']['success']=False;c['monetary_optimal']=False
    c['outcome']['stages'][-1].update(termination='maxTimeLimit',relative_gap=.25)
    store.save_run(real_record);store.save_run(incumbent)
    assert len(store.list_runs('Venus Case Study'))==len(store.list_runs('General Plant'))==1
    saved=store.get_run(incumbent['run_id'])
    assert saved['scenario_type']=='Customized'
    assert saved['results']['completion']['outcome']['stages'][-1]['relative_gap']==.25


@pytest.mark.parametrize('path',[('results','audit','passed'),('results','completion','has_solution')])
def test_invalid_or_incomplete_run_not_saved(store,real_record,path):
    bad=deepcopy(real_record);value=bad
    for key in path[:-1]:value=value[key]
    value[path[-1]]=False
    with pytest.raises(RunStoreError):store.save_run(bad)
    assert store.list_runs()==[]


def test_missing_tables_or_inputs_and_unreconciled_money_rejected(store,real_record):
    for variant in ('table','input','cost'):
        bad=deepcopy(real_record)
        if variant=='table':del bad['results']['tables']['production']
        elif variant=='input':del bad['effective_inputs']['rules']
        else:bad['results']['completion']['costs']['total_delivery_cost']+=10
        with pytest.raises(RunStoreError):store.save_run(bad)


def test_write_failure_and_corruption_are_explicit(tmp_path,store,real_record):
    blocked=tmp_path/'file';blocked.write_text('not a directory')
    with pytest.raises(RunStoreError):RunStore(blocked/'db.sqlite3')
    store.save_run(real_record)
    with sqlite3.connect(store.path) as db:db.execute("UPDATE runs SET payload='{}'")
    with pytest.raises(RunStoreError,match='integrity'):store.get_run(real_record['run_id'])


@pytest.mark.parametrize('name',['','   ','x'*101,None])
def test_names_required_and_bounded(name):
    with pytest.raises(RunStoreError):validate_name(name)


def test_name_trim_and_serialized_dates_and_nulls(real_record):
    assert validate_name(' Original Plan ')=='Original Plan'
    assert datetime.fromisoformat(real_record['created_at']).tzinfo
    text=json.dumps(real_record,allow_nan=False)
    assert json.loads(text)==real_record


def test_exact_two_distinct_same_category(real_record):
    b=changed(real_record)
    assert choose_pair([real_record,b],[real_record['run_id'],b['run_id']])==[real_record,b]
    for ids in ([],[b['run_id']],[b['run_id']]*2,[b['run_id']]*3,['missing',b['run_id']]):
        with pytest.raises(ValueError):choose_pair([real_record,b],ids)
    b['category']='General Plant'
    with pytest.raises(ValueError):choose_pair([real_record,b],[real_record['run_id'],b['run_id']])


def test_difference_percentage_and_zero_baseline():
    assert difference(100,125)==25
    assert percentage(100,125)==25
    assert percentage(0,5) is None
    assert difference(True,False) is None


def test_nested_and_input_demand_changes_are_exact(real_record):
    b=changed(real_record);b['effective_inputs']['rules']['operator_usd_per_month']=800
    b['effective_inputs']['rules']['material_unit_prices']['C']['PM']=.5
    demand=restore_frame(b['effective_inputs']['demand'])
    mask=(demand.month=='2027-06')&(demand.hub=='H1')&(demand.family=='AC')
    demand.loc[mask,'msu']+=45
    from app.run_store import frame_snapshot
    b['effective_inputs']['demand']=frame_snapshot(demand)
    diff=changed_inputs(real_record,b)
    assert len(diff)==3
    assert any('Salary' in s for s in diff.parameter)
    assert not changed_inputs(real_record,deepcopy(real_record)).shape[0]
    table=demand_comparison(real_record,b)
    assert table.month.tolist()==real_record['effective_inputs']['months']
    assert table.difference.sum()==45
    assert demand_comparison(real_record,b,('hub','family','month')).difference.sum()==45
    # Input comparison never uses output demand (unchanged here).
    assert service_comparison(real_record,b).demand_msu_a.sum()==3095
    assert any('Demand or service' in message for message in warnings(real_record,b))


def test_financial_and_workforce_comparisons_saved_values(real_record):
    b=changed(real_record);b['results']['completion']['costs']['operating_expenses']+=100
    f=financial_comparison(real_record,b).set_index('metric')
    assert f.loc['Operating Expenses USD','difference']==100
    assert f.loc['Additional A materials USD','percentage_change']!=f.loc['Additional A materials USD','percentage_change']  # undefined NaN
    employed=paired_table(real_record,b,'staffing',['month','line'],'employed_operators')
    assert employed.difference.abs().sum()==0


def test_incompatible_definitions_withhold_financial_differences(real_record):
    b=changed(real_record);b['financial_version']='historical-operating-only';b['model_version']='Older'
    assert financial_comparison(real_record,b).difference.isna().all()
    assert any('Financial definitions differ' in x for x in warnings(real_record,b))
    assert any('different mathematical' in x for x in warnings(real_record,b))


def test_history_get_does_not_share_mutable_objects(store,real_record):
    store.save_run(real_record);a=store.get_run(real_record['run_id'])
    a['effective_inputs']['rules']['warehouse_pallets']=1
    assert store.get_run(real_record['run_id'])['effective_inputs']['rules']['warehouse_pallets']==1200


def test_main_kpis_exact_material_cards_compact(real_record):
    from app.components.financial_cards import card_html
    html=card_html(real_record['results']['completion']['costs'])
    assert '$1,215,467.50' in html and '$10,941,467.50' in html
    assert '$3.95M' in html and '$5.78M' in html
    assert html.index('total_delivery_cost')<html.index('a_materials')
    assert 'Exact unrounded USD:' in html
