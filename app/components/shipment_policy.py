"""Shared mutually exclusive policy selector; durable value lives in Scenario."""
import streamlit as st
from src.shipment_policy import POLICIES


def selector(*,original=False):
    cfg=st.session_state.scenario
    current=st.session_state.get('original_shipment_policy','independent_materials') if original else cfg.shipment_consolidation_policy
    key='original_shipment_policy' if original else f'custom_shipment_policy_{st.session_state.revision}'
    def changed():
        if not original:cfg.shipment_consolidation_policy=st.session_state[key]
    selected=st.radio('International Shipment Consolidation Policy',list(POLICIES),
        index=list(POLICIES).index(current),format_func=lambda p:POLICIES[p][0],key=key,on_change=changed)
    st.caption(POLICIES[selected][1])
    st.caption('A shipment is a dispatch batch, not a physical container. No inbound container capacity or freight fee is assumed.')
    if selected=='all_products':st.info('Selected assumption: all six materials can use a common international consolidation hub; the original case does not confirm this.')
    return selected
