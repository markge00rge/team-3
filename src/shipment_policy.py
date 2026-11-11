"""Exact dispatch-batch groups; physical material decisions remain separate."""
import pandas as pd
import pyomo.environ as pyo

POLICIES={
 'independent_materials':('Independent RM/PM Shipments',"Each product's RM and PM orders count separately."),
 'per_product':('Consolidate Within Each Product','RM and PM for one product may share a same-month dispatch batch.'),
 'all_products':('Consolidate All Products','All materials may share a same-month batch through an assumed common consolidation hub.')}


def group_id(policy,p,k):
    if not isinstance(policy,str) or policy not in POLICIES:raise ValueError('Unsupported shipment consolidation policy')
    return f'{p}_{k}' if policy=='independent_materials' else p if policy=='per_product' else 'ALL'


def add_shipment_policy(m,data):
    policy=data.rules.get('shipment_consolidation_policy','independent_materials')
    if not isinstance(policy,str) or policy not in POLICIES:raise ValueError('Unsupported shipment consolidation policy')
    m.shipment_consolidation_policy=policy
    # Independent policy keeps the legacy formulation exactly, without extra binaries.
    if policy=='independent_materials':
        m.international_shipments=pyo.Expression(expr=m.additional_order_events)
        return
    groups={}
    for p in m.material_products:
        for k in m.materials:groups.setdefault(group_id(policy,p,k),[]).append((p,k))
    m.shipment_groups=groups
    m.shipment_batch=pyo.Var(list(groups),m.months,domain=pyo.Binary)
    m.shipment_group_links=pyo.ConstraintList()
    for g,members in groups.items():
        for t in m.months:
            for p,k in members:m.shipment_group_links.add(m.shipment_batch[g,t]>=m.order_event[p,k,t])
            m.shipment_group_links.add(m.shipment_batch[g,t]<=sum(m.order_event[p,k,t] for p,k in members))
    m.international_shipments=pyo.Expression(expr=sum(m.shipment_batch.values()))


def shipment_schedule(orders,policy,*,rm_kg_per_pallet=1000,pm_ea_per_pallet=5000):
    """Exact aggregation of selected orders, not a procurement heuristic."""
    columns=['batch_id','policy','dispatch_month','arrival_month','products','materials',
        'individual_quantities','rm_pallets','pm_pallets','material_pallets','purchase_cost_usd','material_order_lines']
    positive=orders[orders.quantity>1e-5].copy()
    if positive.empty:return pd.DataFrame(columns=columns)
    positive['group']=[group_id(policy,r.product,r.material) for r in positive.itertuples()]
    rows=[]
    for (g,t),part in positive.groupby(['group','order_month'],sort=True):
        if part.arrival_month.nunique()!=1:raise ValueError('Consolidated orders have incompatible arrival schedules')
        rm=part[part.material=='RM'].quantity.sum()/rm_kg_per_pallet
        pm=part[part.material=='PM'].quantity.sum()/pm_ea_per_pallet
        rows.append(dict(batch_id=f'{g}_{t}',policy=policy,dispatch_month=t,arrival_month=part.arrival_month.iloc[0],
            products=', '.join(sorted(part['product'].unique())),materials=', '.join(f'{r.product} {r.material}' for r in part.itertuples()),
            individual_quantities='; '.join(f'{r.product} {r.material}: {r.quantity:.15g}' for r in part.itertuples()),
            rm_pallets=rm,pm_pallets=pm,material_pallets=rm+pm,
            purchase_cost_usd=part.purchase_expense_usd.sum() if 'purchase_expense_usd' in part else None,
            material_order_lines=len(part)))
    return pd.DataFrame(rows,columns=columns)


def historical_policy(completion,model_version=''):
    policy=completion.get('shipment_consolidation_policy')
    if policy in POLICIES:return policy
    if any(v in model_version for v in ('Venus V4','Venus V5','Venus V6','Venus V7')):return 'independent_materials'
    return None
