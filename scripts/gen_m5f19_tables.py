#!/usr/bin/env python3
"""
Generate the remaining m5f19 tables: classification decision tree, method
catalogue, step playbooks, tax/penalty decomposition, cost reconciliation and
the flag register.

Every numeric cost cell is produced by scripts/m5f19_engine.py from the verified
2026-11-10 inputs. No cost figure in these CSVs is typed by hand.
"""
from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import m5f19_engine as eng  # noqa: E402

S01 = "https://www.boc.cn/sourcedb/whpj/"
S02 = ("https://www.boc.cn/ebanking/service/cs1/200905/"
       "t20090506_990712.html")
S03 = "https://www.safe.gov.cn/safe/2008/0806/5321.html"
S04 = "https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm"
S05 = ("https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/"
       "art_0dd36157a03f494db7571002c7f785b8.html")
S06 = "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"
S07 = "https://www.safe.gov.cn/tianjin/2024/0229/2402.html"
S09 = "https://www.safe.gov.cn/ningxia/2022/0929/1997.html"
S10 = "https://www.safe.gov.cn/tianjin/2024/0903/2594.html"
S11 = ("https://www.chinatax.gov.cn/n810219/n810744/n3752930/"
       "n3752974/c3970366/content.html")
S12 = ("https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/"
       "USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm")
S13 = ("https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/"
       "USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm")
S14 = ("https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/"
       "subpart-H/section-1010.821")
S15 = ("https://www.irs.gov/businesses/small-businesses-self-employed/"
       "report-of-foreign-bank-and-financial-accounts-fbar")
S16 = ("https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-"
       "for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill")

BLANK = ""  # the repository rule: unverified => empty cell + flag


# ==========================================================================
# 1. Classification decision tree — the question the repository never asked
# ==========================================================================
CLASSIFICATION = [
    ("C1", 1,
     "Was the Chinese account opened on a PASSPORT (not a PRC resident identity card)?",
     "The bank recorded you as an OVERSEAS INDIVIDUAL (境外个人). PBOC Order [2006] No.3 Art. 37(2) puts a foreign citizen holding a passport in that category, and Art. 28 makes the opening documents decisive.",
     "The bank recorded you as a DOMESTIC INDIVIDUAL (境内个人). PBOC Order [2006] No.3 Art. 37(1) limits that category to Chinese citizens holding a PRC resident ID, military ID or armed-police ID.",
     "PBOC Order [2006] No. 3, Arts. 28 and 37", S04, "F07,F08"),
    ("C2", 2,
     "Have you resided CONTINUOUSLY in mainland China for a full year?",
     "A second, conflicting definition is engaged: State Council Order 532 Art. 52(2) counts a foreigner continuously resident for a full year as a DOMESTIC INDIVIDUAL. The two instruments disagree. Ask the account-opening bank which category your account carries in the personal FX monitoring system; Art. 28 makes the bank's record operative.",
     "Only the PBOC definition is engaged and you are an overseas individual.",
     "State Council Order 532 Art. 52(2) vs PBOC Order [2006] No. 3 Art. 37", S03, "F06,F07"),
    ("C3", 3,
     "Do you hold a 外国人永久居留身份证 (Foreign Permanent Residence Identity Card)?",
     "Guidelines Art. 59 para 2: the annual convenience amount for FX PURCHASE applies to you. You can purchase up to USD 50,000 equivalent per year on identity document alone.",
     "Guidelines Art. 59 para 2 does NOT extend the purchase convenience amount to you. Your purchase leg runs on documents, not on a quota.",
     "汇发〔2020〕14号 Guidelines Art. 59 para 2; SAFE Tianjin 2024 Q&A (九)", S06, "F10"),
    ("C4", 4,
     "Is the money LAWFUL CURRENT-ACCOUNT RMB INCOME earned onshore (salary, labour remuneration, rent, royalties, service fees, business income)?",
     "This is the main documented route. Guidelines Art. 59 and PBOC Art. 13 allow the purchase AND the remittance on identity document plus amount-bearing source-of-funds documents INCLUDING A TAX CERTIFICATE. SAFE Ningxia confirms there is no amount limit on genuine, lawful current-account purchase and settlement.",
     "The current-account route is not available to you. Continue to C5-C8; the money's legal character must be established before any route applies.",
     "汇发〔2020〕14号 Guidelines Art. 59; PBOC Order [2006] No. 3 Art. 13; SAFE Ningxia 2022释疑(八)", S09, "F09,F10,F14"),
    ("C5", 5,
     "Is the balance ALREADY in USD or another foreign currency, sitting in an FX account?",
     "NO PURCHASE IS NEEDED, so there is no spread to pay at all. Guidelines Art. 65(1): an overseas individual remits FX from an FX account on identity document alone, with no amount threshold stated. Art. 64(1) for a domestic individual: up to USD 50,000 equivalent per day on identity document, above that identity document plus amount-bearing materials.",
     "You must purchase the FX first, and the purchase leg is what carries the documentation burden and the spread.",
     "汇发〔2020〕14号 Guidelines Arts. 64(1) and 65(1)", S05, "F11,F12"),
    ("C6", 6,
     "Is the money the proceeds of selling ONSHORE REAL PROPERTY that you own?",
     "Capital account. PBOC Art. 22: RMB proceeds of an overseas individual's sale of onshore commercial residential property may, SUBJECT TO SAFE APPROVAL, be purchased into FX and remitted out. IIT is charged at 20% on the GAIN (proceeds less original value and reasonable expenses), and the IIT payment certificate is inspected before the transfer can be registered.",
     "Not this route.",
     "PBOC Order [2006] No. 3 Art. 22; IIT Law Arts. 3(3), 6(5), 15 para 2", S11, "F20,F35,F38"),
    ("C7", 7,
     "Are you EMIGRATING and cancelling your Chinese household registration (户口)?",
     "SEQUENCE IS MANDATORY AND BACKWARDS FROM WHAT MOST PEOPLE ASSUME: IIT Law Art. 13 para 4 requires the tax clearance to be completed BEFORE the household registration is cancelled, and Art. 10(5) makes the cancellation a filing trigger. Only then can 汇发〔2014〕2号 §6 be used: approval at the SAFE branch of your ORIGINAL hukou location, and since 2014 a single lump-sum remittance is permitted and the RMB 500,000 head-office filing and the notarisation requirements are abolished.",
     "The emigrant property-transfer route is not available. A US citizen who never held a Chinese hukou cannot use it at all.",
     "IIT Law Arts. 10(4)-(5), 13 para 4; 汇发〔2014〕2号 §6(1)-(2),(4)", S10, "F23,F24,F37"),
    ("C8", 8,
     "Is the money your share of a LAWFULLY LIQUIDATED foreign-invested enterprise?",
     "State Council Order 532 Art. 22 para 3: after liquidation and tax payment in accordance with relevant State provisions, the RMB belonging to the foreign investor may be purchased into FX and remitted out through an institution operating FX settlement and sale business.",
     "Not this route.",
     "State Council Order 532 Art. 22 para 3", S03, "F22"),
    ("C9", 9,
     "Can you produce a GENUINE, LAWFUL transaction background for the money at all?",
     "Order 532 Art. 5 provides that the State does not restrict current-account international payments and transfers; Guidelines Art. 54 requires a genuine and lawful transaction background for personal current-account FX business; Art. 68 lets the bank refuse anything whose authenticity is doubtful. With documents, a route exists.",
     "NO LAWFUL PERSONAL ROUTE WAS IDENTIFIED IN THE INSTRUMENTS REVIEWED. Do not fall back on an informal channel: Order 532 Art. 45 reaches private and disguised FX dealing with a fine of up to 30% of the amount (30%-100% where serious), Art. 39 reaches unlawful outward transfer on the same scale, and the U.S. side adds a structuring penalty of up to the full amount involved.",
     "State Council Order 532 Arts. 5, 39, 45; Guidelines Arts. 54, 68; 31 U.S.C. §5321(a)(4)", S03, "F05,F13,F17,F28,F29,F50"),
]


