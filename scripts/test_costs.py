#!/usr/bin/env python3
"""Structural checks, not legal/source-content verification."""
import csv, hashlib, subprocess
from pathlib import Path
from html.parser import HTMLParser
R=Path(__file__).resolve().parent.parent
channels=list(csv.DictReader((R/'data/channels.csv').open()))
rows=list(csv.DictReader((R/'data/cost-grid.csv').open()))
assert len(rows)==1400
assert {(x['channel_id'],int(x['amount_usd'])) for x in rows}=={(c['id'],a) for c in channels for a in range(10000,400001,10000)}
for x in rows:
 assert all(x[k]=='' for k in ('total_cost_usd','fx_cost_usd','tax_usd','bank_fee_usd'))
 assert x['source_url']==next(c['source_url'] for c in channels if c['id']==x['channel_id'])
 assert 'UNVERIFIED' in x['status']
class Audit(HTMLParser):
 def __init__(self):super().__init__();self.inbody=False;self.inrow=False;self.link=False;self.rows=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='tbody':self.inbody=True
  if tag=='tr' and self.inbody:self.inrow=True;self.link=False
  if tag=='a':
   href=a.get('href','')
   if href.startswith(('http://','https://')) and self.inrow:self.link=True
   if href and not href.startswith(('http:','https:','#')):assert (R/href.split('#')[0]).exists(),href
 def handle_endtag(self,tag):
  if tag=='tr' and self.inrow:assert self.link,'data row missing source';self.rows+=1;self.inrow=False
  if tag=='tbody':self.inbody=False
for filename,count in [('costs.html',1440),('cost-review.html',6)]:
 p=Audit();p.feed((R/filename).read_text());assert p.rows==count,(filename,p.rows)
files=['costs.html','cost-review.html','data/cost-grid.csv','data/cost-flags.json']
before=[hashlib.sha256((R/f).read_bytes()).hexdigest() for f in files]
subprocess.run(['python3','scripts/build_costs.py'],cwd=R,check=True)
assert before==[hashlib.sha256((R/f).read_bytes()).hexdigest() for f in files]
# Independently test the formula at floor/cap boundaries and throughout a sample grid.
def fee(principal_cny):return min(max(.001*principal_cny,50),260)+150
assert fee(0)==200 and fee(50000)==200 and fee(260000)==410
assert all(200<=fee(a*r)<=410 for a in range(10000,400001,10000) for r in (1,5,7,10))
print('PASS: 1400 unique combinations, blank unknowns, 1446 sourced HTML rows, local links, reproducible generation, tariff boundary arithmetic. Sample rates used only in tests, not quotes.')
