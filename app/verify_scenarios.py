"""Explicit real-solver acceptance runs; never invoked by widget rerenders."""
import argparse
import json
from pathlib import Path
from app.scenarios import original_scenario
from app.optimizer_adapter import execute
from src.data_loader import ROOT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--time-limit",type=float,default=180)
    parser.add_argument("--prefix",default="acceptance")
    args=parser.parse_args()
    original=original_scenario()
    cases=[("original",original),("holding",original.clone("Higher Working Capital")),
        ("salary",original.clone("Higher Crew Salary")),("summer",original.clone("Increased Summer Demand"))]
    cases[1][1].values["rule.fp_holding_fraction_month"]=0.02
    cases[2][1].values["rule.operator_usd_per_month"]=1100
    cases[3][1].values["demand.H1.AC.2027-06"]+=10
    rows=[]
    for name,scenario in cases:
        directory=ROOT / "reports/app_runs" / f"{args.prefix}_{name}"
        print("Running",name,flush=True)
        def notify(stage,state,detail): print(name,stage,state,detail,flush=True)
        result=execute(scenario,directory,time_limit=args.time_limit,notify=notify)
        rows.append(dict(scenario=name,directory=str(directory.relative_to(ROOT)),**result))
        (ROOT / "reports/app_runs" / f"{args.prefix}_verification.json").write_text(json.dumps(rows,indent=2))
    return 0 if all(r["has_solution"] for r in rows) else 1


if __name__=="__main__": raise SystemExit(main())
