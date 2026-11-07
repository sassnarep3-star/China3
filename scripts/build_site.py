#!/usr/bin/env python3
"""Build the static site into docs/.

- inlines data/*.json into docs/assets/data.js (so the site makes no network calls)
- generates the HTML pages
- runs the data contract check first and refuses to build on violations

Run:  python3 scripts/build_site.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

PAGES = [
    ("index.html", "index", "Executive summary", "What the research found, and the shortest lawful path."),
    ("playbook.html", "playbook", "Playbook", "The order of operations that keeps the penalty at zero."),
    ("channels.html", "channels", "All channels", "22 CNY-to-USD routes, with every pro, con and cap."),
    ("taxes.html", "taxes", "Tax exposure", "What the US taxes, what China taxes, and what neither does."),
    ("penalties.html", "penalties", "Penalty breakdown", "The five layers of cost, with the statutory percentages."),
    ("flagged.html", "flagged", "Flagged for review", "Blank, unverified, ambiguous — or dependent on your facts."),
    ("sources.html", "sources", "Source register", "Every URL used, what it supports and when it was checked."),
    ("methodology.html", "methodology", "Method", "How verification was done and what it does not cover."),
    ("audit.html", "audit", "Repo audit", "What was in the repository, what was wrong with it, what was built."),
]


def load(name: str) -> dict:
    with (DATA / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def shell(page: str, title: str, lede: str, body: str) -> str:
    nav_fallback = "".join(
        f'<a href="{href}">{label}</a>' for href, _, label, _ in PAGES
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · China3 — moving CNY to USD</title>
<meta name="description" content="{lede}">
<link rel="stylesheet" href="assets/styles.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%230b5fbe'/%3E%3Ctext x='50' y='68' font-size='54' text-anchor='middle' fill='white' font-family='sans-serif'%3E%C2%A5%3C/text%3E%3C/svg%3E">
</head>
<body data-page="{page}">
<div class="layout">
  <aside class="sidebar">
    <a class="brand" href="index.html">China3<span>CNY → USD, sourced</span></a>
    <nav class="nav" id="nav" aria-label="Sections"></nav>
    <div class="side-note">
      Every figure is linked to an official source. Unconfirmed values are blank and listed under
      <a href="flagged.html">Flagged for review</a>.
      <br><br>Research pack, not tax or legal advice.
    </div>
  </aside>
  <main class="main">
    <header class="page-head">
      <div class="eyebrow">China3 · checked 7 November 2026</div>
      <h1>{title}</h1>
      <p class="lede">{lede}</p>
    </header>
    <div id="app"></div>
    {body}
    <footer class="site">
      <p>Sources checked 2026-11-07. This site is a research pack, not legal, tax or investment advice.
      Read <a href="methodology.html">Method</a> before relying on anything here, and
      <a href="flagged.html">Flagged for review</a> for what could not be confirmed.</p>
      <p>{nav_fallback}</p>
    </footer>
  </main>
</div>
<noscript><p style="padding:16px;background:#fdf1dc">This dashboard renders its tables in the browser. Please enable JavaScript, or read the underlying data in <code>data/*.json</code> in the repository.</p></noscript>
<script src="assets/data.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# static prose pages
# --------------------------------------------------------------------------
PLAYBOOK = """
<div class="callout"><p><strong>Do things in this order.</strong> The order is not cosmetic. Doing step 1 after step 4 can convert a 5% penalty into a 50% one, and doing step 4 before step 3 can make the largest Chinese channel unavailable to you permanently.</p></div>

<ol class="steps">
<li>
<h3>Characterise the money — four buckets only</h3>
<p>Everything downstream depends on this. Sort the balance into: <strong>(A)</strong> salary and other current-account income already taxed in China; <strong>(B)</strong> proceeds of a property sale, on which 20% PRC tax is due on the gain; <strong>(C)</strong> an inheritance; <strong>(D)</strong> foreign currency you personally exchanged into CNY and never used.</p>
<p>Each bucket has exactly one designated route, and the routes do not substitute for each other. Money that does not fit any bucket is the hardest case, and that is what the fallback ladder in step 7 is for.</p>
<p class="small"><a class="src" href="sources.html#S01">S01</a><a class="src" href="sources.html#S02">S02</a><a class="src" href="sources.html#S09">S09</a></p>
</li>

