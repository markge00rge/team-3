"""ABC purchases (V7), historical B expense and exact legacy-first A provenance."""
import pyomo.environ as pyo


def material_price(data, product, material):
    fallback = data.rules["rm_usd_per_kg" if material == "RM" else "pm_usd_per_ea"]
    return data.rules.get("material_unit_prices", {}).get(product, {}).get(material, fallback)


def add_material_financials(m, data):
    m.material_financial_model = True
    m.material_unit_price = pyo.Param(m.products, m.materials,
        initialize=lambda m,p,k: material_price(data,p,k),within=pyo.NonNegativeReals)
    # Original A stocks/fixed receipts all precede additional receipts. Under
    # explicit legacy-first consumption, newly purchased scrap is exactly the
    # minimum of total A scrap and total additional A receipts (orders).
    m.a_new_scrap = pyo.Var(m.materials,domain=pyo.NonNegativeReals)
    m.a_overlap_branch = pyo.Var(m.materials,domain=pyo.Binary)
    m.a_new_scrap_month = pyo.Var(m.materials,m.months,domain=pyo.NonNegativeReals)
    m.scrap_provenance = pyo.ConstraintList()
    for k in m.materials:
        scrap = sum(m.a_scrap[k,d] for d in m.days)
        purchases = sum(m.material_order['A',k,t] for t in m.months)
        bound = m.material_stock_bound['A',k]
        z = m.a_overlap_branch[k]
        m.scrap_provenance.add(m.a_new_scrap[k] <= scrap)
        m.scrap_provenance.add(m.a_new_scrap[k] <= purchases)
        m.scrap_provenance.add(m.a_new_scrap[k] >= scrap-bound*z)
        m.scrap_provenance.add(m.a_new_scrap[k] >= purchases-bound*(1-z))
        m.scrap_provenance.add(sum(m.a_new_scrap_month[k,t] for t in m.months)==m.a_new_scrap[k])
        for t in m.months:
            m.scrap_provenance.add(m.a_new_scrap_month[k,t] <= m.monthly_a_scrap[k,t])
    m.ide_overlap = pyo.Expression(expr=sum(m.a_new_scrap[k]*m.material_unit_price['A',k] for k in m.materials))
    m.a_material_cost = pyo.Expression(expr=sum(m.material_order['A',k,t]*m.material_unit_price['A',k] for k in m.materials for t in m.months))
    m.c_material_cost = pyo.Expression(expr=sum(m.material_order['C',k,t]*m.material_unit_price['C',k] for k in m.materials for t in m.months))
    m.b_material_cost = pyo.Expression(expr=sum(
        (m.material_order['B',k,t] if m.explicit_b_materials else m.b_material_consumption[k,t])*
        m.material_unit_price['B',k] for k in m.materials for t in m.months))
    m.operating_cost_full_ide = pyo.Expression(expr=m.total_cost.expr)
    m.reconciled_operating_cost = pyo.Expression(expr=m.operating_cost_full_ide-m.ide_overlap)
    m.total_cost.set_value(m.reconciled_operating_cost + m.a_material_cost+m.c_material_cost+m.b_material_cost)
