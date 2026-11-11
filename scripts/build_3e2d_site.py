#!/usr/bin/env python3
"""Build the 3E2D verified decision dashboard (session arena/3e2dbf57-china3).

    python3 scripts/build_3e2d_site.py            write data CSVs + HTML pages
    python3 scripts/build_3e2d_site.py --check    regenerate (verifier checks parity)
"""
import argparse, csv, html, sys
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
spec = importlib.util.spec_from_file_location("e3e2d", Path(__file__).resolve().parent / "3e2d_engine.py")
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
RATE, AMOUNTS, METHODS, q, row, fx_gain, grid = eng.RATE, eng.AMOUNTS, eng.METHODS, eng.q, eng.row, eng.fx_gain, eng.grid

ROOT = Path(__file__).resolve().parent.parent
esc = html.escape

SOURCES = [
 ("T01","Bank of China","BOC Exchange Rate board (USD row)","https://www.boc.cn/sourcedb/whpj/enindex_1619.html","2026-11-11","direct","USD per 100: Buying 665.91, Cash Buying 665.91, Selling 668.71, Cash Selling 668.71, Middle 671.91; Pub Time 2026/11/11 20:50:05."),
 ("T02","Bank of China","Personal e-banking transfer tariff","https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html","2026-11-11","direct","Cross-border wire (telegraphic): 1 per mille of amount, min CNY 50, max CNY 260 per transfer; plus cable fee CNY 80 (HK/MO/TW) / CNY 150 (other regions). Standard since 2014-11-01. Note: agreements/discounts/local differences may apply."),
 ("T03","Bank of China","ATM fee announcement (from 2026-11-11)","https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html","2026-11-11","direct","Overseas ATM: UnionPay CNY 12 + 1% of withdrawal, max CNY 112 per withdrawal; Mastercard/VISA 2.5%, min USD 3, max USD 40."),
 ("T04","SAFE Tianjin","Personal FX (08), 2026-07-13 - Art. 59","https://www.safe.gov.cn/tianjin/2026/0713/3088.html","2026-11-11","direct","Art. 59: a foreign individual (jingwai geren) with lawful RMB current-account income in China buys FX at a bank with valid ID + source-of-funds materials including tax vouchers."),
 ("T05","SAFE Tianjin","Current-account Q&A (09), 2024-06-21","https://www.safe.gov.cn/tianjin/2024/0621/2529.html","2026-11-11","direct","Same Art. 59, plus: only a foreign individual holding a Foreign Permanent Resident ID gets the annual purchase convenience amount."),
 ("T06","SAFE Ningxia","FX policy Q&A (08), 2022-09-29","https://www.safe.gov.cn/ningxia/2022/0929/1997.html","2026-11-11","direct","Personal settlement and domestic-individual purchase use an annual convenience amount of USD 50,000 per person per year. It is not a cap: above USD 50,000 ID alone is insufficient; source/use materials are needed."),
 ("T07","SAFE Tianjin","Personal FX (03), 2024-02-29 - Art. 64","https://www.safe.gov.cn/tianjin/2024/0229/2402.html","2026-11-11","direct","Art. 64 (domestic individuals): FX-account FX remitted abroad up to USD 50,000/day with ID; above that, ID + transaction materials. FX banknotes remitted up to USD 10,000/day with ID; above that, ID + customs-stamped declaration or original withdrawal slip + materials."),
 ("T08","SAFE","Current Account Guidelines (2020), Arts. 54-67","http://m.safe.gov.cn/safe/file/file/20200831/f0127756271c43ef9b3908d5d157bd91.pdf","2026-11-11","excerpt","Art. 65: foreign individual's FX-account FX remitted abroad with ID; FX banknotes up to USD 10,000/day with ID. Art. 67: transfers between domestic and foreign individuals' FX accounts count as cross-border. (PDF text via excerpt; see Flagged F11.)"),
 ("T09","SAFE Tianjin","Personal FX (10), 2026-09-17 - Art. 60","https://www.safe.gov.cn/tianjin/2026/0917/3134.html","2026-11-11","direct","Art. 60: unused RMB from own FX exchange reconverted with ID + original exchange slip; slip valid 24 months. Up to USD 500/day (USD 1,000 pre-departure) with ID alone."),
 ("T10","SAFE Tianjin","Personal FX (08), 2025-06-13 - Art. 62","https://www.safe.gov.cn/tianjin/2025/0613/2811.html","2026-11-11","excerpt","Art. 62: borrowing another person's convenience amount or otherwise evading the amount/authenticity rules puts the person on a watchlist for that year + 2 years. (Not opened in full in this session; see F11.)"),
 ("T11","SAFE Tianjin","Service-trade FX Q&A (04), 2021-11-02","https://www.safe.gov.cn/tianjin/2021/1102/1777.html","2026-11-11","excerpt","Foreign individual remitting RMB income from service trade, income and current transfers buys FX with ID + transaction proof including tax vouchers (tax filing form, tax payment or exemption certificate). (Not opened in full; see F11.)"),
 ("T12","People's Bank of China","Order [2004] No. 16 - personal property transfer","http://m.safe.gov.cn/safe/2004/1116/5461.html","2026-11-11","direct","Emigrant transfer = person moving from mainland to live abroad who liquidates pre-move lawful property and buys/remits FX. Inheritance transfer = foreign/HK/MO resident liquidating inherited mainland estate. Docs include tax certificate/payment voucher. Bank remits directly to applicant's own account abroad; no FX cash withdrawal. False documents punished under Regulation Art. 40."),
 ("T13","SAFE","Capital account notice (as amended), 2024-09-03","https://www.safe.gov.cn/tianjin/2024/0903/2594.html","2026-11-11","direct","Sec. 6: emigrant approval by former-hukou SAFE office; inheritance by decedent's last-hukou office; RMB 500,000 HQ-report rule and staged-remittance rule removed (bank may remit once or in instalments within approval); notarisation of property/agent documents removed. Sec. 5: profit remittance above USD 50,000 needs profit-distribution resolution + tax filing form."),
 ("T14","SAFE Tianjin","Property-transfer Q&A (07), 2026-03-19","https://www.safe.gov.cn/tianjin/2026/0319/3018.html","2026-11-11","excerpt","Capital Account Guidelines 2024, 6.4: emigrant transfer approved by former-hukou SAFE office; inheritance by decedent's last-hukou office. (Not opened in full; see F11.)"),
 ("T15","SAFE Anhui","Cross-border financing guide, Sec. 8, 2025-09-25","https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf","2026-11-11","excerpt","Sec. 8: foreign individual selling mainland commodity housing remits proceeds with passport, registered sale contract/title docs, tax voucher; amount may not exceed price less taxes/fees in the sale. (Contents read; Sec. 8 text via excerpt; see F11.)"),
 ("T16","State Taxation Administration / SAFE","Announcement 2013 No. 40 (as amended)","https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html","2026-11-11","excerpt","Single outbound payment of USD 50,000+ (exclusive) in listed categories (incl. foreign individual's China work pay, dividends, real-property transfer income) needs tax filing with the tax office. (Not opened in full; see F11.)"),
 ("T17","State Council","FX Administration Regulation (Order 532)","https://www.safe.gov.cn/safe/2008/0806/5321.html","2026-11-11","direct","Art. 5: current-account payments/transfers not restricted. Art. 12: genuine lawful basis. Art. 39 (flight of FX): fine up to 30%; serious 30%-100%; criminal liability. Art. 40 (false docs to buy FX): same scale. Art. 42 (carrying FX in breach): warning, fine up to 20%. Art. 45 (private FX dealing): warning, confiscation, fine up to 30%; serious 30%-100%. Art. 48: untrue docs, individuals up to CNY 50,000. Art. 52(2): domestic individual = Chinese citizen or foreigner resident in China 1 continuous year."),
 ("T18","People's Bank of China","Individual FX Measures (Order [2006] No. 3)","http://m.safe.gov.cn/safe/2006/1225/5319.html","2026-11-11","excerpt","Art. 13: foreign individual with lawful RMB current-account income buys FX/remits with ID + proof. Art. 14: unused inbound FX returned the same way with ID. Art. 28: bank sets account-holder category from ID at account opening. (Not opened in full; see F11.)"),
 ("T19","SAFE","Card overseas cash withdrawal notice (2017 No. 29)","https://www.safe.gov.cn/hubei/2019/0305/851.html","2026-11-11","direct","Per person (all own cards incl. supplementary): overseas cash withdrawals capped at CNY 100,000/year; over the cap, suspended that year and next. Per card per day: CNY 10,000. Borrowing/lending cards to evade is prohibited."),
 ("T20","SAFE Hebei","Cash-carry Q&A, 2019-05-21","http://www.safe.gov.cn/hebei/2019/0521/1366.html","2026-11-11","direct","FX banknotes carried out: up to USD 5,000 customs direct release; USD 5,000-10,000 bank-issued carry permit; above USD 10,000 SAFE permit in principle not granted except special cases."),
 ("T21","SAFE Guangdong","Online FX exchange reminder, 2020-03-04","https://www.safe.gov.cn/guangdong/2020/0304/1668.html","2026-11-11","excerpt","Personal settlement/purchase must go through qualified designated banks, licensed bureaus or agency outlets; private swaps, app swaps, money changers and underground banks are unlawful. No splitting to evade limits; no false documents. (Not opened in full; see F11.)"),
 ("T22","SAFE Hebei","Splitting case (Zhu), 2017-04-14","https://www.safe.gov.cn/hebei/2017/0414/774.html","2026-11-11","excerpt","Circular 2009 No. 56 pattern: 5+ different persons buying FX same/adjacent/continuous days then remitting to one overseas person/institution. Zhu used 52 people for USD 2.5625m; classed as flight of FX, fined under Art. 39. (Not opened in full; see F11.)"),
 ("T23","People's Bank of China et al.","Notice 2026 No. 42 (virtual currency), 2026-02-06","https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html","2026-11-11","excerpt","Virtual-currency business is unlawful financial activity; fiat/virtual-currency exchange in China is strictly prohibited and will be banned. (Not opened in full; see F11.)"),
 ("T24","People's Bank of China, Beijing","Cross-border RMB policy, 2018-11-09","http://beijing.pbc.gov.cn/beijing/132026/3660457/index.html","2026-11-11","excerpt","Circular 2018 No. 3 supports individuals' other current-account RMB cross-border settlement; example: foreign employee in Beijing remitted RMB salary directly abroad instead of first buying FX. (Not opened in full; see F11.)"),
 ("T25","National People's Congress (STA site)","Personal Income Tax Law (2018)","https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html","2026-11-11","direct","Art. 3(3): interest, dividends, property rental, property transfer and incidental income taxed at flat 20%. Art. 6(5): property-transfer income = proceeds less original value and reasonable costs."),
 ("T26","Internal Revenue Service","Yearly average currency exchange rates","https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates","2026-11-11","direct","China Yuan yearly averages: 2025: 7.129; 2024: 7.189; 2023: 7.075; 2022: 6.730; 2021: 6.452. Divide foreign amount by the rate to get USD."),
 ("T27","Internal Revenue Service","US-China Income Tax Convention, Art. 9","https://www.irs.gov/pub/irs-trty/china.pdf","2026-11-11","direct","Art. 9(2): dividends may be taxed in the payer's state under its law, but if the recipient is the beneficial owner the tax shall not exceed 10% of gross dividends."),
 ("T28","Wise","Guide to CNY transfers (from-CNY)","https://wise.com/help/articles/2955298/guide-to-cny-transfers","2026-11-11","direct","From-CNY eligibility: not mainland Chinese; worked/had worked in China; valid China tax record showing taxes paid within last 3 years. Bank-app max CNY 300,000/transfer; Alipay max CNY 50,000/transfer. Overall limit = China salary less tax paid; does not expire. Recipient must be own account. Fee and FX rate are shown only in-app (not published on this page)."),
 ("T29","Western Union","Send money from China","https://www.westernunion.com/cn/en/send-money.html","2026-11-11","direct","Bank-account delivery temporarily unavailable; cash pickup only (online via partner-bank app or in person at partner bank). IDs: China ID card, passport (excl. HK/MO/TW passports), Mainland Travel Permit. Fee/FX not published on this page."),
 ("T30","Bank of America","Wire transfers","https://info.bankofamerica.com/en/digital-banking/wire-transfers","2026-11-11","direct","Inbound wires may incur a USD 15 fee per wire (schedule of fees controls). Outbound international USD wire USD 45; foreign-currency wire no fee but FX markup applies."),
 ("T31","Internal Revenue Service","Publication 525 (2025)","https://www.irs.gov/publications/p525","2026-11-11","excerpt","Personal foreign-currency transaction: gain of USD 200 or less need not be included; gain over USD 200 reported as capital gain. (Official page text via search excerpt; see F11.)"),
 ("T32","U.S. Code / eCFR","31 U.S.C. 5321; 31 CFR 1010.821","https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm","2026-11-11","direct","Willful foreign-financial-agency (FBAR) violation: max = greater of USD 100,000 (statutory) or 50% of transaction/balance. eCFR penalty table (assessed on/after 2025-01-17): statutory USD 100,000 adjusted to USD 165,353. So willful max = greater of USD 165,353 or 50% of balance."),
 ("T33","FinCEN","Report Foreign Bank and Financial Accounts (FBAR)","https://www.fincen.gov/report-foreign-bank-and-financial-accounts","2026-11-11","excerpt","US person with financial interest/signature authority must file FBAR if aggregate foreign accounts exceed USD 10,000 at any time in the calendar year. (Official page text via search excerpt; see F11.)"),
 ("T34","Internal Revenue Service","Instructions for Form 8938","https://www.irs.gov/instructions/i8938","2026-11-11","excerpt","US-resident single: file if specified foreign financial assets exceed USD 50,000 on last day of year or USD 75,000 at any time; MFJ USD 100,000 / USD 150,000. Higher thresholds if living abroad. (Official page via search excerpt + contents read; see F11.)"),
 ("T35","U.S. Customs and Border Protection","Money and Other Monetary Instruments","https://www.cbp.gov/travel/international-visitors/money-monetary-instruments","2026-11-11","direct","Entering/leaving US with currency/monetary instruments over USD 10,000 must be reported (FinCEN Form 105). Failure risks seizure/forfeiture and civil/criminal penalties."),
]
SRC = {s[0]: s for s in SOURCES}

