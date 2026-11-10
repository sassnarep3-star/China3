document.addEventListener('DOMContentLoaded',function(){
var nav=document.querySelector('nav.main');if(!nav)return;
nav.addEventListener('click',function(e){
var a=e.target.closest('a[data-filter]');if(!a)return;
e.preventDefault();
var pages=nav.getAttribute('data-filter')||'';
nav.setAttribute('data-filter',pages);
});
});
