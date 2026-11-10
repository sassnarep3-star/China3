# T3 — U.S. tax and foreign-account reporting

Session `session-c703e38c` · branch `arena/c703e38c-china3` · reviewed 2026-11-07 (UTC)
Scope: `research/us-tax.md`. Structured data: `data/us_rules.csv` (28 rows, one official link each).

## Method

Primary sources only: irs.gov (FAQs, publications, Internal Revenue Manual, form instructions,
treaty documents), fincen.gov (FBAR instructions, BSA guidance), ecfr.gov (31 CFR 1010.821),
federalregister.gov (2026 inflation adjustment), home.treasury.gov (FATCA / S&ED fact sheet).
Secondary sites that appeared in search results (expat blogs, law-firm summaries) were
**not** used as evidence; every figure in `data/us_rules.csv` was traced to an official text.
Full text retrieved: IRS Gifts from foreign person; IRS Comparison of Form 8938 and FBAR
requirements; 31 CFR 1010.821 (all 3 chunks); IRS Publication 525.

## 1. Worldwide income is the baseline

IRS international FAQ Q1: "If you are a U.S. citizen or resident alien living outside the
United States, your worldwide income is subject to U.S. income tax, regardless of where you
live." [U01](https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-about-international-individual-tax-matters).
Publication 54 repeats this and contains the foreign earned income exclusion (Form 2555,
foreign tax home, no credit/deduction for foreign tax on excluded income)
[U02](https://www.irs.gov/publications/p54). Therefore the CNY account's interest is U.S.
taxable even though 财税〔2008〕132号 temporarily exempts PRC savings interest from Chinese IIT.

**Important negative space.** No official source reviewed states in so many words that
"transferring one's own after-tax principal is not a taxable event." The FBAR is documented
as an information report, not a tax return [U06](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements),
[U26](https://www.fincen.gov/system/files/shared/ReportToCongress361.PDF), and §61 defines
gross income as income "from whatever source derived" — but this research does not assert a
tax conclusion for the transfer itself. The value in `data/penalty.csv` row P23 is **blank**
and flagged UNVERIFIED (IR-011, IR-014).

## 2. FBAR

- Trigger: aggregate foreign financial account value exceeds $10,000 at any time during the
  calendar year; cumulative across accounts (two accounts whose combined balance exceeds
  $10,000 at one time → both reported) [U06].
- Due: received by April 15, with a 6-month automatic extension to October 15 [U06],
  [U18](https://www.fincen.gov/system/files/shared/FBAR%20Line%20Item%20Filing%20Instructions.pdf).
  Older IRS/FinCEN materials still say June 30 with no extension (e.g. the 2011 TD F 90-22.1
  instructions and a 2010 proposed rule); those are obsolete. This conflict is resolved in
  favour of the current IRS comparison page and FinCEN instructions.
- Filed electronically through the BSA E-Filing System, not with Form 1040 [U06], [U26].
- Valuation: maximum value in the account currency from periodic statements, converted to
  USD at the **end of calendar year** exchange rate [U06], [U18].
- Penalties: 31 CFR 1010.821 Table 1 (maximum penalty amounts for penalties assessed on or
  after January 17, 2025) gives $16,536 for a non-willful violation (31 USC
  5321(a)(5)(B)(i)) and $165,353 for a willful violation (31 USC 5321(a)(5)(C)(i)(I));
  the statutory willful formulation is "the greater of $100,000 [as adjusted] or 50 percent
  of the balance in the account at the time of the violation"
  [U20](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821),
  [U18], [U11](https://www.irs.gov/irm/part4/irm_04-026-016).
- **IR-008**: the 2026 civil penalty inflation adjustment was cancelled by OMB M-26-11
  because October 2025 CPI-U data were unavailable; agencies continue to apply 2025 amounts
  [U21](https://www.federalregister.gov/documents/2026/07/07/2026-13629/no-adjustment-to-civil-monetary-penalty-amounts).
  The eCFR section was current through 2026-11-05 with its last substantive change on
  2025-01-17, consistent with no 2026 adjustment.
- **IR-010**: eCFR states it is authoritative but not the official legal edition; the annual
  CFR on govinfo.gov is the official print version [U20].

## 3. Form 8938 (FATCA) is a separate obligation

The IRS comparison page states explicitly that the Form 8938 requirement "does not replace or
otherwise affect" the FBAR obligation and that a taxpayer may need to file both, with
separate penalties [U06]. Thresholds (specified individuals): living in the U.S. —
unmarried/MFS >$50,000 on the last day or >$75,000 at any time; MFJ >$100,000 / >$150,000.
Living outside the U.S. — unmarried/MFS >$200,000 / >$300,000; MFJ >$400,000 / >$600,000
[U06], [U07](https://www.irs.gov/instructions/i8938). Form 8938 is attached to the income tax
return and due with it including extensions; Form 8938 uses the taxable-year-end exchange
rate, while FBAR uses the calendar-year-end rate. Penalty: up to $10,000 for failure to
disclose, plus $10,000 for each 30 days after IRS notice, up to $50,000 additional ($60,000
potential); a separate 40% penalty applies to underpayments attributable to undisclosed
foreign financial assets [U08](https://www.irs.gov/businesses/corporations/fatca-information-for-individuals),
[U10](https://www.irs.gov/irm/part5/irm_05-021-006). If no income tax return is required for
the year, no Form 8938 is required [U08].

**IR-009**: the 2014 U.S.–China Strategic and Economic Dialogue fact sheet says the two sides
reached FATCA IGA "agreement in substance" and committed to sign by end-2014
[U23](https://home.treasury.gov/news/press-releases/jl2561), [U22](https://home.treasury.gov/policy-issues/tax-policy/foreign-account-tax-compliance-act).
No signed mainland-China IGA text was found in this research. Hong Kong and Macao have their
own IGAs. China's CRS rules (公告2017年第14号) are a separate OECD regime and do not by
themselves establish U.S. exchange.

## 4. Foreign gifts and Form 3520

IRS "Gifts from foreign person": foreign gifts and bequests are **not subject to income tax**,
but if the aggregate received from a nonresident alien individual or foreign estate in a tax
year exceeds $100,000, it must be reported on Form 3520 Part IV; gifts over $5,000 must be
identified separately; purported gifts from foreign corporations/partnerships have a much
lower inflation-adjusted threshold ($20,116 for 2025; $20,573 for 2026). Form 3520 is
filed separately from Form 1040, due the 15th day of the 4th month after the tax year ends,
with an extension limited to the 15th day of the 10th month. Penalty for late/incomplete
filing: 5% of the gift per month, capped at 25% of the gift, absent reasonable cause
[U09](https://www.irs.gov/businesses/gifts-from-foreign-person),
[U25](https://www.irs.gov/pub/irs-npl/2023ntf-15-foreign-gift-and-trust-reporting-on-form-3520-and-3520-a.pdf).
This matters only if the stuck CNY is legally a gift or inheritance (IR-019).

## 5. Currency gain on the conversion itself

IRS Publication 525, "Foreign currency transactions": "If you have a gain on a personal
foreign currency transaction because of changes in exchange rates, you don't have to include
that gain in your income unless it's more than $200. If the gain is more than $200, report it
as a capital gain." [U04](https://www.irs.gov/publications/p525). This is the IRC 988(e)
personal-transaction rule, but note the statute's limits: if the gain exceeds $200 the
exclusion does not apply at all — the **full** gain is recognized, not merely the excess over
$200 ([26 U.S.C. §988(e)(2), govinfo](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm)).
A transaction is **not** "personal" to the extent allocable expenses qualify under §162 or
§212 (§988(e)(3)), so an interest-bearing CNY deposit held for investment can fail the
personal-transaction test; §988(a)(1)(A) then treats the gain as **ordinary income**, not a
capital gain. The Pub. 525 "capital gain" statement presumes the personal-transaction
character, which is fact-dependent. The qualitative exposure across $10,000–$400,000 — on the
order of 6–7% of the USD received at the 2024/2025 IRS yearly average rates — is quantified
in `us-fx-gain.html` and cross-check flag **X-11**. No individual gain amount can be
computed here because the acquisition-date basis is unknown (IR-014).

## 6. Treaty, credits and remediation

- The 1984 U.S.–PRC income tax convention caps source-country tax on dividends, interest and
  royalties at 10% [U16](https://www.irs.gov/pub/irs-trty/china.pdf),
  [U15](https://www.irs.gov/businesses/international-businesses/china-tax-treaty-documents).
- Protocol paragraph 2 ("saving clause"): "Notwithstanding any provision of the Agreement,
  the United States may tax its citizens." The Treasury technical explanation repeats this
  for dividends, interest and royalties [U17](https://www.irs.gov/pub/irs-trty/chintech.pdf).
  Publication 519 notes that the U.S.–China treaty has exceptions to the saving clause for
  certain resident aliens [U03](https://www.irs.gov/publications/p519).
- Foreign tax credit: Form 1116; credit is the lesser of foreign tax paid or the FTC
  limitation (U.S. tax × foreign-source taxable income / total taxable income); unused
  foreign tax may be carried back 1 year and forward 10 years
  [U05](https://www.irs.gov/publications/p514).
- Remediation for past non-willful failures: Streamlined Foreign Offshore Procedures —
  3 years of delinquent/amended returns (including 3520/5471/8938 information returns) plus
  6 years of delinquent FBARs, Form 14653 non-willful certification, generally no
  failure-to-file/pay, accuracy, information-return or FBAR penalties
  [U13](https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-outside-the-united-states).
  Streamlined Domestic Offshore Procedures use Form 14654 plus a Title 26 miscellaneous
  offshore penalty [U14](https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-in-the-united-states).
  If the IRS has not contacted the taxpayer and no investigation is open, delinquent FBARs
  should be filed as soon as possible to minimise potential penalties
  [U12](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar).
  Willful violations can also carry criminal penalties [U10], [U08].

## Irregularities raised by this task

IR-008 (2026 inflation adjustment cancelled), IR-009 (no signed mainland FATCA IGA
confirmed), IR-010 (eCFR authoritative but unofficial), IR-011 / IR-014 (no official
statement on the tax character of moving one's own principal; no case facts), IR-019
(gift/inheritance character unknown). Published on `deep-review.html`.

## Verification performed

- Full text of 4 key official pages plus all 3 chunks of the eCFR section.
- Every figure checked against an official text: $10,000; $16,536; $165,353; 50%;
  $50,000/$75,000/$100,000/$150,000/$200,000/$300,000/$400,000/$600,000; $10,000/$60,000;
  40%; $100,000; 5%/25%; $20,116/$20,573; $200; 10%; 3 years/6 years; 1/10 year carryback/forward.
- Obsolete June-30 FBAR due-date and old statutory penalty figures identified and excluded.
- `scripts/verify_deep.py` enforces one official-domain link per row.