QUESTIONS = [
 ("Q01","What is the money? (origin + character of each major deposit)","Nothing about the balance is documented in the repo.","Origin/character per deposit: salary, property sale, inheritance, emigrant property, gift, dividend, prior FX conversion, existing FX.","Route follows origin (see Methods). No route is verified for gift/undocumented money (M14).","Ask the bank for a written account/transaction classification; pull statements, contracts, tax vouchers per deposit.","T04|T12|T17",""),
 ("Q02","How is the account classified: jingwai geren (foreign individual) or jingnei geren (domestic individual)?","Two SAFE instruments use different definitions; bank sets category from ID at opening (T18).","Bank's written classification + ID used at opening.","Determines which article (59 vs 64) and whether convenience amount applies.","Request the bank's written classification; confirm passport vs resident ID on file.","T18|T04|T07","F01"),
 ("Q03","What exactly is the quoted 'considerable tax'? (name, basis, rate, base, office)","No official source reviewed imposes a standalone Chinese tax merely on converting CNY or wiring own principal.","Tax name, legal basis, rate, base, assessing office, written quote.","Bank document requests can look like a conversion tax but are compliance, not tax. Do not pay without the written breakdown.","Ask the bank to itemise in writing: tax vs fee vs FX spread vs document charge.","T04|T17","F02"),
 ("Q04","Has Chinese tax on the income been paid / withheld / exempted?","PRC IIT: 20% flat on dividends/property gains/rent/interest (T25). Salary already taxed has nothing further on remittance.","Filing history, vouchers, exemption certificates per income type.","Unpaid Chinese tax is pursued by the tax office (T16); late charges unknown - blank.","Obtain tax payment/exemption certificates; ask tax office for account transcript.","T25|T16","F03"),
 ("Q05","Are you a US citizen only, or also a Chinese citizen / green-card holder / former hukou holder?","US passport alone does not confer the USD 50,000 convenience amount (T05).","Citizenship(s), green-card status, hukou history, residence days.","Green-card holders get the convenience amount (T05); domestic individuals use Art. 64 (T07); emigrant route needs former hukou (T12).","Confirm ID documents and hukou/residence history in writing.","T05|T07|T12","F04"),
 ("Q06","When and at what rate was the CNY acquired (for US currency gain)?","IRS yearly averages known (T26); actual acquisition dates/rates unknown.","Acquisition date/rate per lot; bank withdrawal method (FIFO/LIFO/pro-rata).","Gain = USD received minus USD basis of RMB sold. Personal gain <=USD 200 ignored; >USD 200 capital gain (T31). Investment/business money: ordinary under s.988 (see Tax page).","Reconstruct lots from statements; pick a reasonable consistent basis method.","T26|T31","F05"),
 ("Q07","What is your US tax residency / filing status / marginal rate?","Unknown.","Residency, filing status, marginal rate, FTC eligibility.","Determines tax on any s.988 gain and FTC for Chinese tax paid. No personal rate is assumed - tax blank.","Confirm with tax adviser; do not use a generic rate.","T31","F06"),
 ("Q08","FBAR / Form 8938 / Form 3520 status?","FBAR threshold USD 10,000 aggregate (T33); Form 8938 US-resident single USD 50k/75k (T34).","Past filings, aggregate max balances, account interest/signature authority.","Willful FBAR max = greater of USD 165,353 or 50% of balance (T32) - dwarfs FX costs. Fix reporting before wiring.","Review prior FBAR/8938 filings; compute aggregate max per year.","T32|T33|T34",""),
 ("Q09","What are the actual transaction quotes (sending bank, provider, intermediary, receiving bank)?","BOC tariff + board known (T01|T02); BofA inbound may be USD 15 (T30).","Sending-bank rate/fees, provider fee/FX, intermediary deductions, receiving fee.","Known BOC-side cost is an estimate, not a quote. Unknowns stay blank, never zero.","Get dated written quotes for the exact amount/date; confirm intermediary deductions.","T01|T02|T30","F07"),
 ("Q10","Do you have the source documents the bank will require?","Art. 59 needs ID + source materials incl. tax vouchers (T04).","Contracts, salary slips, tax vouchers, title docs, inheritance docs per route.","Without documents the bank cannot process the documented route; do not invent a purpose.","List documents per route (Steps page); obtain certified copies.","T04|T12|T15",""),
 ("Q11","Is any part already foreign currency (not CNY)?","Unknown.","Currency breakdown of balance.","If already FX, wire only (M03) - no conversion, no spread.","Confirm currency breakdown with bank.","T08",""),
 ("Q12","Is any part unused CNY from your own prior FX exchange?","Unknown.","Original exchange slip + date (24-month validity, T09).","Reconversion route (M02) if within 24 months.","Locate original exchange slips.","T09","F02"),
 ("Q13","Is the money home-sale proceeds?","Route exists with price-less-taxes cap (T15).","Sale contract, title/registration docs, tax voucher.","M04 applies; remit <= price less taxes.","Collect sale + tax documents.","T15","F03"),
 ("Q14","Is it inheritance or emigrant property?","Approval route exists (T12|T13).","Hukou/settlement/inheritance/tax documents; approval office.","M05/M06 need SAFE approval first; bank remits to own account abroad.","Identify approval office (former/last hukou) and document list.","T12|T13",""),
 ("Q15","Is it dividend from your own Chinese company?","20% statutory (T25); 10% treaty cap if beneficial owner (T27).","Profit resolution, tax filing, beneficial-ownership/residence evidence.","M09 vs M09T differ by USD 40,000 tax on USD 400,000 gross - eligibility is decisive.","Confirm treaty eligibility with adviser; do not assume 10%.","T25|T27","F06"),
 ("Q16","Do you meet Wise from-CNY eligibility?","Needs non-mainland status + China work + tax record in last 3 years; limit = salary less tax (T28).","Tax records, work history, remaining limit.","If eligible, M12 may apply; fee/FX blank until in-app quote.","Check limit in Wise app; upload tax records.","T28","F08"),
 ("Q17","Do you need cash abroad, or bank-to-bank?","WU China: cash pickup only, bank delivery unavailable (T29).","Delivery need; partner-bank access.","M13 only fits cash pickup; fee/FX blank.","Confirm delivery method before using M13.","T29","F09"),
 ("Q18","How much, and over what period? (quota/ATM/cash caps)","Caps: quota USD 50k/yr (T06); ATM CNY 10k/day, 100k/yr (T19); cash USD 5k/10k (T20).","Amount + timeline + trip count.","Caps determine units/years in Costs page; splitting via others is prohibited (T10|T22).","Map amount to caps before choosing route.","T06|T19|T20",""),
 ("Q19","What is the receiving account (own name? US bank?)?","Emigrant/inheritance bank remits to own account abroad (T12).","Receiving bank, account name, SWIFT/IBAN.","Own-name receiving account required for approval routes; BofA inbound may be USD 15 (T30).","Confirm own-name receiving details + fee schedule.","T12|T30",""),
 ("Q20","What must NOT be used?","Private swaps/underground banks unlawful (T21); crypto exchange banned (T23); splitting pattern fined (T22).","-","Relatives' quotas, false invoices/purposes, crypto conversion, borrowed cards, excess cash.","Do not use; see Penalties page ceilings.","T21|T22|T23|T17",""),
 ("Q21","What is the FX rate on the day of execution?","Board 2026/11/11 20:50:05 known (T01); execution rate will differ.","Dated execution quote.","Costs are dated estimates; re-price on execution day.","Get same-day board + bank quote.","T01",""),
 ("Q22","Are there intermediary-bank deductions?","Unknown; not in BOC tariff.","Intermediary chain + deductions.","Excluded from known cost; ask bank to confirm.","Ask sending bank about intermediary deductions.","T02","F07"),
 ("Q23","What Chinese late-payment / surcharge exposure exists if tax is unpaid?","Unpaid tax pursued (T16); surcharge rate/look-back not verified in this session.","Tax arrears, surcharge rate, look-back period.","Blank - do not estimate. See Flagged F03.","Ask tax office for arrears + surcharge calculation in writing.","T16","F03"),
 ("Q24","Does the USD 50,000 figure cap your balance?","No - it is a convenience amount, not a cap/tax (T06).","-","Above USD 50,000 use documented route (M01), not splitting.","Do not split through others (T10).","T06|T10",""),
 ("Q25","Can you wire CNY offshore and convert there (M08)?","Cross-border RMB settlement supported in principle (T24).","Bank offer, offshore account, both price components.","Price blank - no published fee/FX in this session.","Ask bank for written cross-border RMB offer + offshore conversion quote.","T24","F05"),
 ("Q26","What is the cheapest lawful route for your origin?","See Methods ranking; BOC-side cost modest vs tax/reporting exposure.","Origin (Q01) + eligibility (Q05/Q15/Q16).","Match origin to route; cheapest = documented route for that origin.","Use the 4-question test on Summary page.","T04|T12|T15",""),
 ("Q27","What records must you keep for US reporting?","Gain basis, FBAR max balances, 8938 values.","Statements, exchange slips, tax vouchers, wire confirmations.","Keep per-lot basis + max-balance records; file FBAR/8938 as required.","Create a per-deposit file before wiring.","T26|T33|T34",""),
 ("Q28","What is unverified and must stay blank?","Wise/WU fees, cross-border RMB price, surcharge rate, personal US tax rate.","Dated provider/bank quotes; adviser determination.","Blank + flagged (Flagged page); never zero.","Obtain quotes; do not infer.","T28|T29|T24","F08"),
]

