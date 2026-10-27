(function(){
var BITE={
1:{off:"Sailfish (peak season), kingfish, blackfin tuna, wahoo",reef:"Yellowtail snapper, mutton snapper, cero mackerel. Shallow-water grouper closed Jan-Apr",bay:"Redfish, sea trout, snook on warm days (snook harvest closed)",dock:"Snapper, jacks, sheepshead, barracuda"},
2:{off:"Sailfish, kingfish, blackfin tuna",reef:"Yellowtail, mutton snapper, cero mackerel. Grouper closed",bay:"Redfish, trout, early tarpon on warm spells",dock:"Sheepshead, snapper, jacks"},
3:{off:"Sailfish, early mahi, blackfin tuna, cobia",reef:"Yellowtail, mutton snapper (pre-spawn). Grouper closed",bay:"Tarpon arriving, redfish, permit on the flats",dock:"Snapper, jacks, tarpon at the bridges at night"},
4:{off:"Mahi, blackfin tuna, sailfish tapering",reef:"Mutton snapper, yellowtail. Grouper closed through Apr 30",bay:"Tarpon (peak starts), bonefish, permit",dock:"Tarpon at the bridges, snapper"},
5:{off:"Mahi (peak), blackfin tuna, wahoo",reef:"Yellowtail, mutton, grouper reopens May 1",bay:"Tarpon (peak), bonefish, permit",dock:"Tarpon, mangrove snapper, jacks"},
6:{off:"Mahi, blackfin tuna, swordfish (day drops)",reef:"Mangrove and yellowtail snapper, grouper",bay:"Tarpon, bonefish, snook (Atlantic harvest closed Jun-Aug)",dock:"Mangrove snapper (evening), jacks"},
7:{off:"Mahi, blackfin tuna, swordfish",reef:"Mangrove snapper spawn, yellowtail, grouper",bay:"Bonefish, permit, snook (catch-and-release)",dock:"Mangrove snapper, barracuda. Lobster mini-season late July"},
8:{off:"Mahi, swordfish, blackfin tuna",reef:"Yellowtail, mangrove snapper, grouper. Spiny lobster season opens Aug 6",bay:"Bonefish, redfish, snook",dock:"Snapper, jacks, barracuda"},
9:{off:"Mahi tapering, wahoo, blackfin tuna",reef:"Yellowtail, mangrove snapper, grouper",bay:"Snook (harvest reopens Sept 1), redfish, bonefish",dock:"Snook at night, snapper"},
10:{off:"Wahoo, blackfin tuna, kingfish, first sailfish",reef:"Yellowtail, mutton snapper, grouper, hogfish",bay:"Redfish, snook, sea trout, bonefish",dock:"Snapper, snook, jacks, barracuda"},
11:{off:"Sailfish (season starts), kingfish, wahoo, blackfin tuna",reef:"Yellowtail, grouper, cero mackerel, hogfish",bay:"Redfish, snook, sea trout",dock:"Snapper, jacks, ladyfish, Spanish mackerel"},
12:{off:"Sailfish (peak), kingfish, wahoo, blackfin tuna",reef:"Yellowtail, grouper (closes Jan 1), cero mackerel",bay:"Redfish, trout, snook (Atlantic harvest closes Dec 15)",dock:"Sheepshead, snapper, jacks"}};
var M=["January","February","March","April","May","June","July","August","September","October","November","December"];
var m=new Date().getMonth(), b=BITE[m+1];
document.getElementById('month').textContent=M[m];
document.getElementById('bite').innerHTML=[["Offshore (Gulf Stream)",b.off],["Reef and wrecks",b.reef],["Bay and backcountry",b.bay],["Bridges, docks and shore",b.dock]].map(function(x){return '<div class="card"><h3>'+x[0]+'</h3><p>'+x[1]+'</p></div>';}).join('');
function e(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function tides(a){return a.length?a.map(function(t){return '<li><strong>'+t.type+'</strong> '+e(t.time)+' <span class="small">('+t.ft.toFixed(1)+' ft)</span></li>';}).join(''):'<li>Not available</li>';}
fetch('data/fishing.json',{cache:'no-cache'}).then(function(r){return r.json();}).then(function(d){
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
