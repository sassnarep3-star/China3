/* m5f19 — progressive enhancement only. Every page is complete and readable with
   JavaScript disabled: the tables are real <table> markup, the playbooks are real
   <details> elements, and no figure is injected at runtime. This file adds
   filtering, expand/collapse-all, and mobile table labels. */
(function () {
  "use strict";
  if (!document.body.classList.contains("m5f19")) return;

  /* Mobile card labels: copy each <th> into its <td> so the collapsed phone
     layout can name every value. Purely presentational; the data-l attributes
     the CSS reads are generated server-side by build_m5f19_site.py, so this
     only backfills anything missed. */
  function labelCells() {
    document.querySelectorAll("table.m5f19-t").forEach(function (tbl) {
      var heads = [].map.call(
        tbl.querySelectorAll("thead th"),
        function (th) { return th.textContent.trim(); }
      );
      tbl.querySelectorAll("tbody tr").forEach(function (tr) {
        [].forEach.call(tr.children, function (td, i) {
          if (!td.getAttribute("data-l") && heads[i]) {
            td.setAttribute("data-l", heads[i]);
          }
        });
      });
    });
  }

  /* Expand / collapse all <details> on the page. */
  function addControls() {
    var groups = document.querySelectorAll("section.m5f19-sec");
    groups.forEach(function (sec) {
      var ds = sec.querySelectorAll("details.m5f19-d");
      if (ds.length < 3) return;
      var bar = document.createElement("div");
      bar.className = "m5f19-filter";
      bar.innerHTML =
        '<button type="button" data-act="open">Expand all ' + ds.length +
        '</button><button type="button" data-act="close">Collapse all</button>';
      bar.querySelectorAll("button").forEach(function (btn) {
        btn.style.cssText =
          "background:var(--panel2);color:var(--ink);border:1px solid var(--line);" +
          "border-radius:8px;padding:7px 11px;font-size:13px;cursor:pointer;" +
          "font-family:var(--sans)";
        btn.addEventListener("click", function () {
          var open = btn.getAttribute("data-act") === "open";
          ds.forEach(function (d) { d.open = open; });
        });
      });
      sec.insertBefore(bar, sec.querySelector("h2").nextSibling);
    });
  }

  /* Text filter over any table that opts in via data-filterable. */
  function addFilter() {
    document.querySelectorAll("[data-filterable]").forEach(function (host) {
      var tbl = host.querySelector("table.m5f19-t");
      if (!tbl) return;
      var bar = document.createElement("div");
      bar.className = "m5f19-filter";
      bar.innerHTML =
        '<label for="m5f19-q">Filter</label>' +
        '<input id="m5f19-q" type="search" placeholder="Search these rows\u2026">' +
        '<span class="m5f19-count"></span>';
      host.insertBefore(bar, tbl.parentNode);
      var input = bar.querySelector("input");
      var count = bar.querySelector(".m5f19-count");
      var rows = [].slice.call(tbl.querySelectorAll("tbody tr"));
      function apply() {
        var q = input.value.trim().toLowerCase();
        var shown = 0;
        rows.forEach(function (tr) {
          var hit = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
          tr.style.display = hit ? "" : "none";
          if (hit) shown++;
        });
        count.textContent = shown + " / " + rows.length + " rows";
      }
      input.addEventListener("input", apply);
      apply();
    });
  }

  /* Report the exact inputs behind the figures on the page, so a reader can
     see which board reading produced them without opening the CSV. */
  function stampBoard() {
    var el = document.querySelector("[data-board]");
    if (!el) return;
    el.textContent = el.getAttribute("data-board");
  }

  function init() {
    try {
      labelCells();
      addControls();
      addFilter();
      stampBoard();
    } catch (err) {
      /* Never let enhancement break a readable page. */
      if (window.console && console.warn) console.warn("m5f19:", err);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