# ==========================================================================
# 2. Method catalogue
# ==========================================================================
# id, name, legal_status, who, governing_instrument, documents_required,
# amount_ceiling_stated_in_text, cost_model, pros, cons, source_url, fact_ids
METHODS = [
    ("M01", "Bank FX purchase + outward wire — overseas individual with documented current-account RMB income",
     "Lawful", "境外个人 (a US citizen classified on passport)",
     "汇发〔2020〕14号 Art. 59 (purchase) + Art. 65(1) (remittance); PBOC Order [2006] No. 3 Art. 13",
     "Valid ID + amount-bearing source-of-funds documents for the purchase, INCLUDING a tax certificate",
     "No ceiling stated in Art. 59 or Art. 65(1)",
     "priced",
     "The only route in the reviewed instruments that both converts and remits on documents rather than on a quota; no annual cap appears in the text; a single wire is permitted because Art. 65(1) states no amount threshold; the tax certificate you need is evidence of tax already paid, not a new conversion tax",
     "The bank decides whether your documents are sufficient and may refuse under Art. 68; the tax certificate must exist, so unpaid PRC tax on the underlying income blocks the route; branch practice varies because much of the guidance is branch-level Q&A",
     S06, "F09,F10,F11,F14,F17"),
    ("M02", "Bank FX purchase + outward wire — domestic individual above the convenience amount, on purpose documents",
     "Lawful", "境内个人 (a Chinese citizen, or a foreigner continuously resident 1 year on the Order 532 reading)",
     "汇发〔2020〕14号 Arts. 54, 56, 57, 64(1)",
     "Valid ID + amount-bearing documents on the PURPOSE of the purchase funds + a completed 个人购汇申请书; above USD 50,000/day on the remittance leg, amount-bearing materials",
     "USD 50,000 per person per year is a DOCUMENTATION threshold, not a cap (SAFE Ningxia 2022)",
     "priced",
     "Works for any amount provided the documents exist; the purchase above the convenience amount expressly does not occupy the quota; e-banking and counter are both permitted under Art. 55",
     "Art. 57 makes you personally and legally responsible for the accuracy of the 购汇申请书; Art. 64(1) requires the purchase purpose and the remittance purpose to be consistent, and the bank reviews that; Art. 62 makes splitting a watch-list offence",
     S07, "F12,F13,F14,F15,F16"),
    ("M03", "Remit foreign currency you ALREADY hold in an FX account — no purchase, no spread",
     "Lawful", "境外个人: Art. 65(1), ID only. 境内个人: Art. 64(1), ID up to USD 50,000/day, ID + documents above",
     "汇发〔2020〕14号 Arts. 64(1), 65(1); PBOC Order [2006] No. 3 Arts. 13, 14",
     "Valid ID (overseas individual). Domestic individual above USD 50,000/day also needs amount-bearing materials",
     "Art. 65(1) states NO amount threshold for an overseas individual",
     "priced_no_spread",
     "Cheapest route that exists: with no purchase there is no bid/ask spread at all, so the only published cost is the wire fee and the telecom charge; an overseas individual needs nothing but ID",
     "Only available if the balance is already in foreign currency; a CNY balance cannot use it; the remittance must still be current-account in character",
     S05, "F09,F11,F12,F18"),
    ("M04", "Annual convenience amount — FX purchase on identity document alone",
     "Lawful within its own scope", "境内个人 for purchase; 境外个人 ONLY if holding a Foreign Permanent Residence Identity Card. All individuals for SETTLEMENT (USD->CNY)",
     "汇发〔2020〕14号 Arts. 54, 55, 59 para 2; PBOC Order [2006] No. 3 Arts. 9, 40",
     "Valid ID only, inside the amount",
     "USD 50,000 equivalent per person per year, expressly NOT a limit on the total you may transact",
     "priced",
     "The simplest paperwork of any route: counter or e-banking on ID alone; SAFE Ningxia states in terms that it is not an annual ceiling",
     "A US citizen without a Chinese permanent-residence ID does not get it for PURCHASE under Art. 59 para 2 — this is the single most commonly mis-stated point in the repository's earlier layers; above the amount you are back to producing documents anyway",
     S09, "F10,F13,F14"),
    ("M05", "Emigrant property transfer (移民财产转移)",
     "Lawful, approval required", "A person emigrating who is cancelling a Chinese household registration",
     "汇发〔2014〕2号 §6(1),(2),(4); PBOC Order [2006] No. 3 Art. 26",
     "Application to the SAFE branch at the ORIGINAL hukou location; property-right documents (notarisation abolished in 2014); the household-registration cancellation certificate",
     "No amount ceiling stated; the RMB 500,000 head-office filing requirement was abolished in 2014",
     "priced",
     "Since 2014 a SINGLE lump-sum remittance is permitted — the earlier installment requirement was abolished; the head-office filing above RMB 500,000 was abolished; notarisation of property documents and of agency agreements was abolished",
     "Unavailable to a US citizen who never held a Chinese hukou; gated by the IIT Law Art. 13 para 4 tax clearance, which must be completed BEFORE the hukou is cancelled; approval is discretionary and evidence-heavy",
     S10, "F21,F23,F24,F25,F37"),
    ("M06", "Inheritance property transfer (继承财产转移)",
     "Lawful, approval required", "An heir of a decedent who held a Chinese household registration",
     "汇发〔2014〕2号 §6(1),(3)",
     "Application to the SAFE branch at the decedent's PRE-DEATH hukou location; since 2014 inheritances from different decedents may be combined in one application",
     "No amount ceiling stated", "priced",
     "Combined applications permitted since 2014; one lump sum or installments at the applicant's choice within the approved amount",
     "Requires a Chinese decedent with a hukou; approval is discretionary; the underlying estate must be documented",
     S10, "F23,F24,F25"),
    ("M07", "Proceeds of selling onshore real property you own",
     "Lawful, SAFE approval required", "境外个人 who owns onshore commercial residential property",
     "PBOC Order [2006] No. 3 Art. 22; IIT Law Arts. 3(3), 6(5), 15 para 2",
     "SAFE approval for the purchase-and-remit; the IIT payment certificate is inspected before the property transfer is registered",
     "No ceiling stated in Art. 22", "priced",
     "A genuine capital-account exit for property wealth; the 20% IIT is charged on the GAIN (proceeds less original value and reasonable expenses), not on the sale price, and is creditable in principle against U.S. tax",
     "You must actually own and sell the property; SAFE approval is required before the FX purchase; the 20% IIT on the gain is a real cash cost that must be paid before the money can move",
     S04, "F20,F35,F38"),
    ("M08", "Investor's share of a lawfully liquidated foreign-invested enterprise",
     "Lawful", "The foreign investor in a terminated FIE",
     "State Council Order 532 Art. 22 para 3",
     "Evidence of lawful termination, completed liquidation and tax payment",
     "No ceiling stated", "priced",
     "Expressly provided for in a State Council administrative regulation — the highest-ranking instrument reviewed; covers capital, not just income",
     "Only available where there is a real enterprise, a real liquidation and tax actually paid; the liquidation itself takes time and professional cost; Art. 22 para 3 speaks to the RMB 'belonging to the foreign investor', so personal savings are out of scope",
     S03, "F22"),
    ("M09", "Company profit / dividend remittance",
     "Lawful if the money belongs to the company", "A domestic institution distributing profit to a foreign shareholder",
     "汇发〔2014〕2号 §5(1),(2); 汇发〔2020〕14号 Art. 49(4)",
     "Board (or partnership) profit-distribution resolution + the ORIGINAL tax filing form for remittances above USD 50,000; the bank stamps the original with the amount and date",
     "USD 50,000 is a document-review threshold, not a cap; the old limit tied to 'dividends payable + undistributed profits' in the latest audit report was abolished in 2014",
     "priced",
     "The 2014 reform removed the audit-report and capital-verification-report review above USD 50,000 and abolished the undistributed-profits ceiling; a real corporate route for real corporate money",
     "Not a personal route at all — using it for personal savings is a disguised transfer and engages Order 532 Art. 39; corporate income tax and withholding tax fall before the remittance; the tax recordal must exist",
     S10, "F26,F27"),
    ("M10", "Service-trade outward payment against a genuine service contract",
     "Lawful if the transaction is genuine", "A domestic institution or individual paying for a real cross-border service",
     "汇发〔2020〕14号 Arts. 47, 49(1),(4), 53",
     "Contract, invoice or settlement list showing the subject matter, parties and amount; above USD 50,000 per transaction, tax recordal first and the bank verifies the recordal form",
     "USD 50,000 per transaction is a review/recordal threshold, not a cap", "priced",
     "A legitimate channel for genuine services; below USD 50,000 the bank in principle need not review the documents at all",
     "Art. 47 expressly forbids fabricating a trade background and forbids evading FX control by splitting; a payment without a real service behind it is 非法套汇 under Order 532 Art. 40 with a fine up to 30% (30%-100% where serious)",
     S05, "F27,F28,F30"),
    ("M11", "Convert back RMB left over from an earlier exchange",
     "Lawful within its terms", "境外个人 who previously exchanged FX into RMB and did not use it all",
     "汇发〔2020〕14号 Art. 60",
     "Valid ID + the ORIGINAL EXCHANGE SLIP; slip valid for conversion back for 24 months from the exchange date",
     "Up to USD 500 equivalent same-day on ID alone; up to USD 1,000 equivalent same-day at pre-departure locations outside the customs area",
     "not_priced",
     "No source-of-funds documentation beyond the slip; the small same-day amounts need nothing but ID",
     "Only reverses an exchange you already made — it cannot export money that originated as RMB; hard 24-month expiry on the slip",
     S05, "F19"),
    ("M12", "Return unused FX that was remitted IN, along the original route",
     "Lawful", "境外个人 with FX previously remitted into China and not used",
     "PBOC Order [2006] No. 3 Art. 14", "Valid ID", "No ceiling stated in Art. 14", "not_priced",
     "Identity document only; the simplest reversal route in the reviewed instruments",
     "Only for money that came IN from abroad and was not used; it is a refund path, not an export path for domestically earned CNY",
     S04, "F18"),
    ("M13", "Entrust a close relative to act for you",
     "Lawful as AGENCY only", "Any individual; 近亲属 means spouse, parents, children, siblings, paternal and maternal grandparents, paternal and maternal grandchildren",
     "汇发〔2020〕14号 Art. 61",
     "Both parties' valid IDs + a power of attorney + relationship documentation (hukou book, marriage certificate, birth certificate; a commitment letter may substitute where these genuinely cannot be provided)",
     "Within the convenience amount for quota-occupying business; with amount-bearing materials for non-quota-occupying business",
     "not_priced",
     "A genuine convenience where you are not in China; the relationship can be evidenced by a commitment letter where documents cannot be obtained",
     "This is agency for YOUR OWN genuine transaction. Using a relative's quota to move your money is exactly the borrowing that Art. 62(2) puts on the watch list for three years, and it exposes the relative under Art. 62(1)",
     S05, "F16"),
    ("M14", "Carry foreign cash across the border",
     "Lawful only inside narrow limits", "Any individual",
     "汇发〔2020〕14号 Arts. 86, 89; State Council Order 532 Art. 42; PBOC Order [2006] No. 3 Arts. 33-35",
     "Inbound above USD 5,000 equivalent: written declaration to Customs. Outbound USD 5,000-10,000 with no or exceeded inbound record: a Permit for Carrying FX Out of the Country from a BANK. Outbound above USD 10,000 to a war-affected, strictly-controlled or financially unstable country: the permit from the SAFE BRANCH",
     "Withdrawal from a bank: up to USD 10,000 equivalent cumulative per day on ID; above that, SAFE branch pre-filing and a 提取外币现钞备案表 valid 30 days and not reusable",
     "not_priced",
     "No wire fee and no spread if the cash already exists",
     "Physically impractical at the amounts in this brief; Order 532 Art. 42 allows a fine of up to 20% of the amount for carrying FX across the border in violation of the rules; on arrival in the United States a currency amount above USD 10,000 must be reported and failure to report is separately penalised under 31 U.S.C. §5321(a)(2)",
     S05, "F31,F33"),
    ("M15", "Remit CNY and convert abroad (cross-border RMB)",
     "Lawful if the underlying transaction is genuine", "A payer with a genuine current-account or approved capital-account obligation denominated in RMB",
     "State Council Order 532 Art. 5; 汇发〔2020〕14号 Art. 54",
     "The same authenticity documentation as the underlying transaction; the receiving bank and any offshore RMB liquidity determine execution",
     BLANK,
     "not_priced",
     "Moves the conversion offshore, so the onshore bid/ask spread is not paid; Art. 5 confirms current-account payments and transfers are not restricted",
     "Requires a counterparty willing to receive CNY and a genuine transaction; the offshore CNY/CNH rate and the receiving bank's charges are NOT published by any official source reviewed here, so the cost is left BLANK and flagged; does not work for exporting your own savings with no counterparty",
     S03, "F05,F13"),
    ("M16", "Domestic transfer between your own accounts, or to a close relative",
     "Lawful within its terms", "Any individual",
     "汇发〔2020〕14号 Art. 67; PBOC Order [2006] No. 3 Arts. 28, 32",
     "Valid ID; the accounts must belong to the same subject category",
     "Transfers are limited to between the person's own accounts and between the person and close relatives, of the SAME subject category",
     "not_priced",
     "Useful for consolidating balances before a single outward wire, which minimises the fixed telecom charge",
     "Does not move money out of China at all; a transfer between a domestic-individual account and an overseas-individual account is managed as a CROSS-BORDER transaction and must satisfy the outward-remittance rules; FX savings accounts cannot be used for business receipts and payments",
     S05, "F08,F11"),
    ("M17", "Quota splitting across several people (分拆)",
     "PROHIBITED", "n/a",
     "汇发〔2020〕14号 Art. 62; PBOC Order [2006] No. 3 Art. 7; State Council Order 532 Arts. 39, 40; 31 U.S.C. §5321(a)(4)",
     "n/a", "n/a", "not_priced",
     BLANK,
     "Expressly forbidden. Art. 62 puts both the borrower and the lender of a quota on a watch list for the year of listing plus two further years. Order 532 Art. 39 and Art. 40 both carry a fine of up to 30% of the amount, rising to 30%-100% where the circumstances are serious. On the U.S. side, 31 U.S.C. §5321(a)(4) permits a structuring penalty of up to the FULL AMOUNT of the currency involved.",
     S03, "F16,F28,F30,F50"),
    ("M18", "Underground bank / informal value transfer (地下钱庄)",
     "PROHIBITED", "n/a", "State Council Order 532 Art. 45; PBOC Order [2006] No. 3 Art. 39",
     "n/a", "n/a", "not_priced", BLANK,
     "Order 532 Art. 45: warning, confiscation of illegal gains and a fine of up to 30% of the illegal amount for privately buying or selling FX, doing so in disguised form, scalping, or illegally brokering in a relatively large amount; 30%-100% where the circumstances are serious; criminal liability where a crime is constituted. In the United States the same flow is a money-laundering exposure and forfeitable.",
     S03, "F29"),
    ("M19", "Buy cryptocurrency with CNY, sell abroad for USD",
     "PROHIBITED in substance", "n/a",
     "State Council Order 532 Arts. 39, 45",
     "n/a", "n/a", "not_priced", BLANK,
     "The exchange of CNY for a token offshore and back into USD is 变相买卖外汇 (buying or selling FX in disguised form) within Art. 45 where it is used to move value across the border, and Art. 39 reaches the unlawful outward transfer of onshore capital by deceptive means: up to 30%, and 30%-100% where serious, plus criminal exposure. No official instrument reviewed here authorises the route.",
     S03, "F28,F29"),
    ("M20", "False invoices or false transaction documents",
     "PROHIBITED", "n/a",
     "State Council Order 532 Art. 40; 汇发〔2020〕14号 Arts. 47, 62, 68; PBOC Order [2006] No. 3 Art. 7",
     "n/a", "n/a", "not_priced", BLANK,
     "Art. 40 treats fraudulently purchasing FX with false or invalid transaction documents as 非法套汇: the funds are ordered converted back and a fine of up to 30% is imposed, 30%-100% where serious, with criminal liability where a crime is constituted. Art. 7 forbids using false commercial documents to evade authenticity management and Art. 68 entitles the bank to refuse.",
     S03, "F16,F17,F30"),
]


