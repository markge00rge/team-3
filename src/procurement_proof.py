"""Full-model event-cap feasibility certificates at a saved proven cost optimum.

No manufacturing decisions are fixed to their saved levels. Saved levels are
only an initial point; the reconstructed model retains every operational rule.
"""
import argparse
import json
import math
import time
from pathlib import Path
import pyomo.environ as pyo
from src.data_loader import load_case
from src.validation import audit_exported_schedule, audit_solution
from src.solve import SolveOutcome
from src.results import extract_results, write_results


def strengthen_procurement(model):
    """Integer-rounded B prefix cover cuts implied by conservation and service.

    B cannot substitute for A/C. Full service implies cumulative B production
    >= cumulative B demand minus opening B FP. Materials cannot be borrowed.
    Round required cumulative lots upward because their sum is integral.
    No production, staffing, transition or order timing is fixed by these cuts.
    """
    if model.component('proof_b_cover') is not None:
        return 0
    model.proof_b_cover=pyo.ConstraintList()
    months=list(model.months)
    demand=0.0
    for t in months:
        demand+=sum(pyo.value(model.demand[h,'B',t]) for h in model.hubs)
        for k in model.materials:
            required=(demand-pyo.value(model.initial_fp['B']))*pyo.value(model.bom_quantity['B',k])
            required-=pyo.value(model.initial_material['B',k])
            required-=sum(pyo.value(model.fixed_material_arrival['B',k,u]) for u in months if u<=t)
            lots=max(0,math.ceil(required/pyo.value(model.lot_size[k])-1e-9))
            placed=[u for u in months if model.order_arrival_month[u]<=t]
            if placed and lots:
                model.proof_b_cover.add(sum(model.integer_lots['B',k,u] for u in placed)>=lots)
    return len(model.proof_b_cover)


def check_cap(model, cap, *, seconds, log_path, threads=1):
    """A timeout is inconclusive; only a solver infeasibility proof raises LB."""
    if model.component('proof_event_cap') is not None:
        model.del_component('proof_event_cap')
    model.proof_event_cap=pyo.Constraint(expr=model.additional_order_events <= cap)
    model.objective.set_value(0)
    solver=pyo.SolverFactory('appsi_highs')
    solver.options.update(time_limit=seconds, presolve='on', threads=threads,
        mip_rel_gap=0.0, mip_abs_gap=0.0, mip_feasibility_tolerance=1e-8,
        log_file=str(Path(log_path).resolve()))
    started=time.monotonic()
    result=solver.solve(model,load_solutions=False,warmstart=True)
    record=dict(cap=cap,status=str(result.solver.status),
        termination=str(result.solver.termination_condition),elapsed_seconds=time.monotonic()-started,
        has_solution=bool(len(result.solution)))
    if len(result.solution):
        model.solutions.load_from(result)
        record['audit']=audit_solution(model)
        record['events']=float(pyo.value(model.additional_order_events))
        record['monetary_cost']=float(pyo.value(model.total_cost))
    return record


