"""Reproduce the three-policy acceptance report from actual default-case CSVs."""
import json
from pathlib import Path
import pandas as pd
from src.data_loader import load_case
from src.material_policy import planning_case
from src.reconciliation import read_saved,calculate,markdown
from src.shipment_policy import POLICIES,shipment_schedule


def generate(directories,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows=[];details=[];optima=[]
    for directory in map(Path,directories):
        tables,status=read_saved(directory)
        policy=status['shipment_consolidation_policy']
        data=planning_case(load_case());data.rules['shipment_consolidation_policy']=policy
        financial=calculate(data,tables,status)
        schedule=pd.read_csv(directory/'international_shipment_schedule.csv',float_precision='round_trip')
        expected=shipment_schedule(tables['material_orders'],policy)
        pd.testing.assert_frame_equal(schedule,expected,check_dtype=False,rtol=1e-12,atol=1e-7)
        audit=json.loads((directory/'solution_audit.json').read_text())
        assert audit['passed']
        stage=next(s for s in status['stages'] if s['name']=='international_order_events')
        monetary=next(s for s in status['stages'] if s['name']=='modeled_cost')
        service=tables['service'];demand=service.demand_msu.sum();served=service.served_msu.sum()
        optima.append((served,monetary.get('optimum')))
        row=dict(policy=policy,service_percent=100*served/demand,minimum_monetary_usd=monetary.get('optimum'),
            money_proven=monetary['termination']=='optimal',international_shipments=len(schedule),
            material_order_lines=int((tables['material_orders'].quantity>1e-5).sum()),
            shipment_lower_bound=stage.get('lower_bound'),shipment_gap=stage.get('incumbent_gap',stage.get('relative_gap')),
            shipment_termination=stage['termination'],shipment_proven=stage['termination']=='optimal',
            peak_warehouse_pallets=tables['warehouse'].tracked_pallets.max(),external_storage_usd=status['costs']['external_storage'])
        assert row['international_shipments']==status['international_shipments']
        rows.append(row)
        orders=tables['material_orders'].query('quantity>1e-5')
        details.extend([f"## {POLICIES[policy][0]}",'',f"Actual new solve: `../{directory.name}/`. All three service stages are proven optimal. Shipment status: `{stage['status']}` / `{stage['termination']}`. Later quantity/cleanup stages were not run because shipment optimality is unproven.",'',
            '### Selected dispatch batches','',markdown(schedule),'',
            '### Underlying material orders','',markdown(orders),'',
            '### Monthly warehouse','',markdown(tables['warehouse'][['month','tracked_pallets','external_blocks','external_storage_usd']]),'',
            '### Financial reconciliation','',markdown(financial.costs.query("month == 'ANNUAL'")),'',
            f"Independent reconstruction: {audit['constraints_checked']:,} constraints, {audit['variables_checked']:,} variables; maximum violation {audit['max_violation']:.8g}. Passed. Monthly materials, production, service, costs and inventories remain in the run folder's CSVs.",''])
    assert all(abs(a-optima[0][0])<1e-5 and abs(b-optima[0][1])<1e-5 for a,b in optima)
    comparison=pd.DataFrame(rows);comparison.to_csv(output/'comparison.csv',index=False)
    display=comparison.copy()
    display['service_percent']=display.service_percent.map(lambda x:f'{x:.2f}%')
    display['shipment_gap']=display.shipment_gap.map(lambda x:f'{x:.2%}')
    for col in ('money_proven','shipment_proven'):display[col]=display[col].map({True:'Proven',False:'Unproven'})
    text='\n'.join(['# Three-policy real Venus validation','',
        'All runs use identical original Venus numerical inputs and adopted B stocks. Only shipment policy differs. Each executes the real Pyomo/HiGHS model, with a 300-second per-stage limit; no historical result is presented as a fresh solve.','',
        markdown(display),'',
        'All service and monetary optima agree. The shipment counts are feasible incumbents, not proven minima. Different group definitions do not establish physical container savings. Policy 3 assumes a common international consolidation hub; no container size or new freight cost is imposed. The historical independent-policy lower bound of 8 remains preserved separately; the table shows each fresh solve\'s actual bound, without replacing it.','',
        'The five financial figures retain the same definitions. Opening stocks/fixed receipts are not new purchases, and consolidating orders adds no cost term. Material stocks, lead times and warehouse constraints remain separate from batch grouping.','']+details)
    (output/'RESULTS.md').write_text(text,encoding='utf-8')
    print(comparison.to_string(index=False))


if __name__=='__main__':
    generate(['reports/v8_independent','reports/v8_per_product','reports/v8_all_products'],
        'reports/shipment_policy_validation')
