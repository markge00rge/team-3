import io
import pandas as pd
import streamlit as st
from app.components.fields import number, toggle, table
from app.scenarios import RULE_FIELDS, demand_frame, apply_demand
from app.state import navigate
from app.theme import heading

SECTIONS=["Plant & Products","Manufacturing","Materials & Procurement","Workforce & Upgrades",
          "Warehouse & Cash","Distribution & Demand","Review & Optimize"]


def rules(page):
    cols=st.columns(2)
    for i,(key,(_,_,_,section)) in enumerate((x for x in RULE_FIELDS.items() if x[1][3]==page)):
        with cols[i%2]: number("rule."+key)


def plant():
    source=st.session_state.source
    st.info("Venus structure is fixed. Numerical inputs can be customized on the next pages.")
    a,b=st.columns(2)
    with a:
        with st.container(border=True):
            st.subheader("A → C · one demand family")
            st.write("A is discontinued in manufacturing at qualification. Existing A finished goods can still sell through.")
            st.caption("B remains independently demanded. No separate A or C forecasts.")
    with b:
        with st.container(border=True):
            st.subheader("12 months · 28 days each")
            st.write("October 2026 – September 2027 · 2 lines · 3 regional hubs")
            st.caption("Product identities, line eligibility, hub identities and four-week calendar are locked.")
    options=["optimize"]+list(source.months)
    widget=f"qualification:{st.session_state.revision}"
    def update(): st.session_state.scenario.values["qualification_month"]=st.session_state[widget]
    st.selectbox("Qualification timing",options,index=options.index(st.session_state.scenario.values["qualification_month"]),
        format_func=lambda x:"Optimize timing across the horizon" if x=="optimize" else "Restrict start to "+x,
        key=widget,on_change=update,help="A selected month restricts the existing qualification candidates. The solver still selects the valid planning day.")
    st.caption("Three consecutive common base working days; both lines shut down. No fixed-day input is offered.")
    with st.expander("Opening finished-product stock (MSU)"):
        for p in source.products: number("initial_fp."+p,f"Product {p} opening FP (MSU)")


def manufacturing():
    source=st.session_state.source
    for col,l in zip(st.columns(2),source.lines.index):
        with col,st.container(border=True):
            st.subheader("Line "+l[1:])
            st.caption("Eligible products: "+", ".join(source.lines.loc[l,"products"]))
            number("rate."+l,"Daily output (MSU) — "+l,help="MSU: 1,000 statistical units. Capacity is before shutdown/changeover losses.")
            toggle("upgrade."+l,"Allow optional "+source.rules["upgraded_profiles"][l]+" upgrade — "+l)
            rate=st.session_state.scenario.values["rate."+l]
            st.metric("Base monthly capacity",f"{rate*source.lines.loc[l,'days_per_month']:,.1f} MSU")
            days=4*int(source.rules["upgraded_profiles"][l].split("/")[1])
            st.write(f"Base {source.lines.loc[l,'profile']} · {int(source.lines.loc[l,'operators'])} existing operators")
            st.caption(f"Upgraded theoretical maximum: {days*rate:,.1f} MSU / four-week month.")
    st.info("L2: one full scheduled day per routine product switch; at most one switch/month. Qualification: three simultaneous shutdown days. These rules remain fixed.")


def materials():
    from app.components.shipment_policy import selector
    selector()
    st.subheader('Product-specific material prices')
    for col,p in zip(st.columns(3),('A','B','C')):
        with col:
            number(f'price.{p}.RM',f'Product {p} RM ($/kg)')
            number(f'price.{p}.PM',f'Product {p} PM ($/EA)')
    for col,p in zip(st.columns(3),("A","B","C")):
        with col,st.container(border=True):
            st.subheader("Product "+p)
            number(f"bom.{p}.rm_kg_per_msu","RM consumption (kg/MSU) — "+p)
            number(f"bom.{p}.pm_ea_per_msu","PM consumption (EA/MSU) — "+p)
            number(f"stock.{p}.RM","Opening RM (kg) — "+p)
            number(f"stock.{p}.PM","Opening PM (EA) — "+p)
            if p=='B':
                settings=st.session_state.scenario.values
                st.caption(f"Previously committed B shipments: None. RM lot {settings['rule.rm_moq_kg']:,.0f} kg; PM lot {settings['rule.pm_moq_ea']:,.0f} EA; lead time {settings['rule.sea_lead_months']:g} planning months. Edit shared procurement settings below.")
    with st.expander("Scheduled receipts · dates and material identities locked",expanded=True):
        for i,r in st.session_state.source.arrivals.iterrows():
            number(f"receipt.{i}",f"{r['product']} {r['material']} · {str(r['date'])[:10]} · {r['unit']}")
    with st.expander("Ordering lots, sea freight, values, pallet factors & disposal",expanded=False): rules(3)
    st.info('Product B RM and packaging are now explicitly tracked. New materials must be ordered three months in advance, subject to minimum order increments, and unused inventory occupies warehouse space.')
    st.caption('B opening RM 200,000 kg / PM 750,000 EA are adopted clarification assumptions, not numerical opening quantities in the original Word/Excel files. All A/B/C new purchases are charged at placement; opening inventory and fixed receipts are not charged again.')