METHODS_DETAIL = [
 ("M01","Documented current-account income - buy USD + one wire","Foreign individual with lawful Chinese salary/fees/current-account income","One wire, no annual cap; bank cost modest ($53.37 on $10k; $898.75 on $400k at 11 Nov board)","Needs ID + source materials incl. tax vouchers; bank may ask for more; execution rate differs from board","Passport -> source docs + tax evidence -> buy USD -> one own-name wire -> keep confirmations","T04|T01|T02",""),
 ("M02","Reconvert unused CNY from own FX exchange + wire","Foreign individual who previously exchanged FX->CNY and still holds the slip","Uses own prior exchange; no new source proof beyond slip","Only within 24 months; amount limited to original exchange; slip required","Passport + original slip -> reconvert -> wire","T09|T01|T02","F02"),
 ("M03","Already foreign currency - wire only","Anyone holding FX (not CNY) in own account","No conversion, no spread; cheapest BOC-side ($32.43 on $10k; $61.31 on $400k)","Still needs ID; receiving/intermediary fees may apply","Passport -> instruct own-name outward remittance -> pay wire fee","T08|T02",""),
 ("M04","Chinese home-sale proceeds","Foreign individual who sold mainland housing","Dedicated route; capped at price less taxes (no invented amount)","Needs registered contract/title + tax voucher; bank checks cap","Passport -> sale/title docs + tax voucher -> bank conversion/remittance","T15|T01|T02","F03"),
 ("M05","Inheritance transfer","Foreign/HK/MO heir of mainland estate","Approval route; bank remits to own account abroad","Needs SAFE approval + inheritance/property/tax docs; no cash withdrawal","Inheritance/property/tax docs -> SAFE approval -> own-name overseas account","T12|T13|T01|T02",""),
 ("M06","Emigrant property transfer","Person who moved from mainland to live abroad (former hukou)","No annual quota; bank may remit once or in instalments within approval","Needs hukou cancellation/settlement/property/tax docs + SAFE approval","Hukou/settlement/property/tax docs -> SAFE approval -> remit","T12|T13|T01|T02",""),
 ("M07","Annual convenience quota - $50k/yr ID-only","Green-card holders (T05) / domestic individuals (T07) within quota","ID-only up to USD 50k/yr; no source docs within quota","US passport alone insufficient; above quota needs documents; $400k = 8 years; splitting via others prohibited","ID -> buy/remit up to USD 50k/yr -> repeat next year(s)","T05|T06|T07","F04"),
 ("M08","Cross-border RMB offshore, convert there","Individual whose bank offers cross-border RMB settlement","Avoids onshore conversion; convert offshore","Both price components blank in this session; needs bank offer + offshore account","Bank cross-border RMB -> own offshore account -> convert there","T24","F05"),
 ("M09","Dividend - 20% statutory scenario","Shareholder of Chinese company (domestic-law scenario)","Straightforward 20% on gross dividend (T25)","Tax dwarfs wire cost ($80,000 on $400k gross); needs profit resolution + tax filing","Profit resolution + tax filing -> 20% -> remit net","T25|T13","F06"),
 ("M09T","Dividend - 10% treaty-cap scenario","Beneficial-owner resident eligible for treaty relief","Halves Chinese dividend tax vs 20% (saves $40,000 on $400k)","Eligibility (residence/beneficial ownership) must be proved; not automatic","As M09 + treaty eligibility evidence -> 10% cap -> remit net","T27|T25","F06"),
 ("M10","Overseas ATM withdrawals","Holder of mainland UnionPay card needing cash abroad","No wire; small amounts simple","CNY 10k/day, 100k/yr caps; $400k needs 268 withdrawals / 27 years; fees high ($4,480.93 on $400k)","Card -> withdraw abroad within caps -> pay per-withdrawal fee","T19|T03","F07"),
 ("M11","Carry lawfully purchased FX banknotes","Traveller carrying own FX cash","No wire fee; spread only ($20.94 on $10k)","USD 5k/trip (10k with bank permit); $400k = 80 trips; declare >USD 10k entering US; theft/loss risk","Buy FX -> carry within limits -> declare >USD 10k to CBP","T20|T35",""),
 ("M12","Wise from-CNY (own account only)","Non-mainland person who worked in China with recent tax record","Bank-app funding; limit = salary less tax; own-account only","Fee/FX blank (in-app only); max CNY 300k/transfer; eligibility strict","Verify ID/tax records -> fund from bank app -> own account","T28","F08"),
 ("M13","Western Union China (cash pickup)","Sender wanting overseas cash pickup","Cash pickup in minutes at 525k+ locations","Bank delivery unavailable; fee/FX blank; partner-bank restrictions possible","Partner bank -> verify -> pay quoted fee -> cash pickup","T29","F09"),
 ("M14","Gift / undocumented origin - NO verified route","-","-","No verified lawful route in this research; do not invent purpose or use others' quota","Obtain bank's written determination; do not proceed without it","T04|T17","F10"),
]

