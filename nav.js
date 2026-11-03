/* Shared top bar for every page on mrmikerbrown-maker.github.io.
   A page loads it with one line in <head>:  <script src="/nav.js" defer></script>
   It puts the same full-width bar at the top of the page: logo + site name (links home), a link to every tool,
   and the page's own sun/moon button (moved into the bar). On narrow screens the links fold into a menu button.
   The page's own logo row is hidden so there is only one header.
   To add a tool to every page, add one line to TOOLS below. To rename the site, change NAME. */
(function(){
var NAME="Pulse";
var TOOLS=[
 ["Home","/"],
 ["Economy Thermometer","/economy-thermometer/"],
 ["Index Contribution","/index-contribution-site/"],
 ["Data Surprises","/surprises/"],
 ["Market Clock","/clock/"]
];
var LOGO="data:image/png;base64,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";
window.NQ_TOOLS=TOOLS;
var here=location.pathname.replace(/index\.html$/,"");
function isHere(h){return h==="/"?here==="/":here.indexOf(h)===0}
var F="ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";
var css=
".nq-hd{display:block;border-bottom:1px solid var(--line);background:var(--bg);position:relative;z-index:40;margin-bottom:18px}"+
".nq-in{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:14px;padding:14px 16px 12px}"+
".nq-br{display:flex;align-items:center;gap:12px;flex:none;text-decoration:none;margin-right:auto}"+
".nq-br img{display:block;width:120px;height:auto;margin:0}"+
":root.light .nq-br img{filter:invert(1) hue-rotate(180deg)}"+
".nq-br span{font:800 15px/1 "+F+";letter-spacing:.16em;text-transform:uppercase;color:var(--accent);border-left:1px solid var(--line);padding:4px 0 4px 12px}"+
".nq-ln{display:flex;gap:2px;flex:none}"+
".nq-ln a,.nq-p a{font:500 14px/1.2 "+F+";color:var(--text2);text-decoration:none;padding:8px 10px;border-radius:8px;white-space:nowrap}"+
".nq-ln a:hover,.nq-p a:hover{background:var(--card);color:var(--text)}"+
".nq-ln a[aria-current]{color:var(--text);background:var(--card);box-shadow:inset 0 0 0 1px var(--line)}"+
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
"@media (max-width:520px){.nq-br img{width:96px}.nq-br span{font-size:13px;padding-left:10px}.nq-br{gap:10px}.nq-in{gap:10px}}"+
".nq-gone{display:none!important}";
function build(){
 if(document.querySelector(".nq-hd"))return;
 var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);
 var links=TOOLS.map(function(t){return '<a href="'+t[1]+'"'+(isHere(t[1])?' aria-current="page"':"")+">"+t[0]+"</a>"}).join("");
 var hd=document.createElement("header");hd.className="nq-hd";
 hd.innerHTML='<div class="nq-in"><a class="nq-br" href="/" aria-label="'+NAME+' home"><img alt="Newsquawk" width="120" src="'+LOGO+'"><span>'+NAME+'</span></a>'+
  '<nav class="nq-ln" aria-label="Tools">'+links+'</nav>'+
  '<button class="nq-b" type="button" aria-expanded="false" aria-label="Menu"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M2.5 4h11M2.5 8h11M2.5 12h11"/></svg></button>'+
  '<span class="nq-th"></span></div><nav class="nq-p" aria-label="Tools">'+links+"</nav>";
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
  var need=inn.querySelector(".nq-br").offsetWidth+ln.scrollWidth+slot.offsetWidth+60;
  if(need>inn.clientWidth)hd.classList.add("nq-n");else{hd.classList.remove("nq-o");b.setAttribute("aria-expanded","false")}}
 fit();addEventListener("resize",fit);
 b.onclick=function(e){e.stopPropagation();var o=hd.classList.toggle("nq-o");b.setAttribute("aria-expanded",o)};
 document.addEventListener("keydown",function(e){if(e.key==="Escape"){hd.classList.remove("nq-o");b.setAttribute("aria-expanded","false")}});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",build);else build();
})();
