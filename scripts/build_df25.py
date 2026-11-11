#!/usr/bin/env python3
"""df25 — the U.S. tax on turning RMB into dollars.

One page, one question: what does the United States tax at the moment RMB held
in a Chinese bank becomes dollars, how is the amount measured, and what does it
come to at every USD 10,000 step from USD 10,000 to USD 400,000.

Everything is generated from the registers in this file:

    data/df25_sources.csv      every official page read, with a quotation
    data/df25_rules.csv        each rule, its official words and its link
    data/df25_inputs.csv       every number the arithmetic uses
    data/df25_ladder.csv       gain and tax at each step, by acquisition period
    data/df25_example.csv      the three withdrawal methods, worked
    data/df25_steps.csv        the worksheet
    data/df25_levers.csv       what lawfully changes the number
    data/df25_flags.csv        what could not be settled (Flagged for Review)
    data/df25_repo_review.csv  how the rest of the repository states the rule
    research/df25-us-conversion-tax.md
    df25-conversion-tax-review.html, assets/df25.css

Rules of the house: a value that was not read on an official page stays blank
and carries a flag; nothing is inferred; arithmetic is exact (Decimal, half-up
to the cent). No timestamps are written, so a rebuild is byte-identical.

    python3 scripts/build_df25.py           write the files
    python3 scripts/build_df25.py --check   fail if the files on disk differ
"""
from __future__ import annotations

import csv
import html
import io
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READ_ON = "2026-11-11"
PAGE = "df25-conversion-tax-review.html"
REVIEW_COMMIT = "ea594da"

GOV = "https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-"
U988 = GOV + "subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm"
U985 = GOV + "subtitleA-chap1-subchapN-partIII-subpartJ-sec985.htm"
U1001 = GOV + "subtitleA-chap1-subchapO-partI-sec1001.htm"
U1012 = GOV + "subtitleA-chap1-subchapO-partII-sec1012.htm"
U1014 = GOV + "subtitleA-chap1-subchapO-partII-sec1014.htm"
U1015 = GOV + "subtitleA-chap1-subchapO-partII-sec1015.htm"
U1221 = GOV + "subtitleA-chap1-subchapP-partIII-sec1221.htm"
U1222 = GOV + "subtitleA-chap1-subchapP-partIII-sec1222.htm"
U165 = GOV + "subtitleA-chap1-subchapB-partVI-sec165.htm"
U1411 = GOV + "subtitleA-chap2A-sec1411.htm"
U6707A = GOV + "subtitleF-chap68-subchapB-partI-sec6707A.htm"
R9881 = "https://www.ecfr.gov/current/title-26/part-1/section-1.988-1"
R9882 = "https://www.ecfr.gov/current/title-26/part-1/section-1.988-2"
R6011 = "https://www.ecfr.gov/current/title-26/part-1/section-1.6011-4"
R1411 = "https://www.ecfr.gov/current/title-26/part-1/section-1.1411-4"
P525 = "https://www.irs.gov/publications/p525"
IRSAVG = "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates"
IRSFX = "https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates"
TC409 = "https://www.irs.gov/taxtopics/tc409"
TC559 = "https://www.irs.gov/taxtopics/tc559"
RP2532 = "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf"
IR103 = ("https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-"
         "including-amendments-from-the-one-big-beautiful-bill")
F8886 = "https://www.irs.gov/forms-pubs/about-form-8886"
G5A = "https://www.federalreserve.gov/releases/g5a/current/"
H10 = "https://www.federalreserve.gov/releases/h10/current/"
FREDA = "https://fred.stlouisfed.org/data/AEXCHUS.txt"
FREDM = "https://fred.stlouisfed.org/data/EXCHUS.txt"
BOC = "https://www.boc.cn/sourcedb/whpj/enindex_1619.html"

# --------------------------------------------------------------------------- sources
# (id, issuer, short label, title, url, how it was read, quotation)
SOURCES = [
    ("DS01", "Bank of China", "BOC board", "Exchange-rate board (English)", BOC,
     "read in full",
     "USD per 100: Buying Rate 666.06, Cash Buying Rate 666.06, Selling Rate 668.86, Cash Selling Rate 668.86, "
     "Middle Rate 671.91, Pub Time 2026/11/11 15:30:04."),
    ("DS02", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 988",
     "26 U.S.C. 988 — Treatment of certain foreign currency transactions", U988,
     "statutory text read in full, subsections (a) to (e); the statutory notes were not read",
     "(a)(1)(A) 'any foreign currency gain or loss attributable to a section 988 transaction shall be computed "
     "separately and treated as ordinary income or loss'. (e)(1) 'The preceding provisions of this section shall "
     "not apply to any section 988 transaction entered into by an individual which is a personal transaction.'"),
    ("DS03", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 985",
     "26 U.S.C. 985 — Functional currency", U985, "read in full",
     "(b)(1) 'the term \"functional currency\" means— (A) except as provided in subparagraph (B), the dollar, or "
     "(B) in the case of a qualified business unit, the currency of the economic environment in which a "
     "significant part of such unit's activities are conducted'."),
    ("DS04", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1001",
     "26 U.S.C. 1001 — Determination of amount of and recognition of gain or loss", U1001, "read in full",
     "(a) 'The gain from the sale or other disposition of property shall be the excess of the amount realized "
     "therefrom over the adjusted basis'. (b) 'The amount realized from the sale or other disposition of property "
     "shall be the sum of any money received plus the fair market value of the property (other than money) received.'"),
    ("DS05", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1012",
     "26 U.S.C. 1012 — Basis of property—cost", U1012, "subsection (a) read",
     "(a) 'The basis of property shall be the cost of such property, except as otherwise provided in this subchapter'."),
    ("DS06", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1014",
     "26 U.S.C. 1014 — Basis of property acquired from a decedent", U1014,
     "subsections (a) to (f)(1) read",
     "(a) 'the basis of property in the hands of a person acquiring the property from a decedent … shall … be— "
     "(1) the fair market value of the property at the date of the decedent's death'."),
    ("DS07", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1015",
     "26 U.S.C. 1015 — Basis of property acquired by gifts and transfers in trust", U1015,
     "subsections (a) to (e) read",
     "(a) 'the basis shall be the same as it would be in the hands of the donor … except that if such basis … is "
     "greater than the fair market value of the property at the time of the gift, then for the purpose of "
     "determining loss the basis shall be such fair market value.'"),
    ("DS08", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1221",
     "26 U.S.C. 1221 — Capital asset defined", U1221, "subsections (a) and (b) read",
     "(a) 'the term \"capital asset\" means property held by the taxpayer (whether or not connected with his trade "
     "or business), but does not include—' followed by eight exceptions, none of which names currency."),
    ("DS09", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1222",
     "26 U.S.C. 1222 — Other terms relating to capital gains and losses", U1222, "read in full",
     "(3) 'The term \"long-term capital gain\" means gain from the sale or exchange of a capital asset held for "
     "more than 1 year'."),
    ("DS10", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 165",
     "26 U.S.C. 165 — Losses", U165, "subsections (a) to (h)(5) read",
     "(c) 'In the case of an individual, the deduction under subsection (a) shall be limited to— (1) losses "
     "incurred in a trade or business; (2) losses incurred in any transaction entered into for profit, though not "
     "connected with a trade or business; and (3) … losses of property … if such losses arise from fire, storm, "
     "shipwreck, or other casualty, or from theft.'"),
    ("DS11", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 1411",
     "26 U.S.C. 1411 — Imposition of tax (net investment income)", U1411, "read in full",
     "(a)(1) 'a tax equal to 3.8 percent of the lesser of— (A) net investment income for such taxable year, or "
     "(B) the excess (if any) of— (i) the modified adjusted gross income for such taxable year, over (ii) the "
     "threshold amount.' (c)(1)(A)(iii) 'net gain (to the extent taken into account in computing taxable income) "
     "attributable to the disposition of property'."),
    ("DS12", "U.S. Code, 2024 edition (Government Publishing Office)", "26 U.S.C. 6707A",
     "26 U.S.C. 6707A — Penalty for failure to include reportable transaction information with return", U6707A,
     "read in full",
     "(b)(1) '75 percent of the decrease in tax shown on the return as a result of such transaction'. (b)(2)(B) "
     "'in the case of any other reportable transaction, $50,000 ($10,000 in the case of a natural person)'. "
     "(b)(3) 'shall not be less than $10,000 ($5,000 in the case of a natural person)'."),
    ("DS13", "Electronic Code of Federal Regulations (eCFR)", "26 CFR 1.988-1",
     "26 CFR 1.988-1 — Certain definitions and special rules", R9881,
     "read in full; the page showed 'up to date as of 11/09/2026'",
     "(a)(9)(i) 'A transaction entered into by an individual which otherwise qualifies as a section 988 "
     "transaction shall be considered a section 988 transaction only to the extent expenses properly allocable to "
     "such transaction meet the requirements of section 162 or 212 (other than the part of section 212 dealing "
     "with expenses incurred in connection with taxes).'"),
    ("DS14", "Electronic Code of Federal Regulations (eCFR)", "26 CFR 1.988-2",
     "26 CFR 1.988-2 — Recognition and computation of exchange gain or loss", R9882,
     "paragraphs (a) and (b)(1) read; the remaining paragraphs (debt instruments, forward contracts) were not read",
     "(a)(2)(iii)(B)(1) 'The basis of nonfunctional currency withdrawn from an account with a bank or other "
     "financial institution shall be determined under any reasonable method that is consistently applied from "
     "year to year by the taxpayer to all accounts denominated in a nonfunctional currency. For example, a "
     "taxpayer may use a first in first out method, a last in first out method, a pro rata method … However, a "
     "method that consistently results in units of nonfunctional currency with the highest basis being withdrawn "
     "first shall not be considered reasonable.'"),
    ("DS15", "Electronic Code of Federal Regulations (eCFR)", "26 CFR 1.6011-4",
     "26 CFR 1.6011-4 — Requirement of statement disclosing participation in certain transactions by taxpayers",
     R6011, "paragraphs (a), (b)(1) to (b)(6) and (b)(8) read; paragraphs (d) to (h) were not read",
     "(b)(5)(i) 'A loss transaction is any transaction resulting in the taxpayer claiming a loss under section "
     "165 of at least— … (E) $50,000 in any single taxable year for individuals or trusts … if the loss arises "
     "with respect to a section 988 transaction'."),
    ("DS16", "Electronic Code of Federal Regulations (eCFR)", "26 CFR 1.1411-4",
     "26 CFR 1.1411-4 — Definition of net investment income", R1411,
     "searched, not read: the eCFR full-text search of this section returned no match for 'foreign currency' or "
     "'section 988'; a control search for 'net gain' matched",
     ""),
    ("DS17", "Internal Revenue Service", "IRS Pub. 525", "Publication 525 (2025), Taxable and Nontaxable Income",
     P525, "the passage 'Foreign currency transactions' under 'Other Income' was read; the rest was not",
     "'If you have a gain on a personal foreign currency transaction because of changes in exchange rates, you "
     "don't have to include that gain in your income unless it's more than $200. If the gain is more than $200, "
     "report it as a capital gain.'"),
    ("DS18", "Internal Revenue Service", "IRS yearly averages", "Yearly average currency exchange rates", IRSAVG,
     "read in full",
     "China, Yuan: 2025 7.129; 2024 7.189; 2023 7.075; 2022 6.730; 2021 6.452. 'The Internal Revenue Service "
     "has no official exchange rate. Generally, it accepts any posted exchange rate that is used consistently.'"),
    ("DS19", "Internal Revenue Service", "IRS currency page", "Foreign currency and currency exchange rates", IRSFX,
     "read in full",
     "'If your functional currency is the U.S. dollar, you must immediately translate into dollars all items of "
     "income, expense, etc. (including taxes), that you receive, pay, or accrue in a foreign currency … Use the "
     "exchange rate prevailing when you receive, pay, or accrue the item.'"),
    ("DS20", "Internal Revenue Service", "IRS Topic 409", "Topic no. 409, Capital gains and losses", TC409,
     "read to the section 'Additional information'",
     "'Losses from the sale of personal-use property, such as your home or car, aren't tax deductible.' "
     "'Generally, if you hold the asset for more than one year before you dispose of it, your capital gain or "
     "loss is long-term.' 'Net short-term capital gains are subject to taxation as ordinary income at graduated "
     "tax rates.'"),
    ("DS21", "Internal Revenue Service", "IRS Topic 559", "Topic no. 559, Net investment income tax", TC559,
     "read in full",
     "'the NIIT is 3.8 percent on the lesser of: the net investment income, or the excess of modified adjusted "
     "gross income (MAGI) over the following threshold amounts: $250,000 for married filing jointly or qualifying "
     "surviving spouse; $125,000 for married filing separately; $200,000 for single or head of household'."),
    ("DS22", "Internal Revenue Service", "Rev. Proc. 2025-32", "Revenue Procedure 2025-32 (2026 adjusted items)",
     RP2532, "sections 1, 2, 3 and 4.01 to 4.17 read; later sections were not read",
     "Section 2.01 'The existing seven tax rates of 10%, 12%, 22%, 24%, 32%, 35%, and 37% remain in effect for "
     "individual taxpayers.' Section 4.03 gives the 2026 maximum zero rate amounts and maximum 15 percent rate "
     "amounts."),
    ("DS23", "Internal Revenue Service", "IRS IR-2025-103",
     "IRS releases tax inflation adjustments for tax year 2026 (IR-2025-103, 9 Oct 2025)", IR103,
     "read in full; the page carries the banner 'Notice: Historical Content'",
     "'For tax year 2026, the top tax rate remains 37% for individual single taxpayers with incomes greater than "
     "$640,600 ($768,700 for married couples filing jointly).'"),
    ("DS24", "Board of Governors of the Federal Reserve System", "Fed G.5A",
     "Foreign Exchange Rates — G.5A Annual (release of 5 January 2026)", G5A, "read in full",
     "China, P.R., Yuan: 2025 7.1875; 2024 7.1957; 2023 7.0809; 2022 6.7290. 'Averages are based on daily noon "
     "buying rates for cable transfers in New York City certified for customs purposes by the Federal Reserve "
     "Bank of New York.'"),
    ("DS25", "Board of Governors of the Federal Reserve System", "Fed H.10",
     "Foreign Exchange Rates — H.10 Weekly (release of 9 November 2026)", H10, "read in full",
     "China, P.R., Yuan: Nov. 2 6.6480; Nov. 3 6.6701; Nov. 4 6.6731; Nov. 5 6.6680; Nov. 6 6.6760."),
    ("DS26", "Federal Reserve Bank of St. Louis (FRED)", "Fed annual series",
     "AEXCHUS — Chinese Yuan Renminbi to U.S. Dollar Spot Exchange Rate, annual", FREDA, "read in full",
     "'Source: Board of Governors of the Federal Reserve System (US). Release: G.5A Foreign Exchange Rates. "
     "Frequency: Annual. Averages of daily figures. Noon buying rates in New York City for cable transfers "
     "payable in foreign currencies.' Rows 1981 to 2025."),
    ("DS27", "Federal Reserve Bank of St. Louis (FRED)", "Fed monthly series",
     "EXCHUS — Chinese Yuan Renminbi to U.S. Dollar Spot Exchange Rate, monthly", FREDM,
     "rows October 2004 to October 2026 read; the header block of the page was not read",
     "2026-10-01 6.6844; 2026-09-01 6.7084; 2026-01-01 6.9692; 2025-12-01 7.0432; 2025-01-01 7.2957."),
    ("DS28", "Internal Revenue Service", "About Form 8886", "About Form 8886, Reportable Transaction Disclosure Statement",
     F8886, "read in full",
     "'Use Form 8886 to disclose information for each reportable transaction in which you participated.'"),
]
SRC = {s[0]: s for s in SOURCES}
OFFICIAL_HOSTS = ("www.govinfo.gov", "www.ecfr.gov", "www.irs.gov", "www.federalreserve.gov",
                  "fred.stlouisfed.org", "www.boc.cn")