STEPS = []
def add_steps(m, items, src):
    for i,(a,d) in enumerate(items,1):
        STEPS.append((m,i,a,d,src))
add_steps("M01",[("Bring passport (valid ID) to the bank","Passport"),("Present source-of-funds materials for the income (contract, salary slips)","Source materials"),("Present tax vouchers (payment/exemption/filing)","Tax vouchers"),("Buy USD at the bank's execution rate; confirm amount","-"),("Instruct one own-name international wire; pay wire fee","Wire instruction"),("Keep exchange slip, wire confirmation, tax vouchers for US reporting","All documents")],"T04|T01|T02")
add_steps("M02",[("Bring passport + original exchange slip (within 24 months)","Passport + slip"),("Reconvert unused CNY to FX at bank","Original slip"),("Wire FX to own overseas account","Wire instruction")],"T09|T01|T02")
add_steps("M03",[("Bring passport to bank","Passport"),("Instruct own-name outward remittance of FX balance","Wire instruction"),("Pay wire fee; keep confirmation","Confirmation")],"T08|T02")
add_steps("M04",[("Bring passport","Passport"),("Present registered sale contract + title/registration docs","Sale/title docs"),("Present tax voucher from tax office","Tax voucher"),("Bank converts/remits up to price less taxes","-")],"T15|T01|T02")
add_steps("M05",[("Prepare inheritance/property/tax documents","Inheritance docs"),("Apply to decedent's last-hukou SAFE office for approval","Approval"),("Bank buys FX and remits to own account abroad (no cash)","Approval + wire")],"T12|T13|T01|T02")
add_steps("M06",[("Prepare hukou cancellation/settlement/property/tax documents","Hukou/property docs"),("Apply to former-hukou SAFE office for approval","Approval"),("Bank remits once or in instalments to own account abroad","Approval + wire")],"T12|T13|T01|T02")
add_steps("M07",[("Bring ID (green card / domestic ID as applicable)","ID"),("Buy/remit up to USD 50,000 in the calendar year","-"),("Above USD 50,000: add transaction materials (do not split via others)","Materials")],"T05|T06|T07")
add_steps("M08",[("Ask bank for written cross-border RMB offer","Bank offer"),("Send CNY to own offshore account","-"),("Convert offshore; obtain offshore quote","Quote")],"T24")
add_steps("M09",[("Obtain profit-distribution resolution","Resolution"),("Complete tax filing; pay 20% (statutory scenario)","Tax filing"),("Remit net proceeds","Wire")],"T25|T13")
add_steps("M09T",[("As M09, plus treaty eligibility evidence (residence/beneficial ownership)","Eligibility evidence"),("Apply 10% treaty cap; pay 10%","Tax filing"),("Remit net proceeds","Wire")],"T27|T25")
add_steps("M10",[("Use mainland UnionPay card abroad","Card"),("Withdraw within CNY 10,000/day and CNY 100,000/year","-"),("Pay per-withdrawal fee (CNY 12 + 1%, max CNY 112)","Fee")],"T19|T03")
add_steps("M11",[("Buy FX banknotes lawfully at bank","-"),("Carry <=USD 5,000/trip (<=USD 10,000 with bank permit)","Permit if needed"),("Declare >USD 10,000 entering US (FinCEN Form 105)","Declaration")],"T20|T35")
add_steps("M12",[("Verify identity + tax records in Wise (tax paid within last 3 years)","Tax records"),("Fund from China bank app (max CNY 300,000/transfer)","Bank app"),("Receive in own account; check in-app fee/FX quote","Quote")],"T28")
add_steps("M13",[("Go to WU partner bank with government ID","ID"),("Fill transfer details; pay quoted fee","Fee"),("Receiver picks up cash with MTCN","MTCN")],"T29")

PENALTIES = [
 ("P01","China (Order 532 Art. 39)","Flight of FX (transferring FX abroad in breach / deceitful capital transfer)","Fine up to 30%; serious 30%-100%; criminal liability","T17",""),
 ("P02","China (Order 532 Art. 40)","False/invalid documents to buy FX (illegal FX arbitrage)","Fine up to 30%; serious 30%-100%; criminal liability","T17",""),
 ("P03","China (Order 532 Art. 42)","Carrying FX across border in breach of rules","Warning; fine up to 20%","T17",""),
 ("P04","China (Order 532 Art. 45)","Private buying/selling of FX","Warning, confiscation, fine up to 30%; serious 30%-100%; criminal liability","T17",""),
 ("P05","China (Order 532 Art. 48)","Untrue documents / reporting breaches (individuals)","Warning; fine up to CNY 50,000","T17",""),
 ("P06","China (SAFE Art. 62)","Borrowing others' convenience amount / evading authenticity rules","Watchlist: that year + 2 years","T10","F11"),
 ("P07","US FBAR (31 U.S.C. 5321)","Willful failure to file FBAR","Greater of USD 165,353 (adjusted) or 50% of balance","T32",""),
 ("P08","US FBAR (FinCEN)","Filing duty","File if aggregate foreign accounts > USD 10,000 at any time in year","T33","F11"),
 ("P09","US Form 8938 (IRS)","Filing duty (US-resident single)","File if > USD 50,000 year-end or > USD 75,000 at any time","T34","F11"),
 ("P10","US s.988 / Pub. 525","Currency gain on conversion","Personal gain <=USD 200 ignored; >USD 200 capital gain. Investment/business: ordinary (see Tax page)","T31","F05"),
 ("P11","PRC IIT (Art. 3)","Dividends / property gains / rent / interest","Flat 20%","T25",""),
 ("P12","PRC IIT (Treaty Art. 9)","Dividends to eligible beneficial owner","Cap 10% of gross","T27","F06"),
 ("P13","US CBP / FinCEN 105","Carrying >USD 10,000 without reporting","Seizure/forfeiture; civil/criminal penalties","T35",""),
 ("P14","China (PBOC 2026 No. 42)","Fiat/virtual-currency exchange in China","Strictly prohibited; banned","T23","F11"),
 ("P15","China (SAFE)","Private swaps / underground banks","Unlawful channel (see P04 ceilings)","T21","F11"),
]

