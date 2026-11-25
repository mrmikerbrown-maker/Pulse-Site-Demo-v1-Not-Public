/* Alpha Pulse guided tour for newcomers. One step at a time: the page is dimmed except the part being explained,
   with a small card beside it (Back / Next). Each page starts with a short "why this page" card.
   Started from the homepage "New to markets?" strip. Each tool page in the tour is opened with ?tour=N
   (1 = Economic Calendar, 2 = Cross-Asset Moves, 3 = Central Bank Pricing, done = where next).
   nav.js loads this file only when the address has ?tour=, so it costs nothing on normal visits.
   To change the wording, edit STEPS and NEXT below. "sel" is the part of the page a "Show me" link points at. */
(function(){
var m=/[?&]tour=([^&#]+)/.exec(location.search);if(!m)return;
var ME=document.currentScript&&document.currentScript.src;
var HUB=ME?new URL(".",ME).href:new URL("/Pulse-Site-Demo-v1-Not-Public/",location.href).href;

var STEPS=[
 {path:"calendar/",name:"Economic Calendar",
  why:"Big economic numbers, like jobs, inflation and growth, are the moments when markets move most. This page tells you what is due, when, and what economists expect.",
  pts:[
   ["#next","<b>Next up</b> shows the next big release, its time (London) and the consensus: the average forecast from economists."],
   ["#chips","<b>Country buttons</b> narrow the list to one economy, such as the US or the UK."],
   ["#dayt","<b>Day buttons</b> pick a day, or the whole week. The page opens on today."],
   ["#seg","<b>Key releases</b> shows only the market movers. Key + medium adds the smaller ones."],
   ["#days","<b>Click any release</b> to see what it measures and why markets care."],
   ["#days","<b>Result</b> appears once a number lands and shows how far it was from the consensus. A big miss is what moves markets."]],
  tip:"Make it a habit: check what is due today, and at what time, before anything else."},
 {path:"cross-asset/",name:"Cross-Asset Moves",
  why:"Stocks, bonds, currencies and commodities on one screen, so you can see the mood of the whole market at a glance, and whether today is a normal day or an unusual one.",
  pts:[
   ["#hl","<b>The headline</b> sums up the day in one sentence."],
   ["#per","<b>Today, 1 week, 1 month, YTD</b> changes the period every number covers."],
   ["#mv","<b>Four popular markets</b>: S&amp;P 500 futures, Gold, the US 10-year yield and EUR/USD, always shown first."],
   ["#un","<b>Unusual moves</b> lists markets moving far more than usual. The × number compares a move with a typical day for that market: 1× is normal, 2× or more is worth a look."],
   ["#grid .card:nth-child(2)","<b>Bond yields</b> are in basis points (0.01% each). They turn green when yields fall and red when they rise."],
   ["#how","<b>How the × number is worked out</b> opens a step-by-step explanation with a live example."]],
  tip:"A move only matters relative to what is normal for that market. A 1% move in a currency is big; in oil it is an ordinary day."},
 {path:"cb-pricing/",name:"Central Bank Pricing",
  why:"Interest rates drive almost everything else in markets. This page shows what traders expect each central bank to do at each meeting, so you can tell when a decision would be a surprise.",
  pts:[
   ["#bank","<b>Pick a central bank</b>: the Fed (US), the ECB (euro area) or the Bank of England."],
   ["#rpstats","<b>The top figures</b> show today's rate and what is priced for the next meeting."],
   ["#rplad","<b>Each row is a meeting.</b> One block is 25bp, a normal-size rate move. Green blocks are cuts (easing), red blocks are hikes (tightening). Part of a block means the market sees it as a maybe."],
   ["#rpview","<b>This meeting</b> shows the move priced at each meeting on its own. <b>Cumulative bp</b> adds them up over time."],
   ["#rpseg","<b>Compare</b> shows where pricing was 1 or 3 weeks ago, so you can see how expectations have shifted."]],
  tip:"If a meeting shows about 25bp of easing priced, a cut is fully expected. Markets react when the bank does something different from what is priced."}
];
var NEXT=[
 ["index-contribution-site/","Index Contribution","Which stocks drove the S&amp;P 500, Nasdaq 100 and Dow today."],
 ["surprises/","Data Surprises","Whether recent economic numbers beat or missed forecasts."],
 ["fed-scenario-planner/","Fed Scenario Planner","What markets did after past Fed decisions, and what a surprise might do."],
 ["glossary/","Glossary","Every market term on the site, explained in plain words."]
];

var raw=decodeURIComponent(m[1]),pg=raw==="done"?STEPS.length+1:parseInt(raw,10),total=STEPS.length;
if(!(pg>=1&&pg<=total+1))return;
function url(i){return i>total?HUB+STEPS[total-1].path+"?tour=done":HUB+STEPS[i-1].path+"?tour="+i}
var startAtEnd=/[?&]at=end/.test(location.search);

var css=
".tour-dim{position:fixed;z-index:9997;pointer-events:none;border-radius:10px;box-shadow:0 0 0 9999px rgba(0,0,0,.55);outline:3px solid var(--pink,#C42424);outline-offset:0;transition:top .25s,left .25s,width .25s,height .25s}"+
".tour-dim.full{inset:0;width:auto!important;height:auto!important;outline:0;box-shadow:none;background:rgba(0,0,0,.45);border-radius:0}"+
".tour-dim[hidden],.tour[hidden],.tour-pill[hidden]{display:none}"+
".tour{position:fixed;z-index:9999;width:340px;max-width:calc(100vw - 24px);background:var(--card,#fff);color:var(--text,#111);border:1px solid var(--line,#ddd);border-radius:14px;box-shadow:0 14px 44px rgba(0,0,0,.35);font-size:14.5px;line-height:1.5}"+
".tour.mid{width:440px;left:50%;top:50%;transform:translate(-50%,-50%)}"+
".tour .th{display:flex;align-items:center;gap:8px;padding:11px 12px 0 16px}"+
".tour .st{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#666);font-weight:600}"+
".tour .dots{display:flex;gap:4px}.tour .dots i{width:6px;height:6px;border-radius:99px;background:var(--line,#ccc)}.tour .dots i.on{background:var(--pink,#C42424)}"+
".tour .hd{margin-left:auto;display:flex}"+
".tour .ib{border:0;background:none;color:var(--muted,#666);font:inherit;font-size:12.5px;padding:4px 6px;border-radius:6px;cursor:pointer}.tour .ib:hover{color:var(--text,#111)}"+
".tour .bd{padding:8px 16px 4px}"+
".tour h2{font-size:18px;margin:0 0 6px;font-weight:700;line-height:1.25;text-transform:none;letter-spacing:normal;color:var(--text,#111);font-family:inherit}"+
".tour p{margin:0 0 10px}"+
".tour .tip{padding:9px 11px;border-radius:9px;background:var(--bg,#f4f4f4);font-size:13.5px}"+
".tour .ft{display:flex;align-items:center;gap:8px;padding:6px 12px 12px}"+
".tour .n{font-size:12.5px;color:var(--muted,#666);margin-left:4px}"+
".tour .btn{display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:13.5px;font-weight:600;padding:7px 13px;border-radius:99px;cursor:pointer;text-decoration:none;border:1px solid var(--line,#ccc);background:none;color:var(--text,#111)}"+
".tour .btn.go{margin-left:auto;background:var(--accent,#111);border-color:var(--accent,#111);color:var(--onaccent,var(--bg,#fff))}"+
".tour .opts{display:grid;gap:8px;margin:0 0 10px}"+
".tour .opts a{display:block;padding:9px 12px;border:1px solid var(--line,#ddd);border-radius:10px;color:var(--text,#111);text-decoration:none}.tour .opts a:hover{border-color:var(--pink,#C42424)}"+
".tour .opts b{display:block;font-size:14px}.tour .opts span{font-size:13px;color:var(--muted,#666)}"+
".tour .arr{position:absolute;width:14px;height:14px;background:var(--card,#fff);border:1px solid var(--line,#ddd);transform:rotate(45deg)}"+
".tour .arr.up{top:-8px;border-right:0;border-bottom:0}.tour .arr.dn{bottom:-8px;border-left:0;border-top:0}"+
".tour-pill{position:fixed;right:16px;bottom:16px;z-index:9999;font:inherit;font-size:13.5px;font-weight:600;padding:9px 15px;border-radius:99px;border:0;background:var(--accent,#111);color:var(--onaccent,var(--bg,#fff));box-shadow:0 8px 24px rgba(0,0,0,.3);cursor:pointer}"+
"@media (max-width:640px){.tour:not(.mid){left:8px!important;right:8px;bottom:8px;top:auto!important;width:auto;max-width:none}.tour .arr{display:none}.tour.mid{width:calc(100vw - 24px)}}"+
"@media (prefers-reduced-motion:reduce){.tour-dim{transition:none}}";
var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);

var dim=document.createElement("div");dim.className="tour-dim";
var box=document.createElement("section");box.className="tour";box.setAttribute("role","dialog");box.setAttribute("aria-label","Site tour");box.setAttribute("data-nogloss","");
var pill=document.createElement("button");pill.className="tour-pill";pill.type="button";pill.hidden=true;
document.body.appendChild(dim);document.body.appendChild(box);document.body.appendChild(pill);

/* Sub-steps on this page: 0 = "why this page" card, then one per point. */
var S=pg<=total?STEPS[pg-1]:null,cards=[],i0;
if(S){cards.push({intro:1});S.pts.forEach(function(p,k){cards.push({sel:p[0],html:p[1],last:k===S.pts.length-1})})}
else cards.push({done:1});
var cur=0,el=null,ph=matchMedia("(max-width:640px)");

function visible(c){if(!c.sel)return true;var e=document.querySelector(c.sel);return !!(e&&!e.hidden&&e.offsetParent)}
function dotsHtml(){var h="";for(var i=1;i<=total;i++)h+='<i class="'+(i<=pg?"on":"")+'"></i>';return h}
function head(label){return '<div class="th"><span class="st">'+label+'</span><span class="dots">'+dotsHtml()+'</span><span class="hd"><button class="ib" type="button" data-a="min" title="Hide the tour so you can use the page">Hide</button><button class="ib" type="button" data-a="end" title="End the tour">End ✕</button></span></div>'}

function render(){
 var c=cards[cur],nPts=cards.length-1,h;
 box.classList.toggle("mid",!c.sel);
 if(c.done){
  var op=NEXT.map(function(o){return '<a href="'+HUB+o[0]+'"><b>'+o[1]+' →</b><span>'+o[2]+'</span></a>'}).join("");
  h=head("Tour complete")+'<div class="bd"><h2>That\'s the basics</h2><p>You now know what is coming up, how markets are moving, and what is expected from central banks. That covers most of what moves markets day to day.</p><p class="st" style="margin-bottom:6px">Where next?</p><div class="opts">'+op+'</div></div><div class="ft"><a class="btn" href="'+url(total)+'&at=end">← Back</a><a class="btn go" href="'+HUB+'">End tour, go home</a></div>';
  pill.textContent="Tour · where next? · Show";
 }else if(c.intro){
  var bk=pg>1?'<a class="btn" href="'+url(pg-1)+'&at=end">← Back</a>':'<a class="btn" href="'+HUB+'">← Home</a>';
  h=head("Tour · page "+pg+" of "+total)+'<div class="bd"><h2>'+S.name+'</h2><p>'+S.why+'</p><p class="n" style="margin:0 0 6px">'+nPts+' quick steps on this page.</p></div><div class="ft">'+bk+'<button class="btn go" type="button" data-a="next">Show me how →</button></div>';
  pill.textContent="Tour · "+S.name+" · Show";
 }else{
  var nx=c.last?(pg<total?"Next page: "+STEPS[pg].name+" →":"Finish →"):"Next →";
  h=head(S.name)+'<div class="bd"><p>'+c.html+'</p>'+(c.last?'<p class="tip"><b>Tip.</b> '+S.tip+'</p>':'')+'</div><div class="ft"><button class="btn" type="button" data-a="back">←</button><span class="n">'+cur+' of '+nPts+'</span><button class="btn go" type="button" data-a="next">'+nx+'</button></div><span class="arr"></span>';
  pill.textContent="Tour · "+S.name+" "+cur+"/"+nPts+" · Show";
 }
 box.innerHTML=h;
 el=c.sel?document.querySelector(c.sel):null;
 if(el&&el.tagName==="DETAILS")el.open=true;
 if(el){
  var r=el.getBoundingClientRect(),vh=innerHeight,top=ph.matches?70:Math.max(70,(vh-Math.min(r.height,vh*.55))/2-60);
  var y=scrollY+r.top-top;
  scrollTo({top:Math.max(0,y),behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});
 }
 place();setTimeout(place,350);setTimeout(place,700);
 var f=box.querySelector(".go");if(f)try{f.focus({preventScroll:true})}catch(e){}
}

function place(){
 if(box.hidden){dim.hidden=true;return}
 dim.hidden=false;
 if(!el){dim.classList.add("full");dim.removeAttribute("style");box.style.left=box.style.top="";return}
 dim.classList.remove("full");
 var r=el.getBoundingClientRect(),p=6,vw=innerWidth,vh=innerHeight;
 var t=Math.max(r.top-p,4),b=Math.min(r.bottom+p,vh-4);
 dim.style.left=(r.left-p)+"px";dim.style.top=t+"px";dim.style.width=(r.width+2*p)+"px";dim.style.height=Math.max(0,b-t)+"px";
 if(ph.matches){box.style.left="";box.style.top="";return}
 var bw=box.offsetWidth,bh=box.offsetHeight,a=box.querySelector(".arr");
 var x=Math.min(Math.max(12,r.left),vw-bw-12),y,dir;
 if(r.bottom+p+14+bh<vh-8){y=r.bottom+p+14;dir="up"}
 else if(r.top-p-14-bh>8){y=r.top-p-14-bh;dir="dn"}
 else{y=vh-bh-16;x=vw-bw-16;dir=""}
 box.style.left=x+"px";box.style.top=y+"px";
 if(a){a.className="arr "+dir;a.style.display=dir?"":"none";a.style.left=Math.min(Math.max(16,r.left+Math.min(r.width/2,60)-x),bw-30)+"px"}
}

function go(d){
 var j=cur+d;
 while(j>0&&j<cards.length&&!visible(cards[j]))j+=d;
 if(j<0)return;
 if(j>=cards.length){location.href=url(pg+1);return}
 cur=j;render();
}
function hide(){box.hidden=true;dim.hidden=true;pill.hidden=false}
function end(){box.hidden=true;dim.hidden=true;pill.hidden=true;try{history.replaceState(null,"",location.pathname+location.hash)}catch(e){}}
box.addEventListener("click",function(e){
 var b=e.target.closest("button");if(!b)return;var a=b.dataset.a;
 if(a==="next")go(1);else if(a==="back")go(-1);else if(a==="min")hide();else if(a==="end")end();
});
pill.onclick=function(){pill.hidden=true;box.hidden=false;render()};
document.addEventListener("keydown",function(e){
 if(box.hidden)return;
 if(e.key==="Escape")hide();
 else if(e.key==="ArrowRight"&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))go(1);
 else if(e.key==="ArrowLeft"&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))go(-1);
});
addEventListener("scroll",function(){requestAnimationFrame(place)},{passive:true});
addEventListener("resize",function(){requestAnimationFrame(place)});
/* Coming back from the next page lands on this page's last step. */
if(startAtEnd&&S){cur=cards.length;go(-1)}else render();
})();