# --------------------------------------------------------------------------- inputs
BOC_SELL_PER_100 = D("668.86")
SELL = BOC_SELL_PER_100 / D(100)          # RMB paid for one dollar bought from the bank
AMOUNTS = [D(a) for a in range(10000, 400001, 10000)]
KEY_AMOUNTS = [D(10000), D(100000), D(400000)]

ANNUAL = {  # Federal Reserve annual average, RMB per USD (DS26; 2022-2025 also on DS24)
    1994: "8.6397", 1995: "8.3700", 1996: "8.3389", 1997: "8.3193", 1998: "8.3008", 1999: "8.2783",
    2000: "8.2784", 2001: "8.2770", 2002: "8.2771", 2003: "8.2772", 2004: "8.2768", 2005: "8.1936",
    2006: "7.9723", 2007: "7.6058", 2008: "6.9477", 2009: "6.8307", 2010: "6.7696", 2011: "6.4630",
    2012: "6.3093", 2013: "6.1478", 2014: "6.1620", 2015: "6.2827", 2016: "6.6400", 2017: "6.7569",
    2018: "6.6090", 2019: "6.9081", 2020: "6.9042", 2021: "6.4508", 2022: "6.7290", 2023: "7.0809",
    2024: "7.1957", 2025: "7.1875",
}
MONTHLY = {  # Federal Reserve monthly average, RMB per USD (DS27)
    "2024-01": "7.1707", "2024-02": "7.1935", "2024-03": "7.2015", "2024-04": "7.2374", "2024-05": "7.2327",
    "2024-06": "7.2547", "2024-07": "7.2609", "2024-08": "7.1475", "2024-09": "7.0760", "2024-10": "7.0881",
    "2024-11": "7.2063", "2024-12": "7.2807",
    "2025-01": "7.2957", "2025-02": "7.2734", "2025-03": "7.2493", "2025-04": "7.2968", "2025-05": "7.2166",
    "2025-06": "7.1804", "2025-07": "7.1741", "2025-08": "7.1727", "2025-09": "7.1235", "2025-10": "7.1200",
    "2025-11": "7.1069", "2025-12": "7.0432",
    "2026-01": "6.9692", "2026-02": "6.9064", "2026-03": "6.8921", "2026-04": "6.8371", "2026-05": "6.7996",
    "2026-06": "6.7758", "2026-07": "6.7757", "2026-08": "6.7361", "2026-09": "6.7084", "2026-10": "6.6844",
}
IRS_AVG = {2021: "6.452", 2022: "6.730", 2023: "7.075", 2024: "7.189", 2025: "7.129"}   # DS18
H10_DAILY = {"2026-11-02": "6.6480", "2026-11-03": "6.6701", "2026-11-04": "6.6731",
             "2026-11-05": "6.6680", "2026-11-06": "6.6760"}                               # DS25
ORD_RATES = ["10", "12", "22", "24", "32", "35", "37"]     # DS22 section 2.01
CAP_RATES = ["15", "20"]                                   # DS20; the 0 percent rate gives no tax
NIIT_RATE = "3.8"                                          # DS11
PERSONAL_LIMIT = D("200")                                  # DS02 (e)(2)
LOSS_DISCLOSURE = D("50000")                               # DS15 (b)(5)(i)(E)
# What the canonical dashboard printed for the same formula on the IRS averages
# (data/e347_fx_gain.csv as read at commit ea594da). Recorded, not re-read at build time.
CANONICAL = {10000: {2021: "-366.71", 2022: "61.52", 2023: "546.15", 2024: "696.06", 2025: "617.76"},
             400000: {2021: "-14668.32", 2022: "2460.62", 2023: "21845.94", 2024: "27842.54", 2025: "24710.34"}}

# 2026 tables, Rev. Proc. 2025-32 sections 4.01 and 4.03 (DS22). Order: single, joint, head of household, separate.
STATUSES = ["Single", "Married filing jointly", "Head of household", "Married filing separately"]
ORD_BRACKETS = [  # (rate, lower bound of taxable income for each status)
    ("10", ["0", "0", "0", "0"]),
    ("12", ["12400", "24800", "17700", "12400"]),
    ("22", ["50400", "100800", "67450", "50400"]),
    ("24", ["105700", "211400", "105700", "105700"]),
    ("32", ["201775", "403550", "201750", "201775"]),
    ("35", ["256225", "512450", "256200", "256225"]),
    ("37", ["640600", "768700", "640600", "384350"]),
]
CAP_ZERO_MAX = ["49450", "98900", "66200", "49450"]
CAP_15_MAX = ["545500", "613700", "579600", "306850"]
NIIT_THRESHOLD = ["200000", "250000", "200000", "125000"]   # DS11 (b), DS21

# Illustration for the three withdrawal methods. The deposits are invented round
# numbers; the rates are the Federal Reserve annual averages above.
EX_LOTS = [("A", 2021, D(700000)), ("B", 2023, D(700000)), ("C", 2025, D(700000))]
EX_SALE = D(1050000)      # RMB sold in each of two conversions


def cents(x) -> D:
    return D(x).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def frac_cents(f: Fraction) -> D:
    return cents(D(f.numerator) / D(f.denominator))


def money(x, sign=False) -> str:
    x = D(x)
    q = x.quantize(D("1"), rounding=ROUND_HALF_UP)
    s = f"{abs(q):,}"
    if q < 0:
        return "−$" + s
    return ("+$" if sign and q > 0 else "$") + s


def money2(x) -> str:
    x = cents(x)
    return ("−$" if x < 0 else "$") + f"{abs(x):,.2f}"


def pct(x, places=2) -> str:
    q = D(x).quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return ("−" if q < 0 else "+" if q > 0 else "") + f"{abs(q)}%"


def signed4(x) -> str:
    q = D(x).quantize(D("0.0001"), rounding=ROUND_HALF_UP)
    return ("−" if q < 0 else "+" if q > 0 else "") + f"{abs(q)}"


def gain_for(usd: D, rate: D) -> D:
    """Dollars received minus the dollar cost of the RMB sold to get them."""
    basis = cents(usd * SELL / rate)
    return usd - basis


def gain_pct(rate: D) -> D:
    return (D(1) - SELL / rate) * D(100)


def tax(gain: D, rate: str) -> D:
    return cents(max(gain, D(0)) * D(rate) / D(100))


MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def period_label(kind: str, key) -> str:
    if kind == "year":
        return str(key)
    y, m = key.split("-")
    return f"{MONTH_NAMES[int(m) - 1]} {y}"


PERIODS = [("year", y, D(r), "DS26") for y, r in ANNUAL.items()] + \
          [("month", m, D(r), "DS27") for m, r in MONTHLY.items()]
LADDER_TABLES = [("year", y) for y in range(2025, 2015, -1)]
LADDER_TABLES = [("month", m) for m in sorted(k for k in MONTHLY if k.startswith("2026"))][::-1] + LADDER_TABLES