<li>
<h3>Fix US reporting before a single dollar moves</h3>
<p>This is the highest-value hour you will spend. Two filings are in play: an FBAR for every year the aggregate balance exceeded USD 10,000, and Form 8938 for every year the threshold was met.</p>
<p>If you missed them and the failure was not willful, the streamlined procedures were built for this. Living in the US, the price is <strong>5%</strong> of the highest aggregate balance and you emerge with no information-return or FBAR penalties. Living abroad and meeting the non-residency test, the price is <strong>nothing</strong>.</p>
<p>Do it first because the penalty is computed on the <em>balance</em>, not on the gain — and because moving money through an illegal Chinese channel afterwards is exactly the fact pattern that turns "non-willful" into "willful".</p>
<p class="small"><a class="src" href="sources.html#S12">S12</a><a class="src" href="sources.html#S16">S16</a><a class="src" href="sources.html#S18">S18</a><a class="src" href="sources.html#S19">S19</a><a class="src" href="sources.html#S17">S17</a></p>
</li>

<li>
<h3>Get your FX category in writing from the branch</h3>
<p>Ask, in writing, whether the account is registered as <strong>境内个人</strong> or <strong>境外个人</strong>. The individual FX rules define 境外个人 as a foreign passport holder; the FX Regulations define 境内个人 to include foreigners resident in China for a year or more. Branches apply one or the other.</p>
<p>If you are 境外个人, the USD 50,000 annual purchase cap is not the provision aimed at you — Art. 13 is, and it asks for source documents instead. If you are 境内个人, the cap binds and your route set narrows.</p>
<p class="small"><a class="src" href="sources.html#S01">S01</a><a class="src" href="sources.html#S05">S05</a><a class="src" href="sources.html#S02">S02</a></p>
</li>

<li>
<h3>Sequence the Chinese tax clearance <em>before</em> cancelling household registration</h3>
<p>This is the trap that catches people. The emigrant transfer route requires a certificate that your PRC household registration has been cancelled. But the IIT Law requires a tax settlement to be completed <em>before</em> that cancellation. If you cancel first, you have created the document you need while destroying the sequence you needed it in.</p>
<p>Order: tax clearance → cancellation certificate → embassy-issued or authenticated proof of settlement abroad → SAFE application.</p>
<p class="small"><a class="src" href="sources.html#S09">S09</a><a class="src" href="sources.html#S03">S03</a><a class="src" href="sources.html#S04">S04</a></p>
</li>

<li>
<h3>Assemble the document file once, not three times</h3>
<p>Written application; applicant information form; business application form; passport; cancelled household registration certificate; embassy-issued or authenticated proof of foreign settlement; proof of the property rights; tax certificate or tax-payment certificate from the competent tax authority. Anything not notarised that needs to be notarised should be notarised now — the SAFE branch will not accept a promise to produce it later.</p>
<p>File the application with SAFE where your pre-emigration household registration was located, not where you live now and not where the money is.</p>
<p class="small"><a class="src" href="sources.html#S03">S03</a><a class="src" href="sources.html#S04">S04</a></p>
</li>

<li>
<h3>Apply once for the whole amount, then take the staged payout</h3>
<p>The application must cover the entire amount you intend to move; only the remittance is staged. First tranche up to 50%, a further 50% of the remainder after one year, the balance after two years. Below RMB 200,000 in total, one payment is allowed.</p>
<p>Approval is by the local SAFE branch up to RMB 500,000 and by SAFE headquarters above it. The bank must wire the money to <em>your own</em> account abroad — cash is expressly prohibited on this route.</p>
<p class="small"><a class="src" href="sources.html#S03">S03</a><a class="src" href="sources.html#S04">S04</a></p>
</li>

