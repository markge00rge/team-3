"""Real headless-Chrome card layout audit at common laptop/desktop widths."""
import ast
import json
import re
import subprocess
from pathlib import Path
from src.data_loader import ROOT
from app.components.financial_cards import card_html


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=ROOT/'reports/saved_runs_ui_layout')
    parser.add_argument('--comparison',action='store_true')
    parser.add_argument('--explicit-b',action='store_true')
    options=parser.parse_args()
    browser=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
    if not browser.exists(): raise RuntimeError('Chrome is required for this optional layout audit')
    directory=options.output_dir.resolve()
    directory.mkdir(parents=True,exist_ok=True)
    parsed=ast.parse((ROOT/'app/components/financial_cards.py').read_text(encoding='utf-8'))
    css=next(n.value for n in ast.walk(parsed) if isinstance(n,ast.Constant) and isinstance(n.value,str) and '<style>' in n.value)
    costs=dict(operating_expenses=1234567890123.125,a_materials=123456789.125,c_materials=12345678.123456,
        b_materials=950000,total_delivery_cost=1.234567890123e18)
    cards=card_html(costs,explicit_b=options.explicit_b)
    if options.comparison: cards='<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;">'+cards+cards+'</div>'
    html='<!doctype html><html><head><meta charset="utf-8">'+css+'''<style>body{margin:0;background:#f4f7fb;font-family:Arial;}main{margin-left:280px;padding:24px;max-width:1450px;box-sizing:border-box;}pre{white-space:pre-wrap;overflow-wrap:anywhere;}</style></head><body><main>'''+cards+'''<pre id="audit"></pre></main><script>
    const violations=[];for(const el of document.querySelectorAll('.finance-card,.finance-label,.finance-value')){
    const b=el.getBoundingClientRect(),p=el.parentElement.getBoundingClientRect();
    if(el.scrollWidth>el.clientWidth+1||b.left<p.left-1||b.right>p.right+1)violations.push(el.className);}
    const result={width:innerWidth,cards:document.querySelectorAll('.finance-card').length,
    violations:violations,pageOverflow:document.documentElement.scrollWidth>innerWidth+1};
    document.getElementById('audit').textContent=JSON.stringify(result);
    </script></body></html>'''
    page=directory/'cards.html';page.write_text(html,encoding='utf-8')
    rows=[]
    for width in (1024,1280,1366,1440,1920):
        args=[str(browser),'--headless=new','--disable-gpu','--no-first-run','--disable-background-networking',
            '--user-data-dir='+str(directory/'browser_profile'),'--window-size='+str(width)+',900',
            '--virtual-time-budget=1000','--dump-dom','--screenshot='+str(directory/f'cards_{width}.png'),page.as_uri()]
        result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW)
        match=re.search(r'<pre id="audit">(.*?)</pre>',result.stdout,re.S)
        if not match: raise RuntimeError('Browser did not return layout audit: '+result.stderr[-1000:])
        row=json.loads(match.group(1));rows.append(row)
        if row['violations'] or row['pageOverflow'] or row['cards']!=(10 if options.comparison else 5): raise AssertionError(row)
    (directory/'layout_audit.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))


if __name__=='__main__': main()