# --------------------------------------------------------------------------- rules
# (id, topic, plain statement, official words, source ids, status, flag)
RULES = [
    ("R01", "What is taxed",
     "The gain or loss is the dollars you receive minus the dollar cost (basis) of the RMB you give up. The money itself is not income again.",
     "'Exchange gain realized from the sale or other disposition of nonfunctional currency shall be the excess of the amount realized over the adjusted basis of such currency, and exchange loss realized shall be the excess of the adjusted basis of such currency over the amount realized.' — 26 CFR 1.988-2(a)(2)(i)",
     ["DS14", "DS04"], "verified", ""),
    ("R02", "What is taxed",
     "The dollars the bank actually pays you are the amount realized.",
     "'The amount realized from the sale or other disposition of property shall be the sum of any money received' — 26 U.S.C. 1001(b)",
     ["DS04"], "verified", ""),
    ("R03", "What is taxed",
     "For a U.S. individual the dollar is the functional currency, so RMB is a nonfunctional currency, and converting it to dollars is a disposition of that currency.",
     "'the term \"functional currency\" means— (A) except as provided in subparagraph (B), the dollar' — 26 U.S.C. 985(b)(1). 'The conversion of the 10,000 Canadian dollars to U.S. dollars is a section 988 transaction' — 26 CFR 1.988-1(a)(6) Example 2",
     ["DS03", "DS13"], "verified", ""),
    ("R04", "What is taxed",
     "A bank deposit in RMB counts as the currency itself.",
     "'the term \"nonfunctional currency\" includes coin or currency, and nonfunctional currency denominated demand or time deposits or similar instruments issued by a bank or other financial institution' — 26 U.S.C. 988(c)(1)(C)(ii)",
     ["DS02"], "verified", ""),
    ("R05", "When it is taxed",
     "Depositing RMB, withdrawing RMB, or moving RMB from one RMB deposit to another is not a taxable moment. The dollar cost travels with the money.",
     "'No exchange gain or loss is recognized with respect to the following transactions— … (E) The transfer of nonfunctional currency from a demand or time deposit … to another demand or time deposit or similar instrument denominated in the same nonfunctional currency … The taxpayer's basis in the units of nonfunctional currency … received in the transaction shall be the adjusted basis of the units … transferred.' — 26 CFR 1.988-2(a)(1)(iii)",
     ["DS14"], "verified", ""),
    ("R06", "When it is taxed",
     "Paying for property with RMB is treated as selling the RMB for dollars that day and then buying the property with the dollars.",
     "'the exchange of nonfunctional currency for property (other than nonfunctional currency) shall be treated as— (1) An exchange of the units of nonfunctional currency for units of functional currency at the spot rate on the date of the exchange, and (2) The purchase or sale of the property for such units of functional currency.' — 26 CFR 1.988-2(a)(2)(ii)(B)",
     ["DS14"], "verified", ""),
    ("R07", "When it is taxed",
     "Each conversion is worked out on its own. A loss on one is not netted into another by this rule.",
     "'the amount of exchange gain or loss from a section 988 transaction shall be separately computed for each section 988 transaction, and such amount shall not be integrated with gain or loss recognized on another transaction' — 26 CFR 1.988-1(e)",
     ["DS13"], "verified", ""),
    ("R08", "Which box",
     "Investment or business money: the gain is ordinary income and the loss is an ordinary loss.",
     "'any foreign currency gain or loss attributable to a section 988 transaction shall be computed separately and treated as ordinary income or loss (as the case may be)' — 26 U.S.C. 988(a)(1)(A)",
     ["DS02"], "verified", ""),
    ("R09", "Which box",
     "Personal money: the ordinary-income rule above does not apply at all.",
     "'The preceding provisions of this section shall not apply to any section 988 transaction entered into by an individual which is a personal transaction.' — 26 U.S.C. 988(e)(1)",
     ["DS02"], "verified", ""),
    ("R10", "Which box",
     "The test: a transaction is personal unless, and only to the extent that, the expenses that belong to it would be deductible as business expenses (section 162) or as expenses of producing income (section 212).",
     "'the term \"personal transaction\" means any transaction entered into by an individual, except that such term shall not include any transaction to the extent that expenses properly allocable to such transaction meet the requirements of— (A) section 162 (other than traveling expenses described in subsection (a)(2) thereof), or (B) section 212 (other than that part of section 212 dealing with expenses incurred in connection with taxes).' — 26 U.S.C. 988(e)(3); the same test is in 26 CFR 1.988-1(a)(9)(i)",
     ["DS02", "DS13"], "verified", ""),
    ("R11", "Which box",
     "The regulation gives one example on each side: pounds bought to buy a bond are inside section 988; pounds spent on a holiday are outside it. A savings balance is not addressed by name.",
     "Example 1: 'These transactions are not excluded from the definition of a section 988 transaction … because expenses properly allocable to such transactions meet the requirements of section 212.' Example 2: 'The expenses properly allocable to such dispositions do not meet the requirements of section 162 or 212. Thus, the disposition of the pounds by X on his vacation are not section 988 transactions.' — 26 CFR 1.988-1(a)(9)(ii)",
     ["DS13"], "verified", "DF25-F02"),
    ("R12", "Which box",
     "Personal money, small gain: a gain of $200 or less on a transaction is not recognized. If the gain is more than $200 the exclusion does not apply to any of it.",
     "'no gain shall be recognized for purposes of this subtitle by reason of changes in exchange rates after such currency was acquired by such individual and before such disposition. The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200.' — 26 U.S.C. 988(e)(2)",
     ["DS02"], "verified", ""),
    ("R13", "Which box",
     "Personal money, gain over $200: the IRS says to report it as a capital gain.",
     "'If you have a gain on a personal foreign currency transaction because of changes in exchange rates, you don't have to include that gain in your income unless it's more than $200. If the gain is more than $200, report it as a capital gain.' — IRS Publication 525 (2025)",
     ["DS17"], "verified", ""),
    ("R14", "Which box",
     "A capital gain is long-term when the asset was held for more than one year; a short-term gain is taxed at ordinary rates.",
     "'The term \"long-term capital gain\" means gain from the sale or exchange of a capital asset held for more than 1 year' — 26 U.S.C. 1222(3). 'Net short-term capital gains are subject to taxation as ordinary income at graduated tax rates.' — IRS Topic no. 409",
     ["DS09", "DS20", "DS08"], "verified", "DF25-F12"),
    ("R15", "Losses",
     "An individual may deduct only three kinds of loss: a business loss, a loss on a transaction entered into for profit, and a casualty or theft loss. The IRS says losses on personal-use property are not deductible.",
     "'In the case of an individual, the deduction under subsection (a) shall be limited to— (1) losses incurred in a trade or business; (2) losses incurred in any transaction entered into for profit, though not connected with a trade or business; and (3) … losses of property … if such losses arise from fire, storm, shipwreck, or other casualty, or from theft.' — 26 U.S.C. 165(c). 'Losses from the sale of personal-use property, such as your home or car, aren't tax deductible.' — IRS Topic no. 409",
     ["DS10", "DS20"], "verified", ""),
    ("R16", "Losses",
     "Claiming section 988 losses of $50,000 or more in one tax year makes the conversion a reportable 'loss transaction' for an individual; reportable transactions are disclosed on Form 8886.",
     "'A loss transaction is any transaction resulting in the taxpayer claiming a loss under section 165 of at least— … (E) $50,000 in any single taxable year for individuals or trusts … if the loss arises with respect to a section 988 transaction' — 26 CFR 1.6011-4(b)(5)(i). 'Use Form 8886 to disclose information for each reportable transaction in which you participated.' — IRS, About Form 8886",
     ["DS15", "DS28"], "verified", ""),
    ("R17", "Losses",
     "Leaving out that disclosure carries its own penalty: 75% of the tax saved, not less than $5,000 and not more than $10,000 for a natural person.",
     "'75 percent of the decrease in tax shown on the return as a result of such transaction' … 'in the case of any other reportable transaction, $50,000 ($10,000 in the case of a natural person)' … 'shall not be less than $10,000 ($5,000 in the case of a natural person)' — 26 U.S.C. 6707A(b)",
     ["DS12"], "verified", ""),
    ("R18", "Dollar cost",
     "The dollar cost of currency follows the ordinary basis rules of the Code: cost, or the special rules for inherited and gifted property.",
     "'the adjusted basis of nonfunctional currency is determined under the applicable provisions of the Internal Revenue Code (e.g., sections 1011 through 1023)' — 26 CFR 1.988-2(a)(2)(iii)(A). 'The basis of property shall be the cost of such property' — 26 U.S.C. 1012(a)",
     ["DS14", "DS05"], "verified", ""),
    ("R19", "Dollar cost",
     "RMB taken out of a bank account: use any reasonable method, the same one every year and for every foreign-currency account. First in first out, last in first out and pro rata are named. A method that always takes the highest-cost RMB first is not allowed.",
     "'The basis of nonfunctional currency withdrawn from an account with a bank or other financial institution shall be determined under any reasonable method that is consistently applied from year to year by the taxpayer to all accounts denominated in a nonfunctional currency. For example, a taxpayer may use a first in first out method, a last in first out method, a pro rata method (as illustrated in the example below), or any other reasonable method that is consistently applied. However, a method that consistently results in units of nonfunctional currency with the highest basis being withdrawn first shall not be considered reasonable.' — 26 CFR 1.988-2(a)(2)(iii)(B)(1)",
     ["DS14"], "verified", ""),
    ("R20", "Dollar cost",
     "The regulation's own example: an account holding 1,200 Swiss francs with a total cost of $600; 500 francs are withdrawn; pro rata, their cost is $250 and $350 stays with the rest.",
     "'X's basis in the 500 Swiss francs is $250 … X's basis in the Swiss francs remaining in the account is $350 ($600−$250). X must use this method consistently from year to year with respect to withdrawals of nonfunctional currency from all of X's accounts.' — 26 CFR 1.988-2(a)(2)(iii)(B)(2)",
     ["DS14"], "verified", ""),
    ("R21", "Dollar cost",
     "Income received in RMB is translated into dollars at the rate on the day it is received; that dollar figure is what the RMB cost.",
     "'you must immediately translate into dollars all items of income, expense, etc. … that you receive, pay, or accrue in a foreign currency … Use the exchange rate prevailing when you receive, pay, or accrue the item.' — IRS, Foreign currency and currency exchange rates. 'The acquisition of nonfunctional currency is treated as a section 988 transaction for purposes of establishing the taxpayer's basis in such currency' — 26 CFR 1.988-1(a)(1)",
     ["DS19", "DS13"], "verified", ""),
    ("R22", "Dollar cost",
     "Bank interest credited in RMB is translated at the rate on the day received, or by one consistent convention such as month-end; crediting it creates no currency gain.",
     "'Interest income received with respect to a demand account … shall be translated into functional currency at the spot rate on the date received or accrued or pursuant to any reasonable spot rate convention consistently applied … No exchange gain or loss is realized upon the receipt or accrual of interest income with respect to a demand account' — 26 CFR 1.988-2(b)(1)",
     ["DS14"], "verified", ""),
    ("R23", "Dollar cost",
     "RMB received for selling property takes its dollar cost on the day it is received (for listed securities sold by a cash-basis taxpayer, the settlement date). The currency clock starts then.",
     "'The acquisition of the 100,000 krone on January 1, 1989, and the acquisition of the 120,000 krone on August 1, 1989, are section 988 transactions for purposes of establishing the basis of such krone.' — 26 CFR 1.988-1(a)(6) Example 8. 'X's basis in the £110 received from the sale of the stock is $166.' — 26 CFR 1.988-2(a)(2)(iv)(C)",
     ["DS13", "DS14"], "verified", ""),
    ("R24", "Dollar cost",
     "Inherited property takes its value at the date of death.",
     "'the basis of property in the hands of a person acquiring the property from a decedent … shall … be— (1) the fair market value of the property at the date of the decedent's death' — 26 U.S.C. 1014(a)",
     ["DS06"], "verified", ""),
    ("R25", "Dollar cost",
     "Gifted property keeps the giver's cost; for working out a loss, the value on the day of the gift is used if it is lower.",
     "'the basis shall be the same as it would be in the hands of the donor … except that if such basis … is greater than the fair market value of the property at the time of the gift, then for the purpose of determining loss the basis shall be such fair market value' — 26 U.S.C. 1015(a)",
     ["DS07"], "verified", "DF25-F03"),
    ("R26", "Which exchange rate",
     "The IRS has no official rate and accepts any posted rate used consistently. The regulation names Federal Reserve, IMF and published daily rates as acceptable evidence of the spot rate.",
     "'The Internal Revenue Service has no official exchange rate. Generally, it accepts any posted exchange rate that is used consistently.' — IRS, Yearly average currency exchange rates. '… exchange rates published by the Board of Governors of the Federal Reserve System pursuant to 31 U.S.C. section 5151; exchange rates published in newspapers, financial journals or other daily financial news sources' — 26 CFR 1.988-1(d)(1)",
     ["DS18", "DS13"], "verified", ""),
    ("R27", "Which exchange rate",
     "Where an official rate and a free-market rate differ, the rate that most clearly reflects income is used.",
     "'If a currency has an official government established rate that differs from a free market rate, the spot rate shall be the rate which most clearly reflects the taxpayer's income. Generally, this shall be the free market rate.' — 26 CFR 1.988-1(d)(4)(i)",
     ["DS13"], "verified", ""),
    ("R28", "Tax rates",
     "Ordinary income is taxed at seven rates from 10% to 37%; the 2026 brackets are in the table on this page.",
     "'The existing seven tax rates of 10%, 12%, 22%, 24%, 32%, 35%, and 37% remain in effect for individual taxpayers.' — Rev. Proc. 2025-32, section 2.01; tables in section 4.01",
     ["DS22", "DS23"], "verified", "DF25-F10"),
    ("R29", "Tax rates",
     "A long-term capital gain is taxed at 0%, 15% or 20% depending on taxable income; the 2026 limits are in the table on this page.",
     "'Net capital gains are taxed at different rates depending on overall taxable income, although some or all net capital gain may be taxed at 0%.' — IRS Topic no. 409. 'the maximum zero rate amounts and maximum 15 percent rate amounts' — Rev. Proc. 2025-32, section 4.03",
     ["DS20", "DS22"], "verified", ""),
    ("R30", "Tax rates",
     "A further 3.8% applies to net investment income once modified adjusted gross income passes $200,000 (single or head of household), $250,000 (joint) or $125,000 (married filing separately). The statute counts net gain from the disposition of property; whether a currency gain is inside that is not stated by name.",
     "'a tax equal to 3.8 percent of the lesser of— (A) net investment income for such taxable year, or (B) the excess (if any) of— (i) the modified adjusted gross income for such taxable year, over (ii) the threshold amount' … 'net gain (to the extent taken into account in computing taxable income) attributable to the disposition of property' — 26 U.S.C. 1411(a)(1), (c)(1)(A)(iii)",
     ["DS11", "DS21", "DS16"], "verified", "DF25-F06"),
    ("R31", "Where the gain is from",
     "A section 988 gain is sourced to the country of the individual's tax home; with no tax home, a U.S. citizen is treated as resident in the United States.",
     "'the source of such amount shall be determined by reference to the residence of the taxpayer' … 'in the case of an individual, the country in which such individual's tax home (as defined in section 911(d)(3)) is located' … 'If an individual does not have a tax home (as so defined), the residence of such individual shall be the United States if such individual is a United States citizen or a resident alien' — 26 U.S.C. 988(a)(3)",
     ["DS02"], "verified", ""),
    ("R32", "Guard rail",
     "The IRS may treat a transaction, or a series of them, as a section 988 transaction when its effect is to avoid section 988.",
     "'The Commissioner may recharacterize a transaction (or series of transactions) in whole or in part as a section 988 transaction if the effect of such transaction (or series of transactions) is to avoid section 988.' — 26 CFR 1.988-1(a)(11)(i)",
     ["DS13"], "verified", ""),
    ("R33", "Return line",
     "A capital gain is reported on Form 8949 and Schedule D. The line for an ordinary section 988 gain or loss was not found on an official page.",
     "'Report most sales and other capital transactions and calculate capital gain or loss on Form 8949, Sales and Other Dispositions of Capital Assets, then summarize capital gains and deductible capital losses on Schedule D (Form 1040).' — IRS Topic no. 409",
     ["DS20"], "verified", "DF25-F05"),
]
RULE = {r[0]: r for r in RULES}

