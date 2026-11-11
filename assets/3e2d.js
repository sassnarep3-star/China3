// 3E2D: no content depends on this file. It only adds a "jump to amount" helper on the costs page.
document.addEventListener('DOMContentLoaded',function(){
  var sel=document.getElementById('3e2d-amount-jump');
  if(!sel)return;
  sel.addEventListener('change',function(){
    var el=document.getElementById('amt-'+sel.value);
    if(el){el.scrollIntoView({block:'center'});el.style.background='#fff6e0';setTimeout(function(){el.style.background='';},2500);}
  });
});