# ==========================================================================
# 3. Step playbooks
# ==========================================================================
STEPS = [
    ("M01", 1, "Establish, in writing from the account-opening bank, which subject category your account carries in the personal FX monitoring system — 境内个人 or 境外个人. PBOC Order [2006] No. 3 Art. 28 makes the identity documents you supplied at opening decisive, and the two definitions in the reviewed instruments conflict.", S04),
    ("M01", 2, "Assemble the amount-bearing source-of-funds documents for the RMB you intend to convert: the employment or service contract, the payment records showing the money actually arrived, and the PRC tax certificate. Guidelines Art. 59 requires the tax certificate expressly (含税务凭证).", S05),
    ("M01", 3, "Confirm the amount is lawful CURRENT-ACCOUNT income. Art. 59 reaches 经常项目合法人民币收入 only. If the money is savings, a capital gain or something else, stop — a different route applies (see C6-C8).", S05),
    ("M01", 4, "Ask the bank for a WRITTEN quotation for the FX purchase and the outward wire, and for its intermediary and beneficiary charge options. The published board at S01 is expressly 仅供参考 and BOC disclaims responsibility for results based on it; the tariff note 1 at S02 allows agreements, promotions and local differences to override the published charges. Every cost figure in this edition is a model built on those two published pages, not a quote.", S01),
    ("M01", 5, "Submit the purchase application. Do not split the amount across days, people or accounts: Guidelines Art. 62 forbids evasion by splitting and puts you on a watch list for the year plus two more, and 31 U.S.C. §5321(a)(4) permits a U.S. structuring penalty up to the full amount involved.", S05),
    ("M01", 6, "Remit the purchased FX. As an overseas individual, Guidelines Art. 65(1) requires only your valid identity document for a remittance out of an FX account, and states no amount threshold — so one wire is permitted and the fixed RMB 150 telecom charge is paid once rather than eight times.", S05),
    ("M01", 7, "Keep the bank's refusal or approval record. Art. 68 obliges a bank that refuses a transaction to explain the reason and the appeal channel accurately; that record is your evidence if you need to escalate to the local SAFE branch.", S05),
    ("M01", 8, "Before the calendar year ends, check the U.S. side: if the aggregate value of your foreign financial accounts exceeded USD 10,000 at ANY time in the year, FinCEN Form 114 is due 15 April with an automatic extension to 15 October, filed electronically through the BSA E-Filing System and not with your tax return. Records are kept five years.", S15),
    ("M03", 1, "Confirm the balance is already denominated in USD or another foreign currency inside an FX account. If it is in CNY this route does not apply and you are back to M01 or M02.", S05),
    ("M03", 2, "If you are an overseas individual, present your valid identity document and instruct the outward remittance. Guidelines Art. 65(1) states no amount threshold for FX remitted from within an FX account, and requires nothing beyond the ID.", S05),
    ("M03", 3, "If you are a domestic individual, Guidelines Art. 64(1) applies instead: up to USD 50,000 equivalent cumulative PER DAY on ID alone; above that, ID plus amount-bearing relevant materials, and you must cooperate with the bank's consistency review of the purchase purpose against the remittance purpose.", S05),
    ("M03", 4, "Choose ONE wire rather than several. With no purchase there is no spread, so the only published costs are the 1 permille wire fee (floor RMB 50, ceiling RMB 260) and the RMB 150 telecom charge — both of which are per transaction, so splitting multiplies the fixed element for no benefit.", S02),
    ("M05", 1, "Complete the PRC TAX CLEARANCE FIRST. IIT Law Art. 13 para 4 requires a taxpayer who cancels Chinese household registration because of emigrating abroad to complete the tax clearance BEFORE the cancellation, and Art. 10(5) makes the cancellation itself a filing trigger. This ordering is the trap: step 2 cannot happen before step 1.", S11),
    ("M05", 2, "Cancel the Chinese household registration and obtain the cancellation certificate.", S11),
    ("M05", 3, "Apply to the SAFE branch at your ORIGINAL household-registration location — 汇发〔2014〕2号 §6(1) assigns approval there, not to the branch where the money now sits.", S10),
    ("M05", 4, "Submit the property-right documents. §6(4) abolished the requirement to notarise them, and also abolished notarisation of the agency agreement and the agent's identity proof.", S10),
    ("M05", 5, "Once approved, instruct the bank. §6(2) abolished the installment requirement, so within the approved amount the bank may remit in ONE SUM; the RMB 500,000 head-office filing requirement was also abolished by §6(1). Confirm the approval is still unamended — 汇发〔2023〕28号 Annex 4 changed only §3 of the notice.", S10),
    ("M07", 1, "Sell the onshore property. Under IIT Law Art. 15 para 2 the registration authority must inspect the IIT payment certificate for the transfer before registering it, so the tax is unavoidable and comes first in time.", S11),
    ("M07", 2, "Compute and pay IIT at 20% on the GAIN — Art. 6(5) sets the taxable amount as the proceeds less the original value of the property and reasonable expenses; Art. 3(3) sets the rate for property-transfer income at a proportional 20%.", S11),
    ("M07", 3, "Apply to SAFE for approval of the purchase-and-remit. PBOC Order [2006] No. 3 Art. 22 conditions the conversion and remittance of an overseas individual's onshore property-sale RMB on SAFE approval (经外汇局核准).", S04),
    ("M07", 4, "Obtain the bank's written quotation, then purchase and remit. The published board is reference-only and BOC disclaims results based on it.", S01),
    ("M07", 5, "On the U.S. side, assess whether the PRC IIT paid qualifies for a foreign tax credit, and whether the currency movement produces a §988 gain. §988(e)(1)-(2) excludes gain on a PERSONAL disposition of nonfunctional currency unless the gain exceeds USD 200, and §988(e)(3) removes that protection to the extent allocable expenses meet §162 or §212. Whether your facts are personal is not determinable from the material reviewed.", S12),
    ("M17", 1, "DO NOT DO THIS. This row exists so the option is on the record with its consequences rather than being silently omitted.", S05),
    ("M17", 2, "China: Guidelines Art. 62 forbids evading convenience-amount or authenticity management by splitting. The borrower of a quota is placed on the watch list; the lender receives a risk-warning letter and is placed on the watch list on repetition. The watch period is the year of listing plus the following two consecutive years, during which every settlement or purchase requires ID plus amount-bearing materials and strict bank review.", S05),
    ("M17", 3, "China: Order 532 Art. 39 (unlawful outward transfer of onshore FX or capital) and Art. 40 (illegal FX arbitrage) each carry a fine of up to 30% of the amount, rising to between 30% and 100% of the amount where the circumstances are serious, plus criminal liability where a crime is constituted.", S03),
    ("M17", 4, "United States: 31 U.S.C. §5321(a)(4) permits a civil money penalty for a §5324 structuring violation of up to the full amount of the currency involved in the transaction. §5321(b)(1) gives the Secretary six years from the date of the transaction to assess, §5321(d) confirms a civil penalty may be imposed even where a criminal penalty is imposed for the same violation, and §5321(f) allows an ADDITIONAL penalty for a repeat violator of up to the greater of three times the profit gained or loss avoided, or twice the maximum penalty.", S13),
]


