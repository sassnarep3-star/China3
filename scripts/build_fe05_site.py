#!/usr/bin/env python3
"""Generate a self-contained static research supplement and its CSVs."""
import csv, html, io
from pathlib import Path
from fe05_engine import quote
P=Path(__file__).resolve().parent.parent
S={
'safe':'https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html',
'foreign':'https://www.safe.gov.cn/tianjin/2026/0713/3088.html',
'property':'https://www.safe.gov.cn/tianjin/2024/0903/2594.html',
'home':'https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf',
'boc':'https://www.boc.cn/sourcedb/whpj/', 'fee':'https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html',
'atm':'https://www.safe.gov.cn/hubei/2019/0305/851.html', 'cash':'https://www.safe.gov.cn/hebei/2019/0521/1366.html',
'private':'https://www.safe.gov.cn/guangdong/2020/0304/1668.html',
'crypto':'https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html',
'fxlaw':'https://www.safe.gov.cn/safe/2008/0806/5321.html',
'iit':'https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html',
'late':'https://fgk.chinatax.gov.cn/zcfgk/c100009/c5195081/content.html',
'interest':'https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html',
'vat':'https://shanghai.chinatax.gov.cn/zcfw/zcfgk/zzs/202601/t478899.html',
'irs':'https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements',
'988':'https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm',
'credit':'https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit',
'fbpen':'https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821',
'gift':'https://www.irs.gov/businesses/gifts-from-foreign-person',
'stream':'https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures',
'cbp':'https://www.cbp.gov/travel/international-visitors/money-monetary-instruments',
'fxirs':'https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates',
'bank':'https://info.bankofamerica.com/en/digital-banking/wire-transfers',
'filing':'https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html',
'taxrecord':'https://tianjin.chinatax.gov.cn/11200000000/0300/030004/03000418/20190121142506605.shtml',
'wise':'https://wise.com/help/articles/2955298/guide-to-cny-transfers',
'wu':'https://www.westernunion.com/cn/en/send-money.html',
}
# Each row cites primary authorities; product-provider information is marked as such.
methods=[
('income','Documented current-account income','Conditional','Foreign individual: passport, transaction-amount source evidence and tax voucher. No universal $50k hard cap.','Can remit documented income; paperwork and bank review.','Collect contract, payslips and tax records; confirm classification and documents with bank; buy USD; wire to own account; retain receipts.','foreign',True),
('quota','Annual convenience quota','Conditional','Foreign permanent residence ID holders qualify for purchase quota; confirm eligibility and permitted purpose.','Simple inside quota; not a blanket route for every passport holder.','Confirm PRC permanent resident ID and unused quota with bank; provide ID and truthful purpose; convert and remit with bank approval.','foreign',True),
('reconvert','Reconvert unused exchanged RMB','Conditional','Original exchange receipt valid 24 months; ID-only thresholds apply to genuinely unused exchanged RMB.','Useful for identifiable unused exchange; receipt and time restriction.','Locate original exchange slip; establish unused balance and date; present passport and slip; convert and arrange lawful wire.','safe',True),
('sale','Property sale proceeds','Conditional','Bank checks transfer completion, tax documents and net proceeds; 2025 capital-account guide §8.','Eligible net sale proceeds may be remitted; sale, tax and documentary costs vary.','Complete genuine sale and title transfer; obtain contract and tax proof; seek bank review of net share; convert and remit.','home',True),
('inheritance','Inherited property transfer','SAFE approval','Foreign heir applies through appropriate SAFE branch; specific evidence and tax documentation required.','Route for qualifying inheritance; approval and proof required.','Gather death, inheritance, ownership and tax documentation; apply to competent SAFE branch; present approval to bank; remit to own overseas account.','property',True),
('emigrant','Emigrant property transfer','SAFE approval','Narrow eligibility for pre-emigration property; 2014 reform removed mandatory staging.','May remit approved assets in one or several payments; not available to everyone.','Document emigration, eligible pre-emigration assets and tax; apply to competent SAFE branch; bank remits approved amount to own overseas account.','property',True),
('alreadyusd','Existing foreign currency wire','Conditional','Applies only if already held in foreign currency, not CNY; check account classification.','Avoids another CNY conversion; wire and receiving costs still apply.','Confirm foreign-currency balance and source; provide identification and any required evidence; instruct bank to wire; retain confirmation.','safe',False),
('offshore','Cross-border RMB then offshore conversion','Unverified eligibility','Specific route, bank acceptance, RMB receiving account and offshore conversion quote must be confirmed.','Potential offshore pricing; two legs, fees and authorization uncertain.','Ask both banks in writing about applicable category and permitted RMB cross-border transfer; compare firm all-in quotes; proceed only if approved.','fxlaw',False),
('atm','Overseas ATM withdrawal','Restricted','Domestic cards combined: RMB 100,000 equivalent per person per calendar year; RMB 10,000 per card per day.','Cash access; caps, ATM and FX fees; not a bulk wire replacement.','Verify card overseas access and fees; withdraw within applicable limits; keep records; do not borrow cards to evade limits.','atm',False),
('cash','Physical foreign cash','Restricted','China departure rules depend on amount and declaration history; U.S. reporting applies above $10,000.','Cash is portable but loss risk, permits and reporting make it unsuitable for bulk transfers.','Lawfully acquire foreign cash; check China exit permit and prior declaration; report over $10,000 on U.S. entry using FinCEN 105; retain proof.','cash',False),
('dividend','Company dividend','Conditional','Only genuine distributable company profits; applicable tax and corporate approvals vary.','Not a way to relabel a personal deposit; corporate tax and paperwork.','Confirm company ownership and distributable profits; obtain resolutions, audit and tax documents; ask bank for eligible dividend remittance process.','fxlaw',False),
('provider','Licensed provider / bank agent','Unverified eligibility','Provider eligibility and quote depend on service; bank FX rules still apply.','May be convenient; no verified personalized rate or eligibility.','Ask licensed provider and partner bank about passport eligibility, source documents, limits and written total quote; use only approved service.','safe',False),
('split','Borrowing others’ quotas','Prohibited','Splitting to evade convenience or authenticity controls is prohibited.','No lawful advantage; watchlist and penalties possible.','Do not use; obtain legitimate documentation and request bank guidance.','safe',False),
('underground','Private swap / underground bank','Prohibited','SAFE warns private online or informal exchange is illegal.','Potential confiscation, penalties and fraud risk.','Do not use; use licensed institutions and truthful documents.','private',False),
('crypto','Mainland crypto conversion','Prohibited activity','PBOC 2026 notice prohibits mainland fiat-to-virtual-currency exchange business.','Regulatory, fraud and loss risks.','Do not use as a workaround; consult licensed bank about lawful route.','crypto',False),
]
questions=[
('Who owns the funds and how were they earned?','Unknown','Get statements, employment contracts, payslips, sale or inheritance records; reconcile deposits by date and amount.','foreign'),
('What identity and residence classification applies?','Known: U.S. citizen. Passport, PRC permanent residence ID and bank classification unknown.','Ask the account branch to confirm its recorded category and documents required.','foreign'),
('What is the balance and deadline?','Unknown','Obtain current balance, account restrictions and intended schedule from the bank; request an executable quote.','boc'),
('Were China taxes paid, exempt or withheld?','Unknown','Request payroll records and tax records in tax app, electronic tax bureau or tax service hall; resolve gaps with tax adviser.','taxrecord'),
('Are U.S. returns, FBAR and Form 8938 current?','Unknown','Review foreign account maximum values and prior filings with U.S. tax professional; thresholds differ.','irs'),
('Is there a U.S. dollar basis for the CNY?','Unknown','Reconstruct acquisition dates, amounts and contemporaneous USD values; assess §988 with adviser.','988'),
('Where will funds be received and which charges apply?','Unknown','Get receiving bank SWIFT details, full OUR/SHA fees, intermediary charges and exchange quote in writing.','fee'),
('Is this inheritance, property sale or emigrant property?','Unknown','Collect estate, title, sale and emigration records and confirm the applicable route with SAFE and the bank.','property'),
]
penalties=[
('Late PRC tax','Tax Administration Law art. 32: 0.05% of overdue tax per day; underlying tax still due.','late'),
('Tax evasion / nonfiling','Arts. 63–64: specified conduct may attract 50%–500% of unpaid tax, plus surcharge; facts and criminal rules matter.','late'),
('Illegal FX transactions','FX Regulations arts. 39, 40 and 45 have different elements and fine ranges; severe cases can trigger criminal liability. Do not presume a penalty applies.','fxlaw'),
('FBAR','31 CFR 1010.821 shows $16,536 nonwillful and $165,353 adjusted willful statutory dollar component for assessments on or after 2025-01-17; willful alternative 50% may apply; verify current adjustments and facts.','fbpen'),
('Disclosure remediation','IRS streamlined procedures require certification of nonwillfulness and additional eligibility; not an automatic waiver. Seek qualified advice.','stream'),
('Currency reporting','More than $10,000 transported into or out of U.S. must be reported; failure may result in seizure, forfeiture and penalties.','cbp'),
('PRC income tax','IIT law specifies 3%–45% comprehensive income, and 20% for specified categories. Tax base, exemptions and residency matter; this is not a tax on the wire itself.','iit'),
('Interest and property','China temporarily exempts eligible savings interest earned since 2008-10-09; home sale VAT depends on holding period and applicable rules. U.S. treatment is separate.','interest'),
('U.S. currency gain','§988 applies to certain currency dispositions; the $200 personal-transaction exception has conditions. Basis and character are fact-dependent.','988'),
('Foreign tax credit','Qualifying foreign income tax may be credited subject to conditions and limitations; no credit for taxes on excluded income.','credit'),
('Foreign gifts','Foreign individual or estate gifts/bequests over $100,000 aggregate may require Form 3520; related-party aggregation and separate rules apply.','gift'),
]
flags=[
('F01','data/d646_methods.csv:2–4','Foreign passport holders are not automatically eligible for the $50,000 ID-only purchase quota.','foreign'),
('F02','data/d646_methods.csv:6; data/channels.csv:9','Mandatory two-year staging and head-office threshold are superseded by 2014 reform.','property'),
('F03','data/s775_methods.csv:5; data/s775_sources.csv:22','ATM is not unrestricted; the annual cap aggregates cards in the person’s name, not per card.','atm'),
('F04','data/s775_methods.csv:4; data/s775_sources.csv:23','China departure permit rules differ from U.S. >$10,000 reporting; verify entry history and permits.','cash'),
('F05','data/d646_sources.csv:13','2021 crypto notice was repealed in 2026; check current notice rather than treating the old text as current.','crypto'),
('F06','index.html:38,104; data/cost_inputs.csv:2–5','Historical FX snapshots differ from today’s quote; not necessarily errors, but not executable current rates.','boc'),
('F07','data/s775_sources.csv:35; data/e347_steps.csv:5','Do not assume every >$50,000 individual remittance needs the same tax recordal: announcement distinguishes categories and foreign-individual payments; check bank and tax authority.','filing'),
('F08','This supplement: all scenario costs','Intermediary deductions, account-specific fees, actual execution price, taxes and eligibility unknown; total landed cost left blank.','fee'),
('F09','Repository-wide audit coverage','Selected high-risk rows and automated pattern scans reviewed, not a complete line-by-line verification of all repository content. Remaining claims require independent review.','safe'),
]