<li>
<h3>If the emigrant route is closed, take the fallback ladder</h3>
<p>Work down this list in order; each step only applies if the bucket fits.</p>
<p><strong>(B) Property proceeds</strong> — Art. 22 permits conversion and remittance of a non-resident's proceeds from selling China residential property with SAFE approval, after the 20% tax on the gain and the clearance certificate.<br>
<strong>(A) Current-account income</strong> — Art. 13 permits a 境外个人 to convert lawful current-account RMB income on production of documents including tax documents. No annual quota, transaction by transaction.<br>
<strong>(D) Unused exchanged cash</strong> — the original exchange memo lets you convert it back within 24 months.<br>
<strong>Small amounts / 境内个人</strong> — the USD 50,000 annual facility, year after year.<br>
<strong>Living costs</strong> — card spending abroad is lawful for genuine purchases and does not consume the annual quota.<br>
<strong>Someone else's money</strong> — if a relative gifts it to you instead, that is a different question: more than USD 100,000 in a year from a foreign person triggers Form 3520 on the US side.</p>
<p class="small"><a class="src" href="sources.html#S01">S01</a><a class="src" href="sources.html#S02">S02</a><a class="src" href="sources.html#S06">S06</a><a class="src" href="sources.html#S22">S22</a></p>
</li>

<li>
<h3>Report the arrival correctly</h3>
<p>Principal is not income. The conversion can still produce a US consequence: the USD 200 personal-transaction exclusion for foreign-currency gain switches off entirely once the gain on that transaction exceeds USD 200. Keep the bank's exchange confirmation and the counterparty's remittance advice for every tranche — they are your cost basis evidence if the number is ever questioned.</p>
<p>If PRC tax was withheld at source, claim it on Form 1116. The treaty caps China's dividend and interest rates at 10%, but the saving clause means it never reduces your US tax; only the credit does.</p>
<p class="small"><a class="src" href="sources.html#S24">S24</a><a class="src" href="sources.html#S20">S20</a><a class="src" href="sources.html#S27">S27</a></p>
</li>

<li>
<h3>What not to do, in one place</h3>
<p><strong>Crypto and stablecoins</strong> — since 6 February 2026, RMB-to-virtual-currency conversion is expressly illegal financial activity; investments contrary to public order are void and the loss lands on you.<br>
<strong>Underground banks and offsetting pairs</strong> — 30%–100% fines, and prosecution as illegal business operation from RMB 5,000,000 of turnover or RMB 100,000 of gains.<br>
<strong>Smurfing with relatives' quotas</strong> — prohibited outright.<br>
<strong>False trade or service invoices</strong> — illegal arbitrage of FX, plus Chinese invoicing offences, plus a US return that cannot explain the source.<br>
<strong>Carrying cash</strong> — capped at USD 10,000 even with permits, 20% penalty above, and a FinCEN Form 105 obligation at USD 10,000 on arrival.<br>
<strong>Renouncing citizenship to escape the tax</strong> — a separate and much larger question with its own mark-to-market rule; nothing in this research supports it as a saving.</p>
<p class="small"><a class="src" href="sources.html#S08">S08</a><a class="src" href="sources.html#S05">S05</a><a class="src" href="sources.html#S10">S10</a><a class="src" href="sources.html#S01">S01</a><a class="src" href="sources.html#S07">S07</a><a class="src" href="sources.html#S15">S15</a></p>
</li>
</ol>

