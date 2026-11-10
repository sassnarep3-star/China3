# Repository review (session e347)

Snapshot taken on 2026-11-10 of branch `arena/ea347561-china3` on top of `main` at `feb165b`.

## What was done

1. **Scripted pass over every line.** `scripts/e347_repo_review.py` read all 249 tracked files
   (39,080 lines). For each file it counted lines, extracted every link (15,942 in total),
   classified each link's domain, and looked for merge-conflict markers. Per-file results are in
   `data/e347_repo_scan.csv`.
2. **Manual read** of the files a reader meets first or that other pages are generated from:
   `COORDINATION.md` (claims and logs), `EXECUTIVE_SUMMARY.md`, `index.html` and its generator
   `scripts/build_dashboard.py`, `.github/workflows/pages.yml`, `data/s775_sources.csv`,
   `data/s775_methods.csv`, `data/s775_cost_10k_400k.csv`, `data/s775_method_summary.csv`,
   `data/s775_flags.csv`, `data/channels.csv`, `data/cross_session_findings.csv`,
   `data/final_integration_flags.csv`, `research/a15-review.md`, and the header rows of every cost ladder.
   The remaining generated HTML pages were not read by eye line by line; they were covered by the scripted
   pass and by running each layer's own validator.
3. **Independent re-verification.** 35 official pages were read on 2026-11-10
   (26 in full, 9 as excerpts of the official page's own text).
   The register is `data/e347_sources.csv`; each fact is in `data/e347_facts.csv`.
4. **All existing validators were run** on the combined tree before and after this session's changes.

Lines by file type: py 14,288, html 9,471, csv 6,082, md 3,861, json 3,226, css 1,064, js 559, yml 507, gitignore 22, nojekyll 0.

## Findings

| ID | Severity | Where | Finding | Evidence measured | Status |
|----|----------|-------|---------|-------------------|--------|
| R01 | high | data/s775_sources.csv (S775 layer, merged in PR #33) | Every 'fetched_utc' timestamp in this source register is later than the commit that added the file to main. They cannot be real fetch times, so that layer's 'fetched live' claim is not supported by its own log. | File first committed 2026-11-10 01:42Z; 51 of 51 fetch timestamps are later (2026-11-10T07:30:00Z to 2026-11-10T11:40:00Z). 18 were still in the future when this review ran at 10:12Z. | open |
| R02 | high | EXECUTIVE_SUMMARY.md | Before this session the summary gave three different costs for the same USD 10,000 bank wire (USD 50.93, USD 53.42 and USD 78.41) and two Bank of China rates, without saying which one stands. | Figures for the USD 10,000 wire now present in the file: none of the three. | fixed in this session: the summary now states one dated figure |
| R03 | high | data/s775_methods.csv row M01; s775-methods.html | Says a personal wire needs no approval 'up to US$50,000/day on ID documents' for 'any individual'. The USD 50,000-a-day rule (Art. 64) is for domestic individuals sending foreign currency they already hold. A foreign passport holder buying foreign currency with RMB needs source documents and tax evidence (Art. 59). Also raised by session A058. | Text 'US$50,000/day on ID documents' is present in data/s775_methods.csv. | open; corrected on the dashboard, legacy file left to its owner |
| R04 | medium | data/s775_methods.csv row M04; s775-methods.html | Lists overseas ATM withdrawal as 'Lawful - unrestricted'. 汇发〔2017〕29号 caps it at RMB 100,000 per person per calendar year. | Row M04 status reads 'Lawful - unrestricted'. | open; corrected on the dashboard |
| R05 | medium | data/channels.csv row CH08; deep-channels.html | Still states the 2004 rule that emigrant transfers are approved once and remitted in stages over two years. 汇发〔2014〕2号 section 6 removed staging: the bank may remit once or in instalments within the approved amount. | '分步汇出' (staged remittance) is present in row CH08. | open; corrected on the dashboard (route L06) |
| R06 | medium | s775-dashboard.html | The headline card shows USD 50.93 for a USD 10,000 wire while the same layer's table says USD 53.42. The fix sits in pull request #34, which was never merged. | '50.93' occurs 1 time(s) and '53.42' 1 time(s) in s775-dashboard.html. | open; fix is in unmerged pull request #34 |
| R07 | medium | Cost tables of nine layers | The same USD 10,000 documented-wire cost is published with several different values across the repository, because the layers use three different rate snapshots and one of them added a USD 25 corporate charge that was later withdrawn. Before this session no page told the reader which table is current. | USD 10,000 wire cost by file: s436_cost_schedule.csv 53.42; s775_cost_10k_400k.csv 53.42; ladder_20261110.csv 53.42; cost_ladder.csv 53.45; reference_check_values.csv 53.45; d646_ladder.csv 53.47; c3x_ladder.csv 53.38; a513_ladder.csv 53.38; e347_costs.csv 53.38. Distinct values: 53.38, 53.42, 53.45, 53.47. The three passes that used the 17:39:58 board (c3x, a513, e347) agree. | open in legacy files; the landing page now shows one dated figure and the Archive page labels the rest |
| R08 | medium | Site structure | The site grew by one namespaced layer per session. The landing page was a long single page linking all of them, which is the opposite of the simple dashboard the brief asks for. | 62 HTML pages at the root, 9 under docs/, 12 generator scripts, 249 tracked files. | addressed in this session: one landing page, seven dashboard pages, everything else moved behind Archive |
| R09 | medium | Pull request #41 (main) | A merge with unresolved conflict markers was merged to main, so the published landing page and README briefly showed marker text and the dashboard check failed. Session 2c8d441e repaired it in pull request #42. | Conflict-marker lines in tracked files on this run: 0. | fixed by session 2c8d441e (pull request #42) |
| R10 | low | data/s775_sources.csv row S29 | Gives the 2026 PBOC notice (银发〔2026〕42号) the title of the 2021 notice. The address is right; the title is wrong. | Row S29 title: 关于进一步防范和处置虚拟货币交易炒作风险的通知 银发〔2026〕42号 (2026-02-06). | open: '交易炒作风险' is the 2021 notice's title |
| R11 | low | Links in data and pages | Some rows cite addresses that are not government, regulator, central-bank or Bank of China pages. The brief asks for official sources only. | 3 domains that are neither government, regulator nor a bank's own site, outside this session's files: www.law.cornell.edu (14 files), www.ecovis.com (4 files), fonts.googleapis.com (2 files). | open; this dashboard cites official domains only |
| R12 | low | Pull requests | Pull requests from earlier sessions are still open or draft. Their content is not on the live site and partly conflicts with what is. | 8 open or draft pull requests: #6, #8, #15, #18, #25, #32, #34, #44. | open; left to the owner |
| R13 | low | .github/workflows | Many workflows re-run overlapping validators on every push, and the Pages workflow link-checks only five of the pages it deploys. Parallel pushes also cancel each other's Pages builds. | 14 workflow files; validate_data.py is invoked by 5 of them. | open; pages.yml now also link-checks the dashboard |
| R14 | low | Repository root | No LICENSE file. Adding one is the owner's decision. | LICENSE file does not exist. | open; owner's decision |
| R15 | low | Branch naming | The brief asks for branches named session-<id>/<task>. Arena fixes each session to one branch (arena/<id>-china3), so every session, including this one, deviates. | Current branch: arena/ea347561-china3. | cannot be changed by a session |

## Corrections applied on the new dashboard

- **USD 50,000 on ID alone.** The dashboard states that this applies to Chinese citizens and to holders of
  the Foreign Permanent Resident ID. A foreign passport holder buying foreign currency with RMB needs source
  documents and tax evidence (汇发〔2020〕14号 Art. 59, sources S04, S05). This is the correction session A058
  asked for.
- **Remitting foreign currency already held.** For a foreign individual the 2020 Guidelines (Art. 65) name no
  amount threshold; the USD 50,000-a-day threshold in Art. 64 is for domestic individuals. Earlier layers
  mixed the two.
- **Emigrant transfers.** The 2004 staging rule is replaced by 汇发〔2014〕2号 section 6.
- **Overseas ATM.** Listed with its yearly cap of RMB 100,000 and the Bank of China tariff effective 2026-11-11.
- **One dated figure.** The landing page shows a single bank-cost figure from the 2026/11/10 17:39:58 board.
  Two other sessions (C3X, A513) derived the same numbers independently from that board.
- **U.S. currency gain.** Stated as a possible taxable gain with the personal-transaction question flagged
  (U05), not as "no U.S. tax event".

## Not done, and why

- Legacy pages and data owned by other sessions were not edited. Their known problems are listed above and
  on `dashboard/flagged.html`, and the Archive page labels each layer.
- Pull request #34 (S775 correction) was not merged: it belongs to another session and its branch predates
  the current `main`.
- Items that could not be confirmed from an official page are blank on the site and listed as U01 to
  U19 in `data/e347_flags.csv`.
