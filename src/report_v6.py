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
    text='\n'.join(['# V6: flexible crews and complete material financial objective','',
        f"All-stage optimality: **{status['success']}**. Minimum proven monetary value: {status.get('minimum_cost')}. Actual reported plan: ${status['costs']['total_delivery_cost']:,.2f}.",'',
        '## Solver status and bounds','',markdown(stages),'',
        '## Five financial figures (USD)','',markdown(outputs['financial_five_kpis']),'',
        'Operating expenses include all original categories and full IDE, less the exact overlap with new A procurement. Full IDE/disposal is not hidden. A/C purchases are charged at order placement, B at actual production. Opening material and fixed receipts are not new purchases. Opening B FP generates no B material consumption.','',
        '## Full monthly reconciliation','',markdown(financial.costs),'',
        '## Historical financial definitions','',
        f"V5 operating-only objective was ${baseline['costs']['total_modeled']:,.2f}; it excluded additional A/C purchasing and B consumption. It is not the target or directly comparable total delivery cost. Current operating-only subtotal with full IDE is ${status['costs']['operating_full_ide']:,.2f}; the reconciled subtotal is ${status['costs']['operating_expenses']:,.2f}.",'',
        '## Transition and full IDE','', '```json',json.dumps(transition,indent=2),'```','',
        '## Workforce plan','',markdown(tables['staffing']),'',
        '## Monthly production and inventory','',markdown(financial.monthly),'',
        '## New orders (placement and receipt)','',markdown(tables['material_orders'].query('order_event > .5')),'',
        '## Material balances','',markdown(tables['material_balances']),'',
        '## Warehouse','',markdown(tables['warehouse']),'',
        '## Transportation','',markdown(tables['transport']),'',
        '## Assumptions','',
        'Additional-crew dismissal is optional; default severance is $0/operator, a new assumption. Base 70 employees stay permanent. Rehiring pays fees and retrains from zero. Additional material costs are a new requested monetary policy. A material provenance uses legacy-first consumption: all original opening/fixed A stocks arrive before new A receipts. Newly purchased A scrap equals min(total A scrap, additional A receipts); its value is subtracted once from operating expense, while full IDE is retained for case accounting. Disposal is never subtracted.','',
        'All manufacturing/material/service rules and the 28-day calendar remain. Packaging ages, B physical stock/space, intramonth warehouse peaks and unspecified overtime/headcount rules remain limitations. See V6_SCOPE.md.',''])
    (directory/'ANALYSIS.md').write_text(text,encoding='utf-8')
    (directory/'FINANCIAL_RECONCILIATION.md').write_text(text,encoding='utf-8')
    marker = '=== V6 FINANCIAL RECONCILIATION (generated) ==='
    summary = directory/'summary.txt'
    original = summary.read_text(encoding='utf-8').split(marker)[0].rstrip()
    summary.write_text(original+'\n\n'+marker+'\n'+markdown(financial.costs)+'\n',encoding='utf-8')
    return outputs
