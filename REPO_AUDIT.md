# Repository audit

Audited at commit `03021bc` ("Initial commit") on branch `arena/7e08715a-china3`, before any work in this session.

## What was there

```
$ git ls-files
README.md

$ wc -c README.md
8 README.md

$ cat README.md
# China3        (no trailing newline)
```

`du -sh .` was 120 KB, essentially all of it `.git`.

## Findings

| # | Finding | Severity | Action |
|---|---------|----------|--------|
| A1 | The repository is empty apart from an 8-byte `README.md`. There is no source code, no data, no tests, no CI, no documentation. | Informational | Nothing to review. The "repo review" in this project is therefore an audit of an empty repository plus the build created here. |
| A2 | `README.md` has no trailing newline and no content beyond the repository name. | Low | Replaced with a substantive README. |
| A3 | No `LICENSE` in a public repository. | Medium — legal | **Flagged, not fixed.** Choosing a licence is the owner's decision, so none was added. |
| A4 | No `.gitignore`. Generated files and editor droppings would be committed. | Low | Fixed: added `.gitignore`. |
| A5 | No CI, so no check that published figures have sources. | Medium | Fixed: `.github/workflows/ci.yml` runs the data contract check and the link check on every push, and fails the build on a violation. |
| A6 | No GitHub Pages configuration, although the brief requires a live site. | Medium | Fixed: Pages is served from `/docs` on `main`. |
| A7 | `COORDINATION.md` absent, although the brief requires a shared task board to be created if it does not exist. | Medium | Fixed: created and claimed before work started. |
| A8 | No branch other than `main` and the session branch; no competing claims anywhere. | Informational | No conflict to resolve. |

## Irregularities found in the *sources* (recorded on the site)

These were found while researching and are published on the *Flagged for review* page rather than quietly corrected:

| # | Irregularity | Handling |
|---|--------------|----------|
| S1 | Two United States Code sections (§ 988 and § 5321) could only be reached through a non-government mirror; `uscode.house.gov` returns a "temporary format" notice and the govinfo paths for those sections 404. | Cited, labelled `third-party`, and itemised as I05 on the flagged page. |
| S2 | The 2008 gov.cn URL originally holding the FX Regulations has been renumbered and now redirects to the gov.cn homepage. | Replaced with the live URL; the dead one is not cited. |
| S3 | Most published commentary on China's crypto rules cites 银发〔2021〕237号, which was **repealed** on 6 February 2026 by 银发〔2026〕42号. | The site cites the replacement and says so explicitly. |
| S4 | SAFE's page for the 2007 implementing rules is marked "已修改" and notes two amended/repealed articles. | Disclosed as I16; none of the articles relied on here is among them, but the page does not certify the list is exhaustive. |
| S5 | The individual FX measures (2006) and the FX Regulations (2008) define `境内个人` differently. | Not resolved — it cannot be resolved from public sources, because it depends on how the bank registered the account. Published as the single most consequential open question (I03). |

## Files created

See the table in `docs/audit.html`, or:

```
data/{sources,channels,taxes,penalties,flagged}.json
scripts/{validate_data.py,check_links.py,build_site.py}
docs/{index,playbook,channels,taxes,penalties,flagged,sources,methodology,audit}.html
docs/assets/{styles.css,app.js,data.js}   (data.js is generated)
.github/workflows/ci.yml
.gitignore
COORDINATION.md
VERIFICATION.md
REPO_AUDIT.md
README.md
```