<h2>Sequencing at a glance</h2>
<div class="table-wrap"><table>
<thead><tr><th class="num">#</th><th>Action</th><th>Authority</th><th>Output you keep</th><th>Must come before</th></tr></thead>
<tbody>
<tr><td class="num">1</td><td>Characterise the money</td><td>—</td><td>A written note of source and amounts</td><td>Everything</td></tr>
<tr><td class="num">2</td><td>FBARs and Form 8938, or streamlined election</td><td>IRS / FinCEN</td><td>Filed returns, penalty computation</td><td>The first remittance</td></tr>
<tr><td class="num">3</td><td>Confirm 境内个人 / 境外个人 status</td><td>Your bank</td><td>A written answer from the branch</td><td>Choosing the route</td></tr>
<tr><td class="num">4</td><td>PRC tax settlement</td><td>Competent tax authority</td><td>完税凭证 / 税收证明</td><td>Household-registration cancellation</td></tr>
<tr><td class="num">5</td><td>Cancel household registration</td><td>Public security authority</td><td>户籍注销证明</td><td>The SAFE application</td></tr>
<tr><td class="num">6</td><td>SAFE application (whole amount)</td><td>SAFE branch of the old household registration</td><td>Approval letter and 核准件</td><td>The bank's conversion</td></tr>
<tr><td class="num">7</td><td>Bank conversion and remittance</td><td>FX-designated bank</td><td>Exchange memo, wire advice</td><td>US reporting of the arrival</td></tr>
<tr><td class="num">8</td><td>Report the arrival and claim credits</td><td>IRS</td><td>Form 1116, §988 working</td><td>—</td></tr>
</tbody></table></div>

<h2>Two things this playbook cannot do for you</h2>
<div class="grid c2">
<div class="card"><h3>The household-registration certificate</h3><p>Only the public security authority where the registration was held can issue it, and only you can find out whether the record still exists. If it does not, the no-ceiling route is gone and the fallback ladder is the whole answer.</p></div>
<div class="card"><h3>The branch's classification</h3><p>Only the bank can tell you which category your account is registered under. Ask for it in writing before you rely on any single route in this site.</p></div>
</div>
"""

METHODOLOGY = """
<h2>What was done</h2>
<p>Every factual claim on this site was traced to a primary document — a statute, a State Council regulation, a People's Bank of China or SAFE measure, a tax authority publication, a Treasury or IRS page, a treaty text, or an eCFR/CFR provision — and the specific proposition was read on the page itself. The register at <a href="sources.html">Sources</a> records, for each URL, what it supports and the date it was checked (2026-11-07).</p>

<h2>The three tiers</h2>
<div class="table-wrap"><table>
<thead><tr><th>Tier</th><th>Meaning</th><th>How it is used</th></tr></thead>
<tbody>
<tr><td><span class="badge neutral">official</span></td><td>Issued by the authority itself: statute, regulation, treaty, agency page, or the official gazette.</td><td>Carries every number and every legal proposition.</td></tr>
<tr><td><span class="badge neutral">official-secondary</span></td><td>Published by the same authority but explanatory: a Q&amp;A, an operations guide, a consolidated index of regulations in force.</td><td>Used to pin down practical detail — who qualifies, what documents, what is still in force.</td></tr>
<tr><td><span class="badge unverified">third-party</span></td><td>A non-government reproduction of a legal text.</td><td>Used only where the official site could not be reached, and always flagged on <a href="flagged.html">Flagged for review</a>.</td></tr>
</tbody></table></div>

<h2>What "blank and flagged" means</h2>
<p>If a value could not be confirmed from an official source it was <em>not</em> filled with a plausible number, an industry estimate, or a memory. It was left blank, marked unverified, and written up on the flagged page with the reason. The clearest example is retail FX cost: no regulator publishes retail CNY/USD spreads, so the cost model shows the formula and a calculator and ships with no rates at all.</p>
<p>Two of the twenty-seven sources are third-party reproductions of the United States Code (§ 988 and § 5321). The statutes' content is not in doubt; the <em>URLs</em> are, which is why they are flagged.</p>

