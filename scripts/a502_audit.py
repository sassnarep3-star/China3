#!/usr/bin/env python3
"""Local structural checks for the independent review; not legal verification."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
class Review(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.current=None; self.hrefs=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag == 'tr': self.current=[]
        if tag == 'a':
            href=attrs.get('href',''); self.hrefs.append(href)
            if self.current is not None: self.current.append(href)
    def handle_endtag(self, tag):
        if tag == 'tr': self.rows.append(self.current); self.current=None
p=Review(); p.feed((ROOT/'a502-review.html').read_text(encoding='utf-8'))
assert len(p.rows)==7, 'Expected header plus six finding rows'
for row in p.rows[1:]:
    assert any(urlparse(x).hostname in {'www.safe.gov.cn','www.boc.cn','www.govinfo.gov','www.irs.gov','bsaefiling.fincen.gov'} for x in row), 'Finding lacks primary source'
for link in p.hrefs:
    if not urlparse(link).scheme and not link.startswith('#'):
        assert (ROOT / link.split('#')[0]).is_file(), f'Missing local target: {link}'
print('PASS: six finding rows have primary source links; review-page local targets exist. Content and external links are not checked by this script.')
