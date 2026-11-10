"""Isolated real HiGHS worker, usable from the application and regression CLI."""
import argparse
import json
import traceback
from pathlib import Path
from app.scenarios import Scenario
from app.optimizer_adapter import execute


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--time-limit",type=float,default=180)
    parser.add_argument('--scenario-type',choices=['Original','Customized'])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    def notify(name,state,detail):
        with (args.output_dir / "events.jsonl").open("a",encoding="utf-8") as stream:
            stream.write(json.dumps(dict(name=name,state=state,detail=detail))+"\n")
    try:
        scenario = Scenario.from_json(args.scenario.read_text(encoding="utf-8"))
        result = execute(scenario,args.output_dir,time_limit=args.time_limit,notify=notify,scenario_type=args.scenario_type)
        return 0 if result["has_solution"] else 2
    except Exception as exc:
        notify("error","failed",dict(message=str(exc)))
        (args.output_dir / "error.json").write_text(json.dumps(dict(message=str(exc),traceback=traceback.format_exc()),indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
