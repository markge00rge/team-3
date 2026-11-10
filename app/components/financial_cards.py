"""Responsive, nonoverlapping cost cards; exact values remain in tooltips/CSV."""
from html import escape
import streamlit as st


def compact_currency(value):
    value=float(value)
    for scale,suffix in ((1e12,'T'),(1e9,'B'),(1e6,'M')):
        if abs(value)>=scale:
            display=value/scale
            return f'${display:.2f}{suffix}' if abs(display)<10000 else f'${value:.2e}'
    return f'${value:,.0f}'


def card_html(costs):
    entries=[('Operating Expenses','operating_expenses','Full operating costs including IDE less the disclosed new-A scrap overlap.'),
        ('Additional A Materials','a_materials','New A RM/PM orders only, charged at placement.'),
        ('Additional C Materials','c_materials','New C RM/PM orders only, charged at placement.'),
        ('Product B Materials','b_materials','Material consumption expense based on actual B production, not shipments.'),
        ('TOTAL DELIVERY COST','total_delivery_cost','Modeled supply chain planning cost including specified material expenses; not transportation expense alone.')]
    cards={}
    for label,key,explanation in entries:
        exact=repr(float(costs[key]))
        title=escape(f'{explanation} Exact unrounded USD: {exact}',quote=True)
        classes='finance-card total-card' if key=='total_delivery_cost' else 'finance-card'
        display=f"${float(costs[key]):,.2f}" if key in ('operating_expenses','total_delivery_cost') else compact_currency(costs[key])
        size=min(36,430/max(10,len(display)))
        cards[key]=f'<section class="{classes}" data-finance-key="{key}" title="{title}"><div class="finance-label">{escape(label)}</div><div class="finance-value" style="font-size:clamp(14px,2.4vw,{size:.2f}px)">{display}</div></section>'
    return ('<div class="finance-grid"><div class="finance-main">'+cards['operating_expenses']+cards['total_delivery_cost']+
        '</div><div class="finance-materials">'+''.join(cards[k] for k in ('a_materials','c_materials','b_materials'))+'</div></div>')



def render(costs):
    st.markdown('''<style>
    .finance-grid{margin:12px 0 24px;min-width:0;container-type:inline-size;}.finance-main,.finance-materials{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-bottom:16px;}.finance-materials{grid-template-columns:repeat(3,minmax(0,1fr));}
    .finance-card{box-sizing:border-box;min-width:0;min-height:145px;background:white;border:1px solid #dce6ee;border-radius:16px;padding:22px;}
    .finance-label{font-size:clamp(.8rem,1.1vw,1rem);font-weight:600;white-space:normal;overflow-wrap:anywhere;line-height:1.4;}
    .finance-value{font-family:Manrope,sans-serif;font-weight:800;font-size:clamp(1.4rem,2.6vw,2.5rem);line-height:1.3;margin-top:14px;white-space:normal;overflow-wrap:anywhere;font-variant-numeric:tabular-nums;}
    .total-card{background:#102f4d;color:white;border-color:#102f4d;}
    @media(max-width:1100px){.finance-materials{grid-template-columns:minmax(0,1fr);}}
    @media(max-width:700px){.finance-main{grid-template-columns:minmax(0,1fr);}.finance-card{min-height:125px;}}
    @container(max-width:650px){.finance-main,.finance-materials{grid-template-columns:minmax(0,1fr);}}
    [data-testid="stMetricValue"]{font-size:clamp(1rem,1.8vw,1.9rem)!important;white-space:normal!important;overflow-wrap:anywhere;}
    [data-testid="stMetricLabel"]{white-space:normal!important;overflow-wrap:anywhere;}
    </style>''',unsafe_allow_html=True)
    st.markdown(card_html(costs),unsafe_allow_html=True)
    with st.expander('Exact financial amounts and IDE adjustment'):
        st.json({k:costs[k] for k in ('operating_full_ide','ide_overlap_adjustment','operating_expenses','a_materials','c_materials','b_materials','total_delivery_cost')})