def writecsv(name, header, rows):
    with (P/'data'/('fe05_'+name+'.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)
def links(*ids):
    return ' '.join('<a href="'+html.escape(S[i],quote=True)+'">'+html.escape(i.upper())+'</a>' for i in ids)
def table(headers,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th scope="col">'+html.escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def esc(x): return html.escape(str(x))
writecsv('methods',['id','method','status','eligibility','pros_cons','steps','official_source','priced_scenario'],[(a,b,c,d,e,f,S[g],h) for a,b,c,d,e,f,g,h in methods])
writecsv('questions',['question','known_or_missing','discovery','official_source'],[(a,b,c,S[d]) for a,b,c,d in questions])
writecsv('penalties',['topic','detail','official_source'],[(a,b,S[c]) for a,b,c in penalties])
writecsv('flags',['id','location','finding','official_source'],[(a,b,c,S[d]) for a,b,c,d in flags])
writecsv('sources',['id','url','accessed','type'],[(k,v,'2026-11-11','provider first-party' if k in ('wise','wu','boc','fee','bank') else 'government / regulator') for k,v in S.items()])
ladder=[]
for ident,name,status,elig,pros,step,src,priced in methods:
 for n in range(10000,400001,10000):
  q=quote(n) if priced else ('','','','','')
  ladder.append((ident,n,*q,'',S[src],S['boc'] if priced else '',S['fee'] if priced else ''))
writecsv('ladder',['method_id','gross_usd','cny_for_usd','spread_vs_mid_usd','boc_fee_cny','boc_fee_mid_usd','known_cost_usd','total_landed_cost_usd','route_source','rate_source','fee_source'],ladder)
nav=[('dashboard','Overview'),('questions','Questions'),('methods','Methods'),('costs','Costs'),('steps','Steps'),('penalties','Taxes & risks'),('flagged','Flagged'),('sources','Sources')]
css='''*{box-sizing:border-box}body{font:16px/1.55 system-ui,sans-serif;color:#17283d;background:#f6f8fb;margin:0}header{background:#10263c;color:white;padding:1.3rem max(1rem,calc((100% - 1100px)/2))}header p{color:#c2d9ec}nav{display:flex;gap:.7rem;overflow:auto;padding:1rem;background:white;white-space:nowrap}nav a{color:#064f75}main{max-width:1100px;margin:auto;padding:1.2rem}h1,h2{line-height:1.2}a{color:#075f88}.card{background:white;border:1px solid #dce4ec;border-radius:10px;padding:1rem;margin:1rem 0}.alert{border-left:4px solid #c47720}.scroll{overflow-x:auto}table{border-collapse:collapse;background:white;width:100%;min-width:680px}th,td{text-align:left;padding:.65rem;border-bottom:1px solid #dce4ec;vertical-align:top}th{background:#eaf1f6}small{color:#516477}footer{padding:2rem 1rem;text-align:center}details{margin:1rem 0;background:white;padding:1rem;border:1px solid #dce4ec;border-radius:8px}summary{font-weight:700;cursor:pointer}'''
(P/'assets/fe05.css').write_text(css,encoding='utf-8')
intro='''<section class="card alert"><strong>Start with the source of your money.</strong> A U.S. passport alone does not establish a $50,000 annual FX purchase entitlement. For a foreign individual’s lawful current-account income, SAFE requires ID and source evidence including tax documentation. <a href="%s">SAFE guidance</a></section><section class="card"><h2>Best first move</h2><p>Ask your bank to classify your account and identify the correct route, then collect evidence and obtain an all-in quote. Sale proceeds, inherited property and emigrant property have different procedures; do not borrow other people’s quotas or use informal exchange.</p><p>Exchange rate spread and bank fees are costs, not necessarily penalties. Tax depends on income, history and U.S. currency basis; the transfer amount alone cannot determine it.</p><p><a href="fe05-questions.html">Start with the decision checklist →</a></p></section><section class="card"><h2>What this edition can and cannot tell you</h2><p>Historical BOC quote observed 11 November 2026, 15:30:04 Beijing: USD spot bid 6.6606, ask 6.6886 CNY per USD. The model is illustrative, not a quote. Unknown costs and taxes are blank. <a href="fe05-costs.html">See all 40 amounts and assumptions</a>.</p><p>Selected repository findings are published, but the entire repository has not been independently verified line by line. <a href="fe05-flagged.html">See limitations and flags</a>.</p></section>'''%S['foreign']
pages={'dashboard':intro,
'questions':'<p>Known: U.S. citizenship and a mainland bank account holding CNY. All other personal facts require confirmation.</p>'+table(['Decision question','Known / missing','How to discover','Source'],[(esc(a),esc(b),esc(c),links(d)) for a,b,c,d in questions]),
'methods':'<p>Eligibility is conditional on facts, bank review and current rules. This is a practical catalogue, not proof that every conceivable route has been exhausted.</p>'+table(['Route','Status','Eligibility','Benefits and limitations','Source'],[(esc(b),esc(c),esc(d),esc(e),links(g)) for a,b,c,d,e,f,g,h in methods]),
'steps':''.join('<details><summary>'+esc(b)+' — '+esc(c)+'</summary><p>'+esc(f)+'</p><p>'+links(g)+'</p></details>' for a,b,c,d,e,f,g,h in methods),
'penalties':'<p>Not legal or tax advice. Penalties are contingent, not routine transaction fees; no personalized tax or penalty has been estimated.</p>'+table(['Issue','Rule / caveat','Source'],[(esc(a),esc(b),links(c)) for a,b,c in penalties])+'<p>PRC home sales: <a href="'+S['vat']+'">2026 housing VAT announcement</a>. FBAR and Form 8938 are separate: <a href="'+S['irs']+'">IRS comparison</a>. The U.S.–China treaty and its saving clause require case-specific analysis: <a href="https://www.irs.gov/pub/irs-trty/china.pdf">IRS treaty text</a>.</p>',
'flagged':'<p>These findings are review items, not a finding that the account holder violated any rule. Other layers are preserved; historical rates need not agree.</p>'+table(['ID','Location','Issue / needed action','Source'],[(esc(a),esc(b),esc(c),links(d)) for a,b,c,d in flags]),
'sources':'<p>Read 11 November 2026. BOC and U.S. bank sites are primary provider sources; government publications are authoritative references for legal rules. Dynamic rates can change.</p>'+table(['ID','Source','Type'],[(esc(k),'<a href="'+esc(v)+'">Open source</a>','Provider' if k in ('wise','wu','boc','fee','bank') else 'Government / regulator') for k,v in S.items()])}
costnote='''<section class="card alert"><strong>Not a total cost or a promise of eligibility.</strong> Blank cells mean unverified or inapplicable, not zero. The shown BOC scenario assumes one permitted gross USD wire with BOC e-banking fees paid separately in CNY. For comparison, spread = (gross USD × ask − gross USD × bid/ask midpoint) / midpoint; fee is translated at that midpoint. No tax, receiving fee, intermediary deduction, discount, legal expense or time cost is included. The bank may use a different fee calculation or decline the route. Ask for a live quote. '''+links('boc','fee','bank')+'</section>'
body=costnote
for ident,name,status,elig,pros,step,src,priced in methods:
    rows=[r for r in ladder if r[0]==ident]
    body+='<details '+('open' if ident=='income' else '')+'><summary>'+esc(name)+' — '+('BOC scenario' if priced else 'cost unverified / not applicable')+'</summary><p>'+esc(elig)+' '+links(src)+'</p>'
    body+=table(['Gross USD','CNY to buy USD','Spread USD','BOC fee CNY','Known cost USD','Total landed cost','Sources'],[(f'${r[1]:,}',esc(r[2]),esc(r[3]),esc(r[4]),esc(r[6]),esc(r[7]),links(src,*(['boc','fee'] if priced else []))) for r in rows])+'</details>'
pages['costs']=body
for key,title in nav:
    doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+' | China funds guide</title><link rel="stylesheet" href="assets/fe05.css"></head><body><header><small>RESEARCH SUPPLEMENT · 11 NOV 2026</small><h1>'+esc(title)+'</h1><p>Moving CNY from mainland China to USD · verify eligibility before acting</p></header><nav aria-label="Sections">'+''.join('<a href="fe05-'+x+'.html">'+esc(y)+'</a>' for x,y in nav)+'</nav><main>'+pages[key]+'</main><footer>Informational only · <a href="fe05-flagged.html">Unverified items</a> · <a href="index.html">Repository home</a></footer></body></html>\n'
    (P/('fe05-'+key+'.html')).write_text(doc,encoding='utf-8')
