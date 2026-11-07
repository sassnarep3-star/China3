// Minimal progressive enhancement: route filters + keyword search. The site is fully
// readable and every table row is complete with the JavaScript disabled.
(function () {
  var chips = document.querySelectorAll('.chip');
  var search = document.getElementById('q-ch');
  if (!chips.length) return;

  function apply() {
    var active = document.querySelector('.chip.active');
    var legal = active ? active.dataset.filter : 'all';
    var q = search ? search.value.trim().toLowerCase() : '';
    var rows = document.querySelectorAll('#channels tbody tr');
    var shown = 0;
    rows.forEach(function (tr) {
      var okLegal = legal === 'all' || tr.dataset.legal === legal;
      var okText = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
      var show = okLegal && okText;
      tr.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    var counter = document.getElementById('chcount');
    if (counter) counter.textContent = shown + ' shown';
  }

  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      chips.forEach(function (x) { x.classList.remove('active'); });
      c.classList.add('active');
      apply();
    });
  });
  if (search) search.addEventListener('input', apply);
})();