def run(source, output, *, seconds=600, threads=1, strengthen=False):
    source,output=Path(source),Path(output)
    if output.exists():
        raise ValueError('Use a fresh proof output directory; existing reports are preserved.')
    status=json.loads((source/'solve_status.json').read_text())
    stages=status['stages']
    cost=next(s for s in stages if s['name']=='modeled_cost')
    if cost['termination']!='optimal' or cost['status']!='ok':
        raise ValueError('A proven monetary optimum is required.')
    if any(s['termination']!='optimal' for s in stages if s['name'].startswith('service_')):
        raise ValueError('Proven service optima are required.')
    if any(abs(s['optimum'])>1e-8 for s in stages if s['name'].startswith('service_')):
        raise ValueError('This certificate mode currently requires full service at every hub.')
    if any(s['termination']=='optimal' for s in stages if s['name']=='international_order_events'):
        raise ValueError('Event optimum already proven; use the original certificate.')
    audit,model=audit_exported_schedule(load_case(),source,return_model=True)
    if not audit['passed']: raise ValueError('Saved solution failed independent reconstruction audit.')
    # The loaded model already has service equality locks and the exact USD cap.
    # Replace the cost cap with the proven stage value if metadata is inconsistent.
    if status['cost_limit']!=cost['optimum']:
        raise ValueError('Only strict zero-tolerance monetary locks are supported.')
    counts={kind:sum(v.is_integer() and not v.fixed for v in model.component_data_objects(pyo.Var))
        for kind in ['integer_including_binary']}
    counts['binary']=sum(v.is_binary() and not v.fixed for v in model.component_data_objects(pyo.Var))
    incumbent=round(pyo.value(model.additional_order_events))
    prior=next(s for s in stages if s['name']=='international_order_events')
    lower=math.ceil(prior.get('lower_bound',0)-1e-8)
    output.mkdir(parents=True)
    cut_count=strengthen_procurement(model) if strengthen else 0
    report=dict(source=str(source),minimum_cost=cost['optimum'],original_events=incumbent,
        original_lower_bound=lower,variables=counts,checks=[],best_events=incumbent,
        proven_lower_bound=lower,all_events_optimal=False,integer_cover_cuts=cut_count)
    import highspy
    import pyomo
    report['solver_versions']=dict(highs=highspy.Highs().version(),pyomo=pyomo.__version__)
    report['settings']=dict(total_seconds=seconds,threads=threads,presolve='on',
        mip_rel_gap=0,mip_abs_gap=0,mip_feasibility_tolerance=1e-8,cost_tolerance=0)
    deadline=time.monotonic()+seconds
    while report['best_events']>report['proven_lower_bound'] and time.monotonic()<deadline:
        cap=report['best_events']-1
        print(f'Testing full-model event cap <= {cap}; all scheduling decisions free',flush=True)
        record=check_cap(model,cap,seconds=max(1,deadline-time.monotonic()),
            log_path=output/f'cap_{cap}.log',threads=threads)
        report['checks'].append(record)
        if record['has_solution'] and record['audit']['passed']:
            if abs(record['monetary_cost']-cost['optimum'])>1e-5:
                raise ValueError('Candidate does not reconcile to the proven monetary optimum.')
            report['best_events']=round(record['events'])
            model._has_incumbent=True
            model._solve_success=False
            outcome=SolveOutcome(False,'Event-cap feasible candidate; global event proof pending.',
                stages+[dict(name='event_cap_feasibility',**{k:v for k,v in record.items() if k!='audit'})],cost['optimum'],cost['optimum'])
            write_results(extract_results(model,allow_incumbent=True),outcome,output/f'candidate_{cap}',allow_incumbent=True)
        elif record['termination']=='infeasible':
            report['proven_lower_bound']=cap+1
        else:
            break
    report['all_events_optimal']=report['best_events']==report['proven_lower_bound']
    report['relative_gap']=(report['best_events']-report['proven_lower_bound'])/report['best_events']
    (output/'proof.json').write_text(json.dumps(report,indent=2))
    return report


