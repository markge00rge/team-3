"""Launch: python -m streamlit run app/main.py"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import streamlit as st
from src.data_loader import load_case, ROOT
from app.scenarios import original_scenario, Scenario
from app.state import initialize, reset, navigate, load_scenario
from app.theme import apply, heading
from app.jobs import start_job, events
from app.pages.questionnaire import render as questionnaire, SECTIONS
from app.dashboard import render as dashboard, compare
from app.optimizer_adapter import validated_baseline
from app.run_store import RunStore, RunStoreError, validate_name

st.set_page_config(page_title="Cairo Plant Supply Chain Optimizer",page_icon="◈",layout="wide",initial_sidebar_state="expanded")


@st.cache_data
def source_data(): return load_case()


def go(screen): st.session_state.screen=screen


def start(original=False):
    try:
        job=st.session_state.job
        if job is not None and job["process"].poll() is None:
            st.session_state.screen="running"; return
        if job is not None:
            completed=Path(job["directory"])/"completion.json"
            if completed.exists():
                previous=json.loads(completed.read_text())
                st.session_state.history[Path(job["directory"]).name]=dict(
                    name=previous["name"],directory=job["directory"],has_solution=previous["has_solution"])
        cfg=original_scenario(st.session_state.source) if original else st.session_state.scenario.clone()
        cfg.name=validate_name(st.session_state.get('original_run_name' if original else 'custom_run_name',''))
        if not original and "demand_error" in st.session_state:
            raise ValueError("Correct or reset invalid demand cells before optimizing")
        st.session_state.job=start_job(cfg,st.session_state.get("time_limit",180),scenario_type='Original' if original else 'Customized')
        st.session_state.screen="running"
        st.session_state.pop("notice",None)
    except (ValueError,TypeError) as exc: st.session_state.notice=str(exc)


def customize():
    st.session_state.screen="questionnaire"
    if st.session_state.scenario.name=="Original Venus": st.session_state.scenario.name="Custom Venus"


def sidebar():
    with st.sidebar:
        st.markdown("### ◈ CAIRO PLANT")
        st.caption("SUPPLY CHAIN OPTIMIZER")
        st.divider()
        st.button("Home",on_click=go,args=("home",),width="stretch")
        st.button("Venus Case Study",on_click=go,args=("venus",),width="stretch")
        st.button("Configure scenario",on_click=customize,width="stretch")
        st.button("Compare Runs",icon=':material/compare_arrows:',on_click=go,args=("comparison",),width="stretch")
        if st.session_state.screen=="questionnaire":
            st.selectbox("Configuration sections",range(7),index=st.session_state.page,
                format_func=lambda i:f"{i+1}. {SECTIONS[i]}",key="section_navigation",
                on_change=lambda:setattr(st.session_state,"page",st.session_state.section_navigation))
        job=st.session_state.job
        if job is not None:
            st.button("View running / latest job",on_click=go,args=("running",),width="stretch")
        if st.session_state.history:
            options=list(st.session_state.history)
            selected=st.selectbox("Completed runs",options,format_func=lambda k:st.session_state.history[k]["name"],key="run_selector")
            def view():
                st.session_state.selected_run=st.session_state.history[selected]["directory"]
                st.session_state.screen="results"
            st.button("Open selected dashboard",on_click=view,width="stretch")
        st.divider()
        st.caption(f"{len(st.session_state.scenario.changes(st.session_state.source))} modified values · edits saved in this session")
        st.button("Reset entire scenario",on_click=reset,args=(st.session_state,st.session_state.source),width="stretch")
        st.download_button("Save scenario JSON",st.session_state.scenario.to_json(),"venus_scenario.json","application/json",width="stretch")
        with st.expander("Reload a scenario"):
            uploaded=st.file_uploader("Scenario JSON",type="json",key="scenario_upload")
            if st.button("Load configuration",disabled=uploaded is None):
                try:
                    if uploaded.size>1_000_000: raise ValueError("Scenario JSON exceeds 1 MB")
                    load_scenario(st.session_state,Scenario.from_json(uploaded.getvalue()))
                    st.session_state.pop("demand_error",None)
                    st.rerun()
                except (ValueError,TypeError) as exc: st.error(str(exc))
        with st.expander("Planning glossary"):
            st.write("**MSU** · 1,000 statistical units\n\n**MOQ** · material ordering increment\n\n**3PL** · external logistics/storage provider\n\n**IDE** · inventory disposition expense\n\n**C:D** · cumulative capacity or supply divided by demand\n\n**Holding expense** · monthly charge on ending finished-product value")
        st.caption("V6 · Strict Scenario A\n\nPyomo + HiGHS · 28-day calendar")


def home():
    st.markdown('''<div class="hero"><div class="eyebrow">DECISIONS THAT MOVE THE PLANT FORWARD</div>
    <h1>Cairo Plant<br>Supply Chain Optimizer</h1><p>Plan Production. Optimize Resources. Maximize Service.</p>
    <p style="font-size:13px;margin-top:26px">COST &nbsp; / &nbsp; CASH &nbsp; / &nbsp; SERVICE &nbsp; / &nbsp; PRODUCTIVITY</p></div>''',unsafe_allow_html=True)
    st.subheader("Choose your planning workspace")
    a,b=st.columns(2,gap="large")
    with a,st.container(border=True):
        st.markdown('<span class="pill">READY TO OPTIMIZE</span>',unsafe_allow_html=True)
        st.markdown("### Venus Case Study")
        st.write("Optimize the existing P&G Venus Egypt supply chain using its validated manufacturing, procurement, warehouse and distribution model.")
        st.caption("3 products · 2 manufacturing lines · 3 regional hubs · 12 months")
        st.button("Open Venus Case Study →",type="primary",on_click=go,args=("venus",),width="stretch")
    with b,st.container(border=True):
        st.markdown('<span class="pill coming">COMING NEXT</span>',unsafe_allow_html=True)
        st.markdown("### Create a New Plant")
        st.write("Design and optimize a supply chain with a different number of products, production lines and distribution hubs.")
        st.caption("Structural model generalization is the next development phase.")
        st.button("Explore what’s coming →",on_click=go,args=("future",),width="stretch")
    st.caption("A case-competition planning application. Every new optimization executes the existing V6 MILP; saved baselines are identified explicitly.")


def venus():
    heading("WORKSPACE / VENUS EGYPT","From planning inputs to a proven plan","Configure supported business inputs or run the original case immediately.")
    a,b,c,d=st.columns(4)
    a.metric("Planning horizon","12 months"); b.metric("Calendar","4 weeks / month")
    c.metric("Manufacturing","2 lines"); d.metric("Regional network","3 hubs")
    st.caption("October 2026 – September 2027 · A, B, C · A → C transition · Pyomo + HiGHS")
    a,b=st.columns(2,gap="large")
    with a,st.container(border=True):
        st.subheader("Run the original case")
        st.write("Load the original P&G data and accepted V6 assumptions. No questionnaire required.")
        st.button("Run Original Case",type="primary",on_click=go,args=('name_original',),width="stretch")
        st.caption("Starts a new real solve. Your custom draft is preserved.")
    with b,st.container(border=True):
        st.subheader("Explore a business scenario")
        st.write("Seven prefilled sections. Change what matters and keep the Venus model structure intact.")
        st.button("Customize Parameters",on_click=customize,width="stretch")
        st.caption("Demand, capacity, materials, workforce costs, warehouse and distribution.")
    st.number_input("Solver limit per stage (seconds)",min_value=10,max_value=1800,value=180,step=10,key="time_limit")
    with st.expander("Saved validated baseline — not a new optimization"):
        saved=validated_baseline()
        st.caption(saved["label"])
        if not saved["corresponding_engine_version"]: st.warning("Engine or baseline changed since acceptance validation. Revalidate original-case parity before using this saved benchmark as a regression reference.")
        st.json(saved["costs"])


def name_original():
    heading('VENUS / ORIGINAL CASE','Name your optimization run','Original business inputs remain unchanged. Your custom draft is preserved.')
    from app.components.fields import run_name_input
    run_name_input('original_run_name')
    name=st.session_state.get('original_run_name','')
    valid=True
    try:
        validate_name(name)
        if RunStore().name_in_use(name): st.info('This display name is already in use. A separate unique run ID will preserve both plans.')
    except RunStoreError as exc:
        valid=False
        if name: st.error(str(exc))
    st.button('Run Optimization',type='primary',disabled=not valid,on_click=start,args=(True,))
    st.button('Back to Venus',on_click=go,args=('venus',))


@st.fragment(run_every="1s")
def running():
    job=st.session_state.job
    if job is None: st.info("No run is active. Choose Run Original Case or Optimize Supply Chain."); return
    heading("OPTIMIZATION / LIVE EXECUTION",job["name"],"Actual solver stages are shown below. No estimated progress percentage is used.")
    records=events(job)
    states={r["name"]:r for r in records}
    code=job["process"].poll()
    groups=[("Validating scenario",["validation"]),("Building the mathematical model",["building"]),
        ("Optimizing customer service",["service_H1","service_H2","service_H3"]),
        ("Optimizing monetary cost",["modeled_cost"]),
        ("Minimizing procurement events and quantities",["international_order_events","procurement_quantity_tiebreak","cost_cleanup"]),
        ("Extracting and validating results",["extraction"]),("Saving local run history",['saving']),("Preparing the dashboard",["dashboard"])]
    finished=(Path(job["directory"])/"completion.json").exists()
    for title,names in groups:
        actual=[states[n] for n in names if n in states]
        if actual and any(s["state"] in ("stopped","failed") for s in actual): label="Stopped — inspect solver status"
        elif all(n in states and states[n]["state"]=="completed" for n in names): label="Completed"
        elif actual and not finished: label="Running" if code is None else "Failed"
        elif finished: label="Not run"
        else: label="Waiting" if code is None else "Not run"
        st.write(("✓" if label=="Completed" else "◌" if label=="Running" else "—")+" **"+title+"** · "+label)
    with st.expander("Actual stage details",expanded=False): st.json(records)
    if finished:
        result=json.loads((Path(job["directory"])/"completion.json").read_text())
        key=Path(job["directory"]).name
        st.session_state.history[key]=dict(name=result["name"],directory=job["directory"],has_solution=result["has_solution"])
        st.session_state.selected_run=job["directory"]
        if result["has_solution"]:
            if result.get('saved_run_id'):
                st.session_state.selected_saved_id=result['saved_run_id']
                st.session_state.screen='saved_results'
            else: st.session_state.screen="results"
            st.rerun()
        else:
            st.error(result["outcome"]["message"])
            st.button("Return to editing",on_click=go,args=("questionnaire",))
    elif code is not None:
        error=Path(job["directory"])/"error.json"
        message=json.loads(error.read_text())["message"] if error.exists() else f"Worker exited with code {code}. No unchecked results published."
        st.error(message)
        with st.expander("Worker log"): st.code((Path(job["directory"])/"worker.log").read_text(encoding="utf-8",errors="replace"))
        st.button("Return to editing",on_click=go,args=("questionnaire",))
    else: st.caption("You can return to editing; this job continues with its frozen input snapshot. Refreshing a widget does not launch a new solve.")


def main():
    initialize(st.session_state)
    if "source" not in st.session_state: st.session_state.source=source_data()
    if "original" not in st.session_state or st.session_state.original.schema_version!=2:
        st.session_state.original=original_scenario(st.session_state.source)
    apply(); sidebar()
    if "notice" in st.session_state: st.error(st.session_state.notice)
    screen=st.session_state.screen
    if screen=="home": home()
    elif screen=="venus": venus()
    elif screen=="questionnaire": questionnaire(start)
    elif screen=="running": running()
    elif screen=="results": dashboard(st.session_state.selected_run)
    elif screen=='name_original': name_original()
    elif screen in ('comparison','saved_results','saved_parameters','saved_comparison'):
        from app.history import history_page, saved_dashboard, configured_parameters, comparison_page
        {'comparison':history_page,'saved_results':saved_dashboard,'saved_parameters':configured_parameters,
         'saved_comparison':comparison_page}[screen]()
    elif screen=="future":
        heading("NEXT DEVELOPMENT PHASE","Create a New Plant","Coming Next")
        st.info("Structural model generalization is under development. Arbitrary products, production lines, replacement mappings and hub networks are not supported in this version.")
        st.write("The next phase requires a generalized input schema, eligibility rules, transition relationships and independent validation for new plant structures.")
        st.button("Back to Venus",on_click=go,args=("venus",))


if __name__=="__main__": main()
