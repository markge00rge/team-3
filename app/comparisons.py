"""Pure comparisons of saved inputs/results. No defaults, loader or solver."""
import math
import numbers
import pandas as pd
from app.run_store import restore_frame, unpack_results


def difference(a,b):
    if isinstance(a,numbers.Real) and isinstance(b,numbers.Real) and not isinstance(a,bool) and not isinstance(b,bool):
        return b-a
    return None


def percentage(a,b):
    delta=difference(a,b)
    return delta/a*100 if delta is not None and a!=0 else None


def choose_pair(records,ids):
    if len(ids)!=2 or len(set(ids))!=2: raise ValueError('Select exactly two distinct runs.')
    chosen=[next((r for r in records if r['run_id']==i),None) for i in ids]
    if any(r is None for r in chosen): raise ValueError('Saved run not found in this category.')
    if chosen[0]['category']!=chosen[1]['category']: raise ValueError('Run categories must match.')
    return chosen


LABELS={
    'rules':'Planning rules','lines':'Manufacturing line','bom':'Product BOM / valuation',
    'demand':'Demand MSU','initial_fp':'Opening FP MSU','initial_materials':'Opening materials',
    'arrivals':'Fixed incoming shipment','hubs':'Distribution hub','months':'Planning horizon',
    'material_unit_prices':'Material unit price','operator_usd_per_month':'Salary $/operator/month',
    'hiring_usd_per_operator':'Hiring fee $/operator','dismissal_usd_per_operator':'Dismissal fee $/operator',
    'training_months':'Full training months','upgrade_operators_per_line':'Additional crew size',
    'flexible_workforce':'Allow crew dismissal / rehiring','upgrade_permissions':'Allow upgrade',
    'warehouse_pallets':'On-site warehouse pallets','overflow_usd_per_pallet_month':'3PL $/pallet/month',
    'overflow_block_pallets':'3PL booking block pallets','fp_holding_fraction_month':'Monthly FP holding rate',
    'rm_moq_kg':'RM order increment kg','pm_moq_ea':'PM order increment EA',
    'sea_lead_months':'Sea-freight lead months','msu_per_day':'Daily capacity MSU',
    'rm_kg_per_msu':'RM kg/MSU','pm_ea_per_msu':'PM EA/MSU','fp_usd_per_msu':'FP valuation $/MSU',
    'dedicated_trucks_month':'Monthly dedicated fleet','truck_msu':'Truck capacity MSU',
    'spot_surcharge_fraction':'Spot-market surcharge','truck_usd':'Dedicated $/truck',
    'unserved_usd_per_msu':'Unserved penalty $/MSU','upgraded_profiles':'Upgraded schedule',
    'profile':'Base schedule','operators':'Permanent operators','priority':'Service priority',
    'qualification_days':'Qualification shutdown days','qualification_allowed_months':'Allowed qualification months'}
LABELS.update({'AC':'A/C combined','RM':'Raw materials','PM':'Packaging materials'})


def input_flat(record):
    output={}
    def walk(value,path):
        if isinstance(value,dict) and {'columns','data'}<=set(value):
            frame=restore_frame(value)
            for index,row in frame.iterrows():
                if path=='demand':
                    output[f'demand.{row.month}.{row.hub}.{row.family}']=row.msu
                elif path=='initial_materials':
                    output[f'{path}.{row.product}.{row.material}']=row.quantity
                elif path=='arrivals':
                    output[f'{path}.{row.product}.{row.material}.{row.date}']=row.quantity
                else:
                    for k,v in row.items(): walk(v,f'{path}.{index}.{k}')
        elif isinstance(value,dict):
            for k,v in value.items(): walk(v,f'{path}.{k}' if path else k)
        else: output[path]=value
    for k,v in record['effective_inputs'].items(): walk(v,k)
    return output


def changed_inputs(a,b):
    aa,bb=input_flat(a),input_flat(b)
    labels=LABELS.copy()
    hubs=restore_frame(a['effective_inputs']['hubs'])
    labels.update({str(index):str(row['name']) for index,row in hubs.iterrows()})
    rows=[]
    for key in sorted(set(aa)|set(bb)):
        av,bv=aa.get(key),bb.get(key)
        if av==bv: continue
        label=' / '.join(labels.get(part,part.replace('_',' ').capitalize()) for part in key.split('.'))
        rows.append(dict(parameter=label,scenario_a=av,scenario_b=bv,difference=difference(av,bv)))
    return pd.DataFrame(rows,columns=['parameter','scenario_a','scenario_b','difference'])


def compare_values(rows,compatible=True):
    return pd.DataFrame([dict(metric=label,scenario_a=a,scenario_b=b,
        difference=difference(a,b) if compatible else None,
        percentage_change=percentage(a,b) if compatible else None) for label,a,b in rows])


