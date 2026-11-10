from copy import deepcopy
import streamlit as st
from app.scenarios import RULE_FIELDS
from app.state import reset


def run_name_input(key):
    """Keep the draft outside widget state, which Streamlit clears off-page."""
    def remember(): st.session_state[key+'_draft']=st.session_state[key]
    st.text_input('Scenario Run Name',key=key,max_chars=100,
        value=st.session_state.get(key+'_draft',''),on_change=remember,
        placeholder='e.g., Original Venus Plan, Increased Summer Demand, Reduced Hiring Costs')


def number(key,label=None,help=None):
    scenario,original = st.session_state.scenario,st.session_state.original
    minimum,integer = 0.0,False
    if key.startswith("rule."):
        title,minimum,integer,_ = RULE_FIELDS[key[5:]]
        label = label or title
    else:
        label = label or key
        if key.startswith(("rate.","bom.")) and not key.endswith("fp_usd_per_msu"): minimum=0.001
    percent = key in ("rule.fp_holding_fraction_month","rule.spot_surcharge_fraction")
    if help is None:
        if "moq" in key: help="MOQ: every additional order is an integer multiple of this lot size; original fixed receipts are not re-lotted."
        elif "overflow" in key: help="3PL is external storage. Every booked block is charged in full, even if partly occupied."
        elif key=="rule.fp_holding_fraction_month": help="Monthly working-capital holding expense on actual ending finished-product value. Inventory value itself is not an operating expense."
        elif key.startswith("initial_fp."): help="MSU means 1,000 statistical units. Opening stock contributes to supply once."
    factor = 100 if percent else 1
    value = scenario.values[key]*factor
    widget = f"field:{st.session_state.revision}:{key}"
    changed = scenario.values[key] != original.values[key]
    def store():
        st.session_state.scenario.values[key] = st.session_state[widget]/factor
    left,right = st.columns([10,1],vertical_alignment="bottom")
    with left:
        st.number_input(label+(" • changed" if changed else ""),min_value=int(minimum) if integer else float(minimum),
            value=int(value) if integer else float(value),step=1 if integer else (0.1 if percent else 1.0),
            key=widget,on_change=store,help=help,format="%d" if integer else "%.3f")
    with right:
        st.button("↺",key="reset:"+widget,help=f"Reset {label}",on_click=reset,args=(st.session_state,st.session_state.source,key))


def toggle(key,label,help=None):
    widget=f"field:{st.session_state.revision}:{key}"
    def store(): st.session_state.scenario.values[key] = st.session_state[widget]
    st.toggle(label,value=st.session_state.scenario.values[key],key=widget,on_change=store,help=help)


def table(frame):
    st.dataframe(frame,hide_index=True,width="stretch")