FLAGS = [
 ("F01","Account classification (jingwai vs jingnei geren)","(blank)","Two instruments define categories differently; bank's written classification not in repo.","Ask bank for written classification + ID on file.","T18|T04|T07"),
 ("F02","The quoted 'considerable tax' + reconversion slip","(blank)","No tax name/basis/rate/base in repo; slip not in repo.","Ask bank to itemise quote in writing; locate original exchange slip.","T04|T09"),
 ("F03","Chinese tax arrears / late surcharge rate / look-back","(blank)","Unpaid tax pursued (T16) but surcharge rate/period not verified in this session.","Ask tax office for arrears + surcharge calculation in writing.","T16|T25"),
 ("F04","Convenience-amount eligibility (US passport alone)","(blank)","US passport alone insufficient (T05); green-card/domestic status unknown.","Confirm citizenship/green-card/hukou/residence in writing.","T05|T07"),
 ("F05","Cross-border RMB price (M08) + s.988 character of savings balance","(blank)","No published fee/FX for M08; whether savings balance is personal vs investment money not settled.","Ask bank for written M08 offer; obtain tax advice on character.","T24|T31"),
 ("F06","Dividend treaty eligibility (10% vs 20%) + US marginal rate","(blank)","Beneficial ownership/residence and personal US rate unknown; no rate assumed.","Confirm treaty eligibility + marginal rate with adviser.","T27|T25"),
 ("F07","Intermediary / receiving deductions + ATM FX rate","(blank)","Intermediary deductions not in BOC tariff; UnionPay ATM FX rate not published.","Get dated quotes; confirm intermediary chain.","T02|T03"),
 ("F08","Wise fee / FX rate (M12)","(blank)","Fee/FX shown only in-app; not published on help page.","Check in-app quote for exact amount/date.","T28"),
 ("F09","Western Union fee / FX rate (M13)","(blank)","Fee/FX not published on send-money page.","Get partner-bank quote before sending.","T29"),
 ("F10","Gift / undocumented origin route (M14)","(blank)","No verified lawful route in this research.","Obtain bank's written determination; do not invent purpose.","T04|T17"),
 ("F11","Excerpt-level sources (T08, T10, T11, T14-T16, T18, T21-T24, T31, T33, T34)","(see Sources page)","Official page text via search excerpt or contents read, not opened in full in this session.","Open each URL in full before acting; upgrade to direct.","T08|T10|T11|T14|T15|T16|T18|T21|T22|T23|T24|T31|T33|T34"),
 ("F12","Execution-day FX rate + sending-bank discounts","(blank)","Board is a dated snapshot; tariff notes allow agreements/discounts/local differences.","Re-price on execution day; get bank's written quote.","T01|T02"),
]

def src_links(ids):
    out=[]
    for i in ids.split("|"):
        s=SRC[i]
        out.append(f'<a class="src" href="{esc(s[3])}" target="_blank" rel="noopener">{i}</a>')
    return " ".join(out)

NAV = [("3e2d-dashboard.html","Dashboard"),("3e2d-summary.html","Summary"),("3e2d-questions.html","Questions"),("3e2d-methods.html","Methods"),("3e2d-costs.html","Costs"),("3e2d-steps.html","Steps"),("3e2d-penalties.html","Penalties"),("3e2d-tax.html","Tax"),("3e2d-flagged.html","Flagged"),("3e2d-sources.html","Sources"),("3e2d-repo-review.html","Repo review")]
def page(title, body, active):
    nav="".join(f'<a href="{h}" class="{"on" if h==active else ""}">{esc(t)}</a>' for h,t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} - 3E2D China money dashboard</title><link rel="stylesheet" href="assets/3e2d.css"></head>
<body><header class="top"><nav class="main">{nav}</nav></header><main class="wrap">{body}
<footer>3E2D session arena/3e2dbf57-china3 - Board 2026/11/11 20:50:05 Beijing - Dated general research, not legal/tax/banking advice. Every row links an official/first-party source; blanks are flagged.</footer>
</main><script src="assets/3e2d.js"></script></body></html>
"""

def usd(x):
    if x is None: return '<span class="blank">(blank)</span>'
    return f"${q(x):,.2f}"
def usd_plain(x):
    if x is None: return ""
    if isinstance(x, int): return str(x)
    return f"{q(x):.2f}"
def pct(x):
    if x is None: return '<span class="blank">(blank)</span>'
    return f"{q(x, D('0.01')):.2f}%"

def write_csv(path, header, rows):
    with open(path,"w",encoding="utf-8",newline="") as fh:
        w=csv.writer(fh); w.writerow(header); w.writerows(rows)

def build_csvs():
    write_csv(ROOT/"data/3e2d_sources.csv",["id","issuer","title","url","read_on","how_read","what_it_establishes"],[list(s) for s in SOURCES])
    write_csv(ROOT/"data/3e2d_questions.csv",["id","question","known","missing","answer","discovery","sources","flag"],[list(x) for x in QUESTIONS])
    _model={m[0]:m[2] for m in METHODS}
    write_csv(ROOT/"data/3e2d_methods.csv",["id","name","who","pros","cons","steps_summary","sources","flag","model"],[list(x)+[_model[x[0]]] for x in METHODS_DETAIL])
    write_csv(ROOT/"data/3e2d_steps.csv",["method","step_no","action","document","sources"],[list(x) for x in STEPS])
    write_csv(ROOT/"data/3e2d_penalties.csv",["id","regime","violation","ceiling","sources","flag"],[list(x) for x in PENALTIES])
    write_csv(ROOT/"data/3e2d_flags.csv",["id","item","value","why","suggestion","sources"],[list(x) for x in FLAGS])
    rows=[]
    for r in grid():
        m=[x for x in METHODS if x[0]==r["method_id"]][0]
        urls=" ".join(SRC[i][3] for i in m[3].split("|"))
        rows.append([r["method_id"],int(r["amount_usd"]),r["model"],r["units"] or "",r["units_label"],r["calendar_years"] or "",
                     usd_plain(r["spread_usd"]),usd_plain(r["fee_usd"]),usd_plain(r["tax_usd"]),usd_plain(r["known_cost_usd"]),
                     usd_plain(r["known_cost_pct"]),usd_plain(r["rmb_debited"]),usd_plain(r["extra"]),m[3],m[4],urls])
    write_csv(ROOT/"data/3e2d_ladder.csv",["method_id","amount_usd","model","units","units_label","calendar_years","spread_usd","fee_usd","tax_usd","known_cost_usd","known_cost_pct","rmb_debited","extra","sources","flag","urls"],rows)
    keys=[D(10000),D(50000),D(100000),D(200000),D(400000)]
    wrows=[]
    for (mid_,name,model,srcs,flag) in METHODS:
        if model=="none":
            wrows.append([mid_,name,model,"","","","","","","","","","","","","","","",srcs,flag]); continue
        vals=[]
        for k in keys:
            r=row(mid_,model,k); vals.append(usd_plain(r["known_cost_usd"]))
        r400=row(mid_,model,D(400000))
        wrows.append([mid_,name,model]+vals+[r400["units"] or "",r400["calendar_years"] or "",srcs,flag])
    write_csv(ROOT/"data/3e2d_method_costs.csv",["method_id","name","model","cost_10k","cost_50k","cost_100k","cost_200k","cost_400k","units_400k","years_400k","sources","flag"],wrows)

def p_dashboard():
    g={(r["method_id"],int(r["amount_usd"])):r for r in grid()}
    def c(m,a): return usd(g[(m,a)]["known_cost_usd"])
    body=f"""
