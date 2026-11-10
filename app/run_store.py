"""Transactional, immutable local run snapshots. No solver or input-loader calls."""
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

import pandas as pd
from src.data_loader import ROOT

SCHEMA_VERSION = 1
CATEGORIES = ('Venus Case Study', 'General Plant')
FINANCIAL_VERSION = 'venus-v7-abc-additional-purchases-1'
MODEL_VERSION = 'Venus V7 / explicit ABC procurement / strict Scenario A'


class RunStoreError(ValueError):
    """An actionable storage or snapshot-integrity error."""


def clean(value):
    """JSON-safe full precision, including numpy scalars and nullable cells."""
    if isinstance(value, dict): return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)): return [clean(v) for v in value]
    if hasattr(value, 'item'): return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value): return None
    if isinstance(value, (datetime,pd.Timestamp)): return value.isoformat()
    if value is pd.NA or value is pd.NaT: return None
    return value


def frame_snapshot(frame):
    return clean(dict(columns=list(frame.columns), index=list(frame.index),
        index_name=frame.index.name, data=frame.to_numpy().tolist()))


def restore_frame(value):
    frame=pd.DataFrame(value['data'],columns=value['columns'],index=value.get('index'))
    frame.index.name=value.get('index_name')
    return frame


def snapshot_case(data):
    # All effective fields used by model construction, not just UI differences.
    names=('months','products','families','lines','hubs','bom','initial_fp',
           'initial_materials','arrivals','demand','rules')
    return {name:frame_snapshot(getattr(data,name)) if isinstance(getattr(data,name),pd.DataFrame)
            else clean(getattr(data,name)) for name in names}


def validate_name(name):
    if not isinstance(name,str) or not name.strip() or len(name.strip())>100:
        raise RunStoreError('Enter a Scenario Run Name of 1–100 characters.')
    return name.strip()


def make_record(name,scenario,effective,completion,tables,transition,audit,*,
                category='Venus Case Study',scenario_type='Customized',run_id=None,
                created_at=None,source_run_id=None,assumptions=None):
    costs=completion.get('costs',{})
    explicit=completion.get('material_policy')=='explicit_abc_v7'
    financial=(FINANCIAL_VERSION if explicit else 'venus-v6-reconciled-materials-1') if 'total_delivery_cost' in costs else 'historical-operating-only'
    record=clean(dict(schema_version=SCHEMA_VERSION,run_id=run_id or uuid4().hex,
        name=validate_name(name),category=category,scenario_type=scenario_type,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        model_version=completion.get('model_version',MODEL_VERSION if explicit else 'Venus V6 / strict Scenario A' if 'total_delivery_cost' in costs else 'Historical / unspecified'),
        financial_version=financial,engine_fingerprint=completion.get('engine_fingerprint'),
        source_run_id=source_run_id,configuration=scenario,effective_inputs=effective,
        assumptions=assumptions or {},results=dict(completion=completion,
            tables={k:frame_snapshot(v) for k,v in tables.items()},transition=transition,audit=audit)))
    validate_record(record)
    return record


def validate_record(record):
    try:
        if record['schema_version']!=SCHEMA_VERSION: raise ValueError('Unsupported snapshot schema')
        validate_name(record['name'])
        if record['category'] not in CATEGORIES: raise ValueError('Unknown run category')
        if record['scenario_type'] not in ('Original','Customized'): raise ValueError('Unknown scenario type')
        if not record['run_id'] or not datetime.fromisoformat(record['created_at']).tzinfo:
            raise ValueError('Run identity or timestamp missing')
        effective=record['effective_inputs']
        if not isinstance(record['configuration'].get('values'),dict):
            raise ValueError('Original serialized scenario configuration required')
        if not set(('months','products','families','lines','hubs','bom','initial_fp',
                    'initial_materials','arrivals','demand','rules'))<=set(effective):
            raise ValueError('Complete effective input snapshot required')
        results=record['results']; completion=results['completion']
        if not completion['has_solution'] or not results['audit']['passed']:
            raise ValueError('Only numerically validated feasible solutions can be saved')
        if not completion['outcome']['stages']: raise ValueError('Solver status required')
        required={'production','inventory','shipments','service','transport','staffing',
                  'material_orders','material_balances','warehouse','line_capacity'}
        if not required<=set(results['tables']): raise ValueError('Incomplete result tables')
        costs=completion['costs']
        if not isinstance(costs.get('total_modeled'),(int,float)):
            raise ValueError('Saved objective value required')
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in costs.values() if v is not None):
            raise ValueError('Invalid saved monetary value')
        if 'total_delivery_cost' in costs:
            total=math.fsum(costs[k] for k in ('operating_expenses','a_materials','c_materials','b_materials'))
            if abs(total-costs['total_delivery_cost'])>.01: raise ValueError('Financial KPIs do not reconcile')
    except (KeyError,TypeError,ValueError) as exc:
        raise RunStoreError('Invalid saved run: '+str(exc)) from exc
    return True