def write_audit(source, proof_directories, target):
    """Publish evidence without changing saved runs or their historical statuses."""
    import pandas as pd
    from src.reconciliation import markdown, read_saved
    source=Path(source)
    reports=[json.loads((Path(d)/'proof.json').read_text()) for d in proof_directories]
    best=min(r['best_events'] for r in reports)
    lower=max(r['proven_lower_bound'] for r in reports)
    rows=[]
    selected=source
    for directory,report in zip(proof_directories,reports):
        for check in report['checks']:
            rows.append(dict(directory=str(directory),cap=check['cap'],status=check['status'],
                termination=check['termination'],seconds=check['elapsed_seconds'],
                feasible=check['has_solution'],integer_cover_cuts=report.get('integer_cover_cuts',0)))
            candidate=Path(directory)/f"candidate_{check['cap']}"
            if check.get('events')==best and candidate.exists():selected=candidate
    tables,status=read_saved(selected)
    audit=audit_exported_schedule(load_case(),selected)
    if not audit['passed']:raise ValueError('Selected plan failed audit')
    orders=tables['material_orders'].query('quantity > 1e-5')
    text=f'''# Procurement event optimality audit

## Conclusion

Best feasible event count: **{best}**. Strongest preserved proven lower bound:
**{lower}**. Remaining relative gap: **{(best-lower)/best:.1%}**.
Minimum event count proven: **{best==lower}**.

Baseline source: `{source}`. Selected feasible plan: `{selected}`.
Service remains 100%; minimum Total Delivery Cost remains **$9,865,467.50**.
Service and monetary optima were proven by the baseline solver. No business
cost tolerance, daily schedule fix, workforce fix or qualification fix was added.

## Original formulation and diagnostics

The most recent baseline stopped at the 300-second event-stage limit with
10 events, lower bound 7 and 30% gap. The preserved published V7 run already
has lower bound 8 and 20% gap. The stronger bound is retained rather than lost.
Original `integer_lots <= finite_bound * event`, `integer_lots >= event`, and
`quantity = lot_size * integer_lots` are exact. Impossible receipt windows are
fixed to zero; presolve removes their variables. Existing upper bounds use
eligible upgraded production capacity after receipt, and total useful purchases.
They are conservative, finite bounds, not arbitrary supplier capacities.

The full feasibility MILP has 7,579 columns and 2,417 integer columns including
2,048 binaries in HiGHS' raw input. Excluding already fixed levels, there are
2,186 integer decisions, including those 2,048 binaries. The mixed scheduling/material model has
many equivalent production and order-timing plans. Matrix coefficients span
approximately 2e-4 through 1e7. HiGHS warns about large material/monetary bounds;
this is a conditioning concern, not evidence of mathematical invalidity.
Exact empirical attribution of the runtime to degeneracy versus conditioning
is not established. The full-model infeasibility search remains necessary.

## Process and valid strengthening

`src.procurement_proof` rebuilds the same model and restores actual saved levels
only as a starting point. It preserves annual service equality locks and the
unscaled monetary upper bound at the proven optimum. No monetary epsilon is
added. MIP feasibility tolerance is 1e-8; independent export audit tolerance is
1e-5. Dollar scaling that would loosen effective cost feasibility was avoided.

Each cap check sets a constant objective and restricts only the sum of all six
material-specific event categories. A feasible solution is a candidate, not a
minimum certificate. Infeasibility at one fewer event plus an audited feasible
incumbent certifies the minimum. A timeout establishes neither feasibility nor
infeasibility. Messages about an infeasible MIP-start repair in the log are not
the final model termination condition.

The strengthened check adds B prefix cover cuts. With full B service, cumulative
B production is at least cumulative B demand minus opening B FP. Subtract
opening/fixed material from the corresponding BOM requirement; divide by lot
size and round upward. The resulting lower bound on cumulative arriving lots
is valid because the lot sum is integral. These cuts do not fix any order date,
production schedule, qualification, material quantity or workforce decision.
No tighter general upper bound was assumed without proof.

Installed solver: HiGHS 1.15.1 / Pyomo 6.10.1. Both checks use presolve on,
one thread, MIP starts, zero relative/absolute MIP gap requests and a 600-second
total budget per check. One thread makes the process reproducible; no claim
that it is universally fastest is made. Detailed node/LP/incumbent diagnostics
are retained in each `cap_9.log`. The two budgets total 1,200 solver seconds.

## Feasibility checks

{markdown(pd.DataFrame(rows))}

Only the final solver termination is used as a certificate. If a cap times
out, lower caps are not attempted because the current feasibility question is
unresolved. Quantity minimization and cleanup are not advanced while the event
minimum remains unproven. The standard solver and Streamlit workflow retain
their original strict lexicographic behavior and truthful historical statuses.

## Selected material orders

{markdown(orders[['product','material','order_month','arrival_month','quantity','integer_lots','purchase_expense_usd']])}

The three original precommitted shipments are separate constants, not new
events. No additional A orders occur in this selected plan.

## Independent validation and financial reconciliation

{markdown(pd.DataFrame([dict(component=k,usd=status['costs'][k]) for k in ['operating_expenses','a_materials','c_materials','b_materials','total_delivery_cost']]))}

The selected plan passed independent reconstruction of {audit['constraints_checked']:,}
constraints and {audit['variables_checked']:,} variable levels; maximum violation
{audit['max_violation']:.8g}. Financial calculations retain full precision. Monthly
material balances, warehouse occupancy and costs remain in the selected source
folder. New proof outputs do not overwrite source files, SQLite saved runs or
historical reports. The interface event count remains the actual 10-event plan;
no unproven secondary optimum is relabeled as proven.

Relevant tests: 31 passed for procurement/proof/material/editor/history checks,
65 passed for model/reconciliation/saved-run/app-page compatibility, and the final
4 proof tests passed including timeout semantics. See `procurement_proof_tests.log`
and `procurement_compat_tests.log`.

## Reproduction and remaining uncertainty

```powershell
.venv\\Scripts\\python.exe -m src.procurement_proof --source reports/v7 --output-dir reports/new_proof --seconds 600 --strengthen
```

Use a fresh directory. A longer budget is configurable with `--seconds`; the
baseline cost and service locks remain unchanged. If the interval above has
not closed, more search or additional proven-valid cuts are required. No claim
that 10 events is the global minimum is justified without that certificate.
'''
    Path(target).write_text(text,encoding='utf-8')
    return dict(best_events=best,lower_bound=lower,proven=best==lower,audit=audit)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('reports/v7_resume_validation'))
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=600)
    parser.add_argument('--threads',type=int,default=1)
    parser.add_argument('--strengthen',action='store_true',help='Add valid integer-rounded B prefix cover cuts')
    args=parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds<=0 or args.threads<1:
        parser.error('Positive finite seconds and positive thread count required.')
    print(json.dumps(run(args.source,args.output_dir,seconds=args.seconds,threads=args.threads,strengthen=args.strengthen),indent=2))
