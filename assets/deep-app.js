/* China Money Research — simple dashboard table filter (no external deps). */
(function () {
  "use strict";
  Array.prototype.forEach.call(document.querySelectorAll("input.filter"), function (input) {
    var id = input.getAttribute("data-filter");
    var table = document.querySelector('table[data-table="' + id + '"]');
    var count = document.querySelector('[data-count="' + id + '"]');
    if (!table) return;
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase(), shown = 0;
      rows.forEach(function (row) {
        var match = !q || row.textContent.toLowerCase().indexOf(q) !== -1;
        row.style.display = match ? "" : "none";
        if (match) shown++;
      });
      if (count) count.textContent = shown + " of " + rows.length + " rows";
    });
    if (count) count.textContent = rows.length + " rows";
  });
})();
