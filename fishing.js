(function(){
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function tides(a){return a.length?a.map(function(t){return '<li><strong>'+t.type+'</strong> '+e(t.time)+' <span class="small">('+t.ft.toFixed(1)+' ft)</span></li>';}).join(''):'<li>Not available</li>';}
var IMG={backcountry:['keys-islamorada-sunset.jpg','Sunset over the Islamorada backcountry'],flats:['ocean-pier-turquoise-water.jpg','Clear turquoise shallows'],reef:['alligator-reef-lighthouse-aerial.jpg','Alligator Reef Lighthouse from the air'],offshore:['boat-at-lighthouse.jpg','Boat near the reef lighthouse']};
var ICO={backcountry:'\u{1F33F}',flats:'\u{1F3A3}',reef:'\u{1F420}',offshore:'\u{1F41F}'};
fetch('data/fishing.json',{cache:'no-cache'}).then(function(r){return r.json();}).then(function(d){
 var R=d.report||{cards:[],conditions:{},wind_days:[]}, c=R.conditions;
 document.getElementById('cards').innerHTML=R.cards.map(function(k){var im=IMG[k.key];return '<article class="fr-card fr-'+k.key+'"><img src="images/web/'+im[0]+'" alt="'+im[1]+'" loading="lazy"><div class="fr-card-b"><h3><span aria-hidden="true">'+ICO[k.key]+'</span> '+e(k.title)+'</h3><p>'+e(k.text)+'</p><h4>Top species</h4><ul class="fr-sp">'+k.species.map(function(x){return '<li><span class="nm">'+e(x.name)+(x.note?' <small>('+e(x.note)+')</small>':'')+'</span><span class="pill p-'+x.rating.toLowerCase()+'">'+e(x.rating)+'</span></li>';}).join('')+'</ul></div></article>';}).join('');
 var L=[['Water temp',c.water],['Winds',c.wind_trend?(c.wind_trend.charAt(0).toUpperCase()+c.wind_trend.slice(1)+' this week; today '+c.wind_now):null],['Seas nearshore',c.seas_near],['Seas offshore',c.seas_off],['Moon',c.moon],['Tides',c.tides]];
 document.getElementById('cond').innerHTML=L.filter(function(x){return x[1];}).map(function(x){return '<li><strong>'+x[0]+':</strong> '+e(x[1])+'</li>';}).join('');
 if(c.wind_trend)document.getElementById('outlook-h').textContent='Outlook: winds '+c.wind_trend;
 document.getElementById('outlook').textContent=c.outlook||'';
 document.getElementById('windbar').innerHTML=R.wind_days.map(function(w){return '<div><b>'+e(w.day)+'</b><span>'+w.wind_kt+' kt</span><i>'+e(w.dir)+'</i></div>';}).join('');
 document.getElementById('updated').innerHTML='<br><strong>Last updated:</strong> '+e(d.generated_label)+'.';
 var w=d.water_temp, t=d.days[0];
 document.getElementById('now').innerHTML='<div class="fr-stat"><span>Moon today</span><b>'+e(t.moon.phase)+'</b><i>'+t.moon.illumination+'% lit</i></div>'+
  (w?'<div class="fr-stat"><span>Water temp</span><b>'+w.f.toFixed(0)+'&deg;F</b><i>'+e(w.station)+', '+e(w.time)+'</i></div>':'')+
  '<div class="fr-stat"><span>Sunrise / sunset</span><b>'+e(t.sunrise)+'</b><i>Sunset '+e(t.sunset)+'</i></div>';
 document.getElementById('days').innerHTML=d.days.map(function(x){var s=x.solunar;return '<article class="fr-day"><h3>'+e(x.label)+' <span class="fr-rate fr-'+s.rating.toLowerCase()+'">'+e(s.rating)+'</span></h3>'+
  '<p class="fr-meta">Sun '+e(x.sunrise)+' &ndash; '+e(x.sunset)+' &middot; '+e(x.moon.phase)+', '+x.moon.illumination+'% &middot; Moonrise '+e(x.moon.rise||'none')+', moonset '+e(x.moon.set||'none')+'</p>'+
  '<div class="fr-cols"><div><h4>Tides, oceanside</h4><ul>'+tides(x.tides_ocean)+'</ul></div><div><h4>Tides, bayside</h4><ul>'+tides(x.tides_bay)+'</ul></div>'+
  '<div><h4>Solunar (estimate)</h4><p><strong>Major:</strong> '+(s.major.map(e).join(', ')||'none')+'</p><p><strong>Minor:</strong> '+(s.minor.map(e).join(', ')||'none')+'</p></div></div></article>';}).join('');
 document.getElementById('marine').innerHTML=d.marine.map(function(z){return '<div class="fr-zone"><h3>'+e(z.name)+' <span class="small">('+e(z.zone)+')</span></h3>'+z.periods.slice(0,4).map(function(p){return '<p><strong>'+e(p.name)+':</strong> '+e(p.text)+'</p>';}).join('')+'</div>';}).join('')||'<p>Marine forecast not available. See weather.gov.</p>';
}).catch(function(){document.getElementById('updated').textContent=' The latest data could not be loaded.';});
})();