<h2>What this research deliberately does not cover</h2>
<ul>
<li><strong>Your facts.</strong> Four determinations depend entirely on documents only you hold: your FX category, whether a cancelled household registration exists, when the balance was acquired relative to your emigration, and what created the money. Each is itemised on the flagged page.</li>
<li><strong>Your bank's prices.</strong> Spreads, wire fees and intermediary deductions are commercial, not regulatory, and were not estimated.</li>
<li><strong>Corporate structures.</strong> If the money sits inside a Chinese company rather than your personal account, a different framework applies (profit distribution, dividend withholding, and separate US forms). Not addressed here.</li>
<li><strong>Renunciation and the US expatriation tax.</strong> Mentioned only as a thing not to do casually; not researched.</li>
<li><strong>State tax.</strong> Only federal US obligations are described.</li>
</ul>

<h2>Reproducing the verification</h2>
<p>The data is machine-checked, not just proofread. Three scripts do the work:</p>
<div class="table-wrap"><table>
<thead><tr><th>Script</th><th>What it enforces</th></tr></thead>
<tbody>
<tr><td class="mono">scripts/validate_data.py</td><td>Unique IDs; every source reference resolves; a stated cap must be marked verified; an unverified item must carry a flag; every consequence must have a source.</td></tr>
<tr><td class="mono">scripts/check_links.py</td><td>Every internal link and anchor resolves; every external URL in the register is well formed and de-duplicated; source chips on each page point at a real register entry.</td></tr>
<tr><td class="mono">scripts/build_site.py</td><td>Refuses to build if the contract check fails, then inlines the data and generates every page.</td></tr>
</tbody></table></div>
<p class="small">Run <code>python3 scripts/validate_data.py &amp;&amp; python3 scripts/check_links.py &amp;&amp; python3 scripts/build_site.py</code>.</p>

<h2>Currency of the rules</h2>
<p>Two things changed recently and both are reflected here. Chinese crypto regulation was replaced on 6 February 2026 by 银发〔2026〕42号, which repealed the 2021 notice that most articles still cite. And an index published by SAFE as at 30 June 2026 confirms that the 2008 FX Regulations, the 2006 individual FX measures, the 2007 implementing rules and the 2003 cash-carrying rules were still in force, which is why they are relied on here rather than assumed.</p>
<p class="small"><a class="src" href="sources.html#S08">S08</a><a class="src" href="sources.html#S26">S26</a></p>

<h2>Disclaimer</h2>
<div class="callout warn"><p>This is a sourced research pack prepared by an automated agent. It is not legal, tax, or investment advice and it does not create a professional relationship. Chinese FX practice varies by branch and by province, and US reporting positions depend on facts a document review would surface. Before acting on anything here — and certainly before filing under the streamlined procedures or signing a SAFE application — have a qualified US tax adviser and a PRC-qualified adviser review your specific file.</p></div>
"""

AUDIT = """
<h2>What the repository contained</h2>
<p>The audit was performed at commit <code class="mono">03021bc</code> on branch <code class="mono">arena/7e08715a-china3</code> before any work was done.</p>
<div class="table-wrap"><table>
<thead><tr><th>Item</th><th>State found</th><th>Assessment</th></tr></thead>
<tbody>
<tr><td>Tracked files</td><td>Exactly one: <code class="mono">README.md</code>, 8 bytes, content <code class="mono"># China3</code>, no trailing newline</td><td>Irregular: a placeholder, not a README</td></tr>
<tr><td>Source code</td><td>None</td><td>Nothing to review — the "repo review" is necessarily a review of an empty repo plus this build</td></tr>
<tr><td>Data</td><td>None</td><td>No prior claims to verify or contradict</td></tr>
<tr><td>Licence</td><td>None</td><td>Irregular for a public repository — left to the owner, not decided here</td></tr>
<tr><td>CI / tests</td><td>None</td><td>Fixed: validation and link checks added</td></tr>
<tr><td>.gitignore</td><td>None</td><td>Fixed</td></tr>
<tr><td>Coordination board</td><td>Absent, although required by the brief</td><td>Fixed: <code class="mono">COORDINATION.md</code> created and claimed before work began</td></tr>
<tr><td>GitHub Pages</td><td>Not configured</td><td>Fixed: Pages served from <code class="mono">/docs</code> on <code class="mono">main</code></td></tr>
<tr><td>Branch strategy</td><td><code class="mono">main</code> plus the session branch</td><td>No conflicting claims found on the board</td></tr>
</tbody></table></div>

