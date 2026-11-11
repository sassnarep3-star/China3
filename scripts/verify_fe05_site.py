#!/usr/bin/env python3
import csv, re, subprocess, sys
from pathlib import Path
from html.parser import HTMLParser
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P/'scripts'))
from fe05_engine import quote
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.rows=[];self.inrow=False;self.haslink=False;self.header=False;self.local=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='tr': self.inrow=True;self.haslink=False;self.header=False
  if tag=='th': self.header=True
  if tag=='a':
   href=d.get('href','')
   if self.inrow and href.startswith('http'):self.haslink=True
   if href and not href.startswith(('http','#','mailto:')): self.local.append(href.split('#')[0])
  if tag=='link' and d.get('href','').startswith('assets/'):self.local.append(d['href'])
 def handle_endtag(self,tag):
  if tag=='tr':self.rows.append(self.haslink or self.header);self.inrow=False
files=sorted(P.glob('fe05-*.html'))
assert len(files)==8
for p in files:
 a=Parser();a.feed(p.read_text(encoding='utf-8'))
 assert all(a.rows), f'row without source: {p}'
 for href in a.local: assert (P/href).is_file(), f'{p}: {href}'
with (P/'data/fe05_ladder.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
with (P/'data/fe05_methods.csv').open(encoding='utf-8',newline='') as f: methods=list(csv.DictReader(f))
assert len(rows)==40*len(methods)
for m in methods:
 subset=[r for r in rows if r['method_id']==m['id']]
 assert [int(r['gross_usd']) for r in subset]==list(range(10000,400001,10000))
 for r in subset:
  assert not r['total_landed_cost_usd']
  if m['priced_scenario']=='True': assert r['known_cost_usd']==str(quote(r['gross_usd'])[-1])
  else: assert not r['known_cost_usd']
before={p:p.read_bytes() for p in files+[P/'assets/fe05.css']+list((P/'data').glob('fe05_*.csv'))}
subprocess.run([sys.executable,str(P/'scripts/build_fe05_site.py')],check=True)
assert all(p.read_bytes()==content for p,content in before.items()),'generation is not deterministic'
print('FE05: links, source per row, ladder coverage, arithmetic, blank totals and reproducibility passed')
