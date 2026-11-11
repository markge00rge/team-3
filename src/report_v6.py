"""Current expanded monetary definition; historical V5 reports stay immutable."""
import json
from pathlib import Path
import pandas as pd
from src.data_loader import ROOT
from src.reconciliation import read_saved,calculate,markdown
from src.kpis import calculate_kpis


def generate(data,directory):
    directory=Path(directory)
    tables,status=read_saved(directory)
    explicit=status.get('material_policy')=='explicit_abc_v7'
    if explicit:
        from src.material_policy import planning_case
        data=planning_case(data,explicit=True)
    for name in ('daily_schedule','line_capacity'):
        tables[name]=pd.read_csv(directory/f'{name}.csv',float_precision='round_trip')
    financial=calculate(data,tables,status)
    outputs=calculate_kpis(data,tables,financial)
    outputs.update(monthly_cost_breakdown=financial.costs,monthly_production_inventory=financial.monthly,
        monthly_inventory_by_product=financial.products)
    columns=['month','operating_expenses_usd','a_material_cost_usd','c_material_cost_usd','b_material_cost_usd','total_delivery_cost_usd']
    outputs['financial_five_kpis']=financial.costs[columns]
    for name,frame in outputs.items(): frame.to_csv(directory/f'{name}.csv',index=False)
    baseline=json.loads((ROOT/'reports/v5/solve_status.json').read_text())
    transition=json.loads((directory/'transition_ide.json').read_text())
    stages=pd.DataFrame(status['stages'])
    version='V7' if explicit else 'V6'
    if 'shipment_consolidation_policy' in status:version='V8'
    text='\n'.join([f'# {version}: flexible crews and complete material financial objective','',
        f"All-stage optimality: **{status['success']}**. Minimum proven monetary value: {status.get('minimum_cost')}. Actual reported plan: ${status['costs']['total_delivery_cost']:,.2f}.",'',
        '## Solver status and bounds','',markdown(stages),'',
        '## Five financial figures (USD)','',markdown(outputs['financial_five_kpis']),'',
        ('All A/B/C additional materials are charged at order placement; consumption, receipts and FP shipments do not add purchase expense. Opening stocks and the three fixed receipts are excluded. Full IDE is reported with exact purchased-A overlap adjustment. B stock assumptions are RM 200,000 kg / PM 750,000 EA, adopted following clarification, not numerical stocks in the source documents.' if explicit else
         'Operating expenses include all original categories and full IDE, less the exact overlap with new A procurement. Full IDE/disposal is not hidden. A/C purchases are charged at order placement, B at actual production. Opening material and fixed receipts are not new purchases. Opening B FP generates no B material consumption.'),'',
        '## Full monthly reconciliation','',markdown(financial.costs),'',
        '## Historical financial definitions','',
        f"V5 operating-only objective was ${baseline['costs']['total_modeled']:,.2f}; it excluded additional A/C purchasing and B consumption. It is not the target or directly comparable total delivery cost. Current operating-only subtotal with full IDE is ${status['costs']['operating_full_ide']:,.2f}; the reconciled subtotal is ${status['costs']['operating_expenses']:,.2f}.",'',
        '## Transition and full IDE','', '```json',json.dumps(transition,indent=2),'```','',
        '## Workforce plan','',markdown(tables['staffing']),'',
        '## Monthly production and inventory','',markdown(financial.monthly),'',
        '## New orders (placement and receipt)','',markdown(tables['material_orders'].query('order_event > .5')),'',
        '## Material balances','',markdown(tables['material_balances']),'',
        '## Fixed incoming shipments (not new procurement)','',markdown(pd.read_csv(directory/'fixed_receipts.csv')),'',
        '## Product B finished inventory and holding','',markdown(financial.products.query("product == 'B'")),'',
        '## Warehouse','',markdown(tables['warehouse']),'',
        '## Transportation','',markdown(tables['transport']),'',
        '## Assumptions','',
        'Additional-crew dismissal is optional; default severance is $0/operator, a new assumption. Base 70 employees stay permanent. Rehiring pays fees and retrains from zero. Additional material costs are a new requested monetary policy. A material provenance uses legacy-first consumption: all original opening/fixed A stocks arrive before new A receipts. Newly purchased A scrap equals min(total A scrap, additional A receipts); its value is subtracted once from operating expense, while full IDE is retained for case accounting. Disposal is never subtracted.','',
        ('All ABC materials and their month-end space are now tracked. Only A is scrapped. Packaging ages, intramonth warehouse peaks and unspecified overtime/headcount rules remain limitations. See V7_SCOPE.md.' if explicit else
         'All manufacturing/material/service rules and the 28-day calendar remain. Packaging ages, B physical stock/space, intramonth warehouse peaks and unspecified overtime/headcount rules remain limitations. See V6_SCOPE.md.'),''])
    if explicit:
        balance=tables['material_balances'].query("product == 'B'")
        balance.to_csv(directory/'b_material_balances.csv',index=False)
        tables['material_orders'].query("product == 'B'").to_csv(directory/'b_material_orders.csv',index=False)
        opening=[]
        for p in data.products:
            opening.append(dict(product=p,category='FP',quantity=data.initial_fp[p],pallets=data.initial_fp[p]*data.rules['fp_pallets_per_msu']))
        for r in data.initial_materials.itertuples():
            opening.append(dict(product=r.product,category=r.material,quantity=r.quantity,pallets=r.quantity/data.rules['rm_kg_per_pallet' if r.material=='RM' else 'pm_ea_per_pallet']))
        pd.DataFrame(opening).to_csv(directory/'opening_warehouse.csv',index=False)
        text+='\n## B material balances\n\n'+markdown(balance)+'\n\n## Opening tracked warehouse footprint\n\n'+markdown(pd.DataFrame(opening))+'\n'
        text+='\n## Product B orders, placement costs and receipt months\n\n'+markdown(tables['material_orders'].query("product == 'B'"))+'\n'
        previous_path=ROOT/'reports/app_runs/v6_original_resumed/solve_status.json'
        if previous_path.exists():
            previous=json.loads(previous_path.read_text())['costs']
            comparison=pd.DataFrame([dict(category=k,historical_v6=previous.get(k),current_v7=status['costs'].get(k))
                for k in ('operating_expenses','a_materials','c_materials','b_materials','total_delivery_cost')])
            comparison.to_csv(directory/'historical_v6_financial_definitions.csv',index=False)
            text+='\n## Historical V6 comparison — incompatible B accounting definitions\n\n'+markdown(comparison)+'\n\nV6 charged B production consumption. V7 charges only additional B orders and adopts prepaid opening B stock. This difference is not a like-for-like operating saving. Lot rounding can create paid terminal inventory. Original historical results are unchanged.\n'
        text+='\n## Monthly service by hub and family\n\n'+markdown(tables['service'])+'\n'
    if 'shipment_consolidation_policy' in status:
        from src.shipment_policy import POLICIES
        policy=status['shipment_consolidation_policy']
        text+='\n## International shipment consolidation\n\n'+POLICIES[policy][0]+'\n\n'
        text+=f"Dispatch batches: {status['international_shipments']}; material order lines: {status['material_order_lines']}. These are dispatch occasions, not physical containers; no freight fee or container capacity is imposed. Policy 3 assumes a common consolidation hub.\n\n"
        text+=markdown(pd.read_csv(directory/'international_shipment_schedule.csv',float_precision='round_trip'))+'\n'
    (directory/'ANALYSIS.md').write_text(text,encoding='utf-8')
    (directory/'FINANCIAL_RECONCILIATION.md').write_text(text,encoding='utf-8')
    marker = f'=== {version} FINANCIAL RECONCILIATION (generated) ==='
    summary = directory/'summary.txt'
    original = summary.read_text(encoding='utf-8').split(marker)[0].rstrip()
    summary.write_text(original+'\n\n'+marker+'\n'+markdown(financial.costs)+'\n',encoding='utf-8')
    return outputs
