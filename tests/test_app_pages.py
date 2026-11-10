"""Exercise every questionnaire section, including spreadsheet callbacks."""
import pytest
from streamlit.testing.v1 import AppTest
from src.data_loader import ROOT


def open_form():
    at=AppTest.from_file(str(ROOT/"app/main.py"),default_timeout=30).run()
    next(b for b in at.button if b.label=="Configure scenario").click().run()
    return at


def test_every_prefilled_section_renders_and_preserves_values():
    at=open_form()
    for page in range(7):
        next(s for s in at.selectbox if s.key=="section_navigation").select_index(page).run()
        assert not at.exception
        assert at.session_state.scenario.values["rule.fp_holding_fraction_month"]==.015
        assert at.session_state.scenario.values["rule.warehouse_pallets"]==1200


def test_spreadsheet_callback_commits_live_family_demand():
    at=open_form()
    next(s for s in at.selectbox if s.key=="section_navigation").select_index(5).run()
    key="demand_editor:0"
    # pivot row zero is H1 / AC. Streamlit editors store cell deltas separately.
    at.session_state[key]={"edited_rows":{0:{"2027-06":115.0}},"added_rows":[],"deleted_rows":[]}
    at.run()
    assert not at.exception
    # Simulating the editor's callback through the runtime is supported by AppTest.
    assert at.session_state.scenario.values["demand.H1.AC.2027-06"]==115

def test_new_workforce_and_six_price_controls_commit_to_scenario():
    at=open_form()
    next(s for s in at.selectbox if s.key=='section_navigation').select_index(2).run()
    prices=[x for x in at.number_input if ':price.' in x.key]
    assert len(prices)==6
    prices[0].set_value(6.25).run()
    assert at.session_state.scenario.values[prices[0].key.split(':',2)[2]]==6.25
    next(s for s in at.selectbox if s.key=='section_navigation').select_index(3).run()
    next(x for x in at.toggle if x.key.endswith(':flexible_workforce')).set_value(False).run()
    next(x for x in at.number_input if x.key.endswith(':rule.training_months')).set_value(2).run()
    next(x for x in at.number_input if x.key.endswith(':rule.dismissal_usd_per_operator')).set_value(100.0).run()
    next(x for x in at.number_input if x.key.endswith(':rule.upgrade_operators_per_line')).set_value(12).run()
    assert not at.exception
    case=at.session_state.scenario.to_case()
    assert case.rules['flexible_workforce'] is False
    assert case.rules['training_months']==2
    assert case.rules['dismissal_usd_per_operator']==100
    assert case.rules['upgrade_operators_per_line']==12


def test_v6_real_application_run_and_five_cards():
    from streamlit.testing.v1 import AppTest
    from app.optimizer_adapter import read_run
    from pathlib import Path
    directory=ROOT/'reports/app_runs/v6_original_resumed'
    completion,tables,_=read_run(directory)
    assert completion['outcome']['success']
    assert all(s['termination']=='optimal' and s['relative_gap']==0 for s in completion['outcome']['stages'])
    costs=completion['costs']
    assert sum(costs[k] for k in ('operating_expenses','a_materials','c_materials','b_materials'))==pytest.approx(costs['total_delivery_cost'],abs=.01)
    at=AppTest.from_file(str(ROOT/'app/main.py'),default_timeout=60).run()
    at.session_state.selected_run=str(directory)
    at.session_state.screen='results'
    at.run()
    assert not at.exception
    cards=[x.value for x in at.markdown if 'data-finance-key=' in x.value]
    assert len(cards)==1 and cards[0].count('data-finance-key=')==5
    assert '$10,941,467.50' in cards[0]
    assert any('All seven' in x.value for x in at.success)