# ==========================================================================
# 4. Tax and penalty decomposition
# ==========================================================================
TAX = [
    ("T01", "CN", "Tax on the ACT of converting your own CNY into USD",
     "None of the nine closed categories of taxable personal income in IIT Law Art. 2 is 'currency conversion'. No instrument reviewed in this session imposes a tax on the act of exchange itself.",
     "This is a statement that the reviewed instruments contain no such tax. It is NOT a ruling that no PRC tax can arise in connection with moving this money: tax depends on how the money was earned, on your residence status under Art. 1, and on whether earlier PRC tax was paid.",
     "PRC IIT Law Arts. 1, 2", S11, "F34,F36", "verified"),
    ("T02", "CN", "IIT on the income that CREATED the money",
     "Comprehensive income (wages, labour remuneration, author's remuneration, royalties): excess-progressive 3%-45%. Business income: excess-progressive 5%-35%. Interest, dividends, bonuses, property leasing, PROPERTY TRANSFER and incidental income: proportional 20%.",
     "The tax that actually bites is the tax on the underlying income, and it is due whether or not the money ever leaves China. The bank's demand for a tax certificate under Guidelines Art. 59 is evidence that this has been settled — it is not a new conversion levy.",
     "PRC IIT Law Art. 3", S11, "F35", "verified"),
    ("T03", "CN", "Tax base on a property sale",
     "Proceeds less the original value of the property and reasonable expenses, taxed at 20%.",
     "Not 20% of the sale price. Art. 6(5) sets the base as the gain.",
     "PRC IIT Law Arts. 3(3), 6(5)", S11, "F35,F38", "verified"),
    ("T04", "CN", "Pre-emigration tax clearance",
     "Mandatory, and it must be completed BEFORE the household registration is cancelled.",
     "Art. 10(5) makes cancelling a Chinese hukou because of emigrating abroad a filing trigger; Art. 13 para 4 requires the tax clearance before the cancellation. Because 汇发〔2014〕2号 §6 routes the emigrant property transfer through the ORIGINAL hukou location, the clearance gates the whole route.",
     "PRC IIT Law Arts. 10(4)-(5), 13 para 4", S11, "F37", "verified"),
    ("T05", "CN", "PRC foreign tax credit for a resident individual",
     "Foreign IIT already paid may be credited against the PRC tax due on that foreign income, capped at the PRC tax computed on the same income under the IIT Law.",
     "Applies to a PRC RESIDENT individual's foreign-source income — the mirror image of the U.S. credit, and relevant only if you also have foreign income reportable in China.",
     "PRC IIT Law Art. 7", S11, "F39", "verified"),
    ("T06", "CN", "Currency used for PRC tax computation",
     "Income in a currency other than RMB is converted at the RMB exchange-rate MIDPOINT.",
     "Note the contrast with the cost model: the tax authority uses the midpoint, while a customer purchasing USD pays the bank's ask. The two are different rates for different purposes and must not be mixed.",
     "PRC IIT Law Art. 16", S11, "F40", "verified"),
    ("T07", "US", "Federal income tax on the currency movement itself",
     "§988(e)(1): the rest of §988 does not apply to a section 988 transaction entered into by an individual which is a PERSONAL transaction. §988(e)(2): on a personal disposition of nonfunctional currency, no gain is recognised by reason of post-acquisition exchange-rate changes — but that sentence does NOT apply if the gain that would otherwise be recognised EXCEEDS USD 200.",
     "Three things must be true for the exclusion to hold, and none is determinable from the material reviewed: the disposition must be of NONFUNCTIONAL currency (§988(c)(1)(C)(ii) expressly includes bank deposits, so a CNY deposit qualifies for a USD-functional taxpayer); the transaction must be PERSONAL; and the gain must not exceed USD 200. §988(e)(3) withdraws 'personal' status to the extent allocable expenses meet §162 (other than §162(a)(2) travel) or §212 (other than the tax-related part).",
     "26 U.S.C. §988(c)(1)(C), §988(e)", S12, "F42,F43", "verified"),
    ("T08", "US", "Character and source of any §988 gain that IS taxable",
     "Ordinary income or loss, computed separately. For an individual the source follows the country of the tax home under §911(d)(3); with no tax home, a U.S. citizen is resident in the United States.",
     "If the exclusion does not hold, the gain is ordinary, not capital, and is U.S.-source for a U.S.-tax-home citizen — which matters because a foreign tax credit is generally not available against U.S.-source income.",
     "26 U.S.C. §988(a)(1)(A), (a)(3)(B)(i)", S12, "F41,F44", "verified"),
    ("T09", "US", "TY2026 foreign earned income exclusion",
     "USD 132,900 for tax year 2026, up from USD 130,000 for 2025.",
     "An exclusion for qualifying FOREIGN EARNED INCOME. It is not a mechanism for repatriating an existing bank balance and it does not apply to investment income, gains, or the conversion itself.",
     "IR-2025-103 / Rev. Proc. 2025-32", S16, "F52", "verified"),
    ("T10", "US", "CY2026 annual gift exclusion",
     "USD 19,000 per donee for calendar year 2026, unchanged from 2025. The exclusion for gifts to a spouse who is NOT a U.S. citizen rises to USD 194,000 for calendar year 2026, from USD 190,000.",
     "Relevant only if part of the balance is being given rather than moved. The non-citizen-spouse figure is the one most often missed and it is materially larger.",
     "IR-2025-103 / Rev. Proc. 2025-32", S16, "F52", "verified"),
    ("T11", "US", "FBAR filing obligation",
     "A U.S. person must file FinCEN Form 114 where the AGGREGATE value of foreign financial accounts EXCEEDED USD 10,000 at ANY TIME during the calendar year. Due 15 April with an automatic extension to 15 October; filed electronically via the BSA E-Filing System, not with the return; records kept five years.",
     "The test is aggregate across all accounts and is 'exceeded', not 'reached'. A single Chinese account holding USD 10,001 at any point in the year triggers it. This obligation exists independently of whether any money moves.",
     "IRS FBAR guidance", S15, "F45,F46", "verified"),
    ("T12", "US", "FBAR penalty — non-willful",
     "Statutory maximum USD 10,000; inflation-adjusted maximum USD 16,536 for penalties assessed on or after 17 January 2025. A REASONABLE CAUSE EXCEPTION applies: no penalty where the violation was due to reasonable cause AND the amount or balance was properly reported.",
     "The reasonable-cause exception is statutory, at §5321(a)(5)(B)(ii). It is unavailable for a willful violation.",
     "31 U.S.C. §5321(a)(5)(B); 31 CFR 1010.821 Table 1", S13, "F47,F48", "verified"),
    ("T13", "US", "FBAR penalty — willful",
     "The GREATER OF USD 100,000 statutory (inflation-adjusted to USD 165,353) OR 50 PERCENT OF the amount determined under §5321(a)(5)(D) — for a failure to report the existence of an account, THE BALANCE IN THE ACCOUNT AT THE TIME OF THE VIOLATION. The reasonable-cause exception does not apply.",
     "On a USD 400,000 balance, 50% is USD 200,000, which exceeds the USD 165,353 adjusted fixed maximum, so the 50% limb governs. This is the single largest number in the whole analysis and it is a REPORTING penalty, not a tax and not an exchange cost.",
     "31 U.S.C. §5321(a)(5)(C),(D); 31 CFR 1010.821 Table 1", S13, "F47,F48", "verified"),
    ("T14", "US", "FBAR penalty — the adjusted maxima are not a total cap",
     "31 CFR 1010.821(b): the adjusted maximum amounts do NOT limit the total penalty where a penalty may be imposed for each day a violation continues.",
     "Multiple years and continuing violations stack. The figures in T12 and T13 are per-violation maxima, not a ceiling on total exposure.",
     "31 CFR 1010.821(b)", S14, "F49", "verified"),
    ("T15", "US", "Structuring penalty",
     "For a violation of 31 U.S.C. §5324, a civil money penalty of up to the FULL AMOUNT of the currency involved in the transaction.",
     "The U.S. counterpart to the PRC anti-splitting rule, and it is harsher in form: up to 100% of the amount structured, not a percentage band.",
     "31 U.S.C. §5321(a)(4)", S13, "F50", "verified"),
    ("T16", "US", "Assessment window, cumulation and repeat-violator uplift",
     "Six years from the date of the transaction to assess (§5321(b)(1)). A civil penalty may be imposed even where a criminal penalty is imposed for the same violation (§5321(d)). For a repeat violator, an ADDITIONAL civil penalty of up to the greater of three times the profit gained or loss avoided, or twice the maximum penalty (§5321(f)).",
     "The §5321(f) uplift counts only previous violations occurring after the enactment date of the Anti-Money Laundering Act of 2020 (1 January 2021).",
     "31 U.S.C. §5321(b)(1),(d),(f)", S13, "F51", "verified"),
    ("T17", "CN", "PRC penalty — unlawful outward transfer (逃汇)",
     "Order to repatriate within a time limit, plus a fine of UP TO 30% of the amount evaded; where the circumstances are serious, BETWEEN 30% AND THE EQUIVALENT AMOUNT (i.e. up to 100%); criminal liability where a crime is constituted.",
     "30% is a CEILING for an ordinary case, not a floor. The 30%-100% band applies only 情节严重 (where the circumstances are serious).",
     "State Council Order 532 Art. 39", S03, "F28", "verified"),
    ("T18", "CN", "PRC penalty — private or disguised FX dealing (地下钱庄)",
     "Warning, confiscation of illegal gains, plus a fine of UP TO 30% of the illegal amount; where serious, BETWEEN 30% AND THE EQUIVALENT AMOUNT; criminal liability where a crime is constituted.",
     "Reaches 私自买卖外汇, 变相买卖外汇 (disguised dealing, which is how informal value transfer and token-based moves are characterised), 倒买倒卖 and illegal brokering in a relatively large amount.",
     "State Council Order 532 Art. 45", S03, "F29", "verified"),
    ("T19", "CN", "PRC penalty — illegal FX arbitrage with false documents (非法套汇)",
     "Order to convert the illegally arbitrated funds back, plus a fine of UP TO 30% of that amount; where serious, BETWEEN 30% AND THE EQUIVALENT AMOUNT; criminal liability where a crime is constituted.",
     "This is the article that reaches a purchase made on fabricated invoices or false transaction documents.",
     "State Council Order 532 Art. 40", S03, "F30", "verified"),
    ("T20", "CN", "PRC penalty — carrying FX across the border unlawfully",
     "Warning, plus a fine of UP TO 20% of the illegal amount. Where laws or administrative regulations provide for Customs to impose the penalty, those provisions prevail.",
     "A lower band than Arts. 39/40/45, but still material, and Customs may be the enforcing authority.",
     "State Council Order 532 Art. 42", S03, "F31", "verified"),
    ("T21", "CN", "PRC penalty — documentary and registration failures by an individual",
     "Order to correct plus a warning, and a fine of UP TO RMB 50,000 for an individual (up to RMB 300,000 for an institution).",
     "Covers failure to make the balance-of-payments declaration, failure to submit valid documents or submitting untrue documents, FX account and FX registration violations, and obstructing a SAFE inspection.",
     "State Council Order 532 Art. 48", S03, "F32", "verified"),
    ("T22", "CN", "Bank spread — the real recurring cost of conversion",
     "BLANK as a percentage of any given transaction. The published board gives an ask of 6.6851 and a bid of 6.6571 per USD at the 2026-11-10 17:39:58 reading, from which a model half-spread can be computed; the EXECUTABLE spread is not published.",
     "BOC's own declaration on the board page states the table is for reference only, that the executable rate is the one shown in its online banking, mobile banking, smart counter or branch counter, and that BOC accepts no responsibility for results from using the table. Tariff note 1 likewise allows agreements, promotions and local differences to override the published charges. A written bank quotation is the only way to close this cell.",
     "BOC board declaration; BOC tariff note 1", S01, "F02,F04", "unverified"),
    ("T23", "CN", "Intermediary (correspondent) and U.S. beneficiary bank charges",
     BLANK,
     "No official source reviewed in this session publishes intermediary or receiving-bank charges for a personal CNY-to-USD wire. They are set commercially by the correspondent chain and by the receiving institution and depend on the charge option (OUR/SHA/BEN) selected. Left blank rather than estimated.",
     BLANK, BLANK, BLANK, "unverified"),
    ("T24", "CN", "Offshore CNY/CNH basis",
     BLANK,
     "No official source reviewed publishes a current onshore-offshore RMB basis. It is a market observable and must be taken from a live market source at the time of execution. Left blank rather than estimated.",
     BLANK, BLANK, BLANK, "unverified"),
    ("T25", "US", "Form 8938 threshold and whether it applies to this account",
     BLANK,
     "Not independently fetched by this session. The repository's earlier layers record the comparison of Form 8938 and FBAR requirements; this edition does not restate figures it did not read on 2026-11-10. Left blank and flagged.",
     BLANK, BLANK, BLANK, "unverified"),
    ("T26", "US", "U.S.-China income tax treaty relief",
     BLANK,
     "The treaty text was not fetched by this session, so no article, rate or relief is asserted here. Left blank and flagged rather than summarised from memory.",
     BLANK, BLANK, BLANK, "unverified"),
    ("T27", "US", "State-level income tax on any §988 gain",
     BLANK,
     "Depends on the taxpayer's state of residence, which was not supplied. No state source was fetched. Left blank and flagged.",
     BLANK, BLANK, BLANK, "unverified"),
]