# --------------------------------------------------------------------------- the two boxes (page table)
# (situation, test, gain, loss, rule ids, flag)
BOXES = [
    ("Investment or business money",
     "The costs that belong to the transaction would be deductible as business expenses or as expenses of producing income. Regulation example: pounds bought in order to buy a bond.",
     "Ordinary income, taxed at your ordinary rate (10% to 37%).",
     "Ordinary loss.",
     ["R08", "R10", "R11"], ""),
    ("Personal money, gain of $200 or less on the transaction",
     "Any transaction by an individual that is not investment or business. Regulation example: pounds spent on a holiday.",
     "Not recognized. No tax.",
     "Not deductible. An individual may deduct only business losses, losses on transactions entered into for profit, and casualty or theft losses.",
     ["R09", "R12", "R15"], ""),
    ("Personal money, gain over $200",
     "Same test. The $200 exclusion then applies to none of the gain.",
     "The whole gain is taxed. The IRS says to report it as a capital gain: 0%, 15% or 20% if the RMB was held more than one year, ordinary rates if not.",
     "Not deductible, for the same reason.",
     ["R09", "R12", "R13", "R14", "R15"], ""),
    ("Partly one, partly the other",
     "The statute and the regulation both say 'to the extent', so one balance can be split by what each part was for.",
     "Each part follows its own box.",
     "Each part follows its own box.",
     ["R10"], "DF25-F02"),
]

# --------------------------------------------------------------------------- dollar cost by origin (page table)
# (where the RMB came from, dollar cost, rule ids, flag)   blank cost = not stated in the texts read
ORIGINS = [
    ("Salary or other income paid in RMB", "Its dollar value on the day it was received.", ["R21"], ""),
    ("Bank interest credited in RMB", "Its dollar value on the day it was credited, or by one consistent convention such as month-end. Crediting it creates no currency gain.", ["R22"], ""),
    ("RMB bought with dollars", "The dollars paid.", ["R18"], ""),
    ("RMB received for selling a home, shares or other property", "Its dollar value on the day the RMB was received (the settlement date for listed securities). The currency gain is counted only from that day.", ["R23"], ""),
    ("Inherited", "Its dollar value at the date of death.", ["R24", "R18"], ""),
    ("Received as a gift", "The giver's dollar cost. For a loss, the value on the day of the gift if that is lower.", ["R25"], "DF25-F03"),
    ("Several deposits over the years in one account", "One reasonable method, kept every year for every foreign-currency account: first in first out, last in first out, or pro rata. Not highest-cost-first.", ["R19", "R20"], ""),
    ("Moved from one RMB account to another", "Unchanged. The move is not a taxable moment.", ["R05"], ""),
    ("Acquired before the holder was a U.S. taxpayer", "", ["R18"], "DF25-F04"),
]

# --------------------------------------------------------------------------- steps
# (n, what to do, why, rule ids, flag)
STEPS = [
    (1, "Get the full history of every RMB account, and of any other foreign-currency account you hold: each credit with its date, its amount and what it was.",
     "The withdrawal method has to be applied to all accounts in a foreign currency, so all of them are needed.", ["R19"], ""),
    (2, "Give each credit a dollar cost using the table 'What did your RMB cost in dollars?'. Take the rate for each date from one published source and keep to it; the Federal Reserve daily series is one.",
     "The IRS accepts any posted rate used consistently, and the regulation names the Federal Reserve's rates.", ["R21", "R22", "R23", "R24", "R25", "R26"], ""),
    (3, "Look at earlier U.S. returns for any earlier conversion. A method already used has to be kept. If there is none, choose first in first out, last in first out or pro rata now and write the choice down.",
     "The method must be 'consistently applied from year to year'.", ["R19"], ""),
    (4, "Write down what each part of the balance was for: living money, or money held to earn a return or for a business. That decides the box.",
     "A transaction is personal except to the extent its costs would be business or income-producing expenses.", ["R10", "R11"], "DF25-F02"),
    (5, "On each conversion day keep the bank's slip: RMB sold, the rate, dollars received.",
     "The dollars received are the amount realized.", ["R02"], ""),
    (6, "For each conversion on its own: gain or loss = dollars received − dollar cost of the RMB sold, by your method.",
     "Each transaction is computed separately.", ["R01", "R07"], ""),
    (7, "Apply the box. Investment or business: ordinary income or ordinary loss. Personal: a gain of $200 or less is ignored, a larger gain is a capital gain (long-term if held more than one year), a loss is not deductible.",
     "These are the two sets of consequences in the statute and in IRS Publication 525.", ["R08", "R09", "R12", "R13", "R14", "R15"], ""),
    (8, "Find your rate for that tax year in the bracket tables, and check whether your income passes the 3.8% threshold.",
     "The tax is the gain placed on top of your other income for the year.", ["R28", "R29", "R30"], "DF25-F06"),
    (9, "If you claim section 988 losses of $50,000 or more for the year, disclose the transaction on Form 8886. When and where to file it is in the form's instructions, which were not read.",
     "A section 988 loss of that size is a reportable loss transaction for an individual, with a separate penalty for leaving it out.", ["R16", "R17"], ""),
    (10, "Report it. A capital gain goes on Form 8949 and Schedule D. For an ordinary section 988 gain or loss, ask the preparer which line; this page could not confirm it from an official page.",
     "Only the capital-gain route was found on an official page.", ["R33"], "DF25-F05"),
]

# --------------------------------------------------------------------------- levers
# (id, what you can do, what it changes, in favour, against, rule ids, flag)
LEVERS = [
    ("V1", "Convert RMB soon after it arrives",
     "The currency clock starts on the day the RMB is received, so little gain or loss has time to build. RMB received in the latest months shows almost none.",
     "Removes most of the currency tax on new money such as a recent sale or recent pay.",
     "Does nothing for RMB that has already been held through a rate move.", ["R23", "R21"], ""),
    ("V2", "Spread the conversion over two tax years",
     "Each conversion is its own transaction, taxed in the year it happens, so the gain is divided between two returns.",
     "Can keep the gain in a lower bracket in each year, and under the 3.8% threshold.",
     "The rate can move against you while you wait, and the bank charges for each wire.", ["R07", "R28", "R30"], ""),
    ("V3", "Choose the withdrawal method with care, once",
     "First in first out, last in first out and pro rata give different gains for a part-conversion; when the account is emptied the total is the same.",
     "Decides which year carries the gain. In the personal box it can also change the total taxed, because a tranche that shows a loss is simply lost.",
     "The choice binds later years and every foreign-currency account. Highest-cost-first is not allowed.", ["R19", "R20", "R15"], ""),
    ("V4", "Establish which box the money is in, with papers",
     "The box sets the rate (ordinary or capital) and decides whether a loss counts.",
     "With a gain on RMB held over a year, the personal box gives the lower capital rates, including 0% under the zero-rate amount. With a loss, the investment box makes it an ordinary loss instead of a lost one.",
     "The box follows the facts; it is not a choice. The official texts do not place a savings balance in either one.", ["R08", "R09", "R10", "R13", "R15"], "DF25-F02"),
    ("V5", "Convert in a year when other income is low",
     "A long-term capital gain is taxed at 0% while taxable income stays within the zero-rate amount: $49,450 single, $98,900 joint in 2026.",
     "A gain in the personal box can then cost nothing in federal tax.",
     "Applies only to a long-term capital gain; an ordinary gain is taxed from the first bracket upward.", ["R29", "R13", "R14"], ""),
    ("V6", "Keep the money in RMB for now",
     "No gain or loss is recognized until the RMB is sold or spent; moving it between RMB deposits does not count.",
     "Defers the tax and keeps the choice of year open.",
     "The gain keeps moving with the rate, the money stays in China, and buying property or investments with it is itself a taxable disposal.", ["R05", "R06"], "DF25-F07"),
    ("V7", "Know whether the money was inherited or given",
     "Inherited RMB starts again at its value on the date of death; gifted RMB keeps the giver's cost.",
     "For inherited money only the movement since the death counts.",
     "This is a fact to prove, not a choice. For a gift from someone who is not a U.S. taxpayer the texts read do not say how the dollar cost is measured.", ["R24", "R25"], "DF25-F03"),
    ("V8", "Do not route the conversion through another person or a company",
     "Nothing: the regulation lets the IRS treat a transaction or a series of transactions as a section 988 transaction where its effect is to avoid the section. The regulation's example is currency placed in a new company whose shares are then sold.",
     "Nothing found in its favour.",
     "Adds risk without changing the gain. The Chinese rules on using someone else's quota are on the dashboard's Methods page.", ["R32"], ""),
]

