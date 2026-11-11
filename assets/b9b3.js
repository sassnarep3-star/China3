// B9B3 cost-table filters. No network calls; all data is already in the page.
(function(){
  'use strict';
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded',fn); }
  ready(function(){
    var table=document.getElementById('cost-table');
    if(!table) return;
    var rows=Array.prototype.slice.call(table.querySelectorAll('tbody tr.cost-row'));
    var method=document.getElementById('method-filter');
    var status=document.getElementById('status-filter');
    var search=document.getElementById('cost-search');
    var count=document.getElementById('visible-count');
    function apply(){
      var m=method?method.value:'all', s=status?status.value:'all';
      var q=search?(search.value||'').trim().toLowerCase():'';
      var n=0;
      rows.forEach(function(r){
        var okM=m==='all'||r.getAttribute('data-method')===m;
        var okS=s==='all'||r.getAttribute('data-status')===s;
        var text=(r.textContent||'').toLowerCase();
        var okQ=!q||text.indexOf(q)!==-1;
        var show=okM&&okS&&okQ;
        r.style.display=show?'':'none';
        if(show) n++;
      });
      if(count) count.textContent=n+' of '+rows.length+' rows shown';
    }
    [method,status].forEach(function(el){ if(el) el.addEventListener('change',apply); });
    if(search) search.addEventListener('input',apply);
    apply();
  });
})();