def workforce():
    source=st.session_state.source
    table(source.lines[["profile","operators"]].reset_index())
    toggle('flexible_workforce','Allow dismissal and rehiring of additional crews',help='Base employees remain permanent. Rehiring requires a new hiring fee and complete retraining.')
    rules(4)
    st.info("At most one additional crew per line. Training is paid and adds no capacity. Dismissal is effective at month start; rehiring requires fresh full training. Existing 70 workers remain permanent.")
    st.caption('Default dismissal expense is $0 per additional operator: a new modeling assumption, not a source case value.')
    st.caption("No invented overtime rate, plant headcount ceiling or separate training fee. Dismissal expense uses the explicit configurable assumption above.")


def warehouse():
    rules(5)
    st.subheader("Finished-product valuations")
    for col,p in zip(st.columns(3),st.session_state.source.products):
        with col: number(f"bom.{p}.fp_usd_per_msu",f"Product {p} FP value ($/MSU)")
    st.info("FP valuation is inventory value, not selling price. Holding expense = ending FP value × monthly rate. Inventory cash is not another operating expense.")
    st.caption('External 3PL is available; full booking blocks are charged. Month-end checks include all A/B/C FP, RM and PM, but do not establish intramonth peaks.')


def distribution():
    rules(6)
    st.caption("Spot-market trucks remain available without an invented supplier limit. Fleet capacity is shared across hubs; trucks cannot mix hubs.")
    with st.expander("Regional transport costs and shortage penalties"):
        for h in st.session_state.source.hubs.index:
            st.markdown(f"**{h} · P{int(st.session_state.source.hubs.loc[h,'priority'])} · {st.session_state.source.hubs.loc[h,'name']}**")
            number(f"hub.{h}.truck_usd",f"Dedicated $/truck — {h}")
            number(f"hub.{h}.unserved_usd_per_msu",f"Unserved $/MSU — {h}")
    st.subheader("Monthly demand planner")
    st.caption("Edit MSU in the forecast. A/C is one shared family; B is separate. Region and family identities are locked.")
    cfg=st.session_state.scenario
    frame=demand_frame(cfg,st.session_state.source)
    wide=frame.pivot(index=["hub","family"],columns="month",values="msu").reset_index()
    key=f"demand_editor:{st.session_state.revision}"
    def save_demand():
        patch=st.session_state[key].get("edited_rows",{})
        copy=cfg.clone()
        try:
            for i,changes in patch.items():
                row=wide.iloc[int(i)]
                for month,value in changes.items():
                    if month not in st.session_state.source.months: raise ValueError("Demand identities are locked")
                    copy.values[f"demand.{row.hub}.{row.family}.{month}"]=float(value)
            copy.validate(st.session_state.source)
            st.session_state.scenario=copy
            st.session_state.pop("demand_error",None)
        except (ValueError,TypeError) as exc: st.session_state.demand_error=str(exc)
    # Stable input per editor instance; callback commits edits to the durable scenario.
    basekey=f"demand_base:{st.session_state.revision}"
    if basekey not in st.session_state: st.session_state[basekey]=wide
    wide=st.session_state[basekey]
    edited=st.data_editor(wide,key=key,on_change=save_demand,disabled=["hub","family"],hide_index=True,width="stretch",
        column_config={t:st.column_config.NumberColumn(t,min_value=0.0,format="%.1f MSU") for t in st.session_state.source.months})
    try:
        incoming=edited.melt(id_vars=["hub","family"],var_name="month",value_name="msu")
        st.session_state.scenario=apply_demand(st.session_state.scenario,incoming,st.session_state.source)
        st.session_state.pop("demand_error",None)
    except (ValueError,TypeError) as exc: st.session_state.demand_error=str(exc)
    if "demand_error" in st.session_state: st.error(st.session_state.demand_error)
    current=demand_frame(st.session_state.scenario,st.session_state.source)
    original=demand_frame(st.session_state.original,st.session_state.source)
    changed=current[current.msu != original.msu]
    st.metric("Full-year demand",f"{current.msu.sum():,.1f} MSU",help="Original forecast: 3,095 MSU. A/C demand is counted once.")
    a,b,c=st.columns(3)
    with a: st.caption("Monthly totals"); table(current.groupby("month",as_index=False).msu.sum())
    with b: st.caption("Regional totals"); table(current.groupby("hub",as_index=False).msu.sum())
    with c: st.caption("Family totals"); table(current.groupby("family",as_index=False).msu.sum())
    if not changed.empty:
        with st.expander(f"{len(changed)} changed forecast cells"): table(changed)
    def reset_forecast():
        for k,v in st.session_state.original.values.items():
            if k.startswith("demand."): st.session_state.scenario.values[k]=v
        st.session_state.revision+=1
        st.session_state.pop("demand_error",None)
    st.button("Reset original forecast",on_click=reset_forecast)
    st.download_button("Export demand CSV",current.to_csv(index=False),"venus_demand.csv","text/csv")
    upload=st.file_uploader("Import demand CSV",type="csv",key="demand_upload")
    if st.button("Apply demand CSV",disabled=upload is None):
        try:
            st.session_state.scenario=apply_demand(st.session_state.scenario,pd.read_csv(io.BytesIO(upload.getvalue())),st.session_state.source)
            st.session_state.pop("demand_error",None)
            st.session_state.revision+=1
            st.rerun()
        except (ValueError,TypeError) as exc: st.error(str(exc))