<div class="hero"><h1>China money to USD: verified decision dashboard (3E2D)</h1>
<p>US citizen with money stuck in a Chinese bank account. What are the lawful ways to convert CNY to USD, what does each really cost, and what is the least-penalty path?</p>
<p><b>FX snapshot:</b> Bank of China board <b>2026/11/11 20:50:05 Beijing</b> - USD buying 6.6591, selling 6.6871 CNY/USD. Costs below are dated estimates, not execution quotes. <a href="{SRC['T01'][3]}" target="_blank" rel="noopener">BOC board (T01)</a></p>
<div class="kpis">
<div class="kpi"><b>{c('M01',10000)}</b><span>Convert + one wire on $10,000 (BOC-side)</span></div>
<div class="kpi"><b>{c('M01',400000)}</b><span>Convert + one wire on $400,000 (BOC-side)</span></div>
<div class="kpi"><b>{c('M03',400000)}</b><span>Wire only if already USD, $400,000</span></div>
<div class="kpi"><b>{c('M07',400000)}</b><span>Quota split, $400,000 (8 years)</span></div>
</div>
<p class="small">BOC-side only. Excludes intermediary/receiving fees (BofA inbound <i>may</i> be $15 - T30) and all personal taxes. Wise (M12) / Western Union (M13) / cross-border RMB (M08) costs are <span class="blank">(blank)</span> - no published fee/FX. See <a href="3e2d-costs.html">Costs</a>.</p></div>
<div class="card"><h2>Bottom line</h2><ol>
<li><b>No standalone Chinese conversion tax</b> on converting CNY or wiring own principal was found in official sources. Bank document requests are compliance, not tax. The actual quoted considerable tax remains unknown - get it itemised in writing (Q03). {src_links('T04|T17')}</li>
<li><b>Least-penalty route = lawful route matching the money's documented origin.</b> For legitimate Chinese current-account income: source docs + tax evidence -> buy USD -> one own-name wire (M01). If already FX: wire only (M03). {src_links('T04|T08')}</li>
<li><b>US passport alone is not the $50,000 convenience amount.</b> Only Foreign Permanent Resident ID holders get it for foreign individuals (T05). Do not split through others (T10). {src_links('T05|T06|T10')}</li>
<li><b>Big exposures are separate:</b> unpaid Chinese tax; US currency gain on appreciated CNY; FBAR/Form 8938 reporting (willful FBAR max = greater of $165,353 or 50% of balance); prohibited-channel fines up to 100%. {src_links('T25|T31|T32|T17')}</li>
</ol></div>
<div class="card"><h2>Start here</h2><div class="tblwrap"><table><tr><th>Page</th><th>What it answers</th></tr>
<tr><td><a href="3e2d-summary.html">Executive summary</a></td><td>Short answer, route ranking, 4-question test</td></tr>
<tr><td><a href="3e2d-questions.html">Questions &amp; discovery</a></td><td>28 questions: known / missing / answer / how to discover</td></tr>
<tr><td><a href="3e2d-methods.html">Methods</a></td><td>14 routes with pros/cons, eligibility, legal basis</td></tr>
<tr><td><a href="3e2d-costs.html">Costs $10k-$400k</a></td><td>40 increments x every priced method; most important first</td></tr>
<tr><td><a href="3e2d-steps.html">Steps</a></td><td>Numbered playbook per route, document by document</td></tr>
<tr><td><a href="3e2d-penalties.html">Penalties</a></td><td>China + US ceilings, line by line</td></tr>
<tr><td><a href="3e2d-tax.html">Tax</a></td><td>PRC 20%/10%, US currency gain, FBAR/8938</td></tr>
<tr><td><a href="3e2d-flagged.html">Flagged for Review</a></td><td>Every blank + irregularity, with source links</td></tr>
<tr><td><a href="3e2d-sources.html">Sources</a></td><td>35 official/first-party pages read 2026-11-11</td></tr>
<tr><td><a href="3e2d-repo-review.html">Repo review</a></td><td>Line-by-line audit of existing repo data/formulas</td></tr>
</table></div></div>
<div class="flagbox"><b>Not legal, tax or banking advice.</b> Dated general research from public official/first-party sources. Confirm eligibility, quotes and tax treatment with the bank and a qualified adviser before acting.</div>
"""
    return page("Dashboard", body, "3e2d-dashboard.html")

def p_summary():
    body=f"""
<div class="hero"><h1>Executive summary</h1><p>China money to USD for a US citizen - Board 2026/11/11 20:50:05 Beijing (buying 6.6591, selling 6.6871) - <a href="{SRC['T01'][3]}" target="_blank" rel="noopener">T01</a></p></div>
<div class="card"><h2>Important details</h2><ol>
<li><b>Permission vs tax vs fee vs reporting are four different things.</b> Chinese capital controls decide <i>whether</i> you may convert/remit; PRC income tax decides tax on <i>what created the money</i>; bank fees/FX spread decide <i>what the wire costs</i>; US reporting decides <i>what you must file</i>. Confusing them is why the balance looks taxed. {src_links('T17|T25|T02|T32')}</li>
<li><b>Documented current-account income has no annual cap.</b> Art. 59 (T04) allows purchase with ID + source materials incl. tax vouchers. The $50,000 figure is a convenience amount for ID-only processing, not a cap (T06). {src_links('T04|T06')}</li>
<li><b>Bank cost is small; tax/reporting exposure is large.</b> Convert+wire $53.37 on $10k (0.53%), $898.75 on $400k (0.22%) BOC-side. Dividend tax alone is $80,000 (20%) or $40,000 (10% treaty cap) on $400k gross. Willful FBAR max is greater of $165,353 or 50% of balance. {src_links('T01|T02|T25|T27|T32')}</li>
<li><b>US currency gain is the hidden conversion tax.</b> If CNY was acquired at the 2024 IRS average (7.189), converting $400,000 at today's ask recognises ~$27,926 gain (illustrative). Personal gain <=$200 ignored; &gt;$200 capital gain (T31). Actual tax depends on character + marginal rate - blank until advised. {src_links('T26|T31')}</li>
<li><b>Gift/undocumented money has no verified route.</b> Do not invent a purpose, use relatives' quotas, private swaps, crypto, or borrowed cards. Fines reach 100% (Order 532). {src_links('T04|T17|T21|T23')}</li>
</ol></div>
<div class="card"><h2>4-question test (picks your route)</h2><div class="tblwrap"><table><tr><th>#</th><th>Question</th><th>If yes -> route</th><th>Source</th></tr>
<tr><td>1</td><td>Is it already foreign currency?</td><td>M03 wire only</td><td>{src_links('T08')}</td></tr>
<tr><td>2</td><td>Is it unused CNY from your own FX exchange (&lt;=24 months, slip in hand)?</td><td>M02 reconversion</td><td>{src_links('T09')}</td></tr>
<tr><td>3</td><td>Is it documented current-account income / home sale / inheritance / emigrant property / dividend?</td><td>M01 / M04 / M05 / M06 / M09(T)</td><td>{src_links('T04|T15|T12|T25')}</td></tr>
<tr><td>4</td><td>None of the above (gift/undocumented)?</td><td><b>No verified route (M14)</b> - get bank's written determination</td><td>{src_links('T04|T17')}</td></tr>
</table></div><p class="small">Convenience quota (M07), Wise (M12), WU (M13), ATM (M10), cash (M11) and cross-border RMB (M08) are alternatives only if their eligibility/caps fit - see Methods.</p></div>
<div class="card"><h2>Cost at a glance (BOC-side, 11 Nov board)</h2><div class="tblwrap"><table><tr><th>Amount</th><th>Wire only (M03)</th><th>Convert+wire (M01)</th><th>Quota split (M07)</th><th>Gain if acquired at 2024 avg*</th><th>Gain at 2025 avg*</th></tr>
"""
    for a in [10000,50000,100000,200000,300000,400000]:
        r3=row("M03","wire_only",D(a)); r1=row("M01","fx_wire",D(a)); r7=row("M07","quota",D(a))
        body+=f"<tr><td class='num'>${a:,}</td><td class='num'>{usd(r3['known_cost_usd'])}</td><td class='num'>{usd(r1['known_cost_usd'])}</td><td class='num'>{usd(r7['known_cost_usd'])} ({r7['calendar_years']} yrs)</td><td class='num'>{usd(fx_gain(D(a),'2024'))}</td><td class='num'>{usd(fx_gain(D(a),'2025'))}</td></tr>\n"
    body+=f"""</table></div><p class="small">*Gain, not tax. Illustrative acquisition at IRS yearly average (T26). Actual basis/character unknown. Full 40-step ladder: <a href="3e2d-costs.html">Costs</a>. Data: <code>data/3e2d_ladder.csv</code>.</p></div>
<div class="card"><h2>Before any decision</h2><p>Answer the 28 questions on the <a href="3e2d-questions.html">Questions</a> page - especially origin (Q01), account classification (Q02), the quoted tax (Q03), Chinese tax evidence (Q04), CNY acquisition lots (Q06) and FBAR/8938 status (Q08). Unverified items stay blank on the <a href="3e2d-flagged.html">Flagged</a> page.</p></div>
"""
    return page("Executive summary", body, "3e2d-summary.html")

def p_questions():
    body=f"""<div class="hero"><h1>Questions, known / missing information, answers &amp; discovery</h1><p>28 questions. Nothing is inferred: unknown values are blank and flagged. Each row links its official source(s).</p></div>
<div class="card"><div class="tblwrap"><table><tr><th>ID</th><th>Question</th><th>Known</th><th>Missing</th><th>Answer</th><th>How to discover</th><th>Source</th></tr>
"""
    for (qid,qu,kn,mi,an,di,srcs,flag) in QUESTIONS:
        f=f' <a class="src" href="3e2d-flagged.html#{flag}">Flag {flag}</a>' if flag else ""
        body+=f"<tr><td>{qid}</td><td>{esc(qu)}</td><td>{esc(kn)}</td><td>{esc(mi)}</td><td>{esc(an)}</td><td>{esc(di)}</td><td>{src_links(srcs)}{f}</td></tr>\n"
    body+="</table></div></div>"
    return page("Questions", body, "3e2d-questions.html")

def p_methods():
    body=f"""<div class="hero"><h1>All CNY to USD methods: pros, cons, eligibility</h1><p>14 routes. Ranked by tax/penalty exposure, not just fee. Blank cost = no published fee/FX (see Flagged).</p></div>
