"""Adopted V7 planning inputs, separate from the unchanged original documents."""
from copy import deepcopy
import pandas as pd

POLICY = 'explicit_abc_v7'
LEGACY_POLICY = 'legacy_ac_smooth_b'


def planning_case(source, *, explicit=None):
    """Fresh effective case. Existing B quantities (including zero) are preserved."""
    data=deepcopy(source)
    enabled=(data.rules.get('explicit_b_materials',not data.rules.get('legacy_v5',False))
             if explicit is None else explicit)
    data.rules['explicit_b_materials']=bool(enabled)
    if not enabled:
        data.initial_materials=data.initial_materials[data.initial_materials['product']!='B'].copy()
    if enabled:
        rows=[]
        for material,quantity,unit,bom in [('RM',200000.,'kg','rm_kg_per_msu'),('PM',750000.,'EA','pm_ea_per_msu')]:
            mask=(data.initial_materials['product']=='B')&(data.initial_materials.material==material)
            if not mask.any():
                rows.append(dict(product='B',material=material,quantity=quantity,unit=unit,
                    stated_support_msu=None))  # no source-stated B support quantity
        if rows:
            additions=pd.DataFrame(rows)
            additions['stated_support_msu']=pd.to_numeric(additions.stated_support_msu,errors='coerce')
            data.initial_materials=pd.concat([data.initial_materials,additions],ignore_index=True)
        data.rules['b_opening_stock_provenance']='Adopted clarification assumptions: RM 200,000 kg / PM 750,000 EA; not numerical stocks in original documents.'
        if ((data.arrivals['product']=='B')&(data.arrivals.quantity!=0)).any():
            raise ValueError('No fixed Product B receipts are supported; additional B receipts must originate from orders.')
    return data
