/* China3 dashboard — renders the verified data set.
   No network calls: all data is inlined in assets/data.js at build time. */
(function () {
  "use strict";

  var DATA = window.CHINA3 || null;
  if (!DATA) {
    document.getElementById("app") && (document.getElementById("app").innerHTML =
      '<div class="callout bad"><p><strong>Data failed to load.</strong> assets/data.js is missing. Run <code>python3 scripts/build_site.py</code>.</p></div>');
    return;
  }

  var SRC = {};
  (DATA.sources.sources || []).forEach(function (s) { SRC[s.id] = s; });

  var NAV = [
    { group: "Overview" },
    { href: "index.html", label: "Executive summary", page: "index" },
    { href: "playbook.html", label: "Playbook", page: "playbook" },
    { group: "Findings" },
    { href: "channels.html", label: "All channels", page: "channels", count: (DATA.channels.channels || []).length },
    { href: "taxes.html", label: "Tax exposure", page: "taxes", count: (DATA.taxes.items || []).length },
    { href: "penalties.html", label: "Penalty breakdown", page: "penalties", count: (DATA.penalties.penalties || []).length },
    { href: "flagged.html", label: "Flagged for review", page: "flagged", count: (DATA.flagged.items || []).length },
    { group: "Reference" },
    { href: "sources.html", label: "Source register", page: "sources", count: (DATA.sources.sources || []).length },
    { href: "methodology.html", label: "Method", page: "methodology" },
    { href: "audit.html", label: "Repo audit", page: "audit" }
  ];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function badge(kind, text) {
    return '<span class="badge ' + esc(kind) + '">' + esc(text) + "</span>";
  }

  function statusBadge(ch) {
    var k = ch.status === "lawful" ? "lawful" : ch.status === "conditional" ? "conditional" : ch.status === "prohibited" ? "prohibited" : "criminal";
    return badge(k, ch.status_label || ch.status);
  }

  function srcChips(ids) {
    if (!ids || !ids.length) {
      return badge("unverified", "no official source — flagged");
    }
    return ids.map(function (id) {
      var s = SRC[id];
      var title = s ? s.title + " — " + s.publisher : id;
      return '<a class="src" href="sources.html#' + esc(id) + '" title="' + esc(title) + '">' + esc(id) + "</a>";
    }).join("");
  }

  function kv(label, value, sub) {
    return '<div class="card kpi"><span class="label">' + esc(label) + '</span><span class="value">' +
      value + "</span>" + (sub ? '<span class="sub">' + esc(sub) + "</span>" : "") + "</div>";
  }

  /* ---------------- nav ---------------- */
  function buildNav() {
    var host = document.getElementById("nav");
    if (!host) return;
    var page = document.body.getAttribute("data-page");
    var html = "";
    NAV.forEach(function (n) {
      if (n.group) { html += '<div class="nav-group">' + esc(n.group) + "</div>"; return; }
      var current = n.page === page ? ' aria-current="page"' : "";
      html += '<a href="' + n.href + '"' + current + "><span>" + esc(n.label) + "</span>" +
        (n.count != null ? '<span class="count">' + n.count + "</span>" : "") + "</a>";
    });
    host.innerHTML = html;
  }

  /* ---------------- index ---------------- */
  function renderIndex() {
    var host = document.getElementById("app");
    if (!host) return;
    var chans = DATA.channels.channels || [];
    var lawful = chans.filter(function (c) { return c.status === "lawful"; }).length;
    var blocked = chans.filter(function (c) { return c.status === "prohibited" || c.status === "criminal"; }).length;
    var flagged = (DATA.flagged.items || []).length;
    var unverified = chans.filter(function (c) { return c.cap_verified === false; }).length;

    var top = chans.slice().sort(function (a, b) { return a.rank - b.rank; }).slice(0, 5);

    var html = "";
    html += '<div class="grid c4">' +
      kv("Channels reviewed", String(chans.length), "From SAFE, PBC and the FX Regulations") +
      kv("Lawful", String(lawful), "Documented procedures") +
      kv("Blocked or criminal", String(blocked), "Fines to 100% and prison exposure") +
      kv("Flagged for review", String(flagged), "Blank, ambiguous or your facts") +
      "</div>";

    html += '<h2>The answer in one paragraph</h2>' +
      '<div class="callout"><p><strong>There is no Chinese "conversion tax" and no US tax on wiring your own money home.</strong> ' +
      'The balance is expensive to move because of three different things that get confused with each other: ' +
      '(1) Chinese capital controls, which are a <em>permission</em> problem, not a tax problem; ' +
      '(2) PRC income tax on whatever created the money — 20% flat if it came from property, interest, rent or dividends, and nothing further if it was already-taxed salary; ' +
      'and (3) US <em>reporting</em> penalties, where a willful FBAR violation is capped at the greater of USD 165,353 or <strong>50% of the account balance</strong> — ' +
      'an order of magnitude larger than any FX spread. The cheapest lawful route is therefore: classify the money, fix US reporting first, then use the one Chinese channel that has no amount ceiling (emigrant property transfer) or the one that has no annual quota (non-resident conversion of current-account income).</p></div>';

    html += '<h2>What actually decides your case</h2>' +
      '<div class="grid c2">' +
      '<div class="card"><h3>1. Which bank category are you in?</h3>' +
      '<p>The individual FX rules put a foreign passport holder in the <strong>境外个人</strong> bucket, and the annual USD 50,000 figure is written as a cap on <em>residents\'</em> purchases. The FX Regulations use a different definition and treat a foreigner who lived in China for a year as a resident. Which one your branch has applied decides whether you are capped or instead need source documents.</p>' +
      '<p class="small">' + srcChips(["S01", "S05"]) + '</p></div>' +
      '<div class="card"><h3>2. What created the money?</h3>' +
      '<p>Salary already taxed in China, a property gain never taxed at 20%, an inheritance, or foreign cash you personally exchanged into RMB — each maps to a different route with a different tax outcome. This is the only question that changes the tax bill.</p>' +
      '<p class="small">' + srcChips(["S09", "S03"]) + '</p></div>' +
      '<div class="card"><h3>3. Can you prove you emigrated?</h3>' +
      '<p>The no-ceiling route needs a cancelled PRC household registration certificate plus embassy-issued or authenticated proof of foreign settlement, and a PRC tax clearance — which itself must be completed <em>before</em> the household registration is cancelled.</p>' +
      '<p class="small">' + srcChips(["S03", "S04", "S09"]) + '</p></div>' +
      '<div class="card"><h3>4. Is your US reporting clean?</h3>' +
      '<p>FBAR above USD 10,000 aggregate and Form 8938 above USD 50,000/75,000 (living in the US). If either was missed, the streamlined procedures replace the penalty with 5% — or with nothing at all if you meet the foreign non-residency test.</p>' +
      '<p class="small">' + srcChips(["S12", "S16", "S18", "S19"]) + '</p></div>' +
      "</div>";

    html += '<h2>Ranked routes</h2><p class="count-line">Five strongest options out of ' + chans.length + '. Full table with every pro and con on the <a href="channels.html">All channels</a> page.</p>';
    html += '<div class="table-wrap"><table><thead><tr>' +
      "<th>#</th><th>Route</th><th>Status</th><th>Cap</th><th>Best for</th><th>Verdict</th><th>Sources</th>" +
      "</tr></thead><tbody>";
    top.forEach(function (c) {
      html += "<tr>" +
        '<td class="num">' + c.rank + "</td>" +
        "<td><strong>" + esc(c.name) + "</strong><div class=\"small muted\">" + esc(c.name_zh) + "</div></td>" +
        "<td>" + statusBadge(c) + "</td>" +
        '<td class="small">' + esc(c.cap || "—") + "</td>" +
        '<td class="small">' + esc(c.best_for) + "</td>" +
        '<td class="small"><strong>' + esc(c.verdict) + "</strong></td>" +
        '<td class="tight">' + srcChips(c.sources) + "</td>" +
        "</tr>";
    });
    html += "</tbody></table></div>";

    html += '<h2>The four numbers that matter</h2>' +
      '<div class="grid c4">' +
      '<div class="card kpi"><span class="label">PRC, property or investment gain</span><span class="value">20%</span><span class="sub">Flat rate on interest, dividends, rent, property transfer, incidental income. ' + srcChips(["S09"]) + "</span></div>" +
      '<div class="card kpi"><span class="label">PRC, evasion of exchange control</span><span class="value">30–100%</span><span class="sub">Fine on the amount involved where serious. ' + srcChips(["S05"]) + "</span></div>" +
      '<div class="card kpi"><span class="label">US, willful FBAR</span><span class="value">50%</span><span class="sub">Of the account balance, or USD 165,353, whichever is greater. ' + srcChips(["S13"]) + "</span></div>" +
      '<div class="card kpi"><span class="label">US, streamlined domestic</span><span class="value">5%</span><span class="sub">Of the highest aggregate balance — the penalty replaced, not added. ' + srcChips(["S18"]) + "</span></div>" +
      "</div>";

    html += '<h2>What not to do</h2>' +
      '<div class="callout bad"><p><strong>Crypto, underground banks, smurfing and false invoices are not shortcuts — they are the expensive branch of this decision tree.</strong> ' +
      'Virtual-currency conversion became expressly illegal financial activity on 6 February 2026 (银发〔2026〕42号). Disguised FX trading carries a fine of 30%–100% and becomes illegal business operation at RMB 5,000,000 of turnover. Pooling relatives\' quotas is prohibited outright. ' +
      'And on the US side each of these converts a non-willful FBAR problem (5%) into a willful one (50%).</p>' +
      '<p class="small">' + srcChips(["S08", "S05", "S10", "S01", "S13"]) + "</p></div>";

    html += '<h2>How to read this site</h2>' +
      '<div class="grid c3">' +
      '<div class="card"><h3>Every claim has a link</h3><p class="small">Each row carries a source chip that jumps to the full citation. Where no official source existed the value is blank and listed on <a href="flagged.html">Flagged for review</a>. Nothing was inferred.</p></div>' +
      '<div class="card"><h3>Two legal systems, one balance</h3><p class="small">Chinese rules decide whether you may move the money. US rules decide what it costs you once it lands. Neither is optional.</p></div>' +
      '<div class="card"><h3>Not advice</h3><p class="small">This is a sourced research pack, not tax or legal advice. See <a href="methodology.html">Method</a> for the limits of the verification.</p></div>' +
      "</div>";

    host.innerHTML = html;
  }

  /* ---------------- channels ---------------- */
  function renderChannels() {
    var host = document.getElementById("app");
    if (!host) return;
    var chans = (DATA.channels.channels || []).slice().sort(function (a, b) { return a.rank - b.rank; });
    var cats = [];
    chans.forEach(function (c) { if (cats.indexOf(c.category) === -1) cats.push(c.category); });

    var html = "";
    html += '<div class="controls">' +
      '<input type="search" id="q" placeholder="Search routes, requirements, notes…" aria-label="Search routes">' +
      '<select id="cat" aria-label="Filter by category"><option value="">All categories</option>' +
      cats.map(function (c) { return '<option value="' + esc(c) + '">' + esc(c) + "</option>"; }).join("") + "</select>" +
      '<button class="pill" data-status="" aria-pressed="true">All</button>' +
      '<button class="pill" data-status="lawful" aria-pressed="false">Lawful</button>' +
      '<button class="pill" data-status="conditional" aria-pressed="false">Conditional</button>' +
      '<button class="pill" data-status="prohibited" aria-pressed="false">Prohibited</button>' +
      '<button class="pill" data-status="criminal" aria-pressed="false">Criminal</button>' +
      "</div>" +
      '<p class="count-line" id="count"></p>';

    html += '<div class="table-wrap"><table id="ctable"><thead><tr>' +
      '<th class="num">#</th><th>Route</th><th>Status</th><th>Applies to</th><th>Cap / limit</th>' +
      '<th>Best for</th><th>Verdict</th><th>Sources</th>' +
      "</tr></thead><tbody></tbody></table></div>";

    html += '<h2>Legend</h2><div class="grid c4">' +
      '<div class="card"><p class="small">' + badge("lawful", "Lawful") + " Expressly permitted, documented procedure only.</p></div>" +
      '<div class="card"><p class="small">' + badge("conditional", "Conditional") + " Only if the facts fit — a specific source of funds, applicant status or approval.</p></div>" +
      '<div class="card"><p class="small">' + badge("prohibited", "Prohibited") + " Expressly banned; fine and/or confiscation.</p></div>" +
      '<div class="card"><p class="small">' + badge("criminal", "Criminal") + " Can constitute a criminal offence.</p></div>" +
      "</div>";

    host.innerHTML = html;

    var tbody = host.querySelector("#ctable tbody");
    var q = document.getElementById("q");
    var cat = document.getElementById("cat");
    var status = "";
    var countEl = document.getElementById("count");

    function draw() {
      var term = (q.value || "").toLowerCase().trim();
      var visible = chans.filter(function (c) {
        if (status && c.status !== status) return false;
        if (cat.value && c.category !== cat.value) return false;
        if (!term) return true;
        var blob = [c.name, c.name_zh, c.category, c.applies_to, c.best_for, c.cap, c.requirements,
          (c.pros || []).join(" "), (c.cons || []).join(" "), c.note, c.verdict].join(" ").toLowerCase();
        return blob.indexOf(term) !== -1;
      });

      var rows = "";
      visible.forEach(function (c) {
        rows += '<tr class="crow" data-id="' + esc(c.id) + '">' +
          '<td class="num">' + c.rank + "</td>" +
          "<td><strong>" + esc(c.name) + '</strong><div class="small muted">' + esc(c.name_zh) + "</div></td>" +
          "<td>" + statusBadge(c) + "</td>" +
          '<td class="small">' + esc(c.applies_to) + "</td>" +
          '<td class="small">' + (c.cap ? esc(c.cap) : '<span class="badge unverified">blank — unverified</span>') + "</td>" +
          '<td class="small">' + esc(c.best_for) + "</td>" +
          '<td class="small"><strong>' + esc(c.verdict) + "</strong></td>" +
          '<td class="tight">' + srcChips(c.sources) + "</td>" +
          "</tr>";
        rows += '<tr class="rowdetail" id="d-' + esc(c.id) + '" hidden><td colspan="8"><div class="rowdetail-inner">' +
          "<div><h4>Requirements</h4><p class=\"small\">" + esc(c.requirements) + "</p>" +
          "<h4>Timeline</h4><p class=\"small\">" + esc(c.timeline) + "</p>" +
          (c.note ? '<h4>Rule note</h4><p class="small">' + esc(c.note) + "</p>" : "") +
          (c.cap_verified === false ? '<p class="small">' + badge("unverified", "cap unverified") + "</p>" : "") +
          "</div>" +
          '<div><h4 class="pro">Pros</h4><ul class="small">' + (c.pros || []).map(function (p) { return "<li>" + esc(p) + "</li>"; }).join("") + "</ul>" +
          '<h4 class="con">Cons</h4><ul class="small">' + (c.cons || []).map(function (p) { return "<li>" + esc(p) + "</li>"; }).join("") + "</ul>" +
          "</div></div></td></tr>";
      });

      tbody.innerHTML = rows || '<tr><td colspan="8" class="muted">No routes match those filters.</td></tr>';
      countEl.textContent = "Showing " + visible.length + " of " + chans.length + " routes. Click a row to open its pros, cons and requirements.";

      Array.prototype.forEach.call(tbody.querySelectorAll(".crow"), function (tr) {
        tr.addEventListener("click", function () {
          var d = document.getElementById("d-" + tr.getAttribute("data-id"));
          if (d) d.hidden = !d.hidden;
        });
      });
    }

    q.addEventListener("input", draw);
    cat.addEventListener("change", draw);
    Array.prototype.forEach.call(document.querySelectorAll(".pill"), function (b) {
      b.addEventListener("click", function () {
        status = b.getAttribute("data-status");
        Array.prototype.forEach.call(document.querySelectorAll(".pill"), function (o) { o.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        draw();
      });
    });
    draw();
  }

  /* ---------------- taxes ---------------- */
  function taxTable(items) {
    var rows = items.map(function (t) {
      var kindBadge = t.kind === "analysis" ? badge("neutral", "analysis") : badge("neutral", "rule");
      var amount = t.amount ? esc(t.amount) : badge("unverified", "blank — unverified");
      return "<tr>" +
        '<td class="mono">' + esc(t.id) + "</td>" +
        "<td><strong>" + esc(t.item) + "</strong><div>" + kindBadge + "</div></td>" +
        '<td class="small">' + esc(t.what_it_means) + (t.flag ? '<div class="small" style="color:#4b3a86">⚑ ' + esc(t.flag) + "</div>" : "") + "</td>" +
        '<td class="small">' + amount + "</td>" +
        '<td class="tight">' + srcChips(t.sources) + "</td>" +
        "</tr>";
    }).join("");
    return '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Item</th><th>What it means</th><th>Amount</th><th>Sources</th></tr></thead><tbody>' + rows + "</tbody></table></div>";
  }

  function renderTaxes() {
    var host = document.getElementById("app");
    if (!host) return;
    var items = DATA.taxes.items || [];
    var us = items.filter(function (t) { return t.jurisdiction === "US"; });
    var x = items.filter(function (t) { return t.jurisdiction === "US–PRC"; });
    var prc = items.filter(function (t) { return t.jurisdiction === "PRC"; });

    host.innerHTML =
      '<div class="callout"><p><strong>The split.</strong> China taxes what happened <em>inside</em> China. The US taxes you on everything, everywhere, forever, and separately punishes you for not <em>reporting</em> the account. Those are three different obligations, and only the first two are taxes.</p></div>' +
      '<h2>United States — income and information reporting</h2><p class="count-line">' + us.length + ' items. “rule” = stated in a statute, treaty or agency guidance; “analysis” = reasoning from the rules, flagged.</p>' + taxTable(us) +
      '<h2>Cross-border — the treaty</h2><p class="count-line">The treaty limits China\'s tax. It does not limit yours, because of the saving clause.</p>' + taxTable(x) +
      '<h2>China — income tax and the emigration gate</h2><p class="count-line">' + prc.length + ' items.</p>' + taxTable(prc);
  }

  /* ---------------- penalties ---------------- */
  function renderPenalties() {
    var host = document.getElementById("app");
    if (!host) return;
    var P = DATA.penalties;
    var html = "";

    html += '<div class="callout"><p><strong>' + esc(P.meta.thesis) + "</strong></p></div>";

    html += "<h2>The five layers of cost</h2>";
    html += '<div class="table-wrap"><table><thead><tr><th class="num">Layer</th><th>Name</th><th>Type</th><th>What it is</th><th>Verification</th></tr></thead><tbody>';
    P.meta.layers.forEach(function (l) {
      html += "<tr>" +
        '<td class="num">' + l.layer + "</td>" +
        "<td><strong>" + esc(l.name) + "</strong></td>" +
        '<td class="small">' + esc(l.type) + "</td>" +
        '<td class="small">' + esc(l.nature) + "</td>" +
        '<td class="small">' + (l.status.indexOf("not published") === 0 || l.status.indexOf("Rates not") === 0 ? badge("unverified", esc(l.status)) : esc(l.status)) + "</td>" +
        "</tr>";
    });
    html += "</tbody></table></div>";

    html += "<h2>Penalty and tax register</h2><p class=\"count-line\">Every provision that can bite, with the exact statutory percentage and a link.</p>";
    html += '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Provision</th><th>Trigger</th><th>Consequence</th><th class="num">Max %</th><th>Severity</th><th>Sources</th></tr></thead><tbody>';
    (P.penalties || []).forEach(function (n) {
      var pct = (n.max_pct === null || n.max_pct === undefined) ? badge("unverified", "blank") : (n.max_pct + "%");
      html += "<tr>" +
        '<td class="mono">' + esc(n.id) + "</td>" +
        "<td><strong>" + esc(n.provision) + "</strong></td>" +
        '<td class="small">' + esc(n.trigger) + "</td>" +
        '<td class="small">' + (n.penalty ? esc(n.penalty) : badge("unverified", "unverified — blank")) +
        (n.flag ? '<div class="small" style="color:#4b3a86">⚑ ' + esc(n.flag) + "</div>" : "") + "</td>" +
        '<td class="num">' + pct + "</td>" +
        '<td class="small">' + esc(n.severity) + "</td>" +
        '<td class="tight">' + srcChips(n.sources) + "</td>" +
        "</tr>";
    });
    html += "</tbody></table></div>";

    html += "<h2>Layer 1 — what the bank charges</h2>" +
      '<p class="small">' + esc(P.cost_model.formula) + "</p>" +
      '<p class="small">' + esc(P.cost_model.effective_cost_pct) + "</p>";
    html += '<div class="table-wrap"><table><thead><tr><th>Component</th><th>Where the number comes from</th><th>Value</th></tr></thead><tbody>';
    (P.cost_model.components || []).forEach(function (c) {
      html += "<tr><td><strong>" + esc(c.name) + "</strong></td><td class=\"small\">" + esc(c.typical_source) + "</td>" +
        "<td>" + (c.value ? esc(c.value) : badge("unverified", "blank — no official source")) +
        '<div class="small muted">' + esc(c.flag) + "</div></td></tr>";
    });
    html += "</tbody></table></div>";

    html += "<h3>Effective-cost calculator</h3>" +
      '<div class="card"><div class="calc">' +
      '<div class="field"><label for="cny">CNY amount</label><input class="calc" id="cny" type="number" min="0" step="1000" placeholder="e.g. 1000000"></div>' +
      '<div class="field"><label for="mid">Mid-market rate (CNY per USD)</label><input class="calc" id="mid" type="number" min="0" step="0.0001" placeholder="your reference rate"></div>' +
      '<div class="field"><label for="bank">Bank\'s rate you were quoted (CNY per USD)</label><input class="calc" id="bank" type="number" min="0" step="0.0001" placeholder="from the branch"></div>' +
      '<div class="field"><label for="fees">Total wire and intermediary fees (USD)</label><input class="calc" id="fees" type="number" min="0" step="1" placeholder="sum of the tariffs"></div>' +
      "</div><div class=\"result\" id=\"calc-out\">Enter your own quoted numbers — this tool deliberately ships with none, because no regulator publishes retail FX spreads.</div></div>" +
      '<p class="small muted">Nothing is stored or transmitted; the calculation runs in your browser.</p>';

    html += "<h2>Worst-case statutory exposure by route</h2><p class=\"count-line\">Percentages are from the provisions above, applied to the amount moved. They are exposure ceilings, not predictions — and the lawful route is 0%.</p>";
    html += '<div class="table-wrap"><table><thead><tr><th>Route</th><th class="num">China penalty</th><th class="num">US penalty</th><th>Basis</th><th>Sources</th></tr></thead><tbody>';
    (P.scenarios.rows || []).forEach(function (r) {
      var cn = r.china_penalty_pct === null ? badge("unverified", "n/a") : r.china_penalty_pct + "%";
      var us = r.us_penalty_pct === null ? badge("unverified", "n/a") : r.us_penalty_pct + "%";
      var tone = (r.china_penalty_pct || 0) > 0 ? "bad" : "lawful";
      html += "<tr><td>" + esc(r.route) + "</td>" +
        '<td class="num"><span class="badge ' + tone + '">' + cn + "</span></td>" +
        '<td class="num">' + us + "</td>" +
        '<td class="small">' + esc(r.basis) + "</td>" +
        '<td class="tight">' + srcChips(r.sources) + "</td></tr>";
    });
    html += "</tbody></table></div>";

    html += '<h2>Read this before you act</h2><div class="callout warn"><p>The penalty tables describe ceilings, not forecasts. Actual assessment depends on facts, on whether conduct was willful, and on whether you come forward before being contacted. The single most consequential choice on this page is not which Chinese channel you pick — it is whether your US reporting is clean before the money moves, because the 50% FBAR figure is calculated on the balance, not on the gain.</p><p class="small">' +
      srcChips(["S13", "S18", "S17"]) + "</p></div>";

    host.innerHTML = html;
    wireCalculator();
  }

  function wireCalculator() {
    var ids = ["cny", "mid", "bank", "fees"];
    var out = document.getElementById("calc-out");
    function run() {
      var cny = parseFloat(document.getElementById("cny").value);
      var mid = parseFloat(document.getElementById("mid").value);
      var bank = parseFloat(document.getElementById("bank").value);
      var fees = parseFloat(document.getElementById("fees").value) || 0;
      if (!cny || !mid || !bank) {
        out.textContent = "Enter your own quoted numbers — this tool deliberately ships with none, because no regulator publishes retail FX spreads.";
        return;
      }
      var ideal = cny / mid;
      var received = (cny / bank) - fees;
      var costPct = ((ideal - received) / ideal) * 100;
      out.innerHTML = "At mid-market you would receive <strong>$" + ideal.toLocaleString(undefined, { maximumFractionDigits: 2 }) + "</strong>. " +
        "After the quoted rate and fees you receive <strong>$" + received.toLocaleString(undefined, { maximumFractionDigits: 2 }) + "</strong>. " +
        "Effective cost: <strong>" + costPct.toFixed(2) + "%</strong> of the transfer" +
        (ideal > 0 ? " — about <strong>$" + (ideal - received).toLocaleString(undefined, { maximumFractionDigits: 0 }) + "</strong> on this amount." : ".");
    }
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener("input", run);
    });
    run();
  }

  /* ---------------- flagged ---------------- */
  function renderFlagged() {
    var host = document.getElementById("app");
    if (!host) return;
    var items = DATA.flagged.items || [];
    var html = '<div class="callout warn"><p><strong>' + items.length + " items flagged.</strong> " + esc(DATA.flagged.meta.rule) + "</p></div>";
    html += '<h2>Index</h2>' +
      '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Item</th><th>Status</th><th>Impact</th><th>Sources</th></tr></thead><tbody>' +
      items.map(function (i) {
        var cls = i.status === "Unverified" ? "unverified" : i.status === "Needs your facts" ? "conditional" : "neutral";
        return '<tr><td class="mono">' + esc(i.id) + "</td><td><strong>" + esc(i.item) + "</strong></td>" +
          "<td>" + badge(cls, i.status) + "</td>" +
          '<td class="small">' + esc(i.impact) + "</td>" +
          '<td class="tight">' + (i.sources && i.sources.length ? srcChips(i.sources) : badge("unverified", "no source")) + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    html += '<h2>Detail</h2><div class="controls">' +
      '<input type="search" id="fq" placeholder="Search flagged items…" aria-label="Search flagged items">' +
      "</div><p class=\"count-line\" id=\"fcount\"></p><div class=\"grid\" id=\"flist\" style=\"gap:12px\"></div>";
    host.innerHTML = html;

    function draw() {
      var term = (document.getElementById("fq").value || "").toLowerCase();
      var list = items.filter(function (i) {
        return !term || (i.item + " " + i.detail + " " + i.impact + " " + i.status).toLowerCase().indexOf(term) !== -1;
      });
      document.getElementById("fcount").textContent = "Showing " + list.length + " of " + items.length + ".";
      document.getElementById("flist").innerHTML = list.map(function (i) {
        var cls = i.status === "Unverified" ? "unverified" : i.status === "Needs your facts" ? "conditional" : "neutral";
        return '<div class="flagitem"><h3>' + esc(i.id) + " — " + esc(i.item) + "</h3>" +
          '<div class="meta">' + badge(cls, i.status) + "<span>sources: " + (i.sources && i.sources.length ? srcChips(i.sources) : "none") + "</span></div>" +
          "<p>" + esc(i.detail) + "</p>" +
          '<div class="impact"><strong>Why it matters:</strong> ' + esc(i.impact) + "</div></div>";
      }).join("") || '<p class="muted">Nothing matches.</p>';
    }
    document.getElementById("fq").addEventListener("input", draw);
    draw();
  }

  /* ---------------- sources ---------------- */
  function renderSources() {
    var host = document.getElementById("app");
    if (!host) return;
    var list = DATA.sources.sources || [];
    var tiers = { official: 0, "official-secondary": 0, "third-party": 0 };
    list.forEach(function (s) { tiers[s.tier] = (tiers[s.tier] || 0) + 1; });

    var html = '<div class="grid c3">' +
      kv("Official", String(tiers.official), "Statute, treaty, regulation, agency page") +
      kv("Official secondary", String(tiers["official-secondary"]), "Agency Q&A, guide, consolidated index") +
      kv("Third-party", String(tiers["third-party"]), "Non-government mirror — flagged") +
      "</div>";
    html += "<h2>Register</h2><p class=\"count-line\">Every URL below was opened and the supported proposition checked on the page on " + esc(DATA.sources.meta.checked) + ".</p>";
    html += '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Source</th><th>Publisher</th><th>Tier</th><th>What it supports</th><th>Checked</th></tr></thead><tbody>';
    list.forEach(function (s) {
      var tierBadge = s.tier === "third-party" ? badge("unverified", s.tier) : badge("neutral", s.tier);
      html += '<tr id="' + esc(s.id) + '">' +
        '<td class="mono">' + esc(s.id) + "</td>" +
        '<td><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer"><strong>' + esc(s.title) + "</strong></a></td>" +
        '<td class="small">' + esc(s.publisher) + "</td>" +
        "<td>" + tierBadge + "</td>" +
        '<td class="small">' + esc(s.supports) + "</td>" +
        '<td class="small tight">' + esc(s.checked || "") + "</td>" +
        "</tr>";
    });
    html += "</tbody></table></div>";
    host.innerHTML = html;
  }

  document.addEventListener("DOMContentLoaded", function () {
    buildNav();
    var page = document.body.getAttribute("data-page");
    if (page === "index") renderIndex();
    else if (page === "channels") renderChannels();
    else if (page === "taxes") renderTaxes();
    else if (page === "penalties") renderPenalties();
    else if (page === "flagged") renderFlagged();
    else if (page === "sources") renderSources();
  });
})();