<div class="card"><div class="tblwrap"><table><tr><th>ID</th><th>Method</th><th>Who</th><th>Pros</th><th>Cons</th><th>Path</th><th>Source</th></tr>
"""
    for (mid_,name,who,pros,cons,path,srcs,flag) in METHODS_DETAIL:
        f=f' <a class="src" href="3e2d-flagged.html#{flag}">Flag {flag}</a>' if flag else ""
        body+=f"<tr><td>{mid_}</td><td><b>{esc(name)}</b></td><td>{esc(who)}</td><td>{esc(pros)}</td><td>{esc(cons)}</td><td>{esc(path)}</td><td>{src_links(srcs)}{f}</td></tr>\n"
    body+="</table></div></div>"
    return page("Methods", body, "3e2d-methods.html")

def p_costs():
    g={(r["method_id"],int(r["amount_usd"])):r for r in grid()}
    keys=[10000,50000,100000,200000,400000]
    body=f"""<div class="hero"><h1>Costs: $10,000 to $400,000 in $10,000 steps</h1>
<p>Board 2026/11/11 20:50:05 (T01). BOC-side known cost only (spread + wire fee + dividend tax where shown). Excludes intermediary/receiving fees and personal taxes. Most important first: convert+wire (M01) and wire-only (M03).</p>
<label>Jump to amount: <select id="3e2d-amount-jump"><option value="">-</option>{''.join(f'<option value="{a}">${a:,}</option>' for a in range(10000,400001,10000))}</select></label></div>
<div class="card"><h2>Summary by method (key amounts)</h2><div class="tblwrap"><table><tr><th>Method</th><th>$10k</th><th>$50k</th><th>$100k</th><th>$200k</th><th>$400k</th><th>Units @ $400k</th><th>Years @ $400k</th><th>Source</th></tr>
"""
    for (mid_,name,model,srcs,flag) in METHODS:
        if model=="none":
            body+=f"<tr><td>{mid_} {esc(name)}</td><td colspan='7'><span class='blank'>(blank - no verified route)</span></td><td>{src_links(srcs)}</td></tr>\n"; continue
        cells="".join(f"<td class='num'>{usd(g[(mid_,a)]['known_cost_usd'])}</td>" for a in keys)
        r400=g[(mid_,400000)]
        u=f"{r400['units']} {r400['units_label']}" if r400['units'] else '<span class="blank">(blank)</span>'
        y=str(r400['calendar_years']) if r400['calendar_years'] else '<span class="blank">(blank)</span>'
        f=f' <a class="src" href="3e2d-flagged.html#{flag}">Flag {flag}</a>' if flag else ""
        body+=f"<tr><td>{mid_} {esc(name)}</td>{cells}<td>{u}</td><td>{y}</td><td>{src_links(srcs)}{f}</td></tr>\n"
    body+="</table></div><p class='small'>Dividend rows (M09/M09T) include Chinese tax on gross; all other rows exclude personal taxes. ATM (M10) and cash (M11) units show why they cannot move large balances.</p></div>\n"
    body+="<div class='card'><h2>Full ladder - every $10,000 increment (M01 convert+wire, most important first)</h2><div class='tblwrap'><table><tr><th>Amount</th><th>Spread</th><th>Wire fee</th><th>Known cost</th><th>%</th><th>CNY debited</th><th>Source</th></tr>\n"
    for a in range(10000,400001,10000):
        r=g[("M01",a)]
        body+=f"<tr id='amt-{a}'><td class='num'>${a:,}</td><td class='num'>{usd(r['spread_usd'])}</td><td class='num'>{usd(r['fee_usd'])}</td><td class='num'>{usd(r['known_cost_usd'])}</td><td class='num'>{pct(r['known_cost_pct'])}</td><td class='num'>CNY {q(r['rmb_debited']):,.2f}</td><td>{src_links('T01|T02')}</td></tr>\n"
    body+="</table></div></div>\n"
    body+="<div class='card'><h2>Full ladder - wire only (M03, already USD)</h2><div class='tblwrap'><table><tr><th>Amount</th><th>Wire fee</th><th>Known cost</th><th>%</th><th>Source</th></tr>\n"
    for a in range(10000,400001,10000):
        r=g[("M03",a)]
        body+=f"<tr><td class='num'>${a:,}</td><td class='num'>{usd(r['fee_usd'])}</td><td class='num'>{usd(r['known_cost_usd'])}</td><td class='num'>{pct(r['known_cost_pct'])}</td><td>{src_links('T01|T02')}</td></tr>\n"
    body+="</table></div></div>\n"
    body+="<div class='card'><h2>Full ladder - quota split (M07, $50k/year)</h2><div class='tblwrap'><table><tr><th>Amount</th><th>Spread</th><th>Wire fees</th><th>Known cost</th><th>Wires / years</th><th>Source</th></tr>\n"
    for a in range(10000,400001,10000):
        r=g[("M07",a)]
        body+=f"<tr><td class='num'>${a:,}</td><td class='num'>{usd(r['spread_usd'])}</td><td class='num'>{usd(r['fee_usd'])}</td><td class='num'>{usd(r['known_cost_usd'])}</td><td>{r['units']} / {r['calendar_years']}</td><td>{src_links('T01|T02|T06')}</td></tr>\n"
    body+="</table></div><p class='small'>M02/M04/M05/M06 price identically to M01 (same fx_wire model); M08/M12/M13 are blank at every increment. Machine-readable: <code>data/3e2d_ladder.csv</code> (560 rows) + <code>data/3e2d_method_costs.csv</code>.</p></div>\n"
    body+="<div class='card'><h2>US currency gain illustration (gain, not tax)</h2><div class='tblwrap'><table><tr><th>Amount</th><th>Gain @ 2021 avg</th><th>Gain @ 2022 avg</th><th>Gain @ 2023 avg</th><th>Gain @ 2024 avg</th><th>Gain @ 2025 avg</th><th>Source</th></tr>\n"
    for a in [10000,50000,100000,200000,300000,400000]:
        cells="".join(f"<td class='num'>{usd(fx_gain(D(a),y))}</td>" for y in ["2021","2022","2023","2024","2025"])
        body+=f"<tr><td class='num'>${a:,}</td>{cells}<td>{src_links('T01|T26')}</td></tr>\n"
    body+="</table></div><p class='small'>Gain = USD received - USD basis of RMB sold at that year's IRS average (T26). Negative = loss. Tax depends on character (personal capital vs s.988 ordinary) and marginal rate - see Tax page.</p></div>\n"
    return page("Costs", body, "3e2d-costs.html")

def p_steps():
    body=f"""<div class="hero"><h1>Step-by-step playbooks</h1><p>Exact sequence per route. Do not skip document steps; do not invent a purpose.</p></div>
"""
    from collections import defaultdict
    by=defaultdict(list)
    for (m,n,a,d,s) in STEPS: by[m].append((n,a,d,s))
    names={x[0]:x[1] for x in METHODS_DETAIL}
    for m in [x[0] for x in METHODS_DETAIL]:
        if m not in by: continue
        body+=f"<div class='card'><h2>{m} - {esc(names[m])}</h2><ol class='steps'>\n"
        for (n,a,d,s) in by[m]:
            body+=f"<li>{esc(a)} <span class='small'>(needs: {esc(d)})</span> {src_links(s)}</li>\n"
        body+="</ol></div>\n"
    return page("Steps", body, "3e2d-steps.html")

def p_penalties():
    body=f"""<div class="hero"><h1>Penalty breakdown</h1><p>Every ceiling with its official source. Up to means maximum; actual penalty depends on facts.</p></div>
<div class="card"><div class="tblwrap"><table><tr><th>ID</th><th>Regime</th><th>Violation</th><th>Ceiling</th><th>Source</th></tr>
"""
    for (pid,reg,viol,ceil,srcs,flag) in PENALTIES:
        f=f' <a class="src" href="3e2d-flagged.html#{flag}">Flag {flag}</a>' if flag else ""
        body+=f"<tr><td>{pid}</td><td>{esc(reg)}</td><td>{esc(viol)}</td><td>{esc(ceil)}</td><td>{src_links(srcs)}{f}</td></tr>\n"
    body+="</table></div><p class='small'>Worked example: willful FBAR on a $400,000 balance -> max = greater of $165,353 or 50% x $400,000 ($200,000) = <b>$200,000</b>. On $100,000 -> greater of $165,353 or $50,000 = <b>$165,353</b>. (T32.)</p></div>"
    return page("Penalties", body, "3e2d-penalties.html")

def p_tax():
    body=f"""<div class="hero"><h1>Tax &amp; reporting</h1><p>Chinese tax on the money's origin vs US tax on the conversion vs US reporting - kept separate.</p></div>
