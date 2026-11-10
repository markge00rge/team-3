"""The UI-to-existing-engine execution path; no mathematical model lives in app/."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import pandas as pd
from src.data_loader import ROOT
from src.model import build_model
from src.solve import solve_lexicographic
from src.results import extract_results, write_results
from src.validation import audit_solution
from src.reconciliation import calculate, INPUT_TABLES
from src.kpis import calculate_kpis
from app.scenarios import Scenario, engine_fingerprint


def execute(scenario: Scenario, directory, *, time_limit=180, notify=None, scenario_type=None):
    from app.run_store import validate_name
    scenario=scenario.clone()
    scenario.name=validate_name(scenario.name)
    directory = Path(directory).resolve()
    allowed = (ROOT / "reports/app_runs").resolve()
    if allowed not in directory.parents:
        raise ValueError("Application runs must use a new reports/app_runs/<run-id> directory")
    directory.mkdir(parents=True,exist_ok=True)
    if (directory / "completion.json").exists():
        raise ValueError("Completed runs are immutable; start a new run")
    notify = notify or (lambda name,state,detail: None)
    notify("validation","running",{})
    data = scenario.to_case()
    from app.run_store import snapshot_case, clean
    effective_inputs = snapshot_case(data)
    (directory / 'effective_inputs.json').write_text(json.dumps(effective_inputs,allow_nan=False),encoding='utf-8')
    notify("validation","completed",{})
    (directory / "scenario.json").write_text(scenario.to_json(),encoding="utf-8")
    notify("building","running",{})
    model = build_model(data)
    notify("building","completed",{})
    outcome = solve_lexicographic(model,time_limit=time_limit,stage_callback=notify)
    completion = dict(name=scenario.name,engine_fingerprint=engine_fingerprint(),
        outcome=asdict(outcome),has_solution=False,monetary_optimal=outcome.minimum_cost is not None)
    if getattr(model,"_has_incumbent",False):
        notify("extraction","running",{})
        audit = audit_solution(model)
        (directory / "solution_audit.json").write_text(json.dumps(audit,indent=2))
        if not audit["passed"]:
            raise RuntimeError("The numerical solution failed validation; results are not published")
        results = extract_results(model,allow_incumbent=not outcome.success)
        write_results(results,outcome,directory,allow_incumbent=not outcome.success)
        notify("extraction","completed",{})
        notify("dashboard","running",{})
        tables = {name:getattr(results,name) for name in INPUT_TABLES}
        status = dict(stages=outcome.stages,costs=results.costs,material_policy=results.material_policy)
        financial = calculate(data,tables,status)
        tables.update({n:getattr(results,n) for n in ("daily_schedule","line_capacity","material_orders")})
        derived = calculate_kpis(data,tables,financial)
        derived.update(monthly_cost_breakdown=financial.costs,monthly_production_inventory=financial.monthly,
                       monthly_inventory_by_product=financial.products)
        for name,frame in derived.items(): frame.to_csv(directory / f"{name}.csv",index=False)
        completion.update(has_solution=True,costs=results.costs,
            reconciliation=financial.diagnostics,baseline=validated_baseline())
        # Publish an immutable, self-contained DB snapshot only after both audits.
        # A storage failure does not discard a valid solve or claim it was saved.
        from app.run_store import RunStore, make_record, MODEL_VERSION, FINANCIAL_VERSION
        from app.scenarios import original_scenario
        from dataclasses import fields
        from uuid import uuid4
        metadata_path=directory/'request_metadata.json'
        metadata=json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        explicit=results.material_policy=='explicit_abc_v7'
        completion.update(material_policy=results.material_policy,
            model_version=MODEL_VERSION if explicit else 'Venus V6 / strict Scenario A',
            financial_version=FINANCIAL_VERSION if explicit else 'venus-v6-reconciled-materials-1')
        all_tables={f.name:getattr(results,f.name) for f in fields(results) if isinstance(getattr(results,f.name),pd.DataFrame)}
        all_tables.update(derived)
        try:
            saved_id=uuid4().hex
            completion['saved_run_id']=saved_id
            record=make_record(scenario.name,json.loads(scenario.to_json()),effective_inputs,
                completion,all_tables,results.transition,audit,run_id=saved_id,
                source_run_id=directory.name,created_at=metadata.get('created_at'),
                scenario_type=scenario_type or ('Original' if scenario.values==original_scenario().values else 'Customized'),
                assumptions={p.name:p.read_text(encoding='utf-8') for p in (ROOT/'ASSUMPTIONS.md',ROOT/'V7_SCOPE.md') if p.exists()})
            RunStore().save_run(record)
            notify('saving','completed',dict(run_id=saved_id))
        except Exception as exc:
            completion.pop('saved_run_id',None)
            completion['save_error']=str(exc)
            notify('saving','failed',dict(message=str(exc)))
        notify("dashboard","completed",{})
    # Atomic publication: UI never reads a half-written completion marker.
    temp = directory / "completion.pending"
    temp.write_text(json.dumps(completion,indent=2),encoding="utf-8")
    temp.replace(directory / "completion.json")
    return completion


def validated_baseline():
    path = ROOT / "reports/v5/solve_status.json"
    status = json.loads(path.read_text())
    manifest=json.loads((ROOT / "app/validated_baseline.json").read_text())
    matches=sha256(path.read_bytes()).hexdigest()==manifest["baseline_sha256"] and all(
        sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in manifest["source_sha256"].items())
    return dict(label="Saved validated V5 baseline — not a new solve",
        costs=status["costs"],stages=status["stages"],path=str(path.relative_to(ROOT)),
        corresponding_engine_version=matches,provenance=manifest)


def read_run(directory):
    directory = Path(directory)
    completion = json.loads((directory / "completion.json").read_text(encoding="utf-8"))
    tables = {p.stem:pd.read_csv(p,float_precision="round_trip") for p in directory.glob("*.csv")}
    transition = json.loads((directory / "transition_ide.json").read_text()) if completion["has_solution"] else {}
    return completion,tables,transition
