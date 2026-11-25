/* Alpha Pulse guided tour for newcomers.
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
   ["#grid","<b>The × number</b> compares a move with a typical day for that market. 1× is normal; 2× or more is unusual and worth a look."],
   ["#grid","<b>Bond yields</b> are in basis points (0.01% each). They turn green when yields fall and red when they rise."],
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

var raw=decodeURIComponent(m[1]),n=raw==="done"?STEPS.length+1:parseInt(raw,10);
if(!(n>=1&&n<=STEPS.length+1))return;
function url(i){return i>STEPS.length?HUB+STEPS[STEPS.length-1].path+"?tour=done":HUB+STEPS[i-1].path+"?tour="+i}
function home(){return HUB}

var css=
".tour{position:fixed;right:20px;bottom:20px;z-index:9999;width:360px;max-width:calc(100vw - 32px);max-height:min(78vh,640px);display:flex;flex-direction:column;background:var(--card,#fff);color:var(--text,#111);border:1px solid var(--line,#ddd);border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.28);font-size:14px;line-height:1.45}"+
".tour[hidden]{display:none}"+
".tour .th{display:flex;align-items:center;gap:10px;padding:12px 14px 10px 16px;border-bottom:1px solid var(--line,#ddd)}"+
".tour .st{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#666);font-weight:600}"+
".tour .dots{display:flex;gap:5px;margin-left:2px}.tour .dots i{width:7px;height:7px;border-radius:99px;background:var(--line,#ccc)}.tour .dots i.on{background:var(--pink,#C42424)}"+
".tour .hd{margin-left:auto;display:flex;gap:2px}"+
".tour .ib{border:0;background:none;color:var(--muted,#666);font:inherit;font-size:12.5px;padding:4px 7px;border-radius:6px;cursor:pointer}.tour .ib:hover{color:var(--text,#111);background:var(--bg,#eee)}"+
".tour .bd{padding:12px 16px 4px;overflow:auto}"+
".tour h2{font-size:19px;margin:0 0 6px;font-weight:700;line-height:1.2;text-transform:none;letter-spacing:normal;color:var(--text,#111);font-family:inherit}"+
".tour .why{margin:0 0 12px;color:var(--text2,var(--text,#111))}"+
".tour .lab{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#666);font-weight:600;margin:0 0 6px}"+
".tour ol{margin:0 0 10px;padding:0;list-style:none;counter-reset:t}"+
".tour li{counter-increment:t;position:relative;padding:7px 0 7px 30px;border-top:1px solid var(--line,#ddd)}.tour li:first-child{border-top:0}"+
".tour li:before{content:counter(t);position:absolute;left:0;top:8px;width:20px;height:20px;border-radius:99px;background:var(--text,#111);color:var(--bg,#fff);font-size:11px;font-weight:700;display:grid;place-items:center}"+
".tour .sm{margin-left:6px;border:0;background:none;padding:0;font:inherit;font-size:12.5px;color:var(--accent,#c00);cursor:pointer;white-space:nowrap;text-decoration:underline;text-underline-offset:2px}"+
".tour .tip{margin:0 0 10px;padding:9px 11px;border-radius:9px;background:var(--bg,#f4f4f4);font-size:13.5px}"+
".tour .ft{display:flex;align-items:center;gap:8px;padding:10px 14px 12px;border-top:1px solid var(--line,#ddd)}"+
".tour .btn{display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:13.5px;font-weight:600;padding:8px 13px;border-radius:99px;cursor:pointer;text-decoration:none;border:1px solid var(--line,#ccc);background:none;color:var(--text,#111)}"+
".tour .btn.go{margin-left:auto;background:var(--accent,#c00);border-color:var(--accent,#c00);color:var(--onaccent,var(--bg,#fff))}"+
".tour .btn:hover{filter:brightness(1.08)}"+
".tour .opts{display:grid;gap:8px;margin:0 0 10px}"+
".tour .opts a{display:block;padding:10px 12px;border:1px solid var(--line,#ddd);border-radius:10px;color:var(--text,#111);text-decoration:none}.tour .opts a:hover{border-color:var(--accent,#c00)}"+
".tour .opts b{display:block;font-size:14px}.tour .opts span{font-size:13px;color:var(--muted,#666)}"+
".tour-pill{position:fixed;right:20px;bottom:20px;z-index:9999;display:flex;align-items:center;gap:8px;font:inherit;font-size:13.5px;font-weight:600;padding:9px 15px;border-radius:99px;border:0;background:var(--accent,#c00);color:var(--onaccent,var(--bg,#fff));box-shadow:0 8px 24px rgba(0,0,0,.25);cursor:pointer}"+
".tour-pill[hidden]{display:none}"+
".tour-hi{outline:3px solid var(--pink,#C42424)!important;outline-offset:4px;border-radius:8px;transition:outline-color .3s;scroll-margin-top:80px}"+
"@media (max-width:640px){.tour{left:0;right:0;bottom:0;width:auto;max-width:none;max-height:58vh;border-radius:16px 16px 0 0;border-bottom:0}.tour-pill{right:16px;bottom:16px}.tour h2{font-size:17px}}"+
"@media (prefers-reduced-motion:reduce){.tour-hi{transition:none}}";
var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);

var box=document.createElement("section");box.className="tour";box.setAttribute("role","dialog");box.setAttribute("aria-label","Site tour");box.setAttribute("data-nogloss","");
var pill=document.createElement("button");pill.className="tour-pill";pill.type="button";pill.hidden=true;

var total=STEPS.length,dots="";
for(var i=1;i<=total;i++)dots+='<i class="'+(i<=Math.min(n,total)?"on":"")+'"></i>';
var head='<div class="th"><span class="st">'+(n<=total?"Tour · step "+n+" of "+total:"Tour complete")+'</span><span class="dots">'+dots+'</span><span class="hd"><button class="ib" type="button" data-a="min" title="Hide the tour so you can use the page">Hide</button><button class="ib" type="button" data-a="end" title="End the tour">End ✕</button></span></div>';

if(n<=total){
 var s=STEPS[n-1];
 var li=s.pts.map(function(p,k){return '<li>'+p[1]+' <button class="sm" type="button" data-k="'+k+'">Show me</button></li>'}).join("");
 var nx=n<total?"Next: "+STEPS[n].name+" →":"Finish →";
 var bk=n>1?'<a class="btn" href="'+url(n-1)+'">← Back</a>':'<a class="btn" href="'+home()+'">← Home</a>';
 box.innerHTML=head+'<div class="bd"><h2>'+s.name+'</h2><p class="why">'+s.why+'</p><p class="lab">How to use it</p><ol>'+li+'</ol><p class="tip"><b>Tip.</b> '+s.tip+'</p></div><div class="ft">'+bk+'<a class="btn go" href="'+url(n+1)+'">'+nx+'</a></div>';
 pill.textContent="Tour · step "+n+" of "+total+" · Show";
}else{
 var op=NEXT.map(function(o){return '<a href="'+HUB+o[0]+'"><b>'+o[1]+' →</b><span>'+o[2]+'</span></a>'}).join("");
 box.innerHTML=head+'<div class="bd"><h2>That\'s the basics</h2><p class="why">You now know what is coming up, how markets are moving, and what is expected from central banks. That covers most of what moves markets day to day.</p><p class="lab">Where next?</p><div class="opts">'+op+'</div></div><div class="ft"><a class="btn" href="'+url(total)+'">← Back</a><a class="btn go" href="'+home()+'">End tour, go home</a></div>';
 pill.textContent="Tour · where next? · Show";
}
document.body.appendChild(box);document.body.appendChild(pill);

var lit=null,tm=0;
function show(sel){
 var el=document.querySelector(sel);
 if(!el||el.hidden||!el.offsetParent){return}
 if(el.tagName==="DETAILS")el.open=true;
 if(lit)lit.classList.remove("tour-hi");
 lit=el;el.classList.add("tour-hi");
 var phone=matchMedia("(max-width:640px)").matches;
 if(phone){box.hidden=true;pill.hidden=false}
 el.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:phone?"start":"center"});
 clearTimeout(tm);tm=setTimeout(function(){el.classList.remove("tour-hi");lit=null},phone?6000:4000);
}
function tidy(){try{history.replaceState(null,"",location.pathname+location.hash)}catch(e){}}
box.addEventListener("click",function(e){
 var b=e.target.closest("button");if(!b)return;
 if(b.dataset.k!=null)show(STEPS[n-1].pts[+b.dataset.k][0]);
 else if(b.dataset.a==="min"){box.hidden=true;pill.hidden=false}
 else if(b.dataset.a==="end"){box.hidden=true;pill.hidden=true;if(lit)lit.classList.remove("tour-hi");tidy()}
});
pill.onclick=function(){pill.hidden=true;box.hidden=false};
document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!box.hidden){box.hidden=true;pill.hidden=false}});
})();
