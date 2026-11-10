"""Streamlit history navigation with isolated SQLite; solver calls forbidden."""
from copy import deepcopy
import json
from uuid import uuid4
import pytest
from streamlit.testing.v1 import AppTest
from src.data_loader import ROOT
from app.scenarios import Scenario
from app.optimizer_adapter import read_run
from app.run_store import RunStore,make_record,snapshot_case


@pytest.fixture
def history(tmp_path,monkeypatch):
    monkeypatch.setenv('CAIRO_RUN_DB',str(tmp_path/'history.sqlite3'))
    directory=ROOT/'reports/app_runs/v6_original_resumed'
    completion,tables,transition=read_run(directory)
    cfg=json.loads((directory/'scenario.json').read_text())
    record=make_record('Original Venus Plan',cfg,snapshot_case(Scenario.from_json(json.dumps(cfg)).to_case()),
        completion,tables,transition,json.loads((directory/'solution_audit.json').read_text()),scenario_type='Original')
    store=RunStore();store.save_run(record)
    # A comparison fixture, never published outside this temporary test database.
    other=deepcopy(record);other.update(run_id=uuid4().hex,name='SalarySensitivity'*5,scenario_type='Customized')
    other['effective_inputs']['rules']['operator_usd_per_month']=800
    store.save_run(other)
    monkeypatch.setattr('app.optimizer_adapter.solve_lexicographic',lambda *a,**k:pytest.fail('No solve allowed during history browsing'))
    monkeypatch.setattr('app.jobs.start_job',lambda *a,**k:pytest.fail('No optimization job allowed while browsing'))
    return store,record,other


def button(at,label): return next(b for b in at.button if b.label==label)


def app():return AppTest.from_file(str(ROOT/'app/main.py'),default_timeout=60).run()


def test_history_survives_new_streamlit_session_and_is_read_only(history):
    store,record,_=history
    at=app();button(at,'Compare Runs').click().run()
    assert not at.exception
    assert [t.label for t in at.tabs]==['Venus Case Study Runs','General Plant Runs']
    assert button(at,'Compare Selected Runs').disabled
    at2=app();button(at2,'Compare Runs').click().run()
    at2.session_state.scenario.values['rate.L1']=99
    next(x for x in at2.selectbox if x.label=='Open a saved run').select(record['run_id']).run()
    button(at2,'Open Saved Dashboard').click().run()
    assert not at2.exception and at2.session_state.screen=='saved_results'
    assert any(x.value==record['name'] for x in at2.title)
    assert any('Read-only saved run' in c.value for c in at2.caption)
    html=next(x.value for x in at2.markdown if 'data-finance-key=' in x.value)
    assert '$1,215,467.50' in html and '$10,941,467.50' in html
    button(at2,'View Configured Parameters').click().run()
    assert not at2.exception and len(at2.tabs)==7
    assert not list(at2.number_input) and not list(at2.get('data_editor'))
    line_tables=[d.value for d in at2.dataframe if 'msu_per_day' in d.value.columns]
    assert line_tables and line_tables[0].msu_per_day.iloc[0]==6
    assert at2.session_state.scenario.values['rate.L1']==99
    button(at2,'Back to Saved Results').click().run()
    assert at2.session_state.screen=='saved_results' and not at2.exception
    assert store.get_run(record['run_id'])==record


def test_compare_two_saved_snapshots_and_show_changed_inputs(history):
    store,a,b=history
    at=app();button(at,'Compare Runs').click().run()
    select=next(x for x in at.multiselect if x.key=='history_comparison_selection')
    select.set_value([a['run_id']]).run()
    assert button(at,'Compare Selected Runs').disabled
    next(x for x in at.multiselect if x.key=='history_comparison_selection').set_value([a['run_id'],b['run_id']]).run()
    assert not button(at,'Compare Selected Runs').disabled
    button(at,'Compare Selected Runs').click().run()
    assert not at.exception and at.session_state.screen=='saved_comparison'
    assert any(x.value=='What Changed Between These Runs?' for x in at.subheader)
    assert len([x for x in at.markdown if 'data-finance-key=' in x.value])==2
    frames=[x.value for x in at.dataframe if 'parameter' in x.value.columns]
    assert any(any('Salary' in s for s in f.parameter) for f in frames)
    assert len(at.get('plotly_chart'))>=7
    assert store.get_run(a['run_id'])==a


def test_original_and_custom_workflows_require_run_name(history):
    at=app()
    next(b for b in at.button if b.label.startswith('Open Venus Case Study')).click().run()
    button(at,'Run Original Case').click().run()
    assert button(at,'Run Optimization').disabled
    next(x for x in at.text_input if x.label=='Scenario Run Name').set_value('  ').run()
    assert button(at,'Run Optimization').disabled
    next(x for x in at.text_input if x.label=='Scenario Run Name').set_value('Original Venus Plan').run()
    assert not button(at,'Run Optimization').disabled
    assert any('already in use' in i.value for i in at.info)
    button(at,'Configure scenario').click().run()
    next(x for x in at.selectbox if x.key=='section_navigation').select_index(6).run()
    assert button(at,'Optimize Supply Chain').disabled
    next(x for x in at.text_input if x.label=='Scenario Run Name').set_value('Higher June Demand').run()
    assert not button(at,'Optimize Supply Chain').disabled and not at.exception
    next(x for x in at.selectbox if x.key=='section_navigation').select_index(2).run()
    next(x for x in at.selectbox if x.key=='section_navigation').select_index(6).run()
    assert next(x for x in at.text_input if x.label=='Scenario Run Name').value=='Higher June Demand'


def test_old_saved_run_with_missing_new_reports_is_graceful(history):
    store,a,_=history
    old=deepcopy(a);old.update(run_id=uuid4().hex,name='Older report schema')
    del old['results']['tables']['productivity']
    store.save_run(old)
    at=app();at.session_state.selected_saved_id=old['run_id'];at.session_state.screen='saved_results';at.run()
    assert not at.exception
    assert any('not saved' in i.value for i in at.info)
    assert store.get_run(old['run_id'])==old
