/* Alpha Pulse guided tour for newcomers. One step at a time: the page is dimmed except the part being explained,
   with a small card beside it (Back / Next). Each page starts with a short "why this page" card.
   Starter tour, from the homepage "New to markets?" strip: ?tour=N (1 = Economic Calendar,
   2 = Cross-Asset Moves, 3 = Central Bank Pricing, done = where next).
   Every page with a guide also gets a "How this page works" button under its title; ?guide opens it straight away.
   nav.js loads this file on every page.
   To change the wording, edit STEPS and NEXT below. "sel" is the part of the page a "Show me" link points at. */
(function(){
var ME=document.currentScript&&document.currentScript.src;
var HUB=ME?new URL(".",ME).href:new URL("/Pulse-Site-Demo-v1-Not-Public/",location.href).href;

var STEPS=[
 {path:"calendar/",name:"Economic Calendar",
  why:"Big economic numbers, like jobs, inflation and growth, are the moments when markets move most. This page tells you what is due, when, and what economists expect.",
  pts:[
   ["#next","<b>Next up</b> shows the next big release, its time (London) and the consensus: the average forecast from economists."],
   ["#chips","<b>Country buttons</b> narrow the list to one economy, such as the US or the UK."],
   ["#dayt","<b>Day buttons</b> pick a day from the last five working days to the next five, or all of them. The page opens on today."],
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

/* Guides for every other page. Each opens with a "why" card, then one highlighted step at a time.
   Opened from the tour's "Where next?" list (?guide=tour) or the "How this page works" button under each page title. */
var MORE=[
 {path:"index-contribution-site/",name:"Index Contribution",
  why:"An index like the S&amp;P 500 can fall even when most of its shares rise, because a few giant companies carry most of the weight. This page shows which stocks actually moved the index.",
  pts:[
   [".tabs","<b>Pick an index</b>: the S&amp;P 500, Nasdaq 100 or Dow."],
   ["#per","<b>Pick a period</b>: today, this week, this month or the year so far."],
   ["#strip","<b>The summary</b> gives the index move and how many stocks rose and fell."],
   ["#fall","<b>Where the move came from</b>: each bar is a stock's contribution in index points. Bigger companies count for more."],
   ["#map","<b>The market map</b> shows every stock, sized by its weight and coloured by its move, grouped by sector."],
   [".views","<b>Weights &amp; stock lookup</b> shows how much each company counts in the index, and lets you look one up."]],
  tip:"When the index moves a lot, check whether it was broad (most stocks) or narrow (a handful of giants). Narrow moves are more fragile."},
 {path:"earnings-moves/",name:"Earnings Moves",
  why:"Share prices often jump or slump when a company reports results. Options traders put a price on how big that move might be, so you can see in advance which reports could rock the market.",
  pts:[
   ["#tabs","<b>Coming up</b> lists the next reports, <b>Latest results</b> shows what just happened, and <b>Scorecard</b> tracks how well options priced past moves."],
   ["#q","<b>Find a stock</b> by its ticker or name."],
   ["#upc","<b>Each row</b> shows the move options are pricing (±%) next to how far the shares moved after past reports. Click a row for the detail."]],
  tip:"If the options price a smaller move than the shares usually make, the market may be too relaxed about that report."},
 {path:"vol-monitor/",name:"Volatility Monitor",
  why:"Volatility is how much traders expect prices to swing. When it jumps, markets are nervous: moves get bigger and faster. This page shows how nervous each market is today, against its own past year.",
  pts:[
   ["#dialc","<b>Market stress today</b> rolls the option-based gauges into one number from 0 (calmest day of the past year) to 100 (most stressed)."],
   ["#hlbox","<b>The headline</b> says which gauges stand out, and turns VIX into the daily S&amp;P 500 swing traders are pricing."],
   [".g","<b>Each gauge</b> shows today's level, where it sits between its 1-year low and high, and the daily move it implies. Green is calm, red is stressed."],
   ["#heath","<b>The heat map</b> shows each gauge day by day over the past 3 months, so you can see stress building or fading."],
   ["#how","<b>How the numbers are worked out</b> explains every figure, with a live example. Currencies use past moves (realised vol), not option prices."]],
  tip:"High volatility is not a signal to buy or sell. It means bigger swings either way, so positions can move against you faster."},
 {path:"yield-curve/",name:"Yield Curves",
  why:"A yield curve plots what a government pays to borrow for different lengths of time. Its shape tells you what markets expect for interest rates and growth.",
  pts:[
   ["#cty","<b>Pick a country</b>: the US, Germany or the UK."],
   ["#hl","<b>The headline</b> sums up how the curve has moved."],
   ["#cv","<b>The chart</b> runs from short-term yields on the left to long-term on the right."],
   ["#cmp","<b>Compare</b> lays last week's or last month's curve over today's, so you can see what changed."],
   ["#sp","<b>Spreads</b> track the gap between two yields over time. A negative 2s10s spread (an inverted curve) has often come before recessions."]],
  tip:"Short-term yields follow central bank expectations; long-term yields reflect growth, inflation and risk."},
 {path:"cftc-positioning/",name:"Speculator Positioning",
  why:"Every week the US regulator (the CFTC) publishes how hedge funds and other speculators are betting in futures markets. When everyone is on the same side, a sharp reversal becomes more likely.",
  pts:[
   ["#top","<b>The most extreme bets</b> right now, measured against the last three years."],
   ["#grp","<b>Pick a group</b>: currencies, rates, stock indices or commodities."],
   ["#who","<b>Pick who</b>: different kinds of speculators."],
   ["#rows","<b>Each row</b> shows the net long or short position and how extreme it is. Near 0% or 100% means close to a three-year low or high."]],
  tip:"The data is collected on Tuesday and published on Friday, so it is a few days old by the time you see it."},
 {path:"clock/",name:"Market Clock",
  why:"Markets do not move evenly through the day. Most of the action comes in a few hours, often around data releases and the open of big stock markets.",
  pts:[
   ["#wd","<b>Pick a day of the week</b>, or all days."],
   ["#ev","<b>Event days</b> narrows it to days with a big release, such as US jobs data."],
   ["#tz","<b>Time zone</b> switches the hours to where you are."],
   ["#plot","<b>The chart</b> shows the average size of the move in each hour. Taller means busier."]],
  tip:"If you can only watch markets for an hour, this page tells you which hour matters most."},
 {path:"release-playback/",name:"Release Playback",
  why:"Big US numbers like inflation and jobs can move every market at once. This page replays what happened after past releases, so you can see how big the first reaction tends to be and whether it usually lasts.",
  pts:[
   ["#relS","<b>Pick a release</b>: CPI inflation, jobs, core PCE, retail sales, ISM services or GDP."],
   ["#mktS","<b>Pick a market</b>: S&amp;P 500 futures, the 10-year Treasury yield, the dollar or gold."],
   ["#hl","<b>The headline</b> says how often the market rose or fell on the day when the number came in above or below forecast."],
   ["#one","<b>The latest release</b>, replayed every 5 minutes on the day, then over the next 10 trading days against the typical path."],
   ["#g3","<b>What happened next</b>: every past release split into above forecast, in line and below forecast, and how often the first move kept going, held or faded."],
   ["#tbody","<b>Every release</b> since 2015. Click one to replay it at the top."]],
  tip:"A surprise of the same size doesn't always get the same reaction: what else is going on that day matters too."},
 {path:"surprises/",name:"Data Surprises",
  why:"Markets do not react to an economic number itself, only to how far it lands from what was expected. This page lets you play with that gap and see how markets usually respond.",
  pts:[
   ["#tabs","<b>Pick a release</b>, such as US jobs or inflation."],
   ["#ctl","<b>Move the sliders</b>: what was expected, and what actually came out."],
   ["#presets","<b>Presets</b> load real past releases."],
   ["#grid","<b>The reaction</b> shows how currencies, bonds and stocks typically move after a surprise that size."]],
  tip:"A number can be strong and still make markets fall, if traders were expecting even stronger."},
 {path:"economy-thermometer/",name:"Economy Thermometer",
  why:"Central banks raise rates when an economy runs hot and cut when it runs cold. This page shows where each major economy sits, from a handful of key data series.",
  pts:[
   ["#ov","<b>Each country</b> is placed from cold to hot. Tap one for the detail."],
   ["#dt","<b>The detail</b> shows which numbers are running hot or cold."],
   ["#tab-time","<b>Over time</b> shows how each economy has warmed up or cooled down."]],
  tip:"A hot economy usually means higher rates for longer; a cold one means cuts are more likely."},
 {path:"central-banks/",name:"Central Banks Overview",
  why:"Interest rates set by central banks drive borrowing costs, currencies and stock prices. This page shows where every major central bank stands and when it meets next.",
  pts:[
   ["#next","<b>Next up</b>: the next central bank meeting and when it is."],
   ["#tbl","<b>The table</b> lists each bank's rate and what it did last time."],
   ["#sort","<b>Sort</b> the table by rate, last move or next meeting."],
   ["#cal","<b>The calendar</b> shows upcoming meetings."]],
  tip:"For what markets expect at the next meeting, see Central Bank Pricing."},
 {path:"fed-scenario-planner/",name:"Fed Scenario Planner",
  why:"What matters at a Fed meeting is not the decision itself but how it compares with what markets have priced. This page shows how markets reacted on past Fed days to a surprise of the size you pick.",
  pts:[
   ["#dec","<b>Pick a decision</b>: hold, cut or hike."],
   ["#tone","<b>Pick the message</b>: hawkish (leaning to higher rates), neutral or dovish (leaning to lower rates)."],
   ["#verdict","<b>The verdict</b> says how big a surprise that would be against current pricing."],
   ["#rows","<b>Market reactions</b> show what stocks, yields, the dollar and gold did on past Fed days like it."]],
  tip:"A cut that was fully expected can still lift the dollar, if the message sounds less dovish than hoped."},
 {path:"glossary/",name:"Glossary",
  why:"Every market term used on the site, in plain English. Words with a dotted underline anywhere on the site show their meaning when you hover or tap.",
  pts:[
   ["#q","<b>Search</b> for any term."],
   ["#chips","<b>Topics</b> narrow the list, for example to central banks or bonds."],
   ["#out","<b>Each entry</b> gives a plain meaning. Tap the link symbol to share it."]],
  tip:"Look out for dotted underlines on every page: tap one for a quick definition."}
];
var NEXT=[
 ["index-contribution-site/","Index Contribution","Which stocks drove the S&amp;P 500, Nasdaq 100 and Dow today."],
 ["surprises/","Data Surprises","Whether recent economic numbers beat or missed forecasts."],
 ["fed-scenario-planner/","Fed Scenario Planner","What markets did after past Fed decisions, and what a surprise might do."],
 ["glossary/","Glossary","Every market term on the site, explained in plain words."]
];


var ALL=STEPS.concat(MORE),total=STEPS.length;
function here(g){return location.pathname.indexOf(new URL(g.path,HUB).pathname)===0}
var G=null;for(var gi=0;gi<ALL.length;gi++)if(here(ALL[gi])){G=ALL[gi];break}
var qs=location.search,mt=/[?&]tour=([^&#]+)/.exec(qs),mg=/[?&]guide(=([^&#]*))?/.exec(qs);
var mode=null,pg=0,fromTour=false;
if(mt){var raw=decodeURIComponent(mt[1]);pg=raw==="done"?total+1:parseInt(raw,10);if(pg>=1&&pg<=total+1)mode="tour"}
else if(mg&&G){mode="guide";fromTour=mg[2]==="tour"}
function url(i){return i>total?HUB+STEPS[total-1].path+"?tour=done":HUB+STEPS[i-1].path+"?tour="+i}
var startAtEnd=/[?&]at=end/.test(qs);

var css=
".tour-dim{position:fixed;z-index:9997;pointer-events:none;border-radius:10px;box-shadow:0 0 0 9999px rgba(0,0,0,.55);outline:3px solid var(--pink,#C42424);outline-offset:0;transition:top .25s,left .25s,width .25s,height .25s}"+
".tour-dim.full{inset:0;width:auto!important;height:auto!important;outline:0;box-shadow:none;background:rgba(0,0,0,.45);border-radius:0}"+
".tour-dim[hidden],.tour[hidden],.tour-pill[hidden]{display:none}"+
".tour{position:fixed;z-index:9999;width:340px;max-width:calc(100vw - 24px);background:var(--card,#fff);color:var(--text,#111);border:1px solid var(--line,#ddd);border-radius:14px;box-shadow:0 14px 44px rgba(0,0,0,.35);font-size:14.5px;line-height:1.5}"+
".tour.mid{width:440px;left:50%;top:50%;transform:translate(-50%,-50%)}"+
".tour .th{display:flex;white-space:nowrap;align-items:center;gap:8px;padding:11px 12px 0 16px}"+
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
".tour-help{display:inline-flex;align-self:flex-start;width:fit-content;align-items:center;gap:6px;margin:0 0 14px;font:inherit;font-size:13px;font-weight:600;padding:5px 12px 5px 8px;border-radius:99px;border:1px solid var(--line,#ccc);background:var(--card,#fff);color:var(--text,#111);cursor:pointer}.tour-help:hover{border-color:var(--pink,#C42424)}.tour-help i{font-style:normal;width:18px;height:18px;border-radius:99px;background:var(--pink,#C42424);color:#fff;font-size:11px;display:grid;place-items:center}"+
"@media (max-width:640px){.tour:not(.mid){left:8px!important;right:8px;bottom:8px;top:auto!important;width:auto;max-width:none}.tour .arr{display:none}.tour.mid{width:calc(100vw - 24px)}}"+
"@media (prefers-reduced-motion:reduce){.tour-dim{transition:none}}";
var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);

var dim,box,pill,cards=[],cur=0,el=null,ph=matchMedia("(max-width:640px)"),S=null;
function build(){
 if(box)return;
 dim=document.createElement("div");dim.className="tour-dim";dim.hidden=true;
 box=document.createElement("div");box.className="tour";box.setAttribute("role","dialog");box.setAttribute("aria-label","Page guide");box.setAttribute("data-nogloss","");
 pill=document.createElement("button");pill.className="tour-pill";pill.type="button";pill.hidden=true;
 document.body.appendChild(dim);document.body.appendChild(box);document.body.appendChild(pill);
 box.addEventListener("click",function(e){
  var b=e.target.closest("button");if(!b)return;var a=b.dataset.a;
  if(a==="next")go(1);else if(a==="back")go(-1);else if(a==="min")hide();else if(a==="end"||a==="close")end();
 });
 pill.onclick=function(){pill.hidden=true;box.hidden=false;render()};
 document.addEventListener("keydown",function(e){
  if(box.hidden)return;var t=document.activeElement&&document.activeElement.tagName;
  if(e.key==="Escape")hide();
  else if(e.key==="ArrowRight"&&!/INPUT|TEXTAREA|SELECT/.test(t))go(1);
  else if(e.key==="ArrowLeft"&&!/INPUT|TEXTAREA|SELECT/.test(t))go(-1);
 });
 addEventListener("scroll",function(){requestAnimationFrame(place)},{passive:true});
 addEventListener("resize",function(){requestAnimationFrame(place)});
}
function visible(c){if(!c.sel)return true;var e=document.querySelector(c.sel);return !!(e&&!e.hidden&&e.getClientRects().length)}
function dotsHtml(){if(mode!=="tour")return "";var h="";for(var i=1;i<=total;i++)h+='<i class="'+(i<=pg?"on":"")+'"></i>';return h}
function head(label){return '<div class="th"><span class="st">'+label+'</span><span class="dots">'+dotsHtml()+'</span><span class="hd"><button class="ib" type="button" data-a="min" title="Hide the guide so you can use the page">Hide</button><button class="ib" type="button" data-a="end" title="Close the guide">End ✕</button></span></div>'}

function render(){
 var c=cards[cur],nPts=S?S.pts.length:0,h;
 box.classList.toggle("mid",!c.sel);
 if(c.done){
  op=NEXT.map(function(o){return '<a href="'+HUB+o[0]+'?guide=tour"><b>'+o[1]+' →</b><span>'+o[2]+'</span></a>'}).join("");
  h=head("Tour complete")+'<div class="bd"><h2>That\'s the basics</h2><p>You now know what is coming up, how markets are moving, and what is expected from central banks. That covers most of what moves markets day to day.</p><p class="st" style="margin-bottom:6px">Where next? Each one opens with its own short guide.</p><div class="opts">'+op+'</div></div><div class="ft"><a class="btn" href="'+url(total)+'&at=end">← Back</a><a class="btn go" href="'+HUB+'">End tour, go home</a></div>';
  pill.textContent="Tour · where next? · Show";
 }else if(c.fin){
  h=head(S.name)+'<div class="bd"><h2>That\'s '+S.name+'</h2><p>You can replay this guide any time with the <b>How this page works</b> button under the page title.</p></div><div class="ft">'+(fromTour?'<a class="btn" href="'+url(total+1)+'">← Where next?</a>':'<button class="btn" type="button" data-a="back">←</button>')+'<button class="btn go" type="button" data-a="close">Done</button></div>';
  pill.textContent=S.name+" guide · Show";
 }else if(c.intro){
  var bk=mode==="tour"?(pg>1?'<a class="btn" href="'+url(pg-1)+'&at=end">← Back</a>':'<a class="btn" href="'+HUB+'">← Home</a>'):(fromTour?'<a class="btn" href="'+url(total+1)+'">← Where next?</a>':'');
  h=head(mode==="tour"?"Tour · page "+pg+" of "+total:"How this page works")+'<div class="bd"><h2>'+S.name+'</h2><p>'+S.why+'</p><p class="n" style="margin:0 0 6px">'+nPts+' quick steps on this page.</p></div><div class="ft">'+bk+'<button class="btn go" type="button" data-a="next">Show me how →</button></div>';
  pill.textContent=S.name+" guide · Show";
 }else{
  var nx=c.last?(mode==="tour"?(pg<total?"Next page: "+STEPS[pg].name+" →":"Finish →"):"Next →"):"Next →";
  h=head(S.name)+'<div class="bd"><p>'+c.html+'</p>'+(c.last?'<p class="tip"><b>Tip.</b> '+S.tip+'</p>':'')+'</div><div class="ft"><button class="btn" type="button" data-a="back">←</button><span class="n">'+cur+' of '+nPts+'</span><button class="btn go" type="button" data-a="next">'+nx+'</button></div><span class="arr"></span>';
  pill.textContent=S.name+" "+cur+"/"+nPts+" · Show";
 }
 box.innerHTML=h;
 el=c.sel?document.querySelector(c.sel):null;
 if(el&&el.tagName==="DETAILS")el.open=true;
 if(el){
  var r=el.getBoundingClientRect(),vh=innerHeight,top=ph.matches?70:Math.max(70,(vh-Math.min(r.height,vh*.55))/2-60);
  scrollTo({top:Math.max(0,scrollY+r.top-top),behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});
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
 if(j>=cards.length){if(mode==="tour")location.href=url(pg+1);else end();return}
 cur=j;render();
}
function hide(){box.hidden=true;dim.hidden=true;pill.hidden=false}
function end(){box.hidden=true;dim.hidden=true;pill.hidden=true;try{history.replaceState(null,"",location.pathname+location.hash)}catch(e){}}
function start(g,m){
 build();S=g;mode=m||mode;cards=[];
 if(!S){cards.push({done:1})}
 else{cards.push({intro:1});S.pts.forEach(function(p,k){cards.push({sel:p[0],html:p[1],last:k===S.pts.length-1})});if(mode!=="tour")cards.push({fin:1})}
 box.hidden=false;pill.hidden=true;cur=0;
 if(startAtEnd&&S&&mode==="tour"){startAtEnd=false;cur=cards.length;go(-1)}else render();
}

/* "How this page works" button under the page title, on every page that has a guide. */
if(G){
 var h1=document.querySelector("main h1, .wrap h1, h1");
 if(h1&&!document.querySelector(".tour-help")){
  var hb=document.createElement("button");hb.type="button";hb.className="tour-help";hb.innerHTML="<i>?</i>How this page works";
  hb.onclick=function(){fromTour=false;start(G,"guide")};
  var sub=h1.nextElementSibling&&/\bsub\b/.test(h1.nextElementSibling.className)?h1.nextElementSibling:h1;
  sub.insertAdjacentElement("afterend",hb);
 }
}
if(mode==="tour")start(pg<=total?STEPS[pg-1]:null,"tour");
else if(mode==="guide")start(G,"guide");
})();