# ==========================================================================
# 5. Reconciliation of the four conflicting published headline figures
# ==========================================================================
def reconciliation():
    """Reproduce every published headline number from first principles.

    The five 'legacy' rows re-derive figures that OTHER sessions published, using
    the board reading those sessions recorded, and must match to the cent. The
    'm5f19' rows are this session's own figures, published on m5f19-costs.html;
    scripts/verify_m5f19_site.py re-derives them from the board snapshot and
    asserts parity with both this table and the generated HTML.
    """
    rows = []

    def add(model, session, board_ask, board_bid, wires, denom, amount,
            published, where):
        got = eng.leg_cost(eng.Decimal(amount), wires,
                           eng.Decimal(board_ask), eng.Decimal(board_bid),
                           denom)["total_usd"]
        delta = eng.money(got - eng.Decimal(published))
        rows.append({
            "model": model, "session": session,
            "board_ask": board_ask, "board_bid": board_bid,
            "wires": wires, "spread_denominator": denom,
            "amount_usd": amount,
            "published_usd": published,
            "reproduced_usd": str(got),
            "delta_usd": str(delta),
            "reproduced_exactly": "yes" if delta == 0 else "NO",
            "appears_in": where,
        })

    # ---- The historical published models, on the board reading they used ----
    add("1 wire, spread / ask", "fbbd3b22 (merged PR #24 / #27)",
        "6.6903", "6.6622", 1, "ask", 10000, "53.42",
        "index.html hero and short-answer list; verify-2026.html")
    add("1 wire, spread / ask", "fbbd3b22 (merged PR #24 / #27)",
        "6.6903", "6.6622", 1, "ask", 400000, "901.30",
        "index.html hero and short-answer list; verify-2026.html")
    add("1 wire, spread / mid", "d6467425 (merged PR #26)",
        "6.6903", "6.6622", 1, "mid", 10000, "53.47",
        "d646-summary.html; d646-costs.html")
    add("8 wires, spread / mid", "d6467425 (merged PR #26)",
        "6.6903", "6.6622", 8, "mid", 400000, "1332.05",
        "d646-summary.html; d646-costs.html")
    add("1 wire, spread / ask", "775c9619 (merged PR #33)",
        "6.6903", "6.6622", 1, "ask", 10000, "53.42",
        "s775-cost-10k-400k.html; s775-dashboard.html")

    # ---- This session, on the later 2026-11-10 board reading ----
    ask, bid = str(eng.ASK), str(eng.BID)

    def own(wires, denom, amount, where):
        got = eng.leg_cost(eng.Decimal(amount), wires, eng.ASK, eng.BID,
                           denom)["total_usd"]
        add(f"{wires} wire{'s' if wires > 1 else ''}, spread / {denom}",
            "5f1925df (this session)", ask, bid, wires, denom, amount,
            str(got), where)

    own(1, "ask", 10000, "m5f19-dashboard.html; m5f19-costs.html (primary)")
    own(1, "ask", 400000, "m5f19-dashboard.html; m5f19-costs.html (primary)")
    own(1, "mid", 10000, "m5f19-costs.html (sensitivity column)")
    own(1, "mid", 400000, "m5f19-costs.html (sensitivity column)")
    own(8, "ask", 400000, "m5f19-costs.html (conditional staging scenario)")
    return rows



