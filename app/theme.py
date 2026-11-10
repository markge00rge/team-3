"""Presentation only; no source data or model quantities."""
import streamlit as st


def apply():
    st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
    .stApp {background:#f4f7fb;color:#152b48;}
    h1,h2,h3 {overflow-wrap:anywhere;min-width:0;font-family:'Manrope',sans-serif;letter-spacing:-.035em;}
    h1 {font-weight:800!important;} .block-container {max-width:1450px;padding-top:2rem;}
    [data-testid="stSidebar"] {background:#102c49;} [data-testid="stSidebar"] * {color:#e6eff8;}
    [data-testid="stSidebar"] [data-baseweb="select"] * {color:#152b48;}
    [data-testid="stSidebar"] button * {color:#152b48;}
    [data-testid="stMetric"] {background:white;border:1px solid #e1e8f0;border-radius:14px;padding:18px;}
    [data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:16px;}
    .hero {background:linear-gradient(120deg,#0c2543,#154c6a);padding:48px;border-radius:22px;margin:12px 0 26px;color:white;}
    .hero h1 {color:white;font-size:42px;max-width:800px;margin:12px 0;line-height:1.16;}
    .hero p {color:#c6dce9;font-size:18px;margin:10px 0;}
    .eyebrow {font-size:11px;letter-spacing:.2em;font-weight:700;color:#6ce0cc;text-transform:uppercase;}
    .pill {display:inline-block;background:#e2f5ef;color:#10705b;padding:5px 12px;border-radius:40px;font-size:12px;font-weight:600;}
    .coming {background:#edf0f7;color:#687b94;}
    .cardicon {font-size:32px;padding-bottom:12px;}
    div.stButton>button {border-radius:9px;font-weight:600;min-height:42px;}
    [data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
    .subtle {color:#64748b;font-size:14px;}
    .run-name {font-size:1.15rem;font-weight:700;overflow-wrap:anywhere;white-space:normal;min-width:0;}
    </style>''',unsafe_allow_html=True)


def heading(kicker,title,subtitle=""):
    st.markdown(f'<div class="eyebrow" style="color:#128575">{kicker}</div>',unsafe_allow_html=True)
    st.title(title)
    if subtitle: st.caption(subtitle)
