"""Versioned JSON scenario schema and explicit editable-field allowlist.

Only normalized numeric inputs are stored. Original data always comes from
load_case(); products, hubs, lines, families, dates and calendar stay locked.
"""
from dataclasses import dataclass, asdict
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import pandas as pd
from src.data_loader import ROOT, load_case
from src.parameters import validate_parameters

# key -> (business label, minimum, integer, questionnaire page)
RULE_FIELDS = {
    "sea_lead_months": ("Sea-freight lead time (months)",1,True,3),
    "rm_moq_kg": ("RM order lot (kg)",1,True,3),
    "pm_moq_ea": ("PM order lot (EA)",1,True,3),
    "rm_kg_per_pallet": ("RM kg per pallet",1,False,3),
    "pm_ea_per_pallet": ("PM EA per pallet",1,False,3),
    "disposal_usd_per_ton": ("Disposal expense ($/metric ton)",0,False,3),
    "pm_kg_per_1000_ea": ("PM weight (kg / 1,000 EA)",0,False,3),
    "operator_usd_per_month": ("Monthly salary ($/operator)",0,False,4),
    "hiring_usd_per_operator": ("One-time hiring fee ($/operator)",0,False,4),
    "dismissal_usd_per_operator": ("Dismissal expense ($/additional operator)",0,False,4),
    "training_months": ("Full training months",1,True,4),
    "upgrade_operators_per_line": ("Additional operators per crew",1,True,4),
    "warehouse_pallets": ("On-site capacity (pallets)",0,False,5),
    "overflow_usd_per_pallet_month": ("External rental ($/pallet/month)",0,False,5),
    "overflow_block_pallets": ("External booking block (pallets)",1,True,5),
    "fp_holding_fraction_month": ("Monthly FP holding rate (%)",0,False,5),
    "truck_msu": ("Truck capacity (MSU)",0.01,False,6),
    "dedicated_trucks_month": ("Dedicated fleet (trucks/month)",0,True,6),
    "spot_surcharge_fraction": ("Spot-market surcharge (%)",0,False,6),
}


def engine_fingerprint():
    files = sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "data").glob("Venus_PS_*"))
    return sha256(b"".join(p.name.encode()+p.read_bytes() for p in files)).hexdigest()