# ==========================================================================
# 6. Flags
# ==========================================================================
FLAGS = [
    ("G01", "irregularity",
     "The repository applies a DOMESTIC-INDIVIDUAL rule to a U.S. citizen. Multiple merged pages state that a personal wire needs no approval 'up to USD 50,000/day on ID' and cite SAFE Tianjin 2024-02-29. That page's own question is 境内个人外汇汇出境外用于经常项目支出 — a DOMESTIC individual remitting FX abroad — and its answer quotes Guidelines Art. 64. The instrument governing a passport-holder is Art. 65(1), which this session fetched and which states NO amount threshold for FX remitted from an FX account, and Art. 59 for the purchase leg. Sessions a502 (merged PR #36) and a058 (open) flagged the same defect; it is still unfixed on main at 9bc2cde.",
     "Correct the source data AND the generator, not only the HTML: replace the Art. 64 citation with Art. 59 + Art. 65(1) for an overseas individual, and delete 'ID only up to USD 50,000/day' as a general statement.",
     "s775-dashboard.html; s775-cost-10k-400k.html; research/s775-executive-summary.md; index.html",
     S05, "F10,F11,F12", "needs review"),
    ("G02", "irregularity",
     "Guidelines Art. 65 — the article that actually governs an overseas individual remitting FX out of an FX account — appears NOWHERE in the repository. A grep across all .md, .html and .csv files for '第六十五条', 'Article 65' and 'art. 65' returns zero matches, while Art. 64 is cited repeatedly. Art. 65(1) requires only a valid identity document and states no amount threshold. This omission is the direct cause of the '8 wires / 8 years' framing used by session d6467425.",
     "Add Art. 65 to the rules tables and re-price the multi-wire scenario as conditional rather than as a requirement.",
     "data/china_rules.csv; deep-china-rules.html; d646-costs.html; d646-summary.html",
     S05, "F11", "needs review"),
    ("G03", "irregularity",
     "The '8 wires over 8 years' scenario has no basis in the text of Art. 64 or Art. 65. Art. 64(1) sets a USD 50,000 PER DAY identity-document threshold for a domestic individual — above it, documents are required, not a prohibition and not a multi-year wait. Art. 65(1) sets no threshold at all for an overseas individual. SAFE Ningxia 2022 states in terms that there is no amount limit on genuine, lawful current-account purchase and settlement. The scenario is still legitimate AS A SCENARIO if a bank or SAFE branch requires staging, but it must not be presented as what the regulation requires.",
     "Relabel the 8-wire figure as a conditional staging scenario, not as a regulatory requirement, and show the single-wire figure as the text-supported case.",
     "d646-costs.html; d646-summary.html; index.html",
     S09, "F11,F12,F14", "needs review"),
    ("G04", "irregularity",
     "Two different spread denominators are in circulation and produce different dollars from the same board. fbbd3b22 divides the half-spread by the ASK; d6467425 divides it by the MID. This session reproduces both to the cent — $53.42 and $901.30 (ask) versus $53.47 and $1,332.05 (mid, 1 and 8 wires) — which confirms the discrepancy is purely a convention plus a wire count, not a data error. The repository logged the convention difference as C3 but never demonstrated it arithmetically.",
     "Publish both conventions side by side with the arithmetic shown, as m5f19-reconciliation.html does, instead of asserting one headline number.",
     "index.html; d646-costs.html; costs.html; cross-session-review.html",
     S01, "", "needs review"),
    ("G05", "irregularity",
     "'No separate China exit tax was identified' is true as far as it goes but understates a real gate. IIT Law Art. 13 para 4 requires a taxpayer who cancels a Chinese hukou because of emigrating abroad to complete a TAX CLEARANCE BEFORE the cancellation, and Art. 10(5) makes the cancellation a filing trigger. Because 汇发〔2014〕2号 §6 routes the emigrant property transfer through the ORIGINAL hukou location, that clearance gates the entire emigrant route. The repository does record the sequencing in data/taxes.json and docs/playbook.html, but the headline on index.html does not carry it.",
     "Carry the clearance-before-cancellation gate into any headline treatment of the emigrant route, not only into the playbook subpage.",
     "index.html; EXECUTIVE_SUMMARY.md",
     S11, "F23,F37", "needs review"),
    ("G06", "irregularity",
     "The universal claim 'there is no PRC tax on converting your own CNY to USD' outruns its sources. What IIT Law Art. 2 actually establishes is that currency conversion is not one of the nine CLOSED CATEGORIES of taxable personal income. That is not the same as a universal exemption: tax depends on how the money was earned, on residence status under Art. 1, and on whether earlier PRC tax was paid and evidenced. Sessions a502 and a058 both flagged this; it remains on merged pages.",
     "Restate as: no instrument reviewed taxes the act of exchange; the nine categories in Art. 2 are closed and do not include it; tax on the underlying income is a separate question that must be settled on the facts.",
     "s775-dashboard.html; index.html; research/s775-executive-summary.md",
     S11, "F34,F36", "needs review"),
    ("G07", "limitation",
     "No cost figure in this repository, including every figure this session publishes, is a quotation. BOC's own declaration on the board page states the table is 仅供参考 (for reference only), that the executable rate is the one shown in BOC online banking, mobile banking, the smart counter or the branch counter, and that BOC accepts no responsibility for results arising from use of the table. Tariff note 1 permits agreements, promotions and local charging differences to override the published charges. The board also moves intraday: this session read ask 6.6851 at 17:39:58 where earlier sessions read 6.6903 at 07:32:39 on the same date.",
     "Treat every dollar figure as a model. Obtain a written bank quotation before acting, and re-read the board at execution time.",
     "all cost pages in the repository",
     S01, "F02,F04", "needs review"),
    ("G08", "limitation",
     "The classification of the user is UNKNOWABLE from the brief, and it changes the answer. Order 532 Art. 52(2) counts a foreigner continuously resident in China for a full year as a DOMESTIC individual; PBOC Order [2006] No. 3 Art. 37(2) counts any passport-holding foreign citizen as an OVERSEAS individual. PBOC Art. 28 makes the bank's record at account opening operative. The brief supplies no account documents, no residence history, no source-of-funds history, no amount and no tax filings.",
     "Ask the account-opening bank which category the account carries before choosing a route. Every conclusion in this edition is conditional on that answer.",
     "all pages",
     S04, "F06,F07,F08", "needs review"),
    ("G09", "limitation",
     "Intermediary (correspondent) charges and U.S. beneficiary-bank charges are BLANK in this edition. No official source fetched on 2026-11-10 publishes them for a personal CNY-to-USD wire; they are set commercially and depend on the OUR/SHA/BEN charge option. The repository's earlier layers variously include and exclude a USD 15/25 OUR charge taken from BOC's TRADE-FINANCE tariff rather than its personal tariff, which session 15d351fb correctly flagged.",
     "Leave blank until a bank quote is obtained. Do not import a corporate or trade-finance tariff into a personal cost model.",
     "cost-tables.html; d646-costs.html; s775-cost-10k-400k.html",
     S02, "F04", "needs review"),
    ("G10", "limitation",
     "Three items in the tax table are BLANK because this session did not fetch them: the Form 8938 threshold, U.S.-China income tax treaty relief, and state-level tax on a §988 gain. Earlier repository layers carry figures for the first two, but this edition will not restate a value it did not read today. State tax is unanswerable without the state of residence.",
     "Fetch and verify before use. Do not treat the blank cells as zero.",
     "m5f19-tax.html",
     BLANK, "", "unverified"),
    ("G11", "process",
     "Six sibling branches committed within five minutes of this session starting, and THREE of them (05552f6e, 2c8d441e, ea347561) independently claimed the SAME shared files: index.html, scripts/build_dashboard.py and README.md. Under the board rule that shared outputs are changed only by a final integration session, and the rule never to start a task another session has claimed, this session declined all shared files and filed request M5F19-REQ-01 instead. The duplication itself is the irregularity: claims live on unmerged branches, so sessions cannot see each other until they merge.",
     "A claim register that is visible before merge — or a single standing integrator — would prevent it. Logged here rather than resolved unilaterally.",
     "COORDINATION.md",
     BLANK, "", "needs review"),
    ("G12", "observation",
     "31 CFR 1010.821 was read on 2026-11-10 and independently corroborates the repository's IR-008. The page states it is up to date as of 11/06/2026, its amendment history ends at 90 FR 5630 (Jan. 17, 2025), and the Table 1 column is headed 'penalties assessed on or after January 17, 2025'. So USD 16,536 and USD 165,353 remain the operative adjusted maxima, with no 2026 uplift applied. This confirms IR-008 from the regulation itself rather than only from the OMB notice.",
     "No change required. Recorded because it upgrades IR-008 from 'needs review' to independently corroborated.",
     "data/flags.csv IR-008; deep-china-rules.html",
     S14, "F48", "verified"),
    ("G13", "observation",
     "31 CFR 1010.821(b) states that the adjusted maxima do NOT limit the total penalty where a penalty may be imposed for each day a violation continues. Combined with §5321(b)(1)'s six-year assessment window, §5321(d)'s confirmation that civil and criminal penalties are not exclusive, and §5321(f)'s repeat-violator uplift of up to three times the profit gained or twice the maximum penalty, the 'USD 200,000 on a USD 400,000 account' figure on the repository's landing page is a PER-VIOLATION maximum, not a ceiling on total exposure.",
     "Present the willful figure as per-violation and note the stacking provisions alongside it.",
     "index.html; penalties.html; d646-penalty.html",
     S13, "F49,F51", "needs review"),
]