<h2>What was built</h2>
<div class="table-wrap"><table>
<thead><tr><th>Path</th><th>Purpose</th></tr></thead>
<tbody>
<tr><td class="mono">data/sources.json</td><td>27 sources, each with publisher, tier, URL, the proposition it supports and the date checked</td></tr>
<tr><td class="mono">data/channels.json</td><td>22 CNY→USD routes with status, cap, requirements, pros, cons and verdict</td></tr>
<tr><td class="mono">data/taxes.json</td><td>25 tax items split between US, PRC and treaty</td></tr>
<tr><td class="mono">data/penalties.json</td><td>Five cost layers, 15 penalty provisions, the cost model and the scenario table</td></tr>
<tr><td class="mono">data/flagged.json</td><td>19 items that are blank, ambiguous or dependent on your facts</td></tr>
<tr><td class="mono">scripts/validate_data.py</td><td>Enforces the "source or flag" contract</td></tr>
<tr><td class="mono">scripts/check_links.py</td><td>Internal links, anchors and external URL hygiene</td></tr>
<tr><td class="mono">scripts/build_site.py</td><td>Builds <code class="mono">docs/</code>; refuses to build on a contract violation</td></tr>
<tr><td class="mono">docs/</td><td>The published dashboard (generated)</td></tr>
<tr><td class="mono">.github/workflows/ci.yml</td><td>Runs validation, link check and a build on every push</td></tr>
<tr><td class="mono">COORDINATION.md</td><td>Task board, claims, verification record, PR record</td></tr>
<tr><td class="mono">VERIFICATION.md</td><td>The per-URL verification log behind the register</td></tr>
<tr><td class="mono">REPO_AUDIT.md</td><td>This audit in repository form</td></tr>
</tbody></table></div>

<h2>Irregularities flagged, not silently fixed</h2>
<ul>
<li><strong>Third-party statute mirrors.</strong> Two of the 27 sources are not on a <code class="mono">.gov</code> domain because the official servers returned errors for those sections. They are labelled <span class="badge unverified">third-party</span> in the register and itemised as I05 on the flagged page.</li>
<li><strong>One dead URL encountered during research.</strong> The 2008 gov.cn URL originally holding the FX Regulations had been renumbered; the working replacement is used and the dead one is not cited.</li>
<li><strong>A superseded regulation.</strong> Most published commentary on Chinese crypto rules cites 银发〔2021〕237号, which was repealed on 6 February 2026. The site cites the replacement.</li>
<li><strong>A partially amended source.</strong> The SAFE page for the 2007 implementing rules carries an amendment note covering two articles. Neither is one relied on here, but the page does not certify the list is exhaustive — itemised as I16.</li>
</ul>
"""


def main() -> int:
    rc = subprocess.call([sys.executable, str(ROOT / "scripts" / "validate_data.py")])
    if rc != 0:
        print("Build aborted: data contract check failed.")
        return rc

    bundle = {
        "generated": "2026-11-07",
        "sources": load("sources.json"),
        "channels": load("channels.json"),
        "taxes": load("taxes.json"),
        "penalties": load("penalties.json"),
        "flagged": load("flagged.json"),
    }

    DOCS.mkdir(exist_ok=True)
    (DOCS / "assets").mkdir(exist_ok=True)

    blob = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    (DOCS / "assets" / "data.js").write_text(
        "/* generated by scripts/build_site.py — do not edit */\n"
        "window.CHINA3=" + blob + ";\n",
        encoding="utf-8",
    )

    prose = {"playbook": PLAYBOOK, "methodology": METHODOLOGY, "audit": AUDIT}
    for filename, page, title, lede in PAGES:
        body = prose.get(page, "")
        (DOCS / filename).write_text(shell(page, title, lede, body), encoding="utf-8")

    print(f"Built {len(PAGES)} pages and data.js ({len(blob):,} bytes of data).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