# --------------------------------------------------------------------------- flags
# (id, severity, item, what is not known, how to settle it, source ids)
FLAGS = [
    ("DF25-F01", "medium", "Two official averages for 2025 differ",
     "The IRS yearly average for China for 2025 is 7.129. The Federal Reserve's annual average for 2025 is 7.1875, and its twelve monthly averages give the same figure. The gap is 0.0585, about 0.8%; for 2021 to 2024 the two sources differ by 0.007 or less. On $400,000 the choice moves the illustrated gain for 2025 money by $3,055. This page uses the Federal Reserve series throughout and shows the IRS figures beside it. Neither is called wrong here.",
     "Use the actual dates and one daily rate source for a real return. Ask the IRS how its 2025 figure was computed if it matters.",
     ["DS18", "DS24", "DS27"]),
    ("DF25-F02", "high", "Which box this money is in",
     "The statute and the regulation give the test (would the costs of the transaction be business or income-producing expenses) and two examples, a bond purchase and a holiday. They do not say where a savings balance, pay left in an account, or sale proceeds waiting to be sent home belong. The regulation's own bank-account example opens with 'Assume expenses associated with the demand account are deductible under section 212'. The box changes the rate and whether a loss counts.",
     "Write down what each part of the balance was for and take it to a U.S. tax professional. Both columns are shown on this page so the range is visible meanwhile.",
     ["DS02", "DS13", "DS14"]),
    ("DF25-F03", "medium", "Gift from someone who is not a U.S. taxpayer",
     "A gift keeps the giver's basis. The texts read do not say how the dollar basis of RMB is measured when the giver never had to keep dollar records.",
     "Collect the giver's own dates of acquisition; a U.S. tax professional decides the method.",
     ["DS07", "DS14"]),
    ("DF25-F04", "medium", "RMB acquired before the holder was a U.S. taxpayer",
     "No rule for this case was found in the texts read, so the dollar cost for it is left blank in the table.",
     "A U.S. tax professional, with the dates.",
     ["DS05", "DS14"]),
    ("DF25-F05", "medium", "Where an ordinary section 988 gain or loss goes on the return",
     "No official page read in this pass names the line. Only non-official sites were found saying Schedule 1, and they are not relied on. How an ordinary loss is taken on an individual's return was not verified either.",
     "The preparer of the return; the Instructions for Form 1040 for the year.",
     ["DS20", "DS02"]),
    ("DF25-F06", "medium", "Whether the 3.8% tax reaches a currency gain",
     "The statute counts 'net gain … attributable to the disposition of property'. The regulation that defines net investment income does not mention foreign currency or section 988 (a full-text search of the current section returned nothing for either phrase). The ladder therefore shows the 3.8% in its own column, to be added only if it applies.",
     "A U.S. tax professional; the Instructions for Form 8960.",
     ["DS11", "DS16", "DS21"]),
    ("DF25-F07", "low", "Onshore and offshore renminbi",
     "A transfer between deposits 'denominated in the same nonfunctional currency' is not taxed. Whether a mainland RMB deposit and an RMB deposit held outside the mainland are the same currency for this rule is not addressed in the text read.",
     "A U.S. tax professional, before moving RMB to an account outside the mainland.",
     ["DS14"]),
    ("DF25-F08", "low", "Many small personal conversions and the $200 line",
     "The $200 line is written per transaction. No official text read says how a run of small conversions of the same money is treated. This page does not suggest relying on it.",
     "A U.S. tax professional.",
     ["DS02", "DS13"]),
    ("DF25-F09", "low", "Averages stand in for real dates",
     "The ladder prices the RMB at a yearly or monthly average because no acquisition dates have been supplied. A real figure uses the rate on each actual day.",
     "Steps 1 and 2 of the worksheet.",
     ["DS26", "DS27", "DS19"]),
    ("DF25-F10", "low", "Editions and dates of the texts",
     "The U.S. Code was read in the 2024 edition on govinfo; changes enacted after that edition were not searched for. The 2026 figures are from Rev. Proc. 2025-32, which states the law 'as in effect on October 9, 2025'. The IRS news release that repeats them carries the banner 'Historical Content'. The regulations were read on the eCFR, which says it is authoritative but unofficial.",
     "Re-read the linked pages before filing.",
     ["DS02", "DS22", "DS23", "DS13"]),
    ("DF25-F11", "medium", "State income tax",
     "Not researched. A state may tax the same gain, and the rules differ by state.",
     "The tax agency of the state of residence.",
     ["DS04"]),
    ("DF25-F12", "low", "Holding period of inherited or gifted RMB",
     "IRS Topic no. 409 says the one-year rule has exceptions for 'property acquired by gift, property acquired from a decedent' and refers to Publication 544, which was not read.",
     "IRS Publication 544.",
     ["DS20"]),
    ("DF25-F13", "low", "Header of the monthly series was not read",
     "The table rows of the monthly Federal Reserve series were read; the header block naming its release was not. As a check, the twelve monthly figures for 2025 average 7.1877 and those for 2024 average 7.1958, against the Board's published annual 7.1875 and 7.1957.",
     "Open the linked page.",
     ["DS27", "DS24"]),
]
FLAG = {f[0]: f for f in FLAGS}

# --------------------------------------------------------------------------- repository review
# (id, file and line at REVIEW_COMMIT, what it says, verdict, what the official text says, source ids, request)
REVIEW = [
    ("RV01", "dashboard/tax.html:44 (from scripts/e347_data.py:462)",
     "'… is ordinary income, unless the conversion is a personal transaction with a gain of USD 200 or less.'",
     "incomplete",
     "For a personal transaction the ordinary-income rule does not apply at any size (988(e)(1)); a personal gain over $200 is taxed, and the IRS says to report it as a capital gain.",
     ["DS02", "DS17"], "DF25-REQ-02"),
    ("RV02", "dashboard/tax.html:64 (from scripts/e347_build.py:376)",
     "'… a negative number is a loss, and whether a loss is usable was not verified.'",
     "can now be stated",
     "Investment or business box: an ordinary loss (988(a)(1)(A)). Personal box: not one of the losses an individual may deduct (165(c)).",
     ["DS02", "DS10"], "DF25-REQ-02"),
    ("RV03", "scripts/e347_data.py:41",
     "The gain table prices 2025 money at the IRS yearly average 7.129.",
     "official, but a second official figure differs",
     "The Federal Reserve's 2025 annual average is 7.1875. See flag DF25-F01.",
     ["DS18", "DS24"], "DF25-REQ-03"),
    ("RV04", "data/n676_ladder.csv:2 (the same note on 120 rows)",
     "'over the USD 200 personal-transaction threshold, so recognised as ordinary income'",
     "inconsistent with the texts",
     "Over $200 a personal gain is recognized, but 988(e)(1) switches off the ordinary-income rule for personal transactions and IRS Publication 525 says capital gain. It is ordinary only if the transaction is not personal.",
     ["DS02", "DS17"], ""),
    ("RV05", "data/m5f19_tax.csv:9",
     "'If the exclusion does not hold, the gain is ordinary, not capital'",
     "inconsistent with the texts",
     "Same point as RV04.",
     ["DS02", "DS17"], ""),
    ("RV06", "data/c3x_penalties.csv:12",
     "'Ordinary income on the gain; personal-transaction exclusion only if the gain is USD 200 or less'",
     "incomplete",
     "Same point as RV01.",
     ["DS02", "DS17"], ""),
    ("RV07", "data/d646_penalty.csv:8",
     "'Ordinary income at your marginal rate'",
     "true for one box only",
     "Ordinary in the investment or business box; capital gain in the personal box.",
     ["DS02", "DS17"], ""),
    ("RV08", "data/b9b3_penalties.csv:21",
     "'Ordinary income/loss; personal gain ≤USD 200 excluded'",
     "incomplete",
     "Same point as RV01.",
     ["DS02", "DS17"], ""),
    ("RV09", "data/f52_flags.csv:6",
     "'26 USC 988(a) treats the gain as ordinary; IRS Publication 525's summary says … capital gain. Both are official; this site does not reconcile them.'",
     "reconciled by the texts",
     "The two statements cover different cases. 988(a) is for section 988 transactions; 988(e)(1) removes personal transactions from it; Publication 525 speaks of 'a personal foreign currency transaction'.",
     ["DS02", "DS17"], ""),
    ("RV10", "data/g8d8_flags.csv:15 and data/g8d8_flag_closures.csv:9",
     "'26 CFR 1.988-1 was opened and is current, but paragraph (a)(9) was not read.'",
     "read today",
     "Paragraph (a)(9) repeats the statutory test and gives the two examples quoted in rule R11. It settles what the test is; it does not place a savings balance.",
     ["DS13"], ""),
    ("RV11", "us-fx-gain.html:83",
     "'personal currency losses are generally not deductible (IRS Pub. 525)'",
     "right rule, wrong citation",
     "The passage of Publication 525 read today speaks only of gains. The loss rule is 26 U.S.C. 165(c).",
     ["DS17", "DS10"], ""),
    ("RV12", "us-fx-gain.html:148-150",
     "The capital-gain statement applies only to personal transactions; inherited RMB takes a fair-market-value basis; gifts take a carryover basis.",
     "consistent",
     "Matches 988(e), 1014(a) and 1015(a), which this page now quotes.",
     ["DS02", "DS06", "DS07"], ""),
    ("RV13", "data/b2d_decisions.csv:25 (decision D03, status Open)",
     "'Does the personal-transaction rule remove the gain?'",
     "can be narrowed",
     "The test and both examples are now read. What stays open is the fact question in flag DF25-F02.",
     ["DS02", "DS13"], "DF25-REQ-02"),
    ("RV14", "data/final_integration_flags.csv:3",
     "'Narrowed to qualifying personal transactions; §988 business/investment characterization, basis and holding facts remain unverified.'",
     "consistent",
     "Matches the reading here.",
     ["DS02", "DS17"], ""),
    ("RV15", "48 data and script files",
     "Section 988 is cited from the 2023 edition of the U.S. Code.",
     "current edition is newer",
     "The 2024 edition is on govinfo. Subsections (a) to (d)(1) were read in both editions and no difference was seen.",
     ["DS02"], ""),
]

# =========================================================================== computation


def build_ladder():
    rows = []
    for kind, key, rate, sid in PERIODS:
        for usd in AMOUNTS:
            g = gain_for(usd, rate)
            basis = usd - g
            if g <= 0:
                rule200 = "no gain"
            elif g <= PERSONAL_LIMIT:
                rule200 = "not recognized if personal"
            else:
                rule200 = "recognized"
            rows.append({
                "period_type": kind, "period": str(key), "acquisition_rate_rmb_per_usd": str(rate),
                "usd_received": str(int(usd)), "rmb_sold": str(cents(usd * SELL)),
                "basis_usd": str(basis), "gain_or_loss_usd": str(g),
                **{f"tax_ordinary_{r}pct_usd": str(tax(g, r)) for r in ORD_RATES},
                **{f"tax_long_term_capital_{r}pct_usd": str(tax(g, r)) for r in CAP_RATES},
                "niit_3_8pct_if_it_applies_usd": str(tax(g, NIIT_RATE)),
                "usd_200_rule": rule200,
                "source_ids": f"{sid}|DS01",
                "source_urls": " | ".join([SRC[sid][4], BOC]),
            })
    return rows


def build_example():
    """Three deposits, two conversions, three methods. Exact fractions, rounded once."""
    sell = Fraction(str(SELL))
    lots = [(n, y, Fraction(int(rmb)), Fraction(int(rmb)) / Fraction(ANNUAL[y])) for n, y, rmb in EX_LOTS]
    total_rmb = sum(l[2] for l in lots)
    total_basis = sum(l[3] for l in lots)
    sale = Fraction(int(EX_SALE))
    proceeds = sale / sell

    def take(order):
        left, basis = sale, Fraction(0)
        for _, _, rmb, b in order:
            use = min(left, rmb)
            basis += b * use / rmb
            left -= use
        return basis

    out = []
    first = {"First in, first out": take(lots), "Last in, first out": take(lots[::-1]),
             "Pro rata": total_basis * sale / total_rmb}
    for name, b1 in first.items():
        b2 = total_basis - b1
        g1, g2 = proceeds - b1, proceeds - b2
        out.append({
            "method": name,
            "conversion_1_basis_usd": str(frac_cents(b1)), "conversion_1_gain_or_loss_usd": str(frac_cents(g1)),
            "conversion_2_basis_usd": str(frac_cents(b2)), "conversion_2_gain_or_loss_usd": str(frac_cents(g2)),
            "total_gain_or_loss_usd": str(frac_cents(g1 + g2)),
            "gain_taxed_if_losses_do_not_count_usd": str(frac_cents(max(g1, 0) + max(g2, 0))),
            "nature": "illustration; the deposits are invented round numbers",
            "source_ids": "DS14|DS26|DS01|DS10",
            "source_urls": " | ".join([R9882, FREDA, BOC, U165]),
        })
    lots_out = [(n, y, int(rmb), ANNUAL[y], frac_cents(b)) for n, y, rmb, b in lots]
    return out, lots_out, frac_cents(proceeds), frac_cents(total_basis)


# =========================================================================== CSV


