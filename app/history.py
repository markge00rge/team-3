"""Persistent history, read-only inputs and saved-scenario comparison screens."""
import json
from html import escape
import pandas as pd
import streamlit as st
from app.run_store import RunStore, RunStoreError, restore_frame, unpack_results
from app.comparisons import (choose_pair, financial_comparison, changed_inputs,
    demand_comparison, service_comparison, paired_table, warnings, compare_values)
from app.dashboard import table, chart, render as dashboard
from app.theme import heading


def open_saved(run_id):
    st.session_state.selected_saved_id=run_id
    st.session_state.screen='saved_results'


def run_label(record):
    return f"{record['name']} · {record['created_at'][:16]} · {record['run_id'][:8]}"


def history_page():
    heading('SCENARIO ANALYSIS / LOCAL HISTORY','Compare Runs',
        'Reopen immutable saved plans or compare two scenarios. Viewing results never starts a solve.')
    try: store=RunStore(); records=store.list_runs('Venus Case Study')
    except RunStoreError as exc: st.error(str(exc)); return
    venus,general=st.tabs(['Venus Case Study Runs','General Plant Runs'])
    with venus:
        if not records:
            st.info('No saved Venus runs yet. Name and optimize an original or customized scenario to save your first plan.')
        else:
            order=st.selectbox('Sort saved runs',['Newest first','Name','Total Delivery Cost'])
            if order=='Name': records.sort(key=lambda r:r['name'].casefold())
            elif order=='Total Delivery Cost': records.sort(key=lambda r:r['results']['completion']['costs'].get('total_delivery_cost',float('inf')))
            rows=[]
            for r in records:
                c,t,_=unpack_results(r); demand=t['service'].demand_msu.sum()
                rows.append({'Run Name':r['name'],'Type':r['scenario_type'],
                    'Saved (Cairo)':pd.Timestamp(r['created_at']).tz_convert('Africa/Cairo').strftime('%Y-%m-%d %H:%M'),
                    'Service':f"{t['service'].served_msu.sum()/demand:.2%}" if demand else 'No demand',
                    'Total Delivery Cost USD':c['costs'].get('total_delivery_cost'),
                    'Solver status':'All stages optimal' if c['outcome']['success'] else ('Monetary optimal / secondary unproven' if c.get('monetary_optimal') else 'Feasible incumbent'),
                    'Run ID':r['run_id']})
            table(pd.DataFrame(rows))
            lookup={r['run_id']:r for r in records}
            selected=st.selectbox('Open a saved run',list(lookup),format_func=lambda k:run_label(lookup[k]))
            st.button('Open Saved Dashboard',icon=':material/history:',on_click=open_saved,args=(selected,),type='primary')
            st.divider()
            st.subheader('Compare two saved plans')
            ids=st.multiselect('Select exactly two runs',list(lookup),format_func=lambda k:run_label(lookup[k]),
                max_selections=2,key='history_comparison_selection')
            def compare():
                choose_pair(records,ids)
                st.session_state.comparison_ids=list(ids)
                st.session_state.screen='saved_comparison'
            st.button('Compare Selected Runs',disabled=len(ids)!=2,on_click=compare,type='primary')
    with general:
        st.markdown('### Your next planning workspace')
        st.info('No general plant runs yet. General plant optimization will be available in a future update.')
        st.caption('Venus history is kept separate. No general-purpose plant engine is enabled.')


def saved_dashboard():
    try: record=RunStore().get_run(st.session_state.selected_saved_id)
    except RunStoreError as exc: st.error(str(exc)); return
    dashboard(record=record)


def _rules(effective,names):
    from app.comparisons import LABELS
    return pd.DataFrame([{'Parameter':LABELS.get(k,k.replace('_',' ').title()),'Saved value':json.dumps(v,ensure_ascii=False)}
        for k,v in effective['rules'].items() if k in names])


