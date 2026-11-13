/* Shared top bar for every page of the Alpha Pulse site (hub repo Pulse-Site-Demo-v1-Not-Public).
   A page loads it with one line in <head>:  <script src="/Pulse-Site-Demo-v1-Not-Public/nav.js" defer></script>
   Links to the hub's own pages (Home, Market Clock, Data Surprises, Glossary) are worked out from where this file
   is loaded from (HUB below), so renaming the hub repo again only needs the <script> line on each page changing.
   It puts the same full-width bar at the top of the page: Alpha Pulse logo (links home), a link to every tool,
   and the page's own sun/moon button (moved into the bar). On narrow screens the links fold into a menu button.
   The page's own logo row is hidden so there is only one header.
   To add a tool to every page, add one line to TOOLS below. NAME is the site name used for screen readers; the visible name is the logo itself. */
(function(){
var ME=document.currentScript&&document.currentScript.src;
var HUB=ME?new URL(".",ME).pathname:"/Pulse-Site-Demo-v1-Not-Public/";
var NAME="Alpha Pulse";
var TOOLS=[
 ["Home",HUB],
 ["This week",HUB+"calendar/"],
 ["Markets",[
  ["Index Contribution",HUB+"index-contribution-site/","Which stocks moved the S&amp;P 500, Nasdaq 100 and Dow"],
  ["Market Clock",HUB+"clock/","When markets open, close and move most"]
 ]],
 ["Economy",[
  ["Data Surprises",HUB+"surprises/","How releases landed against expectations"],
  ["Economy Thermometer",HUB+"economy-thermometer/","Is each G10 economy hot or cold?"],
  ["Central banks overview",HUB+"central-banks/","Every G10 policy rate, last move and next meeting"],
  ["Central bank pricing",HUB+"cb-pricing/","Tightening or easing priced for each Fed, ECB and BoE meeting"],
  ["Fed scenario planner",HUB+"fed-scenario-planner/","Pick the next Fed outcome and see how markets reacted before"]
 ]],
 ["Glossary",HUB+"glossary/"]
];
/* A top-level item is ["Label",HUB+"path/"]; a dropdown is ["Label",[["Name",HUB+"path/","one-line description"],...]].
   A child with an empty path shows greyed out as "coming soon". */
var LOGO=HUB+"brand/logo/bar-paper.svg",LOGO_L=HUB+"brand/logo/bar-near-black.svg"; /* PLACEHOLDER logo files: swap the SVGs in brand/logo/, keep the names */
window.NQ_TOOLS=TOOLS;
var here=location.pathname.replace(/index\.html$/,"");
function isHere(h){return h===HUB?here===HUB:here.indexOf(h)===0}
var F="'AP Display',ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";
var css=
".nq-hd{display:block;border-bottom:1px solid var(--line);background:var(--bg);position:relative;z-index:40;margin-bottom:18px}"+
".nq-in{max-width:1240px;margin:0 auto;display:flex;align-items:center;gap:14px;padding:14px 16px 12px}"+
".nq-br{display:flex;align-items:center;gap:12px;flex:none;text-decoration:none;margin-right:auto}"+
".nq-br img{display:block;height:26px;width:auto;margin:0}"+
".nq-br .nq-lt,:root.light .nq-br .nq-dk{display:none}:root.light .nq-br .nq-lt{display:block}"+
".nq-ln{display:flex;gap:2px;flex:none}"+
".nq-ln a,.nq-p a{font:500 14px/1.2 "+F+";color:var(--text2);text-decoration:none;padding:8px 9px;border-radius:8px;white-space:nowrap}"+
".nq-ln a:hover,.nq-p a:hover{background:var(--card);color:var(--text)}"+
".nq-ln a[aria-current]{color:var(--text);background:var(--card);box-shadow:inset 0 0 0 1px var(--line)}"+
".nq-g{position:relative;display:flex}"+
".nq-gb{appearance:none;display:inline-flex;align-items:center;gap:5px;font:500 14px/1.2 "+F+";color:var(--text2);background:none;border:0;padding:8px 9px;border-radius:8px;cursor:pointer;white-space:nowrap}"+
".nq-gb svg{opacity:.7;transition:transform .15s}.nq-gb[aria-expanded=true] svg{transform:rotate(180deg)}"+
".nq-gb:hover,.nq-gb[aria-expanded=true]{background:var(--card);color:var(--text)}"+
".nq-gb[aria-current]{color:var(--text);background:var(--card);box-shadow:inset 0 0 0 1px var(--line)}"+
".nq-dd{display:none;position:absolute;top:calc(100% + 6px);right:0;min-width:250px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px;box-shadow:0 12px 32px rgba(0,0,0,.35);z-index:60}"+
":root.light .nq-dd{box-shadow:0 12px 32px rgba(11,13,20,.14)}"+
".nq-g.nq-on .nq-dd{display:block}"+
".nq-dd::before{content:'';position:absolute;left:0;right:0;top:-8px;height:8px}"+
".nq-ln .nq-di{display:block;padding:9px 10px;border-radius:8px;white-space:normal}"+
".nq-di b{display:block;font:500 14px/1.25 "+F+";color:var(--text)}"+
".nq-di small{display:block;font:400 12px/1.35 "+F+";color:var(--muted);margin-top:3px}"+
".nq-ln .nq-di:hover,.nq-ln .nq-di[aria-current]{background:var(--bg);box-shadow:none}"+
".nq-di[aria-current] b{color:var(--accent)}"+
".nq-soon{opacity:.55;cursor:default}"+
".nq-ph{font:600 11px/1 "+F+";letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:16px 4px 6px}"+
".nq-p .nq-pc{padding-left:14px}"+
".nq-p span.nq-pc{font:500 15px/1.2 "+F+";color:var(--muted);padding:12px 4px 12px 14px;border-bottom:1px solid var(--line)}"+
".nq-b{display:none;appearance:none;align-items:center;justify-content:center;width:30px;height:30px;padding:0;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text2);cursor:pointer;flex:none}"+
".nq-b:hover,.nq-b[aria-expanded=true]{color:var(--text);border-color:var(--accent)}"+
".nq-b svg{width:16px;height:16px}"+
".nq-th{display:flex;flex:none}.nq-th>*{margin:0!important}"+
".nq-p{display:none;flex-direction:column;padding:4px 16px 12px;max-width:1100px;margin:0 auto}"+
".nq-p a{padding:12px 4px;border-radius:0;border-bottom:1px solid var(--line);font-size:15px}"+
".nq-p a:last-child{border-bottom:0}"+
".nq-p a[aria-current]{color:var(--text);font-weight:700}"+
".nq-hd.nq-n .nq-ln{display:none}"+
".nq-hd.nq-n .nq-b{display:inline-flex}"+
".nq-hd.nq-n.nq-o .nq-p{display:flex;border-top:1px solid var(--line)}"+
"@media (max-width:520px){.nq-br img{height:23px}.nq-in{gap:10px}}"+
".nq-gone{display:none!important}";
function build(){
 if(document.querySelector(".nq-hd"))return;
 // Glossary words get a dotted underline with a pop-up definition on every page (see glossary.js).
 if(!window.NQG&&!document.querySelector('script[src$="glossary.js"]')){var gs=document.createElement("script");gs.src=HUB+"glossary.js";gs.defer=true;document.head.appendChild(gs)}
 var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);
 function cur(h){return h&&isHere(h)?' aria-current="page"':""}
 var CHEV='<svg viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><path d="M2 3.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
 var links=TOOLS.map(function(t,gi){
  if(typeof t[1]==="string")return '<a href="'+t[1]+'"'+cur(t[1])+">"+t[0]+"</a>";
  var on=t[1].some(function(c){return c[1]&&isHere(c[1])});
  return '<span class="nq-g"><button type="button" class="nq-gb" aria-expanded="false" aria-haspopup="true"'+(on?' aria-current="page"':"")+">"+t[0]+CHEV+'</button><div class="nq-dd">'+
   t[1].map(function(c){return c[1]?'<a class="nq-di" href="'+c[1]+'"'+cur(c[1])+"><b>"+c[0]+"</b><small>"+c[2]+"</small></a>":'<span class="nq-di nq-soon"><b>'+c[0]+"</b><small>"+c[2]+"</small></span>"}).join("")+"</div></span>"}).join("");
 var plinks=TOOLS.map(function(t){
  if(typeof t[1]==="string")return '<a href="'+t[1]+'"'+cur(t[1])+">"+t[0]+"</a>";
  return '<div class="nq-ph">'+t[0]+"</div>"+t[1].map(function(c){return c[1]?'<a class="nq-pc" href="'+c[1]+'"'+cur(c[1])+">"+c[0]+"</a>":'<span class="nq-pc nq-soon">'+c[0]+" · coming soon</span>"}).join("")}).join("");
 var hd=document.createElement("header");hd.className="nq-hd";
 hd.innerHTML='<div class="nq-in"><a class="nq-br" href="'+HUB+'" aria-label="'+NAME+' home"><img class="nq-dk" alt="'+NAME+'" src="'+LOGO+'"><img class="nq-lt" alt="" src="'+LOGO_L+'"></a>'+
  '<nav class="nq-ln" aria-label="Tools">'+links+'</nav>'+
  '<button class="nq-b" type="button" aria-expanded="false" aria-label="Menu"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M2.5 4h11M2.5 8h11M2.5 12h11"/></svg></button>'+
  '<span class="nq-th"></span></div><nav class="nq-p" aria-label="Tools">'+plinks+"</nav>";
 // Move the page's own sun/moon button into the bar, so its own behaviour (e.g. redrawing charts) is kept.
 var th=document.getElementById("theme"),slot=hd.querySelector(".nq-th");
 if(th){var oldTop=th.closest(".top");slot.appendChild(th)}
 else{th=document.createElement("button");th.type="button";th.className="theme";th.setAttribute("aria-label","Switch light or dark");
  th.innerHTML='<svg class="i-sun" viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="3"/><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1 1M11.6 11.6l1 1M3.4 12.6l1-1M11.6 4.4l1-1"/></svg><svg class="i-moon" viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M13.5 9.6A5.6 5.6 0 0 1 6.4 2.5a5.6 5.6 0 1 0 7.1 7.1z"/></svg>';th.id="theme";
  th.onclick=function(){var l=document.documentElement.classList.toggle("light");try{localStorage.setItem("ict-theme",l?"light":"dark")}catch(e){}};slot.appendChild(th)}
 // Hide the page's own logo row; keep anything else in it (e.g. the index tracker's page tabs).
 document.querySelectorAll(".top .logo").forEach(function(img){var a=img.closest("a");(a&&a.closest(".top")?a:img).classList.add("nq-gone")});
 document.querySelectorAll(".top").forEach(function(t){
  var vis=[].some.call(t.children,function(c){return !c.classList.contains("nq-gone")&&c.offsetParent!==null&&c.textContent.trim()!==""});
  if(!vis)t.classList.add("nq-gone")});
 document.body.insertBefore(hd,document.body.firstChild);
 // Full width: undo the body's side padding for the bar.
 var b=hd.querySelector(".nq-b"),inn=hd.querySelector(".nq-in"),ln=hd.querySelector(".nq-ln");
 function fit(){var cs=getComputedStyle(document.body);
  hd.style.marginLeft="-"+cs.paddingLeft;hd.style.marginRight="-"+cs.paddingRight;hd.style.marginTop="0px";var tp=hd.getBoundingClientRect().top+scrollY;if(tp>0)hd.style.marginTop=(-tp)+"px";
  hd.classList.remove("nq-n");
  var need=inn.querySelector(".nq-br").offsetWidth+ln.scrollWidth+slot.offsetWidth+44;
  if(need>inn.clientWidth)hd.classList.add("nq-n");else{hd.classList.remove("nq-o");b.setAttribute("aria-expanded","false")}}
 // Dropdowns: click to open/close; with a mouse they also open on hover. Esc or a click elsewhere closes them.
 var groups=[].slice.call(hd.querySelectorAll(".nq-g")),tH=0,fine=matchMedia("(hover:hover) and (pointer:fine)");
 function shut(except){groups.forEach(function(g){if(g!==except){g.classList.remove("nq-on");g.querySelector(".nq-gb").setAttribute("aria-expanded","false")}})}
 function openG(g){shut(g);g.classList.add("nq-on");g.querySelector(".nq-gb").setAttribute("aria-expanded","true")}
 groups.forEach(function(g){var gb=g.querySelector(".nq-gb");
  gb.addEventListener("click",function(e){e.stopPropagation();if(g.classList.contains("nq-on")&&!fine.matches)shut();else openG(g)});
  g.addEventListener("mouseenter",function(){if(fine.matches){clearTimeout(tH);openG(g)}});
  g.addEventListener("mouseleave",function(){if(fine.matches){clearTimeout(tH);tH=setTimeout(function(){shut()},180)}})});
 document.addEventListener("click",function(e){if(!(e.target.closest&&e.target.closest(".nq-g")))shut()});
 document.addEventListener("keydown",function(e){if(e.key==="Escape")shut()});
 fit();addEventListener("resize",fit);
 b.onclick=function(e){e.stopPropagation();var o=hd.classList.toggle("nq-o");b.setAttribute("aria-expanded",o)};
 document.addEventListener("keydown",function(e){if(e.key==="Escape"){hd.classList.remove("nq-o");b.setAttribute("aria-expanded","false")}});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",build);else build();
})();