def csv_text(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def urls(ids):
    return " | ".join(SRC[i][4] for i in ids)


def rule_sources(rule_ids):
    seen = []
    for rid in rule_ids:
        for sid in RULE[rid][4]:
            if sid not in seen:
                seen.append(sid)
    return seen


def build_csvs(ladder, example):
    f = {}
    f["data/df25_sources.csv"] = csv_text(
        ["id", "issuer", "short_label", "title", "url", "read_on", "how_read", "quotation"],
        [[s[0], s[1], s[2], s[3], s[4], READ_ON, s[5], s[6]] for s in SOURCES])
    f["data/df25_rules.csv"] = csv_text(
        ["id", "topic", "rule", "official_words", "source_ids", "source_urls", "status", "flag"],
        [[r[0], r[1], r[2], r[3], "|".join(r[4]), urls(r[4]), r[5], r[6]] for r in RULES])
    inputs = [["boc_usd_selling_rate_per_100", str(BOC_SELL_PER_100), "RMB per 100 USD",
               "Bank of China board, Pub Time 2026/11/11 15:30:04", "DS01", BOC]]
    inputs += [[f"fed_annual_average_{y}", r, "RMB per USD", "Federal Reserve annual average", "DS26", FREDA]
               for y, r in ANNUAL.items()]
    inputs += [[f"fed_monthly_average_{m}", r, "RMB per USD", "Federal Reserve monthly average", "DS27", FREDM]
               for m, r in MONTHLY.items()]
    inputs += [[f"irs_yearly_average_{y}", r, "RMB per USD", "IRS yearly average, shown for comparison", "DS18", IRSAVG]
               for y, r in IRS_AVG.items()]
    inputs += [[f"fed_daily_{d}", r, "RMB per USD", "Federal Reserve H.10 daily rate, shown as the daily source", "DS25", H10]
               for d, r in H10_DAILY.items()]
    inputs += [[f"ordinary_rate_{r}", r, "percent", "Rev. Proc. 2025-32 section 2.01", "DS22", RP2532] for r in ORD_RATES]
    inputs += [[f"long_term_capital_rate_{r}", r, "percent", "IRS Topic no. 409", "DS20", TC409] for r in ["0"] + CAP_RATES]
    inputs += [["net_investment_income_rate", NIIT_RATE, "percent", "26 U.S.C. 1411(a)(1)", "DS11", U1411]]
    for i, st in enumerate(STATUSES):
        key = st.lower().replace(" ", "_")
        for rate, lows in ORD_BRACKETS:
            inputs.append([f"2026_ordinary_{rate}pct_starts_above_{key}", lows[i], "USD of taxable income",
                           "Rev. Proc. 2025-32 section 4.01", "DS22", RP2532])
        inputs.append([f"2026_capital_zero_rate_max_{key}", CAP_ZERO_MAX[i], "USD of taxable income",
                       "Rev. Proc. 2025-32 section 4.03", "DS22", RP2532])
        inputs.append([f"2026_capital_15pct_rate_max_{key}", CAP_15_MAX[i], "USD of taxable income",
                       "Rev. Proc. 2025-32 section 4.03", "DS22", RP2532])
        inputs.append([f"niit_threshold_{key}", NIIT_THRESHOLD[i], "USD of modified adjusted gross income",
                       "26 U.S.C. 1411(b)", "DS11", U1411])
    inputs += [["personal_transaction_gain_limit", str(PERSONAL_LIMIT), "USD", "26 U.S.C. 988(e)(2)", "DS02", U988],
               ["section_988_loss_disclosure_threshold", str(LOSS_DISCLOSURE), "USD in one tax year",
                "26 CFR 1.6011-4(b)(5)(i)(E)", "DS15", R6011]]
    for n, y, rmb in EX_LOTS:
        inputs.append([f"example_lot_{n}_rmb", str(int(rmb)), "RMB",
                       f"illustration only: an invented deposit, priced at the {y} annual average", "DS26", FREDA])
    inputs.append(["example_rmb_sold_per_conversion", str(int(EX_SALE)), "RMB",
                   "illustration only: an invented conversion", "DS14", R9882])
    for amt, by_year in CANONICAL.items():
        for y, v in by_year.items():
            inputs.append([f"dashboard_gain_{amt}_acquired_{y}", v, "USD",
                           f"data/e347_fx_gain.csv as read at commit {REVIEW_COMMIT}; reproduced from the IRS average and the board",
                           "DS18", IRSAVG])
    f["data/df25_inputs.csv"] = csv_text(["key", "value", "unit", "what_it_is", "source_id", "source_url"], inputs)
    f["data/df25_ladder.csv"] = csv_text(list(ladder[0].keys()), [list(r.values()) for r in ladder])
    f["data/df25_example.csv"] = csv_text(list(example[0].keys()), [list(r.values()) for r in example])
    f["data/df25_steps.csv"] = csv_text(
        ["step", "what_to_do", "why", "rule_ids", "source_urls", "flag"],
        [[s[0], s[1], s[2], "|".join(s[3]), urls(rule_sources(s[3])), s[4]] for s in STEPS])
    f["data/df25_levers.csv"] = csv_text(
        ["id", "what_you_can_do", "what_it_changes", "in_favour", "against", "rule_ids", "source_urls", "flag"],
        [[v[0], v[1], v[2], v[3], v[4], "|".join(v[5]), urls(rule_sources(v[5])), v[6]] for v in LEVERS])
    f["data/df25_flags.csv"] = csv_text(
        ["id", "severity", "item", "what_is_not_known", "how_to_settle_it", "source_ids", "source_urls", "status"],
        [[x[0], x[1], x[2], x[3], x[4], "|".join(x[5]), urls(x[5]), "needs review"] for x in FLAGS])
    f["data/df25_repo_review.csv"] = csv_text(
        ["id", "where", "what_it_says", "verdict", "what_the_official_text_says", "source_ids", "source_urls",
         "request", "read_at_commit"],
        [[r[0], r[1], r[2], r[3], r[4], "|".join(r[5]), urls(r[5]), r[6], REVIEW_COMMIT] for r in REVIEW])
    return f


# =========================================================================== HTML

def e(s) -> str:
    return html.escape(str(s), quote=True)


def a(url, text, cls="") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{e(url)}">{e(text)}</a>'


def src_links(ids) -> str:
    return " · ".join(a(SRC[i][4], SRC[i][2]) for i in ids)


def rule_links(rule_ids) -> str:
    return src_links(rule_sources(rule_ids))


def flag_link(fid) -> str:
    return f'<a class="flag" href="#{e(fid)}">{e(fid)}</a>' if fid else ""


def table(headers, rows, cls="stack", caption=""):
    """rows: list of lists of already-escaped HTML cells."""
    out = [f'<div class="tw"><table class="{cls}">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(f"<th scope=\"col\">{e(h)}</th>" for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        rid = ""
        if isinstance(r, tuple):
            rid, r = f' id="{e(r[0])}"', r[1]
        cells = "".join(f'<td data-label="{e(h)}">{c}</td>' for h, c in zip(headers, r))
        out.append(f"<tr{rid}>{cells}</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def ladder_table(kind, key, rate, sid):
    headers = ["Dollars received", "Gain or loss"] + [f"{r}%" for r in ORD_RATES] + \
              [f"Capital {r}%" for r in CAP_RATES] + ["+3.8%", "Source"]
    src = a(SRC[sid][4], "Fed") + " " + a(BOC, "BOC")
    body = []
    for usd in AMOUNTS:
        g = gain_for(usd, rate)
        mark = "*" if D(0) < g <= PERSONAL_LIMIT else ""
        cells = [money(usd), money(g, sign=True) + mark]
        if g > 0:
            cells += [money(tax(g, r)) for r in ORD_RATES + CAP_RATES] + [money(tax(g, NIIT_RATE))]
        else:
            cells += ["–"] * (len(ORD_RATES) + len(CAP_RATES) + 1)
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + f"<td>{src}</td></tr>")
    head = "<thead><tr>" + "".join(f'<th scope="col">{e(h)}</th>' for h in headers) + "</tr></thead>"
    return f'<div class="tw"><table class="num">{head}<tbody>' + "".join(body) + "</tbody></table></div>"


def build_html(ladder, example, lots, proceeds, total_basis):
    r2025, r2024, r2023, r2021 = (D(ANNUAL[y]) for y in (2025, 2024, 2023, 2021))
    g100 = gain_for(D(100000), r2025)
    latest_m = sorted(MONTHLY)[-1]
    g_latest = gain_pct(D(MONTHLY[latest_m]))
    P = []
    P.append(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The U.S. tax on turning RMB into dollars — China money</title>
<meta name="description" content="What the United States taxes when RMB in a Chinese bank becomes dollars: the currency gain, the two boxes that set its rate, and the tax at every $10,000 step to $400,000. Every row links to the official text.">
<link rel="stylesheet" href="assets/df25.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money <small>U.S. tax on the conversion</small></a>
<nav class="nav" aria-label="Site">
<a href="index.html">Home</a>
<a href="dashboard/decisions.html">Decisions</a>
<a href="dashboard/methods.html">Methods</a>
<a href="dashboard/costs.html">Costs</a>
<a href="dashboard/steps.html">Steps</a>
<a href="dashboard/tax.html">Tax</a>
<a href="dashboard/flagged.html">Flagged</a>
<a href="{PAGE}" aria-current="page">Conversion tax</a>
</nav>
</div></header>
<main><div class="wrap">
<h1>The U.S. tax on turning RMB into dollars</h1>
<p class="lead">For a U.S. citizen with RMB in a Chinese bank. This page answers one question: what does the United States tax at the moment the RMB becomes dollars, and how much is it at each $10,000 step up to $400,000? It was read from the statute and the regulation, paragraph by paragraph, on 11 November 2026. Chinese tax, the bank's charges and the reporting forms are on the dashboard's {a("dashboard/tax.html", "Tax")} and {a("dashboard/costs.html", "Costs")} pages.</p>

<section class="callout" id="answer" aria-label="The answer">
<h2>The answer</h2>
<ul class="plain">
<li><b>Only the currency gain is taxed.</b> Sending home money you already own is not income again. The gain is the dollars you receive, minus what the same RMB cost you in dollars on the day you got it. {rule_links(["R01", "R02"])}</li>
<li><b>How big it is depends on when you got the RMB.</b> At the Bank of China selling rate of {BOC_SELL_PER_100} per $100 (11 November 2026, 15:30:04 Beijing), RMB acquired at the 2025 average shows a gain of {pct(gain_pct(r2025))} of the dollars received and at the 2024 average {pct(gain_pct(r2024))}; RMB acquired in {period_label("month", latest_m)} shows {pct(g_latest)}; RMB acquired at the 2021 average shows a loss of {pct(gain_pct(r2021)).lstrip("−")}. {src_links(["DS01", "DS26", "DS27"])}</li>
<li><b>Two boxes set the rate.</b> Investment or business money: the gain is ordinary income (10% to 37%) and a loss is an ordinary loss. Personal money: a gain of $200 or less is ignored, a larger gain is reported as a capital gain (0%, 15% or 20% if held over a year), and a loss is not deductible. {rule_links(["R08", "R09", "R12", "R13", "R15"])}</li>
<li><b>The official texts give the test for the box, not the answer for a savings balance.</b> That is the main open item: {flag_link("DF25-F02")}.</li>
</ul>
<p class="note">Nothing here is a finding about any person. The averages stand in for dates nobody has supplied, and this page reports official texts and arithmetic; it is not advice on a return.</p>
</section>

<div class="kpis">
<div class="kpi"><b>{pct(gain_pct(r2025)).lstrip("+")}</b><span>of the dollars received is currency gain if the RMB was acquired at the 2025 average of {r2025}</span><span class="src">{src_links(["DS26", "DS01"])}</span></div>
<div class="kpi"><b>{money(g100)}</b><span>currency gain on $100,000 converted, same assumption</span><span class="src">{src_links(["DS14"])}</span></div>
<div class="kpi"><b>{money(tax(g100, "15"))} – {money(tax(g100, "37"))}</b><span>federal tax on that gain, from the 15% capital rate to the 37% ordinary rate</span><span class="src">{src_links(["DS22", "DS20"])}</span></div>
<div class="kpi"><b>$0</b><span>when there is no gain. A loss counts only in the investment or business box</span><span class="src">{src_links(["DS10", "DS02"])}</span></div>
</div>

<nav class="chips" aria-label="On this page">
<a href="#box">Which box</a><a href="#cost">Dollar cost</a><a href="#scale">Size of the gain</a><a href="#ladder">Tax ladder</a><a href="#methods">Three methods</a><a href="#steps">Steps</a><a href="#levers">What changes it</a><a href="#rules">Official words</a><a href="#review">Repo review</a><a href="#flagged">Flagged for Review</a><a href="#sources">Sources</a>
</nav>
""")

    # ---- which box
    P.append('<h2 id="box">1. Which box is your money in?</h2>')
    P.append('<p>The box decides the rate and whether a loss counts. The test is the same in the statute and in the regulation: would the costs that belong to the transaction be deductible as business expenses or as expenses of producing income?</p>')
    P.append(table(["Your situation", "The official test", "If there is a gain", "If there is a loss", "Source"],
                   [[e(b[0]) + (" " + flag_link(b[5]) if b[5] else ""), e(b[1]), e(b[2]), e(b[3]), rule_links(b[4])] for b in BOXES]))
    P.append(f'<p class="note">What the texts do not say: where an ordinary bank balance belongs. The regulation\'s own bank-account example begins "Assume expenses associated with the demand account are deductible under section 212" — it assumes the box instead of deciding it. {src_links(["DS14"])} {flag_link("DF25-F02")}</p>')

    # ---- dollar cost
    P.append('<h2 id="cost">2. What did your RMB cost in dollars?</h2>')
    P.append('<p>The gain is measured from this figure, so it matters as much as today\'s rate. It depends on how the RMB reached you.</p>')
    rows = []
    for o in ORIGINS:
        cost = e(o[1]) if o[1] else '<span class="blank">Not stated in the texts read — left blank</span>'
        rows.append([e(o[0]), cost + (" " + flag_link(o[3]) if o[3] else ""), rule_links(o[2])])
    P.append(table(["Where the RMB came from", "Its dollar cost", "Source"], rows))

    # ---- scale
    P.append('<h2 id="scale">3. How big is the gain?</h2>')
    P.append(f'<p>Gain or loss = dollars received − (RMB sold ÷ the rate when the RMB was acquired). The RMB sold is the dollars received × {SELL}, the Bank of China selling rate read on 11 November 2026 at 15:30:04 Beijing time. The acquisition rate is the Federal Reserve average for the period, used for every period so that one source is used consistently. A real figure uses the rate on each actual day. {flag_link("DF25-F09")}</p>')
    rows = []
    for m in sorted(MONTHLY, reverse=True):
        r = D(MONTHLY[m])
        rows.append([e(period_label("month", m)), str(r), pct(gain_pct(r))] +
                    [money(gain_for(k, r), sign=True) for k in KEY_AMOUNTS] + [a(FREDM, "Fed monthly") + " · " + a(BOC, "BOC board")])
    P.append("<h3>By month acquired, January 2024 to October 2026</h3>")
    P.append(table(["Month acquired", "Average rate, RMB per $", "Gain or loss per $100 received", "On $10,000", "On $100,000", "On $400,000", "Source"], rows, cls="num wide"))
    rows = []
    for y in sorted(ANNUAL, reverse=True):
        r = D(ANNUAL[y])
        rows.append([str(y), str(r), pct(gain_pct(r))] +
                    [money(gain_for(k, r), sign=True) for k in KEY_AMOUNTS] + [a(FREDA, "Fed annual") + " · " + a(BOC, "BOC board")])
    P.append("<h3>By year acquired, 1994 to 2025</h3>")
    P.append(table(["Year acquired", "Average rate, RMB per $", "Gain or loss per $100 received", "On $10,000", "On $100,000", "On $400,000", "Source"], rows, cls="num wide"))
    # IRS vs Fed
    rows = []
    for y in sorted(IRS_AVG, reverse=True):
        ri, rf = D(IRS_AVG[y]), D(ANNUAL[y])
        rows.append([str(y), str(ri), str(rf), signed4(rf - ri),
                     money(gain_for(D(400000), ri), sign=True), money(gain_for(D(400000), rf), sign=True),
                     a(IRSAVG, "IRS yearly averages") + " · " + a(G5A if y >= 2022 else FREDA, "Fed G.5A" if y >= 2022 else "Fed annual")])
    P.append("<h3>Two official averages side by side</h3>")
    P.append(f'<p>The dashboard\'s Tax page uses the IRS yearly averages; this page uses the Federal Reserve series because it covers every year and month. They agree closely except for 2025. {flag_link("DF25-F01")}</p>')
    P.append(table(["Year", "IRS yearly average", "Federal Reserve annual average", "Difference", "Gain on $400,000, IRS figure", "Gain on $400,000, Fed figure", "Source"], rows, cls="num wide"))
    P.append(f'<p class="note">Check: the same formula on the IRS averages gives {money2(CANONICAL[10000][2025])} on $10,000 and {money2(CANONICAL[400000][2025])} on $400,000 for 2025 money, which is what the dashboard\'s Tax page showed at commit <code>{REVIEW_COMMIT}</code>.</p>')

    # ---- ladder
    P.append('<h2 id="ladder">4. Tax on the gain, $10,000 to $400,000</h2>')
    P.append('<p>First find your rate. Then open the period in which you got the RMB. Each cell is the gain multiplied by one rate, so it is the tax if the whole gain sits in that bracket; a gain that crosses a bracket line lies between two columns.</p>')
    P.append("<h3>Your rate in 2026</h3>")
    rows = []
    for rate, lows in ORD_BRACKETS:
        rows.append([f"{rate}%"] + [("up to " + money(ORD_BRACKETS[1][1][i])) if rate == "10" else ("over " + money(lows[i])) for i in range(4)] + [a(RP2532, "Rev. Proc. 2025-32 §4.01")])
    P.append(table(["Ordinary rate"] + STATUSES + ["Source"], rows, cls="num wide", caption="Ordinary income — taxable income at which each rate starts"))
    rows = [["0%"] + ["up to " + money(v) for v in CAP_ZERO_MAX] + [a(RP2532, "Rev. Proc. 2025-32 §4.03")],
            ["15%"] + ["up to " + money(v) for v in CAP_15_MAX] + [a(RP2532, "Rev. Proc. 2025-32 §4.03")],
            ["20%"] + ["over " + money(v) for v in CAP_15_MAX] + [a(RP2532, "Rev. Proc. 2025-32 §4.03") + " · " + a(TC409, "IRS Topic 409")]]
    P.append(table(["Long-term capital rate"] + STATUSES + ["Source"], rows, cls="num wide", caption="Long-term capital gain — taxable income limits"))
    rows = [["3.8%"] + ["income over " + money(v) for v in NIIT_THRESHOLD] + [a(U1411, "26 U.S.C. 1411") + " · " + a(TC559, "IRS Topic 559")]]
    P.append(table(["Added tax"] + STATUSES + ["Source"], rows, cls="num wide", caption="Net investment income tax — only if it applies to a currency gain"))
    P.append(f'<p class="note">Whether the 3.8% reaches a currency gain is not settled by the texts read. {flag_link("DF25-F06")} State income tax is not covered. {flag_link("DF25-F11")}</p>')
    P.append("<h3>The ladder, by when the RMB was acquired</h3>")
    P.append(f'<p class="note">Columns 10% to 37% are ordinary rates (investment or business box, or a personal gain held a year or less). "Capital" columns are long-term capital rates (personal box, held over a year). A dash means there is no gain to tax. * marks a gain of $200 or less, which is not recognized if the conversion is a personal transaction. {src_links(["DS02"])} All {len(ladder):,} rows, including every year from 1994, are in {a("data/df25_ladder.csv", "data/df25_ladder.csv")}.</p>')
    for kind, key in LADDER_TABLES:
        rate = D(MONTHLY[key]) if kind == "month" else D(ANNUAL[key])
        sid = "DS27" if kind == "month" else "DS26"
        gp = gain_pct(rate)
        word = "gain" if gp > 0 else "loss"
        opened = " open" if (kind, key) == ("year", 2025) else ""
        P.append(f'<details class="ladder"{opened}><summary><b>RMB acquired in {e(period_label(kind, key))}</b> <span>average rate {rate} · {word} {pct(gp).lstrip("+−")} · on $100,000: {money(gain_for(D(100000), rate), sign=True)}</span></summary>')
        P.append(ladder_table(kind, key, rate, sid))
        P.append("</details>")

    # ---- methods example
    P.append('<h2 id="methods">5. Three ways to count the cost of a withdrawal</h2>')
    P.append(f'<p>When an account holds RMB from different dates, the regulation lets you choose how to decide which RMB you sold, as long as the method is reasonable and you keep it. The illustration below shows why the choice matters. <b>The three deposits are invented round numbers</b>; the rates are the Federal Reserve annual averages. {src_links(["DS14"])}</p>')
    rows = [[f"Deposit {n}", str(y), f"¥{rmb:,}", str(rate), money2(b), a(FREDA, "Fed annual")] for n, y, rmb, rate, b in lots]
    rows.append(["All three", "", f"¥{sum(l[2] for l in lots):,}", "", money2(total_basis), a(R9882, "26 CFR 1.988-2")])
    P.append(table(["Deposit", "Year", "RMB", "Rate, RMB per $", "Dollar cost", "Source"], rows, cls="num wide", caption="The account in the illustration"))
    P.append(f'<p>Two conversions follow, each of ¥{int(EX_SALE):,} at {SELL}, each bringing in {money2(proceeds)}. Figures are worked exactly and rounded once, so a total can differ by a cent from the sum of rounded parts.</p>')
    rows = []
    for x in example:
        rows.append([e(x["method"]), money2(x["conversion_1_gain_or_loss_usd"]), money2(x["conversion_2_gain_or_loss_usd"]),
                     money2(x["total_gain_or_loss_usd"]), money2(x["gain_taxed_if_losses_do_not_count_usd"]),
                     a(R9882, "26 CFR 1.988-2") + " · " + a(U165, "26 U.S.C. 165")])
    P.append(table(["Method", "First conversion: gain or loss", "Second conversion: gain or loss", "Total", "Gain taxed if losses do not count (personal box)", "Source"], rows, cls="num wide"))
    P.append('<p class="note">What it shows: the total is the same under every method; the method decides which conversion carries it. In the personal box a conversion that shows a loss is simply lost, so a method that produces one loss and one larger gain ends with more gain taxed than a method that spreads the cost evenly.</p>')

    # ---- steps
    P.append('<h2 id="steps">6. Work it out, step by step</h2>')
    P.append(table(["Step", "What to do", "Why", "Source"],
                   [[str(s[0]), e(s[1]) + (" " + flag_link(s[4]) if s[4] else ""), e(s[2]), rule_links(s[3])] for s in STEPS]))
    P.append(f'<p class="note">The daily rate for any past date is published by the Federal Reserve; last week\'s release shows {H10_DAILY["2026-11-06"]} for 6 November 2026. {src_links(["DS25"])} The steps for the Chinese side and for the wire itself are on the dashboard\'s {a("dashboard/steps.html", "Steps")} page.</p>')

    # ---- levers
    P.append('<h2 id="levers">7. What lawfully changes the number</h2>')
    P.append(table(["What you can do", "What it changes", "In favour", "Against", "Source"],
                   [[e(v[1]) + (" " + flag_link(v[6]) if v[6] else ""), e(v[2]), e(v[3]), e(v[4]), rule_links(v[5])] for v in LEVERS]))

    # ---- rules in the official words
    P.append('<h2 id="rules">8. The official words behind every row</h2>')
    P.append('<p>Each rule used on this page, in plain words and then in the words of the statute, the regulation or the IRS, for checking by hand.</p>')
    P.append(table(["Rule", "In plain words", "Official words", "Source"],
                   [(x[0], [f"<b>{e(x[0])}</b> {e(x[1])}" + (" " + flag_link(x[6]) if x[6] else ""), e(x[2]), f"<q>{e(x[3])}</q>", src_links(x[4])]) for x in RULES]))

    # ---- review
    P.append('<h2 id="review">9. How the rest of this repository states the rule</h2>')
    P.append(f'<p>Read at commit <code>{REVIEW_COMMIT}</code>. No file belonging to another session was changed; the requests are logged in <code>COORDINATION.md</code>.</p>')
    P.append(table(["Where", "What it says", "Verdict", "What the official text says", "Source"],
                   [[f"<code>{e(r[1])}</code>", e(r[2]), f'<span class="verdict">{e(r[3])}</span>' + (f" <small>{e(r[6])}</small>" if r[6] else ""), e(r[4]), src_links(r[5])] for r in REVIEW]))

    # ---- flagged
    P.append('<h2 id="flagged">10. Flagged for Review</h2>')
    P.append('<p>Everything this page could not settle from an official text. None of it is filled in by guesswork; each item says how to settle it. The dashboard keeps its own list on its ' + a("dashboard/flagged.html", "Flagged") + " page.</p>")
    sev_order = {"high": 0, "medium": 1, "low": 2}
    rows = []
    for x in sorted(FLAGS, key=lambda x: (sev_order[x[1]], x[0])):
        rows.append((x[0], [f'<b>{e(x[0])}</b> <span class="sev sev-{e(x[1])}">{e(x[1])}</span>', e(x[2]), e(x[3]), e(x[4]), src_links(x[5])]))
    P.append(table(["Flag", "Item", "What is not known", "How to settle it", "Source"], rows))

    # ---- sources
    P.append('<h2 id="sources">11. Sources</h2>')
    P.append(f'<p>All read on {READ_ON}. The quotation is what the page showed; where only part of a page was read, the column says which part.</p>')
    P.append(table(["Id", "Issuer", "Page", "How it was read", "Quotation"],
                   [(s[0], [e(s[0]), e(s[1]), a(s[4], s[3]), e(s[5]), e(s[6]) if s[6] else '<span class="blank">none — the page was searched, not read</span> ' + flag_link("DF25-F06")]) for s in SOURCES]))
    P.append(f"""<p class="note">Data behind this page: {a("data/df25_ladder.csv", "ladder")} · {a("data/df25_rules.csv", "rules")} · {a("data/df25_inputs.csv", "inputs")} · {a("data/df25_example.csv", "example")} · {a("data/df25_steps.csv", "steps")} · {a("data/df25_levers.csv", "levers")} · {a("data/df25_flags.csv", "flags")} · {a("data/df25_repo_review.csv", "repo review")} · {a("data/df25_sources.csv", "sources")}.</p>
</div></main>
<footer><div class="wrap">
<p>Generated by <code>scripts/build_df25.py</code>; re-derived cell by cell by <code>scripts/verify_df25.py</code>. Session <code>arena/df256bc2-china3</code>, 11 November 2026. This page reports official texts and arithmetic on published rates. It is not tax advice.</p>
</div></footer>
</body>
</html>
""")
    return "\n".join(P)


CSS = """/* df25 — U.S. tax on the conversion. Mobile first, no JavaScript, no external assets. */
:root{
  --bg:#f5f4ef;--surface:#fff;--ink:#15202b;--muted:#56616d;--line:#dedbd1;
  --accent:#0b5f66;--accent-soft:#e3f0f0;
  --ok:#1c6b45;--ok-bg:#e4f3ea;--warn:#8a5200;--warn-bg:#fdf1d7;--bad:#9c1f1f;--bad-bg:#fbe6e4;
  --radius:10px;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#0f1418;--surface:#171e24;--ink:#e8ebee;--muted:#9ca7b2;--line:#2a333c;
    --accent:#62c7c2;--accent-soft:#17302f;
    --ok:#7fd3a4;--ok-bg:#16301f;--warn:#f0be62;--warn-bg:#33270f;--bad:#f09a94;--bad-bg:#361a18;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:96px}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif}
a{color:var(--accent);text-underline-offset:2px}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
code{font-size:.88em;background:var(--accent-soft);padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}

.top{background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.top .wrap{display:flex;flex-direction:column;gap:2px;padding-top:10px}
.brand{font-weight:700;color:var(--ink);text-decoration:none}
.brand small{font-weight:400;color:var(--muted);margin-left:8px}
.nav{display:flex;gap:2px;overflow-x:auto;margin:0 -16px;padding:0 12px;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav a{flex:none;padding:9px 10px 10px;color:var(--muted);text-decoration:none;font-size:.95rem;border-bottom:3px solid transparent}
.nav a:hover{color:var(--ink)}
.nav a[aria-current=page]{color:var(--ink);font-weight:600;border-bottom-color:var(--accent)}

main{padding:22px 0 48px}
h1{font-size:1.65rem;line-height:1.2;margin:.2em 0 .4em;letter-spacing:-.01em;text-wrap:balance}
h2{font-size:1.25rem;line-height:1.3;margin:2.2em 0 .5em}
h3{font-size:1.03rem;margin:1.5em 0 .4em}
p{margin:.5em 0 .9em;max-width:74ch}
.lead{font-size:1.06rem;color:var(--muted)}
.note{color:var(--muted);font-size:.92rem}
ul.plain{padding-left:1.2em;max-width:76ch;margin:.4em 0}
ul.plain li{margin:.5em 0}

.callout{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:var(--radius);padding:4px 16px 10px;margin:16px 0}
.callout h2{margin:.7em 0 .2em;font-size:1.1rem}
.kpis{display:grid;gap:10px;grid-template-columns:1fr 1fr;margin:14px 0 4px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px}
.kpi b{display:block;font-size:1.35rem;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi span{display:block;font-size:.86rem;color:var(--muted);margin-top:3px}
.kpi .src{font-size:.78rem;margin-top:6px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 0}
.chips a{font-size:.88rem;text-decoration:none;background:var(--accent-soft);color:var(--accent);padding:6px 11px;border-radius:999px}

.tw{overflow-x:auto;margin:10px 0 14px;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.9rem}
caption{text-align:left;padding:9px 12px 3px;font-weight:600;font-size:.9rem}
th,td{padding:8px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
thead th{font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);background:var(--bg);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:target{background:var(--warn-bg)}
table.num td,table.num th{white-space:nowrap;font-variant-numeric:tabular-nums}
table.num td:nth-child(n+2),table.num th:nth-child(n+2){text-align:right}
table.num td:last-child,table.num th:last-child{text-align:left;white-space:normal;min-width:7.5em;font-size:.8rem}
table.num td:first-child,table.num th:first-child{position:sticky;left:0;background:var(--surface);font-weight:600;box-shadow:1px 0 0 var(--line)}
table.num thead th:first-child{background:var(--bg)}
table.wide{min-width:660px}
table.stack td:last-child{font-size:.82rem;min-width:10em}
q{quotes:none;font-size:.88rem;color:var(--muted)}
.blank{display:inline-block;background:var(--warn-bg);color:var(--warn);border-radius:6px;padding:1px 7px;font-size:.86rem}
a.flag{display:inline-block;font-size:.76rem;font-weight:600;text-decoration:none;background:var(--warn-bg);color:var(--warn);border-radius:999px;padding:1px 8px;white-space:nowrap}
.sev{display:inline-block;font-size:.74rem;font-weight:600;border-radius:999px;padding:1px 8px}
.sev-high{background:var(--bad-bg);color:var(--bad)}
.sev-medium{background:var(--warn-bg);color:var(--warn)}
.sev-low{background:var(--ok-bg);color:var(--ok)}
.verdict{font-weight:600}
td small{display:block;color:var(--muted)}

details.ladder{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);margin:8px 0}
details.ladder summary{cursor:pointer;padding:11px 14px;list-style-position:outside}
details.ladder summary span{display:block;color:var(--muted);font-size:.86rem;font-variant-numeric:tabular-nums}
details.ladder[open] summary{border-bottom:1px solid var(--line)}
details.ladder .tw{border:0;border-radius:0 0 var(--radius) var(--radius);margin:0}

footer{border-top:1px solid var(--line);padding:18px 0 34px;color:var(--muted);font-size:.86rem}

/* phones: text tables become one card per row, most important cell first */
@media (max-width:719px){
  table.stack thead{position:absolute;left:-9999px}
  table.stack tr{display:block;padding:10px 12px;border-bottom:1px solid var(--line)}
  table.stack tbody tr:last-child{border-bottom:0}
  table.stack td{display:block;padding:3px 0;border:0}
  table.stack td::before{content:attr(data-label);display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-top:5px}
  table.stack td:first-child{font-weight:600;font-size:.98rem}
  table.stack td:first-child::before{display:none}
}
@media (min-width:720px){
  h1{font-size:2rem}
  .kpis{grid-template-columns:repeat(4,1fr)}
}
@media print{
  .top{position:static}
  details.ladder:not([open]){display:none}
}
"""


# =========================================================================== markdown

def build_md(ladder, example):
    r = {y: D(ANNUAL[y]) for y in ANNUAL}
    L = []
    L.append("# The U.S. tax on turning RMB into dollars — research note (df25)")
    L.append("")
    L.append(f"Session `arena/df256bc2-china3`. Every source was read on {READ_ON}. Generated by `scripts/build_df25.py`; do not edit by hand. The page is [`{PAGE}`](../{PAGE}).")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append("- Only the currency gain is taxed: dollars received minus the dollar cost of the RMB sold (26 CFR 1.988-2(a)(2)(i); 26 U.S.C. 1001).")
    L.append(f"- At the Bank of China selling rate of {BOC_SELL_PER_100} per 100 USD (11 November 2026, 15:30:04 Beijing), RMB acquired at the Federal Reserve's 2025 average ({r[2025]}) shows a gain of {pct(gain_pct(r[2025]))} of the dollars received; 2024 ({r[2024]}) {pct(gain_pct(r[2024]))}; 2023 ({r[2023]}) {pct(gain_pct(r[2023]))}; 2022 ({r[2022]}) {pct(gain_pct(r[2022]))}; 2021 ({r[2021]}) {pct(gain_pct(r[2021]))}.")
    L.append("- Investment or business money (a section 988 transaction): ordinary income or ordinary loss (26 U.S.C. 988(a)(1)(A)).")
    L.append("- Personal money: section 988 does not apply (988(e)(1)); a gain of USD 200 or less is not recognized (988(e)(2)); a larger gain is reported as a capital gain (IRS Publication 525); a loss is not among the losses an individual may deduct (26 U.S.C. 165(c)).")
    L.append("- The texts give the test for the box and two examples. They do not place a savings balance in either box (flag DF25-F02).")
    L.append("- The dollar cost of RMB withdrawn from a bank account is found by any reasonable method used consistently: first in first out, last in first out, or pro rata; not highest-cost-first (26 CFR 1.988-2(a)(2)(iii)(B)).")
    L.append("")
    L.append("## Gain and tax at key amounts (RMB acquired at the 2025 average)")
    L.append("")
    L.append("| Dollars received | Gain | Tax at 12% | 22% | 24% | 32% | 37% | Capital 15% | Capital 20% |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for usd in (D(10000), D(50000), D(100000), D(200000), D(300000), D(400000)):
        g = gain_for(usd, r[2025])
        L.append(f"| {money(usd)} | {money(g)} | " + " | ".join(money(tax(g, x)) for x in ("12", "22", "24", "32", "37", "15", "20")) + " |")
    L.append("")
    L.append(f"Sources: [Fed annual series]({FREDA}) · [Bank of China board]({BOC}) · [Rev. Proc. 2025-32]({RP2532}). The full ladder ({len(ladder):,} rows) is `data/df25_ladder.csv`.")
    L.append("")
    L.append("## Rules, with the official words")
    L.append("")
    for x in RULES:
        L.append(f"**{x[0]} — {x[1]}.** {x[2]}" + (f" _(flag {x[6]})_" if x[6] else ""))
        L.append("")
        L.append(f"> {x[3]}")
        L.append("")
        L.append("Source: " + " · ".join(f"[{SRC[i][2]}]({SRC[i][4]})" for i in x[4]))
        L.append("")
    L.append("## Flagged for Review")
    L.append("")
    L.append("| Flag | Severity | Item | What is not known | How to settle it | Source |")
    L.append("|---|---|---|---|---|---|")
    for x in FLAGS:
        L.append(f"| {x[0]} | {x[1]} | {x[2]} | {x[3]} | {x[4]} | " + " · ".join(f"[{SRC[i][2]}]({SRC[i][4]})" for i in x[5]) + " |")
    L.append("")
    L.append("## Repository review on this subject")
    L.append("")
    L.append(f"Read at commit `{REVIEW_COMMIT}`.")
    L.append("")
    L.append("| Id | Where | What it says | Verdict | What the official text says | Source |")
    L.append("|---|---|---|---|---|---|")
    for x in REVIEW:
        L.append(f"| {x[0]} | `{x[1]}` | {x[2]} | {x[3]} | {x[4]} | " + " · ".join(f"[{SRC[i][2]}]({SRC[i][4]})" for i in x[5]) + " |")
    L.append("")
    L.append("## Sources")
    L.append("")
    L.append("| Id | Issuer | Page | How it was read |")
    L.append("|---|---|---|---|")
    for s in SOURCES:
        L.append(f"| {s[0]} | {s[1]} | [{s[3]}]({s[4]}) | {s[5]} |")
    L.append("")
    return "\n".join(L)


# =========================================================================== main

def main(argv) -> int:
    check = "--check" in argv
    ladder = build_ladder()
    example, lots, proceeds, total_basis = build_example()
    files = build_csvs(ladder, example)
    files[PAGE] = build_html(ladder, example, lots, proceeds, total_basis)
    files["assets/df25.css"] = CSS
    files["research/df25-us-conversion-tax.md"] = build_md(ladder, example)
    stale = []
    for rel, text in files.items():
        path = ROOT / rel
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if check:
        if stale:
            print("STALE — run python3 scripts/build_df25.py:", ", ".join(stale))
            return 1
        print(f"OK — {len(files)} generated files match the generator")
        return 0
    print(f"wrote {len(files)} files; ladder rows: {len(ladder)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