def configured_parameters():
    try: record=RunStore().get_run(st.session_state.selected_saved_id)
    except RunStoreError as exc: st.error(str(exc)); return
    heading('SAVED RUN / READ-ONLY CONFIGURATION',record['name'],'Exact historical effective inputs. Editing is disabled.')
    st.button('Back to Saved Results',on_click=open_saved,args=(record['run_id'],),icon=':material/arrow_back:')
    effective=record['effective_inputs']
    sections=st.tabs(['Plant and Products','Manufacturing and Capacity','Materials and Procurement',
        'Workforce and Upgrades','Warehouse and Working Capital','Distribution and Demand','Review and Summary'])
    with sections[0]:
        st.json({k:effective[k] for k in ('months','products','families')})
        table(_rules(effective,{'weeks_per_month','qualification_days','qualification_allowed_months'}))
    with sections[1]:
        table(restore_frame(effective['lines']).reset_index())
        table(_rules(effective,{'upgraded_profiles','upgrade_permissions','changeover_days','qualification_days','qualification_allowed_months'}))
    with sections[2]:
        for name in ('bom','initial_materials','arrivals'):
            st.caption(name.replace('_',' ').title()); table(restore_frame(effective[name]).reset_index())
        st.json(effective['initial_fp'])
        table(_rules(effective,{'material_unit_prices','rm_usd_per_kg','pm_usd_per_ea','rm_moq_kg','pm_moq_ea','sea_lead_months',
            'rm_kg_per_pallet','pm_ea_per_pallet','pm_kg_per_1000_ea','disposal_usd_per_ton'}))
        st.caption('Product B RM/PM is explicitly balanced and ordered; opening quantities are adopted assumptions.' if effective['rules'].get('explicit_b_materials') else 'Historical Product B smooth replenishment: physical stock was unspecified.')
    with sections[3]:
        table(restore_frame(effective['lines'])[['operators']].reset_index())
        table(_rules(effective,{'operator_usd_per_month','hiring_usd_per_operator','dismissal_usd_per_operator',
            'training_months','upgrade_operators_per_line','training_output_fraction','flexible_workforce','upgrade_permissions','upgraded_profiles'}))
    with sections[4]:
        table(_rules(effective,{'warehouse_pallets','overflow_usd_per_pallet_month','overflow_block_pallets',
            'fp_holding_fraction_month','fp_pallets_per_msu','rm_kg_per_pallet','pm_ea_per_pallet'}))
        table(restore_frame(effective['bom'])[['fp_usd_per_msu']].reset_index())
    with sections[5]:
        table(restore_frame(effective['hubs']).reset_index()); table(restore_frame(effective['demand']))
        table(_rules(effective,{'truck_msu','dedicated_trucks_month','spot_surcharge_fraction'}))
    with sections[6]:
        st.json({k:v for k,v in record.items() if k not in ('results','effective_inputs','assumptions')})
        with st.expander('Every effective input, including all retained model rules'): st.json(effective)
        with st.expander('Assumptions saved with this run'): st.json(record.get('assumptions',{}))
    st.download_button('Download exact configured inputs',json.dumps(effective,indent=2),'historical_inputs.json','application/json')


