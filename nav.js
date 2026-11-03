/* Shared "All tools" menu for every page on mrmikerbrown-maker.github.io.
   A page loads it with one line:  <script src="/nav.js" defer></script>
   It puts a menu button next to the page's sun/moon button (#theme).
   To add a tool to every page's menu, add one line to TOOLS below. */
(function(){
var TOOLS=[
 ["Home","/"],
 ["Economy Thermometer","/economy-thermometer/"],
 ["Index Contribution","/index-contribution-site/"],
 ["Data Surprises","/surprises/"],
 ["Market Clock","/clock/"],
 ["Chain Reaction","/chain-reaction/"]
];
window.NQ_TOOLS=TOOLS;
var here=location.pathname.replace(/index\.html$/,"");
function isHere(h){return h==="/"?here==="/":here.indexOf(h)===0}
var css=".nq-m{position:relative;flex:none;margin-left:auto}"+
".nq-b{appearance:none;display:inline-flex;align-items:center;gap:6px;height:30px;padding:0 11px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--text2);font:600 13px ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;cursor:pointer}"+
".nq-b:hover,.nq-b[aria-expanded=true]{color:var(--text);border-color:var(--accent)}"+
".nq-b svg{width:14px;height:14px}"+
".nq-p{position:absolute;right:0;top:calc(100% + 8px);min-width:220px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.35);z-index:50;display:flex;flex-direction:column}"+
".nq-p[hidden]{display:none}"+
".nq-p a{display:block;padding:9px 12px;border-radius:8px;color:var(--text2);text-decoration:none;font:500 14px ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}"+
".nq-p a:hover{background:var(--bg);color:var(--text)}"+
".nq-p a[aria-current]{color:var(--text);font-weight:700;box-shadow:inset 3px 0 0 var(--accent)}"+
":root.light .nq-p{box-shadow:0 10px 30px rgba(11,13,20,.14)}"+
"@media (max-width:520px){.nq-b span{display:none}.nq-b{width:30px;padding:0;justify-content:center}}";
function build(){
 var th=document.getElementById("theme");if(!th||document.querySelector(".nq-m"))return;
 var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);
 var m=document.createElement("div");m.className="nq-m";
 var links=TOOLS.map(function(t){return '<a href="'+t[1]+'"'+(isHere(t[1])?' aria-current="page"':"")+">"+t[0]+"</a>"}).join("");
 m.innerHTML='<button class="nq-b" type="button" aria-expanded="false" aria-haspopup="true" aria-label="All tools"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M2.5 4h11M2.5 8h11M2.5 12h11"/></svg><span>All tools</span></button><nav class="nq-p" aria-label="All tools" hidden>'+links+"</nav>";
 th.parentNode.insertBefore(m,th);
 th.style.marginLeft=th.style.marginLeft||"8px";
 var b=m.firstChild,p=m.lastChild;
 function set(o){p.hidden=!o;b.setAttribute("aria-expanded",o)}
 b.onclick=function(e){e.stopPropagation();set(p.hidden)};
 document.addEventListener("click",function(e){if(!m.contains(e.target))set(false)});
 document.addEventListener("keydown",function(e){if(e.key==="Escape")set(false)});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",build);else build();
})();