def financial_comparison(a,b):
    ca,cb=a['results']['completion']['costs'],b['results']['completion']['costs']
    labels={'operating_expenses':'Operating Expenses USD','a_materials':'Additional A materials USD',
        'c_materials':'Additional C materials USD','b_materials':'B production-linked materials USD',
        'total_delivery_cost':'Total Delivery Cost USD','ide':'Full IDE USD','ide_overlap_adjustment':'IDE overlap adjustment USD',
        'transportation':'Transportation USD','external_storage':'External warehouse USD','service_failure':'Service penalties USD'}
    rows=[(label,ca.get(k),cb.get(k)) for k,label in labels.items()]
    _,ta,_=unpack_results(a);_,tb,_=unpack_results(b)
    for column,label in [('base_salaries_usd','Base salaries USD'),('new_crew_salaries_usd','Additional salaries USD'),
        ('hiring_fees_usd','Hiring fees USD'),('dismissal_expense_usd','Dismissal expenses USD'),
        ('fp_holding_usd','FP holding USD'),('dedicated_transport_usd','Dedicated transport USD'),
        ('spot_transport_usd','Spot transport USD')]:
        vals=[]
        for tables in (ta,tb):
            frame=tables.get('monthly_cost_breakdown',pd.DataFrame())
            vals.append(float(frame.query("month != 'ANNUAL'")[column].sum()) if column in frame else None)
        rows.append((label,*vals))
    return compare_values(rows,a['financial_version']==b['financial_version'])


def paired_table(a,b,name,keys,value):
    _,ta,_=unpack_results(a);_,tb,_=unpack_results(b)
    if name not in ta or name not in tb or value not in ta[name] or value not in tb[name]: return pd.DataFrame()
    frames=[]
    for tables,label in ((ta,'scenario_a'),(tb,'scenario_b')):
        frame=tables[name]
        if 'month' in frame: frame=frame[frame.month!='ANNUAL']
        frames.append(frame.groupby(keys,dropna=False)[value].sum().rename(label))
    out=pd.concat(frames,axis=1).reset_index()
    # Missing historical observations stay unavailable, never inferred as zero.
    out['difference']=out.scenario_b-out.scenario_a
    out['percentage_change']=[percentage(x,y) if pd.notna(x) and pd.notna(y) else None for x,y in zip(out.scenario_a,out.scenario_b)]
    return out.sort_values(keys).reset_index(drop=True)


def demand_comparison(a,b,keys=('month',)):
    frames=[restore_frame(r['effective_inputs']['demand']).groupby(list(keys)).msu.sum().rename(label)
        for r,label in ((a,'scenario_a'),(b,'scenario_b'))]
    out=pd.concat(frames,axis=1).reset_index()
    out['difference']=out.scenario_b-out.scenario_a
    return out.sort_values(list(keys))


def service_comparison(a,b,keys=('month',)):
    frames=[]
    for record,label in ((a,'a'),(b,'b')):
        _,tables,_=unpack_results(record)
        frame=tables['service'].groupby(list(keys))[['demand_msu','served_msu','unserved_msu']].sum()
        frame['service_fraction']=frame.served_msu/frame.demand_msu.where(frame.demand_msu>0)
        frames.append(frame.add_suffix('_'+label))
    return pd.concat(frames,axis=1).reset_index().sort_values(list(keys))


def warnings(a,b):
    messages=[]
    if a['financial_version']!=b['financial_version']:
        messages.append('Financial definitions differ. Monetary differences and percentage changes are withheld; saved figures remain visible.')
    if a['model_version']!=b['model_version'] or a.get('engine_fingerprint')!=b.get('engine_fingerprint'):
        messages.append('These runs used different mathematical/code versions; interpret changes with that limitation.')
    _,ta,_=unpack_results(a);_,tb,_=unpack_results(b)
    totals=[(t['service'].demand_msu.sum(),t['service'].served_msu.sum()) for t in (ta,tb)]
    forecast=demand_comparison(a,b,('month','hub','family'))
    service=service_comparison(a,b,('month','hub','family'))
    demand_diff=forecast.difference.isna().any() or (forecast.difference.abs()>1e-5).any()
    service_diff=((service.served_msu_b-service.served_msu_a).abs()>1e-5).any()
    if demand_diff or service_diff or any(abs(x-y)>1e-5 for x,y in zip(totals[0],totals[1])):
        messages.append('Demand or service quantities differ. A lower cost is not automatically a saving or a better service result.')
    if not all(r['results']['completion'].get('monetary_optimal') for r in (a,b)):
        messages.append('At least one monetary minimum is unproven. These are saved feasible plans; inspect solver bounds.')
    return messages