def comparison_page():
    try:
        store=RunStore(); records=[store.get_run(i) for i in st.session_state.get('comparison_ids',[])]
        a,b=choose_pair(records,st.session_state.get('comparison_ids',[]))
    except (RunStoreError,ValueError) as exc: st.error(str(exc)); return
    heading('SAVED SCENARIOS / DECISION COMPARISON','Scenario A vs Scenario B',
        'Differences are B − A. Percentage changes use A as the reference; a zero baseline has no percentage.')
    from app.components.financial_cards import render as financial_cards
    for col,label,r in zip(st.columns(2),('Scenario A · Reference','Scenario B · Comparison'),(a,b)):
        with col:
            st.subheader(label); st.markdown('<div class="run-name">'+escape(r['name'])+'</div>',unsafe_allow_html=True)
            st.caption(f"{r['scenario_type']} · {r['created_at']} · {r['model_version']} · {r['financial_version']}")
            c=r['results']['completion']
            from src.shipment_policy import POLICIES, historical_policy
            policy=historical_policy(c,r['model_version'])
            st.caption('International Shipment Consolidation: '+(POLICIES[policy][0] if policy else 'Legacy / Unknown Policy'))
            st.write('International Shipments:',c.get('international_shipments','Not saved'), ' · Material Order Lines:',c.get('material_order_lines','Not saved'))
            st.caption('All stages optimal' if c['outcome']['success'] else c['outcome']['message'])
            if 'total_delivery_cost' in c['costs']: financial_cards(c['costs'],explicit_b=c.get('material_policy')=='explicit_abc_v7')
            else: st.info('Historical operating-only accounting. No Total Delivery Cost was saved.')
    for message in warnings(a,b): st.warning(message)
    shipment_rows=[]
    from src.shipment_policy import POLICIES,historical_policy
    for r in (a,b):
        c=r['results']['completion'];policy=historical_policy(c,r['model_version'])
        _,saved_tables,_=unpack_results(r)
        lines=int((saved_tables['material_orders'].quantity>1e-5).sum())
        stage=next((s for s in c['outcome']['stages'] if s['name']=='international_order_events'),{})
        shipment_rows.append(dict(scenario=r['name'],policy=POLICIES[policy][0] if policy else 'Legacy / Unknown Policy',
            international_shipments=c.get('international_shipments',lines if policy=='independent_materials' else None),
            material_order_lines=lines,termination=stage.get('termination'),lower_bound=stage.get('lower_bound'),
            relative_gap=stage.get('incumbent_gap',stage.get('relative_gap'))))
    st.subheader('Shipment counts and proof status')
    table(pd.DataFrame(shipment_rows))
    compatible=a['financial_version']==b['financial_version']
    financial=financial_comparison(a,b)
    changes=changed_inputs(a,b)
    st.subheader('What Changed Between These Runs?')
    if changes.empty: st.info('No effective input parameter differences. Run names and timestamps are metadata, not business inputs.')
    else: table(changes.assign(scenario_a=changes.scenario_a.map(str),scenario_b=changes.scenario_b.map(str)))
    tabs=st.tabs(['Financials','Demand & Service','Workforce','Manufacturing','Materials','Warehouse & Cash','Transportation'])
    def paired(name,keys,value,title,plot=False):
        frame=paired_table(a,b,name,keys,value)
        if frame.empty: st.info(title+': this field was not saved in both runs.'); return
        if not compatible and (name=='monthly_cost_breakdown' or 'usd' in value):
            frame[['difference','percentage_change']]=None
        st.caption(title)
        if plot and 'month' in frame and len(keys)==1:
            chart(frame.rename(columns={'scenario_a':'Scenario A','scenario_b':'Scenario B'}),'month',['Scenario A','Scenario B'],kind='line',title=title)
        table(frame)
    with tabs[0]:
        styled=financial.style.format({'scenario_a':'${:,.2f}','scenario_b':'${:,.2f}',
            'difference':'${:,.2f}','percentage_change':'{:+.2f}%'},na_rep='Not available')
        styled=styled.map(lambda v: 'color:#996313;font-weight:600' if pd.notna(v) and v>0 else
            ('color:#176785;font-weight:600' if pd.notna(v) and v<0 else ''),subset=['difference','percentage_change'])
        st.dataframe(styled,hide_index=True,width='stretch')
        st.caption('Amber indicates an increase; blue indicates a decrease. Direction alone does not establish an improvement.')
        st.caption('USD values retain full precision in downloads. Missing historical metrics stay unavailable. Percentage changes are not labelled savings.')
        paired('monthly_cost_breakdown',['month'],'total_modeled_cost_usd','Monthly total modeled cost · USD',True)
        comp=financial[financial.metric.isin(['Operating Expenses USD','Additional A materials USD','Additional C materials USD','B production-linked materials USD'])]
        chart(comp.rename(columns={'scenario_a':'Scenario A','scenario_b':'Scenario B'}),'metric',['Scenario A','Scenario B'],title='Annual saved cost composition · USD',barmode='group')
    with tabs[1]:
        demand=demand_comparison(a,b)
        chart(demand.rename(columns={'scenario_a':'Scenario A','scenario_b':'Scenario B'}),'month',['Scenario A','Scenario B'],kind='line',title='Input monthly demand · MSU'); table(demand)
        st.caption('Annual input demand: '+str(demand[['scenario_a','scenario_b','difference']].sum().to_dict()))
        with st.expander('Full input forecast by hub and family'): table(demand_comparison(a,b,('month','hub','family')))
        for keys in [('month',),('hub',),('family',)]:
            service=service_comparison(a,b,keys)
            if keys==('month',): chart(service.rename(columns={'service_fraction_a':'Scenario A','service_fraction_b':'Scenario B'}),'month',['Scenario A','Scenario B'],kind='line',title='Monthly customer service · fraction')
            table(service)
        ca,ta,_=unpack_results(a); cb,tb,_=unpack_results(b)
        annual=[]
        for label,frame in [('Demand MSU','demand_msu'),('Fulfilled MSU','served_msu'),('Unserved MSU','unserved_msu')]:
            annual.append((label,float(ta['service'][frame].sum()),float(tb['service'][frame].sum())))
        annual.append(('Annual service fraction',ta['service'].served_msu.sum()/ta['service'].demand_msu.sum() if ta['service'].demand_msu.sum() else None,
            tb['service'].served_msu.sum()/tb['service'].demand_msu.sum() if tb['service'].demand_msu.sum() else None))
        table(compare_values(annual))
    with tabs[2]:
        st.caption('INPUT assumptions are in the changed-parameters section and historical configuration view; decisions follow below.')
        for record,label in ((a,'Scenario A'),(b,'Scenario B')):
            st.write(label); table(unpack_results(record)[1]['staffing'])
        paired('productivity',['month'],'employed_operators','Monthly employed workforce',True)
        for value in ('hired_crew','training','dismissed_crew','additional_salary_usd','hiring_usd','dismissal_usd'):
            paired('staffing',['month','line'],value,value.replace('_',' ').title())
    with tabs[3]:
        paired('production',['month'],'msu','Monthly production · MSU',True)
        paired('production',['month','line','product'],'msu','Production by line and product')
        for value in ('capacity_msu','production_msu','qualification_days','changeover_days'):
            paired('line_capacity',['month','line'],value,value.replace('_',' ').title())
        paired('productivity',['month','line'],'capacity_utilization','Capacity utilization')
        for r,label in ((a,'Scenario A'),(b,'Scenario B')):
            st.write(label+' qualification / transition'); st.json(r['results']['transition'])
    with tabs[4]:
        for r,label in ((a,'Scenario A'),(b,'Scenario B')):
            st.write(label+' new orders / arrival months'); frame=unpack_results(r)[1]['material_orders']; table(frame[frame.order_event>.5])
        paired('material_balances',['month','product','material'],'ending','Ending material balances')
        paired('material_balances',['month','product','material'],'scrap','Material scrap')
        paired('material_orders',['order_month','product','material'],'quantity','Ordered material quantities')
        for v in ('a_material_cost_usd','c_material_cost_usd','b_material_cost_usd'):
            paired('monthly_cost_breakdown',['month'],v,v.replace('_',' ').title())
    with tabs[5]:
        paired('inventory',['month','product'],'msu','Ending FP inventory')
        for v in ('tracked_pallets','external_blocks','external_storage_usd'):
            paired('warehouse',['month'],v,v.replace('_',' ').title())
        paired('cash',['month'],'ending_fp_value_usd','Ending FP inventory value · USD')
        paired('monthly_cost_breakdown',['month'],'fp_holding_usd','Monthly working-capital expense · USD',True)
        for r,label in ((a,'Scenario A'),(b,'Scenario B')):
            warehouse=unpack_results(r)[1]['warehouse'].copy()
            if {'tracked_pallets','onsite_capacity','onsite_pallets'}<=set(warehouse):
                warehouse['onsite_utilization']=warehouse.onsite_pallets/warehouse.onsite_capacity.where(warehouse.onsite_capacity>0)
                warehouse['tracked_to_onsite_capacity']=warehouse.tracked_pallets/warehouse.onsite_capacity.where(warehouse.onsite_capacity>0)
                st.caption(label+' warehouse utilization (undefined for zero on-site capacity)')
                table(warehouse[['month','onsite_utilization','tracked_to_onsite_capacity']])
    with tabs[6]:
        for v in ('dedicated_trucks','spot_trucks'):
            paired('transport',['month','hub'],v,v.replace('_',' ').title())
        paired('service',['month','hub','family'],'served_msu','Regional shipments by family')
        for v in ('dedicated_transport_usd','spot_transport_usd'):
            paired('monthly_cost_breakdown',['month'],v,v.replace('_',' ').title())
        for r,label in ((a,'Scenario A'),(b,'Scenario B')):
            e=r['effective_inputs']; fleet=e['rules']['dedicated_trucks_month']; _,t,_=unpack_results(r)
            st.caption(label+' dedicated fleet utilization (trucks / configured fleet)')
            f=t['transport'].groupby('month',as_index=False).dedicated_trucks.sum()
            f['fleet_utilization']=f.dedicated_trucks/fleet if fleet else None
            table(f)
    with st.expander('Full read-only input snapshots · Scenario A and Scenario B'):
        for r,label in ((a,'Scenario A'),(b,'Scenario B')): st.write(label); st.json(r['effective_inputs'])
    st.download_button('Financial comparison CSV',financial.to_csv(index=False),'financial_comparison.csv','text/csv')
    st.download_button('Changed parameters CSV',changes.to_csv(index=False),'changed_parameters.csv','text/csv')
    st.download_button('Complete comparison snapshots JSON',json.dumps({'scenario_a':a,'scenario_b':b},indent=2),'comparison.json','application/json')