def review(start):
    from src.shipment_policy import POLICIES
    st.info('International Shipment Consolidation: '+POLICIES[st.session_state.scenario.shipment_consolidation_policy][0])
    cfg=st.session_state.scenario
    from app.run_store import RunStore, RunStoreError, validate_name
    from app.components.fields import run_name_input
    run_name_input('custom_run_name')
    named=True
    try:
        run_name=validate_name(st.session_state.get('custom_run_name',''))
        if RunStore().name_in_use(run_name): st.info('This display name is already in use. Both runs will have different unique IDs; neither will be overwritten.')
    except RunStoreError as exc:
        named=False
        if st.session_state.get('custom_run_name','').strip(): st.error(str(exc))
        else: st.caption('Enter a run name before starting optimization.')
    try:
        data=cfg.to_case(st.session_state.source)
        if "demand_error" in st.session_state: raise ValueError(st.session_state.demand_error)
        valid=True
        st.success("Scenario validated. Ready to rebuild and run the real V6 MILP.")
    except (ValueError,KeyError,TypeError) as exc:
        st.error(str(exc)); valid=False; data=None
    changed=cfg.changes(st.session_state.source)
    st.metric("Supported values changed",len(changed))
    if not changed.empty: table(changed.astype({"original":str,"modified":str}))
    else: st.info("All business parameters match Original Venus.")
    if data is not None:
        a,b,c=st.columns(3)
        a.metric("Annual demand",f"{data.demand.msu.sum():,.1f} MSU")
        b.metric("Base monthly capacity",f"{sum(data.lines.msu_per_day*data.lines.days_per_month):,.1f} MSU")
        c.metric("Dedicated fleet",f"{data.rules['dedicated_trucks_month']:g} trucks")
        with st.expander("Complete input review",expanded=False):
            table(pd.DataFrame([dict(parameter=k,value=str(v)) for k,v in cfg.values.items()]))
        st.caption("28-day calendar · full-month paid training · strict Scenario A · monthly family priorities · source assumptions retained.")
    st.number_input("Solver limit per stage (seconds)",min_value=10,max_value=1800,value=180,step=10,key="time_limit",
        help="A limit is not an optimality guarantee. The optional procurement warm-start heuristic may use up to 20 extra seconds.")
    st.button("Optimize Supply Chain",type="primary",disabled=not (valid and named),on_click=start,args=(False,))


def render(start):
    page=st.session_state.page
    heading(f"VENUS CONFIGURATION / STEP {page+1} OF 7",SECTIONS[page],"Changes are saved as you work. Reset any value with ↺.")
    st.progress((page+1)/7,text="Questionnaire position — not solver progress")
    [plant,manufacturing,materials,workforce,warehouse,distribution,lambda:review(start)][page]()
    st.divider()
    a,b,c=st.columns([1,4,1])
    a.button("← Previous",disabled=page==0,on_click=navigate,args=(st.session_state,page-1))
    c.button("Next →",disabled=page==6,on_click=navigate,args=(st.session_state,page+1))