def write(name, fieldnames, rows):
    """Write tuples positionally, dicts by field name.

    csv.writer.writerow(dict) writes the KEYS, which silently produces a file
    whose every data row repeats the header. Guard against that explicitly.
    """
    path = os.path.join(DATA, name)
    rows = list(rows)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if rows and isinstance(rows[0], dict):
            missing = [f for f in fieldnames if f not in rows[0]]
            extra = [k for k in rows[0] if k not in fieldnames]
            assert not missing, f"{name}: fieldnames missing {missing}"
            assert not extra, f"{name}: rows carry undeclared keys {extra}"
            w = csv.DictWriter(fh, fieldnames=fieldnames,
                               quoting=csv.QUOTE_MINIMAL)
            w.writeheader()
            w.writerows(rows)
        else:
            for r in rows:
                assert not isinstance(r, dict), f"{name}: mixed row types"
                assert len(r) == len(fieldnames), (
                    f"{name}: row has {len(r)} cells, header has "
                    f"{len(fieldnames)}")
            w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
            w.writerow(fieldnames)
            w.writerows(rows)
    print(f"  wrote {name}: {len(rows)} rows")


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    eng.self_checks()
    print("generating m5f19 tables (engine self-checks passed)")

    write("m5f19_classification.csv",
          ["id", "order", "question", "if_yes", "if_no", "governing_text",
           "source_url", "fact_ids"], CLASSIFICATION)
    write("m5f19_methods.csv",
          ["id", "name", "legal_status", "who", "governing_instrument",
           "documents_required", "amount_ceiling_stated_in_text", "cost_model",
           "pros", "cons", "source_url", "fact_ids"], METHODS)
    write("m5f19_steps.csv",
          ["method_id", "step_no", "instruction", "source_url"], STEPS)
    write("m5f19_tax.csv",
          ["id", "jurisdiction", "item", "verified_rule_or_value",
           "what_it_means", "instrument", "source_url", "fact_ids", "status"],
          TAX)

    rec = reconciliation()
    # Hard gate: every figure ANOTHER session published must re-derive exactly.
    legacy = [r for r in rec if "this session" not in r["session"]]
    failed = [r for r in legacy if r["reproduced_exactly"] != "yes"]
    assert legacy, "no legacy rows to reconcile"
    assert not failed, f"could not reproduce published figures: {failed}"
    print(f"  reconciliation gate: {len(legacy)}/{len(legacy)} published "
          f"figures re-derived to the cent")
    write("m5f19_reconciliation.csv",
          ["model", "session", "board_ask", "board_bid", "wires",
           "spread_denominator", "amount_usd", "published_usd",
           "reproduced_usd", "delta_usd", "reproduced_exactly", "appears_in"],
          rec)
    write("m5f19_flags.csv",
          ["id", "kind", "finding", "recommended_action", "files_affected",
           "source_url", "fact_ids", "status"], FLAGS)

    # board snapshot, so the ladder is reproducible against a recorded reading
    write("m5f19_board.csv",
          ["field", "value", "unit", "source_url", "fetched"],
          [
              ("board_date", eng.BOARD_DATE, "date", S01, eng.FETCHED),
              ("board_time", eng.BOARD_TIME, "time", S01, eng.FETCHED),
              ("usd_bid_per_100", str(eng.BID_PER_100), "CNY per 100 USD", S01, eng.FETCHED),
              ("usd_ask_per_100", str(eng.ASK_PER_100), "CNY per 100 USD", S01, eng.FETCHED),
              ("boc_conversion_per_100", str(eng.BOC_CONV_PER_100), "CNY per 100 USD", S01, eng.FETCHED),
              ("usd_bid", str(eng.BID), "CNY per USD", S01, eng.FETCHED),
              ("usd_ask", str(eng.ASK), "CNY per USD", S01, eng.FETCHED),
              ("midpoint", str(eng.MID), "CNY per USD", "derived (ask+bid)/2", eng.FETCHED),
              ("wire_fee_rate", str(eng.FEE_RATE), "fraction of remittance amount", S02, eng.FETCHED),
              ("wire_fee_min", str(eng.FEE_MIN_CNY), "CNY per transaction", S02, eng.FETCHED),
              ("wire_fee_max", str(eng.FEE_MAX_CNY), "CNY per transaction", S02, eng.FETCHED),
              ("telecom_non_hmt", str(eng.TELECOM_CNY_NON_HMT), "CNY per transaction", S02, eng.FETCHED),
              ("telecom_hmt", str(eng.TELECOM_CNY_HMT), "CNY per transaction", S02, eng.FETCHED),
          ])
    print("done")