<div class="card"><h2>China</h2><div class="tblwrap"><table><tr><th>Item</th><th>Rule</th><th>Source</th></tr>
<tr><td>Dividends / property gains / rent / interest</td><td>Flat 20%</td><td>{src_links('T25')}</td></tr>
<tr><td>Property-transfer income base</td><td>Proceeds less original value + reasonable costs</td><td>{src_links('T25')}</td></tr>
<tr><td>Dividends to eligible beneficial owner</td><td>Treaty cap 10% of gross</td><td>{src_links('T27')}</td></tr>
<tr><td>Salary already taxed</td><td>Nothing further on remittance (documented route)</td><td>{src_links('T04')}</td></tr>
<tr><td>Unpaid tax</td><td>Pursued by tax office; surcharge <span class='blank'>(blank)</span> - see Flagged F03</td><td>{src_links('T16')}</td></tr>
</table></div></div>
<div class="card"><h2>United States - currency gain on the conversion itself</h2><ol>
<li>Only the <b>gain</b> is taxed: USD received minus USD basis of RMB sold. Wiring USD you already hold recognises no gain. {src_links('T26')}</li>
<li><b>Personal money:</b> gain &lt;=$200 ignored; gain &gt;$200 reported as <b>capital gain</b> (Pub. 525). Personal loss generally not deductible (26 U.S.C. 165(c) - see Flagged F05 for character of savings balances). {src_links('T31')}</li>
<li><b>Investment/business money:</b> s.988 gain/loss is <b>ordinary</b> (26 U.S.C. 988(a)(1)(A)); s.988(e)(1) excludes personal transactions from s.988. The two statements cover different cases - do not apply ordinary to personal money. {src_links('T31')}</li>
<li>Illustrative gains at IRS yearly averages are on the Costs page. <b>Tax = gain x your marginal rate</b> (capital vs ordinary) - rate blank until advised (Q07). {src_links('T26|T31')}</li>
</ol></div>
<div class="card"><h2>United States - reporting (not tax)</h2><div class="tblwrap"><table><tr><th>Form</th><th>Threshold</th><th>Source</th></tr>
<tr><td>FBAR (FinCEN 114)</td><td>Aggregate foreign accounts &gt; $10,000 at any time in year</td><td>{src_links('T33')}</td></tr>
<tr><td>Form 8938 (US-resident single)</td><td>&gt; $50,000 year-end or &gt; $75,000 at any time (MFJ $100k/$150k; higher abroad)</td><td>{src_links('T34')}</td></tr>
<tr><td>FinCEN Form 105 (cash)</td><td>Carrying &gt; $10,000 currency/monetary instruments</td><td>{src_links('T35')}</td></tr>
</table></div><p class='small'>Form 3520 (foreign trusts/gifts) applicability not verified in this session - blank, see Q08. Fix reporting before wiring.</p></div>
"""
    return page("Tax", body, "3e2d-tax.html")

def p_flagged():
    body=f"""<div class="hero"><h1>Flagged for Review</h1><p>Every blank, ambiguity and irregularity. Nothing here blocks the site; everything here needs your review. Each row links its sources.</p></div>
<div class="card"><div class="tblwrap"><table><tr><th>ID</th><th>Item</th><th>Value</th><th>Why blank / irregular</th><th>Suggested official source / next step</th><th>Source</th></tr>
"""
    for (fid,item,val,why,sug,srcs) in FLAGS:
        body+=f"<tr id='{fid}'><td>{fid}</td><td>{esc(item)}</td><td>{esc(val)}</td><td>{esc(why)}</td><td>{esc(sug)}</td><td>{src_links(srcs)}</td></tr>\n"
    body+="</table></div></div>\n"
    body+="<div class='card'><h2>Repository irregularities found in this session</h2><div class='tblwrap'><table><tr><th>ID</th><th>Finding</th><th>Evidence</th><th>Source</th></tr>\n"
    body+=f"<tr><td>3E2D-IR-01</td><td>Several older layers state personal currency gain &gt;$200 is ordinary income. Under s.988(e)(1) + Pub. 525 it is capital gain for personal money; ordinary applies to investment/business money.</td><td>DF25-IR-01 (COORDINATION.md); corrected treatment on 3e2d-tax.html</td><td>{src_links('T31')}</td></tr>\n"
    body+=f"<tr><td>3E2D-IR-02</td><td>IRS 2025 average (7.129) vs Federal Reserve 2025 average (7.1875) differ; on $400k the illustrated gain differs by ~$3,055. Neither is called wrong.</td><td>DF25-IR-03; IRS table read live (T26)</td><td>{src_links('T26')}</td></tr>\n"
    body+=f"<tr><td>3E2D-IR-03</td><td>Committed dashboard/archive.html can go stale when sessions add root pages without regenerating (DF25-IR-04). 3E2D does not edit shared navigation; see 3E2D-REQ-01.</td><td>COORDINATION.md DF25 block</td><td>{src_links('T01')}</td></tr>\n"
    body+="</table></div></div>"
    return page("Flagged", body, "3e2d-flagged.html")

def p_sources():
    body=f"""<div class="hero"><h1>Source register</h1><p>35 pages read 2026-11-11. <b>direct</b> = page fetched and read in full in this session. <b>excerpt</b> = official text via search excerpt / contents read (flagged F11). No value is inferred.</p></div>
<div class="card"><div class="tblwrap"><table><tr><th>ID</th><th>Issuer</th><th>Title</th><th>Read</th><th>How</th><th>What it establishes</th><th>Link</th></tr>
"""
    for s in SOURCES:
        body+=f"<tr><td>{s[0]}</td><td>{esc(s[1])}</td><td>{esc(s[2])}</td><td>{s[4]}</td><td>{s[5]}</td><td>{esc(s[6])}</td><td><a class='src' href='{esc(s[3])}' target='_blank' rel='noopener'>Open</a></td></tr>\n"
    body+="</table></div></div>"
    return page("Sources", body, "3e2d-sources.html")

def p_repo():
    body=f"""<div class="hero"><h1>Repository review (line by line)</h1><p>Audit of existing data, formulas and source links at <code>main @ b677a91</code>. No sibling-owned file was edited.</p></div>
<div class="card"><h2>What was checked</h2><ol>
<li>Canonical engine <code>scripts/e347_costs.py</code> vs independent verifier <code>scripts/e347_verify.py</code>: formulas re-derived (spread = usd x (ask-mid)/ask; wire = min(260,max(50,usd x ask/1000))+150 CNY). Spot-checked: $10k convert+wire $53.36 at old board (6.6606/6.6886) recomputes exactly. {src_links('T01|T02')}</li>
<li>Source register <code>data/e347_sources.csv</code> (S01-S41): 20 load-bearing pages re-fetched live in this session (T01-T07, T09, T12, T13, T17, T19, T20, T25-T30, T32, T35) - all reachable, figures match. Remaining S-rows carried as excerpt (F11). {src_links('T01|T04|T17')}</li>
<li>Cost ladder <code>data/e347_costs.csv</code>: 40 increments x priced methods; blanks (L12/L13) correctly blank, never zero. 3E2D re-prices at the 20:50 board (M01 $53.37/$898.75) - difference is board movement only. {src_links('T01|T02')}</li>
<li>Known irregularities confirmed: DF25-IR-01 (s.988 character), DF25-IR-03 (2025 average gap), DF25-IR-04 (stale archive). See Flagged page. No new arithmetic error found in canonical ladder.</li>
<li>Open PRs (#84, #78, #72, #67, #66, #61, #59, #58, #57, #50, #34, #32, #25, #18, #15, #8, #6) are parallel editions; <code>main</code> already contains later merged work. This session merges none of them.</li>
</ol></div>
<div class="card"><h2>Method</h2><p>Read <code>COORDINATION.md</code> (2,397 lines), scanned all remote branches + open PRs, claimed non-overlapping <code>3e2d</code> scope, pushed claim before any content file. Full log: <code>research/3e2d-verification-log.md</code> + <code>research/3e2d-repo-review.md</code>.</p></div>
"""
    return page("Repo review", body, "3e2d-repo-review.html")

PAGES = {"3e2d-dashboard.html":p_dashboard,"3e2d-summary.html":p_summary,"3e2d-questions.html":p_questions,"3e2d-methods.html":p_methods,"3e2d-costs.html":p_costs,"3e2d-steps.html":p_steps,"3e2d-penalties.html":p_penalties,"3e2d-tax.html":p_tax,"3e2d-flagged.html":p_flagged,"3e2d-sources.html":p_sources,"3e2d-repo-review.html":p_repo}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); a=ap.parse_args()
    build_csvs()
    for name,fn in PAGES.items():
        (ROOT/name).write_text(fn(),encoding="utf-8")
    print(f"3E2D built: {len(PAGES)} pages + 8 CSVs")

if __name__=="__main__":
    main()
