#!/usr/bin/env python3
"""Build the session-43606a6b CNY-to-USD evidence dashboard.

The build intentionally distinguishes (1) a reproducible calculation made from
published BOC/IRS/SAFE inputs from (2) a customer-specific or unquoted figure.
The latter is an empty CSV cell and an UNVERIFIED flag, never a made-up number.
"""
from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
AS_OF = "2026-11-10"
BOARD_TIME = "2026-11-10 07:32:39"
ASK = 6.6903
BID = 6.6622
MID = (ASK + BID) / 2
PARITY = 6.7188
PERSONAL_WIRE_CAP = 260.0
CORPORATE_WIRE_CAP = 1000.0
CABLE = 150.0
OUR = 25.0
AMOUNTS = list(range(10_000, 400_001, 10_000))

# All sources are government, regulator, statutory court, central-bank, IRS,
# eCFR, Federal Reserve, or first-party bank tariff publications.
SOURCES = [
    ("S436-01", "BOC USD/CNY exchange-rate board", "Bank of China", "https://www.boc.cn/sourcedb/whpj/enindex_1619.html", "verified", "Board read 2026-11-10 07:32:39: USD spot ask 6.6903, bid 6.6622, middle 6.7188 CNY/USD."),
    ("S436-02", "Personal e-banking outward remittance tariff", "Bank of China", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "verified", "1 per mille, CNY 50 minimum/CNY 260 maximum; CNY 150 cable to non-HK/Macau/Taiwan."),
    ("S436-03", "Corporate TT and full-amount-received (OUR) tariff", "Bank of China", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html", "verified", "Corporate TT 1 per mille, CNY 50--1,000; standard US OUR USD 25, BOC NY-clearing USD 15."),
    ("S436-04", "Cross-border debit-card ATM fee adjustment", "Bank of China", "https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html", "verified", "UnionPay overseas ATM: CNY 12 + 1%, cap CNY 112 per transaction; Visa/Mastercard change effective 2026-11-11."),
    ("S436-05", "Cross-border multi-currency debit-card features", "Bank of China", "https://www.boc.cn/bcservice/bc2/201704/t20170426_9329829.html", "verified", "Published 0% currency-conversion fee for the named card product; merchant/network rate is not published here."),
    ("S436-06", "Incoming wire fee disclosure", "Bank of China U.S.A.", "https://www.bocusa.com/personal-banking/remittance-exchange", "verified", "BOC U.S.A. says it charges no fee for incoming wire transfers."),
    ("S436-07", "Individual foreign-exchange administration rules", "People's Bank of China / State Council", "https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm", "verified", "PBOC Decree [2006] No. 3, including the foreign-individual documentation framework."),
    ("S436-08", "Foreign individual lawful RMB salary conversion Q&A", "State Administration of Foreign Exchange", "https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "verified", "SAFE Tianjin Q&A applying Current Account Guidelines Art. 59; tax evidence is part of the bank review."),
    ("S436-09", "Tax recordal for certain outward payments", "State Taxation Administration / SAFE", "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", "verified", "STA/SAFE Announcement [2013] No. 40, including foreign-individual payment categories over USD 50,000."),
    ("S436-10", "Electronic Tax Bureau recordal Q&A", "State Taxation Administration", "https://www.chinatax.gov.cn/chinatax/c102449/c5237521/content.html", "verified", "2021 No. 19: online recordal number and verification code replace paper presentation."),
    ("S436-11", "Capital-account administration simplification", "State Administration of Foreign Exchange", "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "verified", "Huifa [2014] No. 2 removed the old emigrant-property SAFE-HQ filing and staged-remittance requirement."),
    ("S436-12", "Personal property-transfer rules (2004 gazette)", "People's Bank of China", "https://www.pbc.gov.cn/chubanwu/114566/114579/114643/2839193/index.html", "verified", "Original 2004 property-transfer framework; read with later Huifa [2014] No. 2 amendments."),
    ("S436-13", "RMB cash at the border", "People's Bank of China", "https://www.pbc.gov.cn/chubanwu/114566/114579/114643/2839193/index.html", "verified", "PBOC [2004] No. 18 sets the RMB 20,000 per-person/per-trip cash limit."),
    ("S436-14", "Resident annual FX convenience amount Q&A", "State Administration of Foreign Exchange", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html", "verified", "USD 50,000 annual convenience amount is not a universal FX ceiling; bank evidence may support other lawful transactions."),
    ("S436-15", "Foreign-exchange administration regulations", "State Council / SAFE", "https://www.safe.gov.cn/safe/2008/0806/5321.html", "verified", "State Council Order 532, including Arts. 39, 40, 44 and 45 administrative sanctions."),
    ("S436-16", "Illegal FX criminal thresholds", "Supreme People's Court / Supreme People's Procuratorate", "https://www.hncourt.gov.cn/public/detail.php?id=176932", "verified", "Fa Shi [2019] No. 1 effective 2019-02-01; RMB 5m/RMB 2.5m and profit thresholds."),
    ("S436-17", "Virtual-currency financial-activity notice", "People's Bank of China", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", "verified", "Yinfa [2026] No. 42, effective 2026-02-06."),
    ("S436-18", "U.S. citizens abroad tax guide", "Internal Revenue Service", "https://www.irs.gov/publications/p54", "verified", "U.S. citizens generally report worldwide income; moving one’s own principal is not separately income."),
    ("S436-19", "Foreign-currency transaction gains", "Internal Revenue Service", "https://www.irs.gov/publications/p525", "verified", "For a qualifying personal transaction, IRS Pub. 525 says gain above USD 200 is capital gain; business/investment transactions require separate IRC 988 analysis."),
    ("S436-20", "FBAR filing requirements", "Internal Revenue Service", "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar", "verified", "FBAR required when aggregate foreign financial accounts exceed USD 10,000 at any time in a calendar year."),
    ("S436-21", "FBAR civil penalties", "eCFR", "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "verified", "31 CFR 1010.821 penalty table; current adjustment status must be checked in an enforcement case."),
    ("S436-22", "Form 8938 and FBAR comparison", "Internal Revenue Service", "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "verified", "Form 8938 and FBAR have different thresholds and filing rules."),
    ("S436-23", "International information-reporting penalties", "Internal Revenue Service", "https://www.irs.gov/payments/international-information-reporting-penalties", "verified", "Form 8938 and Form 3520 penalty descriptions."),
    ("S436-24", "Foreign gifts and Form 3520", "Internal Revenue Service", "https://www.irs.gov/businesses/gifts-from-foreign-person", "verified", "Foreign gifts are not necessarily income, but reportability can apply above USD 100,000."),
    ("S436-25", "Foreign earned income exclusion", "Internal Revenue Service", "https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion", "verified", "Tax-year 2026 FEIE is USD 132,900; conditions apply."),
    ("S436-26", "Foreign tax credit guide", "Internal Revenue Service", "https://www.irs.gov/publications/p514", "verified", "Foreign tax credit is fact- and limitation-dependent; not an automatic dollar-for-dollar calculation."),
    ("S436-27", "U.S.-China income-tax treaty", "Internal Revenue Service", "https://www.irs.gov/pub/irs-trty/china.pdf", "verified", "Treaty text; dividend source-country limitation stated in Art. 9, subject to entitlement and facts."),
    ("S436-28", "Currency/monetary-instrument report", "eCFR", "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-C/section-1010.340", "verified", "FinCEN Form 105 applies when more than USD 10,000 in currency/monetary instruments enters or leaves the U.S."),
    ("S436-29", "FX spread deregulation", "People's Bank of China", "https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html", "verified", "PBOC Yinfa [2014] No. 188 removed the statutory retail FX-spread cap; current quotes vary."),
    ("S436-30", "CNH/CNY market report", "Hong Kong Monetary Authority", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb202503/E_Half-yearly_202503.pdf", "verified", "Historical market analysis; it does not publish a personal retail conversion tariff."),
    ("S436-31", "Online FX service compliance notice", "State Administration of Foreign Exchange", "https://www.safe.gov.cn/guangdong/2020/0304/1668.html", "verified", "Licensed payment institutions are still subject to applicable FX authenticity and quota rules."),
    ("S436-32", "Individual income-tax rates", "State Taxation Administration", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html", "verified", "IIT Law Art. 3 rate categories; liability depends on the origin and facts of the money."),
    ("S436-33", "Bank-deposit interest temporary exemption", "State Taxation Administration Shanghai", "https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html", "verified", "Caishui [2008] No. 132 temporary exemption for personal savings-deposit interest."),
    ("S436-34", "Foreign-individual income conversion Q&A", "State Administration of Foreign Exchange", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html", "verified", "SAFE Q&A: tax-paid lawful remuneration is not taxed again merely when converted/remitted."),
    ("S436-35", "FATCA agreements and arrangements", "U.S. Treasury", "https://home.treasury.gov/policy-issues/tax-policy/foreign-account-tax-compliance-act", "verified", "Treasury FATCA country/arrangement information; reporting duties are determined by statute and filer facts."),
    ("S436-36", "Foreign cash carried out of China Q&A", "State Administration of Foreign Exchange", "http://www.safe.gov.cn/hebei/2019/0521/1366.html", "verified", "SAFE cash-carry explanation; obtain a bank/SAFE permit where required before travel."),
]
SOURCE = {x[0]: x for x in SOURCES}

# method_id, rank, title, class, availability, pros, cons, source IDs, fixed model
METHODS = [
    ("M01", 1, "Foreign individual: tax-paid salary / lawful current-account income → BOC USD wire", "Lawful when documented", "Usually best for a foreign-passport holder whose RMB is lawful, tax-paid income", "One wire; no USD 50k convenience cap if bank accepts foreign-individual evidence; published BOC price", "Bank will require identity and lawful-source/tax evidence; account classification must be confirmed", "S436-08|S436-09|S436-02|S436-01", "personal"),
    ("M02", 2, "Emigrant property transfer after local SAFE evidence review", "Lawful when approved/documented", "Can be a single remittance; the old 2-year staging and RMB 500k SAFE-HQ filing were removed", "Only for genuine emigrant-property transfer; documents and local SAFE/bank review remain", "S436-11|S436-12|S436-02|S436-03|S436-01", "personal"),
    ("M03", 3, "PRC resident annual USD 50,000 convenience amount", "Lawful, conditional", "Simple when the account holder is classified as a resident and amount fits the annual quota", "USD 400k requires eight calendar-year quota uses; not a way to borrow relatives’ quotas", "S436-14|S436-15|S436-02|S436-03|S436-01", "quota"),
    ("M04", 4, "Tax-recorded mainland property-sale proceeds → USD wire", "Lawful when documented", "One documented remittance can be possible; transfer itself is not a new conversion tax", "Property tax/clearance depends on facts; those tax amounts are not known from a bank balance", "S436-09|S436-10|S436-12|S436-02|S436-03|S436-01", "personal_unknown_tax"),
    ("M05", 5, "PRC-company dividend / profit distribution to U.S. owner", "Lawful when company and tax documents qualify", "Formal capital-account route; treaty may limit dividend withholding", "Corporate profit tax, withholding, eligibility and filing facts matter; not a personal-savings shortcut", "S436-03|S436-27|S436-01|S436-11|S436-10", "corporate_dividend"),
    ("M06", 6, "Re-convert unused RMB against original FX exchange memo", "Lawful, narrow", "Can avoid the resident convenience-amount problem when the original inbound exchange and time limit are evidenced", "Only within the documented original amount/time window; bank-specific operation must be confirmed", "S436-07|S436-02|S436-03|S436-01", "personal"),
    ("M07", 7, "Wire USD already held in a China foreign-currency savings account", "Lawful when account/remittance evidence accepted", "No CNY→USD conversion spread on the USD balance", "Wire/document review still applies; non-USD balance is not covered", "S436-07|S436-02|S436-03|S436-01", "usd_wire"),
    ("M08", 8, "Documented CNY cross-border remittance to Hong Kong / offshore CNH then USD", "Conditional / quote unavailable", "May be relevant only where a lawful RMB remittance and offshore account are independently available", "No official personal CNH retail spread/fee tariff; eligibility and live quote are unverified", "S436-30|S436-07", "unverified"),
    ("M09", 9, "China-issued UnionPay debit-card overseas POS spending", "Lawful spending, not USD transfer", "Can pay foreign merchants; named BOC multi-currency card advertises 0% conversion fee", "Does not deliver USD to a U.S. account; merchant/network FX rate is not published", "S436-05|S436-31", "unverified"),
    ("M10", 10, "China-issued UnionPay card overseas ATM cash withdrawal", "Lawful but impractical", "Official BOC per-withdrawal fee is published", "Delivers cash, not a U.S. bank credit; annual/card limits and travel/operator costs make it impractical", "S436-04|S436-14|S436-01", "unionpay_atm"),
    ("M11", 11, "China-issued Visa / Mastercard debit card overseas ATM cash withdrawal", "Lawful but impractical", "Published BOC fee schedule effective 2026-11-11 exists", "No official transaction-count/foreign ATM/operator total for this case; cash is not a USD wire", "S436-04", "unverified"),
    ("M12", 12, "Buy USD and carry it physically with required Chinese permit / U.S. CMIR", "Lawful only within cash-control rules", "Avoids wire fees if travel is already necessary", "Not a scalable bank-transfer method; China cash/permit and U.S. reporting rules apply; travel cost unknown", "S436-36|S436-13|S436-28|S436-01", "cash"),
    ("M13", 13, "Licensed fintech/payment-institution outward service", "Conditional / quote unavailable", "Potentially convenient if a licensed provider accepts the person and purpose", "Provider eligibility, live fee/spread, corridor and documentation are not confirmed by a regulator tariff", "S436-31", "unverified"),
    ("M14", 14, "Use relatives’ quotas / split transactions", "Prohibited", "None", "Can trigger FX-evasion/anti-splitting enforcement; do not use", "S436-15|S436-14", "prohibited_30"),
    ("M15", 15, "Underground bank / OTC matched orders", "Prohibited; potentially criminal", "None", "Administrative fines, forfeiture and criminal exposure; no lawful retail quote", "S436-15|S436-16", "prohibited_30"),
    ("M16", 16, "Convert CNY to USDT/other virtual currency then sell overseas", "Prohibited", "None", "2026 notice prohibits the activity; quote/loss cannot be responsibly estimated", "S436-17", "unverified"),
]
# The first method carries a specific pro field.  The remaining methods have a
# combined applicability/benefit phrase in the compact register above; expand
# it into the same nine-column schema without creating unsupported figures.
METHODS = [m if len(m) == 9 else m[:5] + (("None — do not use." if "Prohibited" in m[3] else "Only consider after written bank/authority confirmation that the real source of funds fits this route."),) + m[5:] for m in METHODS]

FLAGS = [
    ("S436-IR-001", "Process", "Arena fixes this session to one branch rather than the prompt’s per-task branch pattern.", "Logged; namespaced files avoid conflict.", "S436-15", "needs review"),
    ("S436-IR-002", "Coverage", "Earlier pages lacked a complete 40-step, per-method cost ladder.", "This dashboard supplies 16 methods × 40 amounts, blanking unquoted figures.", "S436-01", "resolved here"),
    ("S436-IR-003", "Source link", "Existing SAFE Guangdong S17 URL returned an official soft-404 page.", "Do not rely on that URL; use listed live SAFE/PBOC sources.", "S436-11", "needs review"),
    ("S436-IR-004", "China rules", "Earlier data retained repealed emigrant-transfer HQ filing and staged-remittance requirements.", "Huifa [2014] No. 2 removed those specific requirements.", "S436-11", "needs review"),
    ("S436-IR-005", "China rules", "Earlier corporate-profit data called for mandatory audited-report and paper recordal-form bank review.", "2014/2021 official texts simplified those items; exact bank package still must be checked.", "S436-10", "needs review"),
    ("S436-IR-006", "Bank tariff", "Existing penalty data omitted BOC’s published standard USD 25 US OUR case.", "BOC tariff distinguishes USD 15 BOC-NY clearing from USD 25 other U.S. cases.", "S436-03", "needs review"),
    ("S436-IR-007", "U.S. tax", "Legacy pages labelled personal IRC 988(e) gain over USD 200 as ordinary income.", "IRS Pub. 525 calls it capital gain for personal transactions.", "S436-19", "needs review"),
    ("S436-IR-008", "China crime", "Legacy pages used a repealed USD 200,000 illegal-FX threshold.", "2019 judicial interpretation uses RMB thresholds; facts/aggravating factors control.", "S436-16", "needs review"),
    ("S436-IR-009", "U.S. tax", "Legacy pages used 2025 FEIE USD 130,000 as current.", "IRS lists 2026 FEIE USD 132,900.", "S436-25", "needs review"),
    ("S436-IR-010", "Source quality", "Legacy foreigner-salary discussion relied in part on secondary websites.", "Primary SAFE/PBOC/STA sources require evidence and may require online recordal over USD 50k.", "S436-08", "needs review"),
    ("S436-IR-011", "Cash", "Legacy cash row omitted RMB 20,000 border limit and misdescribed cash over USD 10k.", "Use PBOC/SAFE limits and U.S. CMIR rule, not a generic customs declaration shortcut.", "S436-13", "needs review"),
    ("S436-IR-012", "China rules", "Legacy anti-splitting citations included repealed circulars without disclosure.", "Current enforcement framework must be checked against 2020 guidance/bank review.", "S436-15", "needs review"),
    ("S436-IR-013", "Bank tariff", "BOC announced a Mastercard/Visa overseas ATM tariff change effective 2026-11-11.", "Pre-/post-effective-date charges differ; this is date-sensitive.", "S436-04", "needs review"),
    ("S436-IR-014", "Editorial", "Legacy flagged-review has a stray closing span; tax page says Amsterdam location.", "Editorial defects preserved pending owning-session review.", "S436-01", "needs review"),
    ("S436-IR-015", "Classification", "PBOC/State Council definitions can classify a foreigner differently based on residence/account facts.", "Ask the actual bank for the account’s FX identity classification; no personalized assumption is made.", "S436-07", "UNVERIFIED"),
    ("S436-IR-016", "Facts missing", "No account origin, tax receipts, bank, ID classification, or U.S. filing history was supplied.", "Personal tax, cure cost and eligibility values remain blank.", "S436-18", "UNVERIFIED"),
    ("S436-IR-017", "Commercial quotes", "Non-BOC spreads, SHA deductions and non-BOC-USA incoming fees vary by bank/time.", "All are blank in this model rather than guessed.", "S436-29", "UNVERIFIED"),
    ("S436-IR-018", "Commercial quotes", "Live CNH basis, card-network FX rate and OTC spread lack fixed official tariffs.", "Cells remain blank.", "S436-30", "UNVERIFIED"),
    ("S436-IR-019", "Fintech", "Specific provider eligibility and outbound pricing are not regulator-published.", "Cells remain blank; licensed status does not waive FX rules.", "S436-31", "UNVERIFIED"),
    ("S436-IR-020", "Reporting", "FATCA arrangement status does not replace the filer’s own FBAR/Form 8938 duties.", "Reporting/cure outcomes require facts; no penalty is assumed in lawful schedules.", "S436-35", "needs review"),
]

FIELDS_COST = ["method_id", "target_usd", "cny_principal_at_boc_ask", "execution_count", "minimum_calendar_years", "fx_spread_usd", "bank_wire_and_cable_usd", "our_usd", "published_atm_fee_usd", "published_statutory_tax_or_fine_usd", "known_cost_usd", "net_after_known_cost_usd", "unverified_costs", "status", "source_id", "official_source_url", "formula_note"]


def amount(v: float | str | None) -> str:
    if v is None or v == "": return ""
    return f"{v:.2f}"


def personal_fee(u: float, cap: float = PERSONAL_WIRE_CAP) -> float:
    return min(cap, max(50.0, 0.001 * u * ASK)) / ASK + CABLE / ASK


def spread(u: float) -> float:
    return u * (ASK - MID) / ASK


def source_link(ids: str) -> tuple[str, str]:
    first = ids.split("|")[0]
    return first, SOURCE[first][3]


def model_row(method: tuple, u: float) -> dict[str, str]:
    mid, _, _, _, _, _, _, ids, model = method
    sid, url = source_link(ids)
    base = dict(method_id=mid, target_usd=f"{u:.2f}", cny_principal_at_boc_ask=amount(u*ASK), execution_count="1", minimum_calendar_years="1", fx_spread_usd="", bank_wire_and_cable_usd="", our_usd="", published_atm_fee_usd="", published_statutory_tax_or_fine_usd="", known_cost_usd="", net_after_known_cost_usd="", unverified_costs="", status="verified", source_id=sid, official_source_url=url, formula_note="")
    if model == "personal":
        fx, wire = spread(u), personal_fee(u)
        total = fx + wire
        base.update(fx_spread_usd=amount(fx), bank_wire_and_cable_usd=amount(wire), known_cost_usd=amount(total), net_after_known_cost_usd=amount(u-total), unverified_costs="Receiving/intermediary charges and any optional personal full-amount service are unquoted; corporate USD 25 OUR tariff is not assumed to apply.", status="partial", formula_note="BOC ask vs BOC bid/ask midpoint + BOC personal wire/cable only; no corporate OUR charge assumed.")
    elif model == "quota":
        n = math.ceil(u / 50_000)
        pieces = [min(50_000, u - 50_000*i) for i in range(n)]
        fx = sum(spread(x) for x in pieces)
        wire = sum(personal_fee(x) for x in pieces)
        total = fx + wire
        base.update(execution_count=str(n), minimum_calendar_years=str(n), fx_spread_usd=amount(fx), bank_wire_and_cable_usd=amount(wire), known_cost_usd=amount(total), net_after_known_cost_usd=amount(u-total), unverified_costs="Receiving/intermediary/optional full-amount charges unquoted; annual quota classification required; future-year rates are not forecast.", status="partial", formula_note="Constant-snapshot scenario: each annual USD 50,000-or-less purchase priced at the same dated BOC board; corporate OUR not assumed.")
    elif model == "personal_unknown_tax":
        fx, wire = spread(u), personal_fee(u)
        base.update(fx_spread_usd=amount(fx), bank_wire_and_cable_usd=amount(wire), unverified_costs="Property tax/clearance, receiving/intermediary charges and optional full-amount service are unknown; all-in total blank.", status="UNVERIFIED", formula_note="Personal bank components only; no total because tax and other charges are unknown.")
    elif model == "corporate_dividend":
        fx = spread(u)
        wire = min(CORPORATE_WIRE_CAP, max(50.0, 0.001*u*ASK))/ASK + CABLE/ASK
        wht = .10*u
        base.update(fx_spread_usd=amount(fx), bank_wire_and_cable_usd=amount(wire), our_usd=amount(OUR), published_statutory_tax_or_fine_usd=amount(wht), unverified_costs="All-in total blank: 10% treaty cap and OUR service apply only if eligibility/facts/service conditions are met; corporate income tax and professional costs excluded.", status="UNVERIFIED", formula_note="Conditional components: BOC corporate cap/cable + optional OUR + 10% treaty-rate dividend withholding; no all-in total inferred.")
    elif model == "usd_wire":
        wire = personal_fee(u)
        total = wire
        base.update(cny_principal_at_boc_ask="", fx_spread_usd="0.00", bank_wire_and_cable_usd=amount(wire), known_cost_usd=amount(total), net_after_known_cost_usd=amount(u-total), unverified_costs="Receiving/intermediary charges and optional personal full-amount service unquoted; corporate OUR not assumed.", status="partial", formula_note="No CNY-to-USD conversion on pre-existing USD; personal BOC wire/cable only.")
    elif model == "unionpay_atm":
        cny = u*ASK
        n = math.ceil(cny/10_000)
        withdrawals = [min(10_000, cny-10_000*i) for i in range(n)]
        fee = sum(min(112, 12 + .01*x) for x in withdrawals)/ASK
        years = math.ceil(cny/100_000)
        base.update(execution_count=str(n), minimum_calendar_years=str(years), published_atm_fee_usd=amount(fee), unverified_costs="Cash delivery only; ATM operator fees, travel, network rate and bank limits are not fully quoted.", status="UNVERIFIED", formula_note="BOC UnionPay fee formula applied to CNY 10,000 withdrawal slices; no all-in total because other costs are unknown.")
    elif model == "cash":
        trips = math.ceil(u/10_000)
        fx = spread(u)
        base.update(execution_count=str(trips), minimum_calendar_years="1", fx_spread_usd=amount(fx), unverified_costs="Travel, permit, insurance and cash-handling costs unknown; China and U.S. cash rules apply.", status="UNVERIFIED", formula_note="Shows only BOC conversion half-spread; all-in total intentionally blank.")
    elif model == "prohibited_30":
        fine = .30*u
        base.update(published_statutory_tax_or_fine_usd=amount(fine), unverified_costs="This is a maximum ordinary administrative fine illustration, not a fee or lawful conversion quote; serious cases can be 30%--100% and criminal rules may apply.", status="PROHIBITED", formula_note="State Council Order 532 permits up-to-30% ordinary fine; never use this method.")
    else:
        base.update(cny_principal_at_boc_ask="", execution_count="", minimum_calendar_years="", unverified_costs="Official source does not publish a retail all-in quote or personalized eligibility; blank by rule.", status="UNVERIFIED", formula_note="No amount is inferred.")
    return base


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def cell(text: str) -> str: return html.escape(str(text or "—"))
def money(v: str) -> str: return f"${float(v):,.2f}" if v else "—"
def source_a(sid: str) -> str:
    x = SOURCE[sid]
    return f'<a href="{html.escape(x[3])}" rel="noopener">{html.escape(sid)}</a>'
def nav(active: str) -> str:
    pages = [("schedule-dashboard.html","Dashboard"),("schedule-cost-10k-400k.html","40-step costs"),("schedule-steps.html","Steps"),("schedule-methods.html","Methods"),("schedule-penalties.html","Tax & penalties"),("schedule-flagged-review.html","Flagged for review"),("schedule-sources.html","Official sources"),("final-verification.html","Final verification")]
    return '<nav aria-label="Schedule navigation">' + ''.join(f'<a class="{"active" if href == active else ""}" href="{href}">{label}</a>' for href,label in pages) + '</nav>'
def page(title: str, active: str, body: str) -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Official-source CNY to USD transfer research and cost schedule"><title>{html.escape(title)} · China money-out guide</title><link rel="stylesheet" href="assets/schedule-43606a6b.css"></head><body><header><a class="brand" href="schedule-dashboard.html">CNY → USD <span>official-source schedule</span></a>{nav(active)}</header><main>{body}</main><footer>Research date {AS_OF}. Educational evidence dashboard, not legal, tax, investment, immigration, or bank advice. Verify current bank quote and eligibility before acting.</footer><script src="assets/schedule-43606a6b.js"></script></body></html>'''


def build_assets() -> None:
    (ASSETS / "schedule-43606a6b.css").write_text('''*{box-sizing:border-box}body{margin:0;background:#f5f8fb;color:#152333;font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}header{background:#073b4c;color:#fff;padding:16px max(20px,calc((100% - 1240px)/2));display:flex;gap:24px;align-items:center;flex-wrap:wrap}.brand{font-weight:800;color:#fff;text-decoration:none;font-size:20px}.brand span{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#b5d9df}nav{display:flex;gap:5px;overflow:auto;max-width:100%}nav a{white-space:nowrap;text-decoration:none;color:#d8edf0;padding:7px 9px;border-radius:7px;font-size:13px}nav a:hover,nav a.active{background:#126177;color:white}main{max-width:1240px;margin:auto;padding:28px 20px 48px}h1{font-size:clamp(28px,5vw,42px);line-height:1.1;margin:0 0 12px}h2{margin:36px 0 12px;font-size:24px}h3{margin:0 0 8px;font-size:17px}.lead{font-size:18px;max-width:860px;color:#435466}.notice{border-left:5px solid #d27700;background:#fff5df;padding:12px 16px;border-radius:6px;margin:18px 0}.good{border-left-color:#238454;background:#e9f7f0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:20px 0}.card{background:#fff;border:1px solid #d8e1e9;border-radius:10px;padding:16px;box-shadow:0 1px 2px #09233b0c}.big{font-size:24px;font-weight:800;color:#075c6e}.table-shell{background:#fff;border:1px solid #d8e1e9;border-radius:10px;overflow:auto;box-shadow:0 1px 2px #09233b0c}.data{border-collapse:collapse;width:100%;min-width:780px;font-size:13px}.data th{position:sticky;top:0;background:#e9f0f5;color:#263b4b;text-align:left;z-index:1}.data th,.data td{padding:10px;border-bottom:1px solid #e4ebf0;vertical-align:top}.data tr:hover td{background:#f5fbfc}.data .sticky{position:sticky;left:0;background:#fff;z-index:1;box-shadow:2px 0 3px #09233b0b}.data th.sticky{background:#e9f0f5;z-index:2}.tag{display:inline-block;border-radius:99px;padding:2px 7px;font-size:11px;font-weight:700;white-space:nowrap}.tag.verified,.tag.partial{background:#d8f1e4;color:#12623a}.tag.UNVERIFIED,.tag.unverified,.tag.needs{background:#fff1c7;color:#785100}.tag.PROHIBITED{background:#ffe0df;color:#9e2521}.muted{color:#627386}.filters{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.filters label{font-weight:700}.filters select{margin-left:5px;border:1px solid #aab9c5;border-radius:6px;padding:6px;background:#fff}.steps{padding-left:22px}.steps li{margin:7px 0}.procon{display:grid;grid-template-columns:1fr 1fr;gap:8px}.pros,.cons{padding:9px;border-radius:7px}.pros{background:#eaf7f0}.cons{background:#fff1ed}.kicker{text-transform:uppercase;letter-spacing:.1em;font-weight:700;font-size:12px;color:#007587}a{color:#006b8f}footer{background:#e6edf1;color:#485d6c;padding:20px max(20px,calc((100% - 1240px)/2));font-size:12px}@media(max-width:650px){header{padding:13px 16px}main{padding:22px 12px 36px}h1{font-size:30px}.lead{font-size:16px}.procon{grid-template-columns:1fr}.data{font-size:12px;min-width:680px}.data th,.data td{padding:8px}.table-shell{border-radius:7px}}''', encoding="utf-8")
    (ASSETS / "schedule-43606a6b.js").write_text('''document.querySelectorAll('[data-filter-table]').forEach(t=>{const amount=document.querySelector('[data-amount-filter]');const method=document.querySelector('[data-method-filter]');function go(){for(const row of t.tBodies[0].rows){row.hidden=(amount&&amount.value!=='all'&&row.dataset.amount!==amount.value)||(method&&method.value!=='all'&&row.dataset.method!==method.value)}}amount?.addEventListener('change',go);method?.addEventListener('change',go)});''', encoding="utf-8")


def build_data() -> tuple[list[dict], list[dict], list[dict]]:
    source_rows = [dict(source_id=a, title=b, issuer=c, official_source_url=d, verification_status=e, notes=f, verified_date=AS_OF) for a,b,c,d,e,f in SOURCES]
    method_rows=[]
    for mid,rank,title,legal,availability,pros,cons,ids,model in METHODS:
        sid,url=source_link(ids)
        method_rows.append(dict(method_id=mid,rank=rank,method=title,legal_status=legal,availability=availability,pros=pros,cons=cons,source_ids=ids,source_id=sid,official_source_url=url,cost_model=model))
    cost_rows=[model_row(m,u) for m in METHODS for u in AMOUNTS]
    steps=[]
    for m in METHODS:
        mid,_,title,legal,_,_,_,ids,model=m
        sid,url=source_link(ids)
        common=[
            "Confirm account identity classification and obtain a written/current bank document checklist.",
            "Gather the lawful RMB-origin evidence; do not invent contracts, invoices, tax proof, or a purpose.",
            "Obtain a live bank FX quote and itemized wire/OUR/SHA charges; compare it against the timestamped benchmark.",
            "Complete required tax recordal or SAFE/bank review before payment where the rules apply.",
            "Report U.S. worldwide income and required foreign-account forms; retain records.",
        ]
        if model in {"prohibited_30"}: common=["Do not use this method.","Use a licensed bank and a lawful documented route instead.","Seek qualified PRC and U.S. legal/tax advice if prior conduct may create exposure."]
        elif mid=="M16": common=["Do not use virtual currency to evade or bypass China FX controls.","Do not send money to an informal OTC counterparty.","Use a lawful, documented bank route instead."]
        elif model=="cash": common=["First obtain the Chinese bank/SAFE documentation required for the amount; do not assume a declaration replaces a permit.","Use the bank’s live USD selling quote and preserve exchange receipts.","Carry only within the applicable Chinese cash/permit conditions and file FinCEN Form 105 if more than USD 10,000 enters/leaves the U.S.","Deposit with a U.S. bank only after confirming its cash-source and AML documentation requirements.","Report foreign-account/income items where applicable."]
        elif model=="unionpay_atm": common=["Confirm the issuing card’s overseas ATM availability and limits directly with the issuer.","Withdraw only for a lawful travel purpose and retain ATM receipts.","Do not treat ATM cash as a scalable U.S. bank-transfer technique.","Account for cash travel/reporting rules and foreign-account reporting."]
        elif model=="unverified": common=["Ask the licensed provider/bank for written eligibility, purpose, rate, fee and documentation terms.","If no primary written quote and lawful-purpose pathway is available, do not proceed on assumptions.","Use the relevant licensed-bank documented route instead."]
        for n,text in enumerate(common,1):
            step_sid = ("S436-20" if "U.S. worldwide" in text or "foreign-account" in text else "S436-01" if "live bank FX quote" in text else "S436-09" if "tax recordal" in text else "S436-28" if "FinCEN Form 105" in text else sid)
            steps.append(dict(method_id=mid,method=title,step_number=n,step=text,legal_status=legal,source_id=step_sid,official_source_url=SOURCE[step_sid][3]))
    flag_rows=[]
    for fid,area,issue,action,sid,status in FLAGS:
        flag_rows.append(dict(flag_id=fid,area=area,issue=issue,required_action_or_verified_finding=action,status=status,source_id=sid,official_source_url=SOURCE[sid][3]))
    write_csv(DATA/"s436_sources.csv",source_rows,list(source_rows[0]))
    (DATA/"s436_sources.json").write_text(json.dumps(source_rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_csv(DATA/"s436_methods.csv",method_rows,list(method_rows[0]))
    write_csv(DATA/"s436_cost_schedule.csv",cost_rows,FIELDS_COST)
    write_csv(DATA/"s436_steps.csv",steps,list(steps[0]))
    write_csv(DATA/"s436_flags.csv",flag_rows,list(flag_rows[0]))
    summaries=[]
    for m in METHODS:
        rows=[r for r in cost_rows if r["method_id"]==m[0]]
        sid,url=source_link(m[7]);
        by={int(float(r["target_usd"])):r for r in rows}
        summaries.append(dict(method_id=m[0],rank=m[1],method=m[2],legal_status=m[3],cost_at_10000_usd=by[10000]["known_cost_usd"],cost_at_100000_usd=by[100000]["known_cost_usd"],cost_at_400000_usd=by[400000]["known_cost_usd"],minimum_years_at_400000=by[400000]["minimum_calendar_years"],status=by[10000]["status"],important_constraint=m[4],source_id=sid,official_source_url=url))
    write_csv(DATA/"s436_method_summary_40steps.csv",summaries,list(summaries[0]))
    return cost_rows,method_rows,steps


def dashboard(method_rows: list[dict], costs: list[dict]) -> str:
    top=[]
    for m in method_rows[:7]:
        r=next(x for x in costs if x["method_id"]==m["method_id"] and x["target_usd"]=="10000.00")
        top.append(f'<tr><td class="sticky"><b>{cell(m["method_id"])}</b><br>{cell(m["method"])}</td><td>{cell(m["legal_status"])}</td><td>{money(r["known_cost_usd"])}</td><td>{cell(m["availability"])}</td><td>{source_a(m["source_id"])}</td></tr>')
    return page("Dashboard", "schedule-dashboard.html", f'''<p class="kicker">Bankable first, evidence first</p><h1>Move documented China RMB legally — start with the origin, not a workaround.</h1><p class="lead">For a U.S. citizen holding CNY in mainland China, the lowest verified cost is generally a <b>licensed-bank conversion and wire of lawful, documented, already-taxed funds</b>. Conversion itself is not a new PRC income tax. The largest risks are missing source/tax evidence, an improper FX route, and missed U.S. reporting — not the published BOC bank fee.</p><div class="notice good"><b>Best-cost order:</b> (1) transfer existing USD first; (2) foreign-individual documented salary/current-account route; (3) other documentary routes matching the real origin; (4) do not use quota splitting, underground banks, or crypto.</div><div class="grid"><section class="card"><h3>Published BOC one-way spread</h3><div class="big">0.2100%</div><p>Ask 6.6903 vs bid/ask midpoint 6.67625 CNY/USD, board timestamp {BOARD_TIME}.</p><p>{source_a("S436-01")}</p></section><section class="card"><h3>Personal BOC wire/cable</h3><div class="big">¥50–¥260 + ¥150</div><p>Corporate tariff lists optional USD 25 U.S. OUR; not assumed for personal wires.</p><p>{source_a("S436-02")} · {source_a("S436-03")}</p></section><section class="card"><h3>Known cost: M01 at $10k</h3><div class="big">{money(next(x for x in costs if x["method_id"]=="M01" and x["target_usd"]=="10000.00")["known_cost_usd"])}</div><p>Personal spread + wire/cable only; receiving/intermediary fees remain unquoted.</p><p>{source_a("S436-01")} · {source_a("S436-02")}</p></section><section class="card"><h3>U.S. reporting trigger</h3><div class="big">$10,000</div><p>Aggregate foreign accounts above this at any point generally trigger FBAR.</p><p>{source_a("S436-20")}</p></section></div><h2>Fast route comparison</h2><div class="table-shell"><table class="data"><thead><tr><th class="sticky">Method</th><th>Status</th><th>Known cost at $10k</th><th>Critical constraint</th><th>Official source</th></tr></thead><tbody>{''.join(top)}</tbody></table></div><h2>Read before acting</h2><div class="grid"><section class="card"><h3>1. Identify the money’s real origin</h3><p>Salary, sale proceeds, company profits, inheritance and already-held USD have different evidence and tax paths. A bank balance alone does not establish eligibility.</p><p>{source_a("S436-08")} · {source_a("S436-09")}</p></section><section class="card"><h3>2. Do not confuse cost with tax</h3><p>Published spread/wire/cable costs are calculable. Unpaid income tax, U.S. FX gain, U.S. cure penalties, property tax, intermediary fees and provider rates are fact-dependent and shown blank.</p><p>{source_a("S436-19")} · {source_a("S436-23")}</p></section><section class="card"><h3>3. Do not evade controls</h3><p>Borrowing quotas, underground matched orders and crypto bypasses are not savings strategies. They can create administrative and criminal exposure.</p><p>{source_a("S436-15")} · {source_a("S436-16")} · {source_a("S436-17")}</p></section></div>''')


def cost_page(costs: list[dict], methods: list[dict]) -> str:
    opts=''.join(f'<option value="{m["method_id"]}">{m["method_id"]} — {html.escape(m["method"][:38])}</option>' for m in methods)
    amt=''.join(f'<option value="{u:.2f}">${u:,.0f}</option>' for u in AMOUNTS)
    rows=[]
    for r in costs:
        m=next(x for x in methods if x["method_id"]==r["method_id"])
        links = " · ".join(source_a(sid) for sid in m["source_ids"].split("|"))
        rows.append(f'<tr data-method="{r["method_id"]}" data-amount="{r["target_usd"]}"><td class="sticky"><b>{r["method_id"]}</b><br><span class="muted">{cell(m["method"][:42])}</span></td><td>${float(r["target_usd"]):,.0f}</td><td>{money(r["known_cost_usd"])}</td><td>{money(r["net_after_known_cost_usd"])}</td><td>{money(r["fx_spread_usd"])}</td><td>{money(r["bank_wire_and_cable_usd"])} + {money(r["our_usd"])}</td><td>{money(r["published_atm_fee_usd"])}</td><td>{money(r["published_statutory_tax_or_fine_usd"])}</td><td>{cell(r["execution_count"])} / {cell(r["minimum_calendar_years"])}</td><td><span class="tag {cell(r["status"])}">{cell(r["status"])}</span><br>{cell(r["unverified_costs"])}</td><td>{links}</td></tr>')
    return page("$10k–$400k costs", "schedule-cost-10k-400k.html", f'''<p class="kicker">40 increments × 16 methods = 640 source-linked rows</p><h1>Published-cost schedule: $10,000 to $400,000</h1><p class="lead">Target USD means the amount before known cost components. <b>Known cost</b> sums only components with a published formula. An em dash means the official source does not provide a value or the value depends on your records; it is not zero.</p><div class="notice"><b>Most important:</b> M01’s $10k published BOC benchmark is spread + personal wire/cable only. It excludes unknown receiving/intermediary fees, any optional personal full-amount service, and unpaid underlying tax. The corporate USD 25 OUR tariff is not silently applied to personal wires. Quota rows repeat today’s snapshot across future years; they are not forecasts.</div><div class="filters"><label>Show amount <select data-amount-filter><option value="all">All 40 amounts</option>{amt}</select></label><label>Show method <select data-method-filter><option value="all">All 16 methods</option>{opts}</select></label></div><div class="table-shell"><table class="data" data-filter-table><thead><tr><th class="sticky">Method</th><th>Target</th><th>Known published cost</th><th>Net after known cost</th><th>FX spread</th><th>Wire/cable + OUR</th><th>ATM fee</th><th>Tax/fine shown</th><th>Actions / min years</th><th>Disclosure</th><th>Official source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><p class="muted">Calculation: conversion spread = target USD × (6.6903 − 6.67625) ÷ 6.6903. Personal wire = clamp(0.1% × CNY principal, ¥50, ¥260) + ¥150 cable, converted at the same published selling rate. Personal totals exclude unquoted receiving/intermediary/optional OUR charges. See <a href="research/s436-cost-methodology.md">methodology</a> (repository source) and the official links in each row.</p>''')


def methods_page(methods: list[dict]) -> str:
    rows=[]
    for m in methods:
        tag_class = "PROHIBITED" if "Prohibited" in m["legal_status"] else "partial"
        links = " · ".join(source_a(x) for x in m["source_ids"].split("|"))
        rows.append(
            '<tr><td class="sticky"><b>{}</b><br>{}</td><td><span class="tag {}">{}</span></td><td>{}</td>'
            '<td><div class="procon"><div class="pros"><b>Pros</b><br>{}</div><div class="cons"><b>Cons / limits</b><br>{}</div></div></td><td>{}</td></tr>'.format(
                cell(m["method_id"]), cell(m["method"]), tag_class, cell(m["legal_status"]),
                cell(m["availability"]), cell(m["pros"]), cell(m["cons"]), links
            )
        )
    return page("Methods", "schedule-methods.html", f'''<p class="kicker">All identified routes, including routes to avoid</p><h1>16 CNY → USD methods: applicability before price</h1><p class="lead">A method is not a recommendation merely because it appears here. The lowest-cost lawful option is the method whose documentation matches the actual source of funds. Do not relabel money to fit a route.</p><div class="table-shell"><table class="data"><thead><tr><th class="sticky">Method</th><th>Legal status</th><th>When it may apply</th><th>Pros & constraints</th><th>Official source(s)</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>''')


def steps_page(steps: list[dict], methods: list[dict]) -> str:
    blocks=[]
    for m in methods:
        s=[x for x in steps if x["method_id"]==m["method_id"]]
        list_items = "".join("<li>{} <small>({})</small></li>".format(cell(x["step"]), source_a(x["source_id"])) for x in s)
        blocks.append('<section class="card"><p class="kicker">{} · {}</p><h2>{}</h2><ol class="steps">{}</ol></section>'.format(
            cell(m["method_id"]), cell(m["legal_status"]), cell(m["method"]), list_items
        ))
    return page("Steps", "schedule-steps.html", f'''<p class="kicker">Execution playbooks</p><h1>Step-by-step — without inventing documents or eligibility</h1><p class="lead">Steps describe a compliance-first sequence. They do not override a bank’s current written instructions. Prohibited methods are shown only to make the prohibition unmistakable.</p>{''.join(blocks)}''')


def penalties_page() -> str:
    rows=[
        ("Conversion of already-taxed lawful personal principal", "No separate PRC conversion income tax identified; document source/tax proof.", "—", "S436-34"),
        ("Underlying PRC income", "IIT arises from income/property/dividend facts, not simply from wiring. Rates/tax base must not be inferred from balance.", "UNVERIFIED", "S436-32"),
        ("U.S. income and IRC 988 personal gain", "U.S. citizen reports worldwide income. For a qualifying personal transaction, Pub. 525 says FX gain over $200 is capital gain; §212/business facts can change the analysis, and basis/date are missing.", "UNVERIFIED", "S436-18"),
        ("FBAR", "Aggregate foreign accounts over $10,000 at any point can trigger filing. Penalty outcome depends on facts/willfulness.", "UNVERIFIED", "S436-20"),
        ("Form 8938 / FATCA", "Different thresholds from FBAR; form and penalty rules are fact-dependent.", "UNVERIFIED", "S436-22"),
        ("Foreign gift / Form 3520", "A foreign gift is not necessarily income; reporting above $100,000 and penalty outcome must be assessed from facts.", "UNVERIFIED", "S436-24"),
        ("Illegal FX / splitting / OTC", "Administrative fines can be up to 30% ordinarily and 30%–100% in serious cases; criminal thresholds separately apply.", "Do not use", "S436-15"),
        ("Illegal FX criminal threshold", "2019 judicial interpretation uses RMB 5m general volume / RMB 2.5m with aggravating circumstances, plus profit criteria.", "Do not use", "S436-16"),
        ("Physical currency", "China permit/cash rules and U.S. CMIR rule may apply; more than $10k crossing U.S. border requires FinCEN report.", "Conditional", "S436-28"),
    ]
    rendered=[]
    for a,b,c,d in rows:
        tag_class = "UNVERIFIED" if c == "UNVERIFIED" else "PROHIBITED" if c == "Do not use" else "partial"
        rendered.append('<tr><td class="sticky"><b>{}</b></td><td>{}</td><td><span class="tag {}">{}</span></td><td>{}</td></tr>'.format(cell(a), cell(b), tag_class, cell(c), source_a(d)))
    table=''.join(rendered)
    return page("Tax & penalties", "schedule-penalties.html", f'''<p class="kicker">The large risks are legal and reporting, not just fees</p><h1>Tax, reporting & penalty analysis</h1><p class="lead">Do not call every deduction a “conversion tax.” This page separates a lawful bank’s market spread/fee from underlying tax, U.S. reporting, and prohibited-FX enforcement. Personalized tax or penalties are blank where records are missing.</p><div class="table-shell"><table class="data"><thead><tr><th class="sticky">Layer</th><th>Official-source finding</th><th>Schedule treatment</th><th>Official source</th></tr></thead><tbody>{table}</tbody></table></div>''')


def flags_page() -> str:
    flag_rows=[]
    for fid,area,issue,action,sid,status in FLAGS:
        clas="UNVERIFIED" if status=="UNVERIFIED" else "needs"
        flag_rows.append(f'<tr><td class="sticky"><b>{fid}</b></td><td>{cell(area)}</td><td>{cell(issue)}</td><td>{cell(action)}</td><td><span class="tag {clas}">{cell(status)}</span></td><td>{source_a(sid)}</td></tr>')
    return page("Flagged for review", "schedule-flagged-review.html", f'''<p class="kicker">Transparent irregularity register</p><h1>Flagged for Review</h1><p class="lead">These findings do not block publication. Items marked <b>UNVERIFIED</b> deliberately have blank personalized cost cells. Review the direct official source before relying on any historical page elsewhere in this repository.</p><div class="table-shell"><table class="data"><thead><tr><th class="sticky">ID</th><th>Area</th><th>Issue found</th><th>Action / verified finding</th><th>Status</th><th>Official source</th></tr></thead><tbody>{''.join(flag_rows)}</tbody></table></div>''')


def sources_page() -> str:
    rows=''.join(f'<tr><td class="sticky"><b>{cell(a)}</b></td><td>{cell(b)}</td><td>{cell(c)}</td><td>{cell(e)}</td><td><a href="{html.escape(d)}" rel="noopener">Open official source</a></td></tr>' for a,b,c,d,e,f in SOURCES)
    return page("Official sources", "schedule-sources.html", f'''<p class="kicker">Primary source register</p><h1>36 official sources</h1><p class="lead">Every schedule, method, step, penalty and flag row links to one or more records below. Timestamped bank rates are snapshots, not promises of an executable future quote.</p><div class="table-shell"><table class="data"><thead><tr><th class="sticky">ID</th><th>Title</th><th>Issuer</th><th>Status</th><th>Official link</th></tr></thead><tbody>{rows}</tbody></table></div>''')


def main() -> None:
    DATA.mkdir(exist_ok=True); ASSETS.mkdir(exist_ok=True)
    build_assets()
    costs, methods, steps = build_data()
    (ROOT/"schedule-dashboard.html").write_text(dashboard(methods,costs),encoding="utf-8")
    (ROOT/"schedule-cost-10k-400k.html").write_text(cost_page(costs,methods),encoding="utf-8")
    (ROOT/"schedule-methods.html").write_text(methods_page(methods),encoding="utf-8")
    (ROOT/"schedule-steps.html").write_text(steps_page(steps,methods),encoding="utf-8")
    (ROOT/"schedule-penalties.html").write_text(penalties_page(),encoding="utf-8")
    (ROOT/"schedule-flagged-review.html").write_text(flags_page(),encoding="utf-8")
    (ROOT/"schedule-sources.html").write_text(sources_page(),encoding="utf-8")
    print(f"built {len(costs)} schedule rows, {len(methods)} methods, {len(steps)} steps, {len(SOURCES)} sources")

if __name__ == "__main__": main()
