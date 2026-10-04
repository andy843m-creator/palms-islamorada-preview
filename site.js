(function(){
var b=document.getElementById('menubtn'),n=document.getElementById('nav');
if(b){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)})}
var lb=document.getElementById('lightbox');
if(lb){var im=lb.querySelector('img'),p=lb.querySelector('p');
document.querySelectorAll('.gallery button').forEach(function(x){x.addEventListener('click',function(){im.src=x.dataset.full;im.alt=x.dataset.cap;p.textContent=x.dataset.cap;lb.classList.add('on')})});
lb.addEventListener('click',function(){lb.classList.remove('on')});
document.addEventListener('keydown',function(e){if(e.key==='Escape')lb.classList.remove('on')})}
})();
(function(){
var chips=document.getElementById('chips');if(!chips)return;
var secs=[].slice.call(document.querySelectorAll('.tsec')),cnt=document.getElementById('count');
function apply(f){
 [].forEach.call(chips.querySelectorAll('.chip'),function(c){var on=c.dataset.filter===f;c.classList.toggle('on',on);c.setAttribute('aria-pressed',on)});
 var total=0;
 secs.forEach(function(s){
  var cards=[].slice.call(s.querySelectorAll('.spot')),vis=0;
  cards.forEach(function(c){var show=f==='all'||f===s.dataset.cat||(f==='fav'&&c.dataset.fav==='1');c.hidden=!show;if(show)vis++});
  var isFavSec=s.dataset.cat==='fav';
  s.hidden=isFavSec?(f!=='fav'&&f!=='all'):(vis===0);
  total+=vis;
 });
 if(cnt)cnt.textContent='Showing '+total+' place'+(total===1?'':'s')+'.';
}
chips.addEventListener('click',function(e){var b=e.target.closest('.chip');if(b)apply(b.dataset.filter)});
apply('all');
})();
(function(){
var f=document.getElementById('gfilter'),g=document.getElementById('gallery');if(!f||!g)return;
var items=[].slice.call(g.querySelectorAll('button')),cnt=document.getElementById('gcount');
function apply(c){
 [].forEach.call(f.querySelectorAll('.chip'),function(b){var on=b.dataset.filter===c;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)});
 var n=0;items.forEach(function(b){var show=c==='all'||b.dataset.cat===c;b.hidden=!show;if(show)n++});
 if(cnt)cnt.textContent='Showing '+n+' photo'+(n===1?'':'s')+'.';
}
f.addEventListener('click',function(e){var b=e.target.closest('.chip');if(b)apply(b.dataset.filter)});
apply('all');
})();