@dataclass
class Scenario:
    schema_version: int
    name: str
    values: dict

    def to_json(self):
        return json.dumps(asdict(self), indent=2, allow_nan=False)

    @classmethod
    def from_json(cls, content):
        obj = json.loads(content, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON number")))
        if not isinstance(obj,dict) or set(obj) != {"schema_version","name","values"}:
            raise ValueError("Expected schema_version, name and values only")
        if type(obj["schema_version"]) is not int:
            raise ValueError("Scenario schema version must be an integer")
        scenario = cls(**obj)
        if scenario.schema_version == 1:
            original=original_scenario()
            added={'flexible_workforce','rule.dismissal_usd_per_operator','rule.training_months','rule.upgrade_operators_per_line'}
            oldkeys={k for k in original.values if not k.startswith('price.') and k not in added}|{'rule.rm_usd_per_kg','rule.pm_usd_per_ea'}
            if set(scenario.values)!=oldkeys: raise ValueError('Unsupported historical scenario fields')
            values=original.values.copy()
            values.update({k:v for k,v in scenario.values.items() if k in values})
            for p in ('A','B','C'):
                values[f'price.{p}.RM']=scenario.values['rule.rm_usd_per_kg']
                values[f'price.{p}.PM']=scenario.values['rule.pm_usd_per_ea']
            values['flexible_workforce']=False
            scenario=cls(2,scenario.name,values)
        scenario.validate()
        return scenario

    def clone(self, name=None):
        copy = deepcopy(self)
        copy.name = name or self.name
        return copy

    def validate(self, source=None):
        source = source or load_case()
        expected = original_scenario(source).values
        if self.schema_version != 2 or isinstance(self.schema_version,bool):
            raise ValueError("Unsupported scenario schema version")
        if not isinstance(self.name,str) or not self.name.strip() or len(self.name)>100:
            raise ValueError("Use a scenario name between 1 and 100 characters")
        if not isinstance(self.values,dict) or set(self.values) != set(expected):
            raise ValueError("Unsupported, missing or structural scenario fields")
        for key,value in self.values.items():
            if key.startswith("upgrade.") or key=='flexible_workforce':
                if type(value) is not bool:
                    raise ValueError(f"{key} must be a boolean")
            elif key == "qualification_month":
                if value != "optimize" and value not in source.months:
                    raise ValueError("Qualification must optimize or use a month in the horizon")
            else:
                try: finite=math.isfinite(value)
                except (OverflowError,TypeError): finite=False
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not finite:
                    raise ValueError(f"{key} must be a finite number")
                minimum, integer = (0,False)
                if key.startswith("rule."):
                    _,minimum,integer,_ = RULE_FIELDS[key[5:]]
                elif key.startswith("rate.") or (key.startswith("bom.") and not key.endswith("fp_usd_per_msu")):
                    minimum = 0.001
                if value < minimum or (integer and int(value) != value):
                    raise ValueError(f"{key}: minimum {minimum}" + (", whole numbers only" if integer else ""))
        return self

    def changes(self, source=None):
        original = original_scenario(source).values
        return pd.DataFrame([dict(parameter=k,original=original[k],modified=v)
            for k,v in self.values.items() if v != original[k]], columns=["parameter","original","modified"])

    def to_case(self, source=None):
        source = source or load_case()
        self.validate(source)
        case = deepcopy(source)
        for key,value in self.values.items():
            parts = key.split(".")
            kind = parts[0]
            if kind == "rule": case.rules[parts[1]] = value
            elif kind == 'price': case.rules.setdefault('material_unit_prices',{}).setdefault(parts[1],{})[parts[2]]=value
            elif key=='flexible_workforce': case.rules['flexible_workforce']=value
            elif kind == "rate": case.lines.loc[parts[1],"msu_per_day"] = value
            elif kind == "upgrade": case.rules.setdefault("upgrade_permissions",{})[parts[1]] = value
            elif kind == "bom": case.bom.loc[parts[1],parts[2]] = value
            elif kind == "initial_fp": case.initial_fp[parts[1]] = value
            elif kind == "stock":
                mask = (case.initial_materials["product"] == parts[1]) & (case.initial_materials.material == parts[2])
                case.initial_materials.loc[mask,"quantity"] = value
            elif kind == "receipt": case.arrivals.loc[int(parts[1]),"quantity"] = value
            elif kind == "hub": case.hubs.loc[parts[1],parts[2]] = value
            elif kind == "demand":
                _,h,f,t = parts
                mask = (case.demand.hub == h) & (case.demand.family == f) & (case.demand.month == t)
                case.demand.loc[mask,"msu"] = value
            elif key == "qualification_month" and value != "optimize":
                case.rules["qualification_allowed_months"] = [value]
        validate_parameters(case)
        return case


def original_scenario(source=None):
    data = source or load_case()
    defaults={'dismissal_usd_per_operator':0}
    v = {"rule."+k:float(data.rules.get(k,defaults.get(k))) for k in RULE_FIELDS}
    v['flexible_workforce']=data.rules.get('flexible_workforce',True)
    from src.financial_model import material_price
    for p in data.products:
        for k in ('RM','PM'): v[f'price.{p}.{k}']=float(material_price(data,p,k))
    v["qualification_month"] = "optimize"
    for l in data.lines.index:
        v["rate."+l] = float(data.lines.loc[l,"msu_per_day"])
        v["upgrade."+l] = True
    for p in data.products:
        v["initial_fp."+p] = float(data.initial_fp[p])
        v[f"bom.{p}.fp_usd_per_msu"] = float(data.bom.loc[p,"fp_usd_per_msu"])
        if p != "B":
            for col in ("rm_kg_per_msu","pm_ea_per_msu"):
                v[f"bom.{p}.{col}"] = float(data.bom.loc[p,col])
    for r in data.initial_materials.itertuples():
        v[f"stock.{r.product}.{r.material}"] = float(r.quantity)
    for i,r in data.arrivals.iterrows(): v[f"receipt.{i}"] = float(r.quantity)
    for h in data.hubs.index:
        for col in ("truck_usd","unserved_usd_per_msu"):
            v[f"hub.{h}.{col}"] = float(data.hubs.loc[h,col])
    for r in data.demand.itertuples(): v[f"demand.{r.hub}.{r.family}.{r.month}"] = float(r.msu)
    return Scenario(2,"Original Venus",v)


def demand_frame(scenario, source=None):
    data = source or load_case()
    frame = data.demand[["month","hub","family","msu"]].copy()
    frame["msu"] = [scenario.values[f"demand.{r.hub}.{r.family}.{r.month}"] for r in frame.itertuples()]
    return frame


def apply_demand(scenario, frame, source=None):
    data = source or load_case()
    if set(frame.columns) != {"month","hub","family","msu"}:
        raise ValueError("Demand CSV requires month, hub, family and msu columns")
    expected = set(data.demand[["month","hub","family"]].itertuples(index=False,name=None))
    if frame.duplicated(["month","hub","family"]).any() or set(frame[["month","hub","family"]].itertuples(index=False,name=None)) != expected:
        raise ValueError("Demand must contain exactly the original 72 month/hub/family rows")
    copy = scenario.clone()
    for r in frame.itertuples(): copy.values[f"demand.{r.hub}.{r.family}.{r.month}"] = float(r.msu)
    copy.validate(data)
    return copy