class RunStore:
    def __init__(self,path=None):
        self.path=Path(path or os.environ.get('CAIRO_RUN_DB',ROOT/'app_data/runs.sqlite3'))
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.connection() as db:
                db.execute('CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, name TEXT NOT NULL, '
                    'category TEXT NOT NULL, created_at TEXT NOT NULL, source_run_id TEXT UNIQUE, '
                    'payload TEXT NOT NULL, digest TEXT NOT NULL)')
                db.execute('CREATE INDEX IF NOT EXISTS run_category ON runs(category,created_at)')
        except (OSError,sqlite3.Error) as exc: raise RunStoreError('Cannot initialize local run history: '+str(exc)) from exc

    @contextmanager
    def connection(self):
        try:
            db=sqlite3.connect(self.path,timeout=15)
            try:
                with db: yield db
            finally: db.close()
        except (sqlite3.Error,OSError) as exc: raise RunStoreError('Local run storage failed: '+str(exc)) from exc

    def save_run(self,record):
        validate_record(record)
        payload=json.dumps(record,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
        digest=sha256(payload.encode()).hexdigest()
        with self.connection() as db:
            old=db.execute('SELECT payload,digest FROM runs WHERE run_id=?',(record['run_id'],)).fetchone()
            if old:
                if old==(payload,digest): return record['run_id']  # safe retry, never update
                raise RunStoreError('Saved runs are immutable; this run ID already exists.')
            db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',(record['run_id'],record['name'],
                record['category'],record['created_at'],record.get('source_run_id'),payload,digest))
        return record['run_id']

    def get_run(self,run_id):
        with self.connection() as db:
            row=db.execute('SELECT payload,digest,name,category,created_at FROM runs WHERE run_id=?',(run_id,)).fetchone()
        if not row: raise RunStoreError('Saved run not found.')
        if sha256(row[0].encode()).hexdigest()!=row[1]: raise RunStoreError('Saved run integrity check failed.')
        try: record=json.loads(row[0])
        except ValueError as exc: raise RunStoreError('Saved run JSON is damaged.') from exc
        if (record['name'],record['category'],record['created_at'])!=row[2:] or record['run_id']!=run_id:
            raise RunStoreError('Saved run metadata integrity check failed.')
        validate_record(record)
        return record

    def list_runs(self,category=None):
        with self.connection() as db:
            ids=db.execute('SELECT run_id FROM runs'+(' WHERE category=?' if category else '')+
                ' ORDER BY created_at DESC',(category,) if category else ()).fetchall()
        return [self.get_run(row[0]) for row in ids]

    def get_inputs(self,run_id): return self.get_run(run_id)['effective_inputs']
    def get_results(self,run_id): return self.get_run(run_id)['results']
    def validate_integrity(self,run_id): return validate_record(self.get_run(run_id))
    def name_in_use(self,name):
        with self.connection() as db: names=db.execute('SELECT name FROM runs').fetchall()
        return any(row[0].casefold()==name.strip().casefold() for row in names)


def unpack_results(record):
    result=record['results']
    return result['completion'],{k:restore_frame(v) for k,v in result['tables'].items()},result['transition']
