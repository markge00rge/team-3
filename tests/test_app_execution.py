"""Acceptance artifacts are real solves, never substitutes for execution."""
import json
from pathlib import Path
from copy import deepcopy
from io import BytesIO
import pandas as pd
import pytest
from src.data_loader import ROOT,load_case
from src.model import build_model
from src.solve import solve_lexicographic
from app.optimizer_adapter import read_run
from app.dashboard import excel_export


def test_solver_progress_callback_observes_real_stages_without_changing_objectives():
    data=deepcopy(load_case())
    data.months=data.months[:2]
    data.demand=data.demand[data.demand.month.isin(data.months)].copy()
    data.demand.msu=0
    data.initial_fp={p:0 for p in data.products}
    data.initial_materials.quantity=0
    data.arrivals.quantity=0
    m=build_model(data); events=[]
    outcome=solve_lexicographic(m,time_limit=30,stage_callback=lambda n,s,d:events.append((n,s,d)))
    assert outcome.success
    assert outcome.minimum_cost==pytest.approx(140000)
    assert len(events)==14
    assert [e[0] for e in events if e[1]=="completed"]==[s["name"] for s in outcome.stages]
    assert all(e[2]["termination"]=="optimal" for e in events if e[1]=="completed")


def artifact(name):
    p=ROOT / "reports/app_runs" / f"acceptance_{name}"
    if not (p/"completion.json").exists(): pytest.skip("Run python -m app.verify_scenarios first")
    return read_run(p)


def test_real_original_adapter_reproduces_current_validated_baseline():
    completion,t,_=artifact("original")
    baseline=json.loads((ROOT/"reports/v5/solve_status.json").read_text())
    assert completion["monetary_optimal"]
    assert completion["costs"]["total_modeled"]==pytest.approx(baseline["costs"]["total_modeled"],abs=.01)
    expected=pd.read_csv(ROOT/"reports/v5/service.csv").served_msu.sum()
    assert t["service"].served_msu.sum()==pytest.approx(expected)


def test_identical_ui_adapter_and_cli_solve_equivalent_objectives():
    c,t,_=artifact("original")
    p=ROOT/"reports/app_runs/cli_original/solve_status.json"
    if not p.exists(): pytest.skip("Run the separate CLI parity case first")
    cli=json.loads(p.read_text())
    assert cli["minimum_cost"]==pytest.approx(c["outcome"]["minimum_cost"],abs=.01)
    for a,b in zip(cli["stages"],c["outcome"]["stages"]):
        assert a["name"]==b["name"]
        if a["termination"]==b["termination"]=="optimal": assert a["optimum"]==pytest.approx(b["optimum"],abs=.01)


@pytest.mark.parametrize("name",["holding","salary","summer"])
def test_real_edited_parameter_acceptance(name):
    c,t,_=artifact(name)
    original,base,_=artifact("original")
    assert c["has_solution"]
    assert t["service"].demand_msu.sum()==pytest.approx(3105 if name=="summer" else 3095)
    costs=t["monthly_cost_breakdown"].query("month == 'ANNUAL'").iloc[0]
    assert costs.total_modeled_cost_usd==pytest.approx(c["costs"]["total_modeled"],abs=.01)
    if name=="salary":
        assert costs.base_salaries_usd==pytest.approx(70*1100*12)
    elif name=="holding":
        detail=t["monthly_inventory_by_product"]
        assert (detail.holding_expense_usd-detail.ending_fp_value_usd*.02).abs().max()<1e-5
    elif name=="summer":
        june=t["service"].query("hub == 'H1' and family == 'AC' and month == '2027-06'")
        assert june.demand_msu.item()==115


def test_export_workbook_and_dashboard_render_actual_outputs():
    from streamlit.testing.v1 import AppTest
    _,tables,_=artifact("original")
    workbook=excel_export(tables)
    assert set(pd.ExcelFile(BytesIO(workbook)).sheet_names)=={n[:31] for n in tables}
    at=AppTest.from_file(str(ROOT/"app/main.py"),default_timeout=40).run()
    at.session_state.selected_run=str(ROOT/"reports/app_runs/acceptance_original")
    at.session_state.screen="results"
    at.run()
    assert not at.exception
    assert len(at.metric)==14
    assert any(x.label=='International Shipments' for x in at.metric)
    assert any(x.label=='Material Order Lines' for x in at.metric)
    assert len(at.get("plotly_chart"))>=12
    assert len(at.get("download_button"))>=10


def test_real_ui_timeout_is_published_as_an_incumbent_not_an_optimum():
    from streamlit.testing.v1 import AppTest
    pointer=ROOT/"reports/app_runs/live_ui_job.json"
    if not pointer.exists(): pytest.skip("Run the deliberate short-limit UI smoke job first")
    path=Path(json.loads(pointer.read_text())["directory"])
    if not (path/"completion.json").exists(): pytest.skip("UI smoke job is still running")
    c,_,_=read_run(path)
    if c["outcome"]["success"]: pytest.skip("This smoke job proved all objectives")
    assert c["has_solution"]
    assert any(s["termination"]=="maxTimeLimit" for s in c["outcome"]["stages"])
    at=AppTest.from_file(str(ROOT/"app/main.py"),default_timeout=40).run()
    at.session_state.selected_run=str(path); at.session_state.screen="results"
    at.run()
    assert not at.exception and at.warning
    if not c["monetary_optimal"]:
        assert any(m.label=="Feasible plan cost" for m in at.metric)
        assert all(m.label!="Minimum modeled annual cost" for m in at.metric)
