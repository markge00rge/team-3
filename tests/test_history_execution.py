"""Real Pyomo/HiGHS execution -> validated outputs -> transactional history."""
import json
from uuid import uuid4
import pytest
from src.data_loader import ROOT
from app.scenarios import original_scenario
from app.optimizer_adapter import execute
from app.run_store import RunStore,RunStoreError,restore_frame


def zero_demand_scenario():
    scenario=original_scenario();scenario.name='History integration / zero-demand diagnostic'
    for key in scenario.values:
        if key.startswith(('demand.','stock.','receipt.','initial_fp.')):scenario.values[key]=0
    return scenario


def test_real_solve_automatically_saves_complete_snapshot(tmp_path,monkeypatch):
    monkeypatch.setenv('CAIRO_RUN_DB',str(tmp_path/'runs.sqlite3'))
    directory=ROOT/'reports/app_runs'/('history_test_'+uuid4().hex)
    s=zero_demand_scenario()
    events=[]
    c=execute(s,directory,time_limit=30,scenario_type='Customized',notify=lambda *e:events.append(e))
    assert c['has_solution'] and c['outcome']['success']
    assert c.get('saved_run_id') and not c.get('save_error')
    record=RunStore().get_run(c['saved_run_id'])
    assert record['scenario_type']=='Customized'
    assert record['configuration']['values']==s.values
    assert restore_frame(record['effective_inputs']['demand']).msu.sum()==0
    assert record['effective_inputs']['rules']['weeks_per_month']==4
    assert record['results']['completion']['costs']==c['costs']
    assert record['results']['audit']['passed']
    assert ('saving','completed',{'run_id':c['saved_run_id']}) in events
    assert json.loads((directory/'completion.json').read_text())['saved_run_id']==c['saved_run_id']


def test_save_error_does_not_claim_success_or_discard_valid_solve(tmp_path,monkeypatch):
    monkeypatch.setenv('CAIRO_RUN_DB',str(tmp_path/'runs.sqlite3'))
    def failed_save(*a,**k):raise RunStoreError('Simulated disk write failure')
    monkeypatch.setattr('app.run_store.RunStore.save_run',failed_save)
    directory=ROOT/'reports/app_runs'/('history_failure_test_'+uuid4().hex)
    c=execute(zero_demand_scenario(),directory,time_limit=30,scenario_type='Customized')
    assert c['has_solution'] and c['outcome']['success']
    assert 'disk write failure' in c['save_error']
    assert 'saved_run_id' not in c
    assert RunStore().list_runs()==[]
