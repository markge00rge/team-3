"""Durable scenario state is separate from transient Streamlit widget keys."""
from app.scenarios import original_scenario


def initialize(state, source=None):
    defaults = dict(screen="home",page=0,revision=0,scenario=None,history={},selected_run=None,job=None)
    for k,v in defaults.items():
        if k not in state: state[k] = v
    if state["scenario"] is None: state["scenario"] = original_scenario(source)
    if state['scenario'].schema_version==1:
        from app.scenarios import Scenario
        state['scenario']=Scenario.from_json(state['scenario'].to_json())
        state['revision']+=1


def reset(state, source=None, key=None):
    default = original_scenario(source)
    if key is None: state["scenario"] = default
    else: state["scenario"].values[key] = default.values[key]
    if key is None or key.startswith("demand."): state.pop("demand_error",None)
    state["revision"] += 1


def navigate(state, page):
    state["page"] = max(0,min(6,page))
    state["section_navigation"] = state["page"]


def load_scenario(state, scenario):
    scenario.validate()
    state["scenario"] = scenario.clone()
    state["revision"] += 1
