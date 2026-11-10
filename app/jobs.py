"""One worker per deliberate run; polling never launches another optimization."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from src.data_loader import ROOT


def start_job(scenario,time_limit=180,scenario_type=None):
    from app.run_store import validate_name
    scenario=scenario.clone()
    scenario.name=validate_name(scenario.name)
    scenario.validate()
    directory = ROOT / "reports/app_runs" / uuid4().hex
    directory.mkdir(parents=True)
    (directory / "request.json").write_text(scenario.to_json(),encoding="utf-8")
    (directory / 'request_metadata.json').write_text(json.dumps(dict(
        created_at=datetime.now(timezone.utc).isoformat(),scenario_type=scenario_type)),encoding='utf-8')
    with (directory / "worker.log").open("w",encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable,"-m","app.worker","--scenario",str(directory / "request.json"),
            "--output-dir",str(directory),"--time-limit",str(time_limit)]+(['--scenario-type',scenario_type] if scenario_type else []),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    return dict(directory=str(directory),process=process,name=scenario.name,
        started=datetime.now(timezone.utc).isoformat(),time_limit=time_limit)


def events(job):
    path = Path(job["directory"]) / "events.jsonl"
    records = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try: records.append(json.loads(line))
            except json.JSONDecodeError: pass  # worker may be appending the last line
    return records
