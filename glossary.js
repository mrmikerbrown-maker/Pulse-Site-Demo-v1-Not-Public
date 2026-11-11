/* Shared glossary for every page of the Pulse site (hub repo Pulse-Site-Demo-v1-Not-Public).
   nav.js loads this file on every page, so pages need no changes.
   What it does: finds glossary words in the page text and gives the first visible one of each a dotted underline.
   Hover (mouse) or tap (phone) shows the definition, with a link to the full Glossary page (/glossary/).
   To add or change a term, edit GG below: ["Term shown","Definition",["words","to underline"]].
   Add ,1 after the word list to keep a term in the Glossary page only, without underlining it on pages.
   Words written in lower case match any case. Words written with capitals (GDP, Fed, Bank Rate) only match exactly.
   A page can keep an area free of underlines with the attribute data-nogloss. */
(function(){
if(window.NQG)return;
var ME=document.currentScript&&document.currentScript.src;
var HUB=ME?new URL(".",ME).pathname:"/Pulse-Site-Demo-v1-Not-Public/";
var GG=[
["The big picture",[
["Surprise","The actual number minus the expected number. Markets react to the surprise, not to the number itself.",["surprise","surprises"]],
["Consensus (expected)","The average of what economists forecast a number will be. It is the 'expected' figure in this tool. Different data providers publish slightly different consensus numbers.",["consensus","forecast","forecasts"]],
["Priced in","Already reflected in market prices because people expected it. A number that matches expectations is already priced in, so it usually moves markets less.",["priced in","priced-in"]],
["Textbook reaction","The usual reaction you would expect from the rule of thumb: hotter or stronger data means interest rates stay higher, so yields and the dollar rise and gold falls. Real days often break the rule.",["textbook"]],
["Print","Trader slang for a data release or its number. A 'hot print' means a higher-than-expected figure.",["print","prints"]],
["Beat / miss","A 'beat' means the number came in above the forecast and a 'miss' means below. Whether that is good or bad news depends on the data and on what the market is worried about.",["beat","beats","miss","misses"]],
["Risk-on / risk-off","Risk-on: traders feel confident and buy stocks and other riskier assets. Risk-off: they get nervous and sell them, often buying safer things such as government bonds, the dollar or gold.",["risk-on","risk-off","risk appetite"]],
["Safe haven","An asset people tend to buy when they are nervous, such as US government bonds, the dollar, the Swiss franc or gold. It is a tendency, not a guarantee.",["safe haven","safe-haven","safe havens"]],
["Rally / selloff","A rally is a sharp rise in prices. A selloff is a sharp fall, usually because many people are selling at once.",["rally","rallied","selloff","sell-off"]]
]],
["Economic data",[
["CPI (inflation)","Consumer Price Index. It measures how fast the prices of everyday goods and services are rising compared with a year ago. This is what most people mean by 'inflation'.",["CPI","inflation","consumer price index"]],
["Core inflation","Inflation leaving out food and energy, which jump around a lot. Central banks watch it because it shows the underlying trend. A report can have a calm headline but a surprising core number, or the other way round.",["core inflation","core CPI","core measure"]],
["Headline figure","The main top-line number in a report. The details underneath, such as core inflation, wages or revisions, can tell a different story from the headline.",["headline"]],
["Month-on-month / year-on-year","Month-on-month (m/m) compares with the previous month. Year-on-year (y/y) compares with the same month a year earlier. Inflation is usually quoted year-on-year and retail sales month-on-month.",["month-on-month","year-on-year","m/m","y/y"]],
["Nonfarm payrolls","The monthly count of jobs the US economy added, not including farm work. Often called 'the jobs report'. It usually comes out on the first Friday of the month.",["nonfarm payrolls","payrolls","jobs report","NFP"]],
["Unemployment rate","The share of people who want a job but do not have one. A rising rate can signal a weakening economy, which may raise bets on interest rate cuts.",["unemployment rate","unemployment"]],
["Wages","How fast workers' pay is growing. Fast wage growth can keep inflation high, so markets read it in the jobs report alongside the headline jobs number.",["wages","wage growth","average hourly earnings"]],
["PMI","Purchasing Managers' Index: a monthly survey of company managers about how business is going. 50 is the line between growing and shrinking.",["PMI","PMIs"]],
["ISM","The Institute for Supply Management, a US group that publishes the best-known US PMI surveys. The services version used in this tool covers service companies such as retailers, banks and restaurants.",["ISM"]],
["Contraction / expansion","Shrinking or growing. A PMI above 50 means expansion (businesses growing); below 50 means contraction (businesses shrinking).",["contraction","expansion","contracting","expanding"]],
["Retail sales","How much shoppers spent in shops and online last month compared with the month before.",["retail sales"]],
["GDP","Gross Domestic Product: the total size of the economy. The headline figure is how fast it grew over the last quarter, shown as a yearly rate.",["GDP"]],
["Advance estimate","The first estimate of GDP, published about a month after the quarter ends. It is revised twice later, so the final number can differ.",["advance estimate","advance GDP","first estimate"]],
["Revision","A later correction to a number that was already published. Revisions can be big and sometimes matter more than the original headline.",["revision","revisions","revised"]],
["PCE","Personal Consumption Expenditures price index: another inflation measure, and the one the Fed officially targets. It comes out after CPI.",["PCE"]],
["Recession","A period when the economy shrinks and jobs and spending fall. Fear of one can push stocks down.",["recession"]],
["Stagflation","Weak growth and high inflation at the same time. It is awkward for central banks because cutting rates to help growth could make inflation worse.",["stagflation"]],
["Government shutdown","When the US government runs out of funding and parts of it stop work. A shutdown can disrupt or delay official data, as it did for the November 2025 inflation report.",["government shutdown","shutdown"]],
["Economic calendar","A schedule of upcoming data releases and central bank events, usually showing the forecast and the previous figure. Traders plan around it.",["economic calendar"]],
["Quarter-on-quarter","The change from the previous three months, written q/q. GDP is quoted this way in the UK and Europe. The US quotes an annualised rate, which makes the same growth look about four times bigger.",["quarter-on-quarter","q/q","previous quarter"]],
["Flash estimate","An early first reading, published before all the data is in. Eurozone inflation and the PMIs come out as flash numbers first and can be revised later.",["flash estimate","flash"]],
["Seasonally adjusted (s.a.)","Figures cleaned of regular calendar swings, such as Christmas shopping or summer hiring, so one month can be compared fairly with the next.",["seasonally adjusted","s.a"]],
["JOLTS (job openings)","A monthly US report on how many jobs are open, and how many people are hired and quit. Lots of openings point to a tight jobs market and pressure on wages.",["JOLTS","JOLTs","job openings"]],
["Trade balance","Exports minus imports. A surplus means a country sells more abroad than it buys. Big swings can move its currency.",["balance of trade","trade balance"]],
["Consumer sentiment","Surveys asking households how they feel about their finances and the economy, such as the University of Michigan survey. A fall can signal weaker spending ahead.",["consumer sentiment","consumer confidence"]],
["Percentage point (pp)","The plain difference between two percentages. Inflation going from 3.0% to 3.2% is a rise of 0.2 percentage points, not 0.2%.",["percentage point","percentage points","pp"]],
["Hot / cold economy","Shorthand for how hard an economy is running. Hot means strong growth, low unemployment and rising prices, which pushes central banks to raise rates. Cold is the opposite.",["runs hot","running hot","running warm","runs cold","running cold","overheating"]]
]],
["Central banks and rates",[
["The Fed","The Federal Reserve, the US central bank. It aims to keep inflation low and unemployment low, and it sets the main US interest rate, which influences borrowing costs across the whole economy.",["the Fed","Federal Reserve","Fed"]],
["FOMC","The Federal Open Market Committee: the group inside the Fed that votes on interest rates, about eight times a year. Decision days are often volatile.",["FOMC"]],
["Fed Chair","The head of the Fed. The press conference after each decision is closely watched, and a hawkish or dovish tone can move markets even when rates do not change.",["Fed Chair","Chair Warsh","Warsh","Powell"]],
["Central bank","An institution, such as the Fed, the European Central Bank or the Bank of England, that controls a country's interest rates and money supply.",["central bank","central banks"]],
["Interest rates","The cost of borrowing money. A central bank's main rate affects everything from mortgages to company loans, and it is the biggest driver of bond yields, currencies and stock valuations.",["interest rate","interest rates"]],
["Rate hike / cut / hold","A hike raises the central bank's interest rate, a cut lowers it and a hold leaves it unchanged. Markets often move more on what traders expect next than on the decision itself.",["rate hike","rate hikes","rate cut","rate cuts","hike","hikes"]],
["Hawkish","Favouring higher interest rates or fewer cuts. Markets tend to see this as tougher policy.",["hawkish"]],
["Dovish","Favouring lower interest rates or more rate cuts. Markets tend to see this as easier policy.",["dovish"]],
["Rate expectations","What traders believe the central bank will do with rates, which shows up in futures prices. Data surprises move these expectations, and that is what moves bonds, currencies and stocks.",["rate expectations","rate bets","rate-cut bets"]],
["Forward guidance","What a central bank says about its future plans. Markets often react to the guidance more than to the decision itself.",["forward guidance"]],
["Dissent","When a member of a rate-setting committee votes against the majority. A dissent can hint that policy is about to change.",["dissent","dissents","dissented"]],
["Inflation target","The inflation rate a central bank aims for, usually 2%. Inflation above target makes rate cuts harder and hikes more likely.",["inflation target","2% target","2% goal"]],
["Higher for longer","The idea that interest rates will stay high for a long time rather than fall soon. Strong data or hot inflation feeds this idea, which is why bond yields and the dollar tend to rise.",["higher for longer","higher-for-longer"]],
["Policy rate","The main interest rate a central bank sets. Each bank names it differently: the Fed's fed funds target range, the ECB's deposit facility rate, the Bank of England's Bank Rate, the RBA's cash rate target.",["policy rate","policy rates","Bank Rate","cash rate target","official cash rate","deposit facility rate","deposit rate","fed funds","overnight rate target","overnight call rate"]],
["Rate decision","The announcement after a central bank meeting saying whether rates go up, down or stay where they are. Markets move on the decision and on the wording that comes with it.",["rate decision","rate decisions"]],
["G10","The ten most traded currencies and their economies: the US, eurozone, Japan, UK, Switzerland, Canada, Australia, New Zealand, Norway and Sweden.",["G10"]],
["ECB / BoE / BoJ","The European Central Bank, Bank of England and Bank of Japan: the central banks for the eurozone, the UK and Japan.",["ECB","BoE","BoJ","European Central Bank","Bank of England","Bank of Japan"]]
]],
["Markets and assets",[
["Stocks (equities)","Shares in companies. Stock prices reflect expected future profits, and higher interest rates make those profits worth less today, so rate worries can push stocks down even on good economic news.",["stocks","equities"],1],
["S&amp;P 500","An index of 500 large US companies. It is the most common measure of how US stocks are doing.",["S&P 500"]],
["Nasdaq","A US stock index dominated by big technology companies. Because tech profits lie far in the future, it tends to react strongly to changes in interest rate expectations.",["Nasdaq","Nasdaq 100"]],
["Megacap tech","The handful of giant tech companies (Apple, Microsoft, Alphabet, Amazon, Nvidia, Meta and Tesla) that make up a big share of the S&amp;P 500 and Nasdaq. When they move, the indexes move.",["megacap","Mag7","big tech"]],
["Index","A basket of assets tracked as one number, such as the S&amp;P 500 for 500 big US companies.",["index"],1],
["Earnings","A company's profits, reported every three months. On days when big companies report, earnings can swamp the economic data.",["earnings"]],
["Valuation","How much investors are willing to pay for a company's profits. Higher interest rates make future profits worth less today, so valuations can fall.",["valuation","valuations"]],
["Bond","A loan to a government or company that pays interest. A bond's price moves in the opposite direction to its yield.",["bond","bonds","bond prices","Treasuries","Treasury"]],
["Bond yield","The yearly return you get for holding a bond. When bond prices fall, yields rise, and when prices rise, yields fall.",["bond yield","bond yields","yield","yields"]],
["10-year Treasury","The yield on 10-year US government bonds. It is the benchmark for borrowing costs around the world, including US mortgage rates.",["10-year yield","10-year Treasury","10-year bond","10-year"]],
["2-year yield","The yield on 2-year US government bonds. It tracks what traders expect the Fed to do with rates over the next couple of years, so it reacts fastest to data and Fed comments.",["2-year yield","2-year"]],
["Treasury auction","When the US government sells new bonds to investors. Weak demand pushes yields up, which can ripple into stocks and the dollar.",["Treasury auction","auction"]],
["Effective fed funds rate","The average rate US banks actually pay each other to borrow overnight, published daily by the New York Fed. It sits inside the Fed's target range and is the rate fed funds futures settle on.",["effective fed funds rate","effective fed funds","EFFR"]],
["Fed funds futures","Exchange-traded contracts (CBOT, symbol ZQ) that settle on the average effective fed funds rate for one calendar month. The price is 100 minus that rate, so they show what the market expects the Fed to do at each meeting.",["fed funds futures","fed fund futures","ZQ"]],
["Cumulative pricing","The total move priced from today up to a given meeting, counted in 25bp steps. 100% means one full 25bp hike is priced by then, 200% means two. A figure in brackets means cuts.",["cumulative pricing","Cumulative"]],
["Basis point (bp)","One hundredth of a percentage point. If a yield goes from 4.00% to 4.10%, it moved 10 basis points.",["basis point","basis points","bps","bp"]],
["US dollar (DXY)","The dollar index measures the dollar against a basket of major currencies such as the euro and the yen. Up means the dollar is getting stronger.",["DXY","US dollar","dollar index","dollar"]],
["Currency pairs (FX)","Currencies trade in pairs. EUR/USD is the price of one euro in dollars, so if it rises the euro is getting stronger against the dollar. USD/JPY is the price of one dollar in yen. FX is short for foreign exchange.",["EUR/USD","USD/JPY","GBP/USD","USD/CHF","currency pair","FX","forex"]],
["Gold","A precious metal people buy as a store of value and a safe haven. It pays no interest, so it tends to fall when yields rise and rise when yields fall, but the link is loose.",["gold"],1],
["Oil","Crude oil. Higher oil prices raise fuel and transport costs, so they feed inflation and can change interest rate expectations. Oil also jumps on wars and supply disruptions.",["oil","crude"]],
["Commodities","Raw materials such as oil, gold, metals and crops that are traded on markets.",["commodities","commodity"]],
["Strait of Hormuz","A narrow waterway between Iran and Oman that a big share of the world's oil ships through. Conflict there raises fears for oil supply and pushes oil prices up.",["Strait of Hormuz","Hormuz"]],
["Futures","Contracts to buy or sell something at a set price on a future date. Many markets are quoted using futures prices, such as COMEX gold.",["futures","COMEX"]],
["Daily close","The last price of the trading day. This tool measures reactions as the change in the daily close, so everything that happened that day is mixed in.",["daily close","daily closes"]]
]],
["Stock indices",[
["Index points (pts)","How much a stock added to or took off an index, in the index's own units. If the S&amp;P 500 fell 38 points and Microsoft accounts for 12.7 of them, Microsoft did a third of the damage.",["index points","index pts","pts"]],
["Index weight","How much of an index one stock makes up. In the S&amp;P 500 and Nasdaq 100 bigger companies carry more weight, so a 1% move in Apple matters far more than a 1% move in a small member.",["index weight","weighting","weights","weight"]],
["Market capitalisation","A company's value on the stock market: share price times the number of shares. Most indices weight their members by it.",["market capitalisation","market cap","market-cap","market value"]],
["Price-weighted index","An index where higher-priced shares count for more, whatever the size of the company. The Dow works this way, so a $500 stock moves it far more than a $50 one.",["price-weighted","price weighted"]],
["Dow Jones","The Dow Jones Industrial Average: 30 large US companies, weighted by share price rather than size. Older and narrower than the S&amp;P 500.",["Dow Jones","Dow"]],
["Sector","A group of companies in the same line of business, such as technology, energy or banks. Stocks in a sector often move together.",["sector","sectors"]],
["Breadth","How many stocks in an index rose against how many fell. An index can rise on a handful of giants while most members fall, which is weak breadth.",["breadth","advancers","decliners"]],
["Year to date (YTD)","From the last close of the previous year to now.",["year to date","year-to-date","YTD"]],
["ETF","Exchange-traded fund: a fund you buy and sell like a share, often tracking an index. SPY tracks the S&amp;P 500 and QQQ the Nasdaq 100.",["ETF","ETFs"]]
]],
["News and events",[
["Tariffs","Taxes a government puts on imported goods. News about tariffs can move markets more than economic data because it changes the outlook for growth, inflation and company profits.",["tariff","tariffs"]],
["Trade war / truce","A trade war is when countries keep raising tariffs against each other. A truce or a deal pauses or reduces them, which markets usually cheer.",["trade war","truce","trade deal"]],
["Currency intervention","When a government or central bank steps into the currency market, buying or selling its own currency to move the exchange rate. Japan has done this to support the yen.",["intervention","intervened"]],
["Geopolitics","Politics and conflict between countries, such as wars or sanctions. Geopolitical shocks can push oil and gold higher and shake stocks.",["geopolitics","geopolitical"]],
["IPO","Initial public offering: when a private company first sells shares to the public. Very big IPOs can soak up investor money, which can weigh on other stocks.",["IPO"]]
]],
["Trading basics",[
["Bull / bear market","A bull market is a long period of rising prices; a bear market is a long period of falling prices. 'Bullish' means expecting prices to rise and 'bearish' means expecting them to fall.",["bull market","bear market","bullish","bearish"]],
["Long / short","Going long means buying something to profit if its price rises. Going short means betting on a fall, by selling something you do not own. Losses on a short can be bigger than your original stake.",["long","short"],1],
["Leverage","Trading with borrowed money so you control a bigger position than your own cash would allow. It magnifies losses as well as gains.",["leverage","leveraged"]],
["Margin","The deposit you put up to open a leveraged trade. If the trade moves against you and your balance falls too low, the broker can close it (a 'margin call').",["margin","margin call"]],
["Stop-loss","An order that automatically closes a trade if the price reaches a level you chose, to limit the loss. In fast markets the price can jump past it (see slippage).",["stop-loss","stop loss"]],
["Spread","The gap between the price you can buy at and the price you can sell at. It is a trading cost, and it often widens around big news.",["spread"],1],
["Slippage","Getting a worse price than you expected because the market moved before your order was filled. It is common around data releases.",["slippage"]],
["Pip","The standard small unit of price movement in a currency pair, usually the fourth decimal place (0.0001). Yen pairs use the second decimal.",["pip","pips"]],
["Volatility","How much and how fast prices move. Data releases and central bank meetings usually raise volatility.",["volatility","volatile"]],
["Liquidity","How easily you can buy or sell without moving the price. It can thin out around big news, making prices jumpy.",["liquidity"]],
["Correlation","How closely two things move together. Yields and the dollar often rise together, but correlations change and can break down.",["correlation","correlated"]],
["Whipsaw","When a price lurches one way and then reverses quickly, catching out traders who chased the first move. Common in the minutes after a data release.",["whipsaw","whipsawed"]],
["Hedge","A trade placed to offset the risk of another position, like insurance. It limits losses but usually costs something.",["hedge","hedging"]],
["Trading the news","Trying to profit from price moves right after a data release or headline. It is fast, spreads are wide and prices whipsaw, which is why many traders avoid it.",["trading the news","trade the news"]],
["Fundamental vs technical analysis","Fundamental analysis looks at the economy, data and company finances to judge value. Technical analysis studies price charts and patterns. This tool is about the fundamental side.",["fundamental analysis","technical analysis"]],
["Risk management","Deciding in advance how much you can afford to lose on a trade and how you will limit it, for example with position size and stop-losses. Poor risk management is a common reason beginners lose money.",["risk management"]],
["Trading session","The hours a market is open. The regular US stock session runs 9:30 to 16:00 New York time (14:30 to 21:00 London most of the year). FX trades round the clock on weekdays and is busiest when London and New York overlap.",["trading session","regular session","sessions","session"]]
]]
];
var GL=[];GG.forEach(function(g){g[1].forEach(function(it){GL.push({g:g[0],t:it[0],d:it[1],a:it[2],x:it[3]})})});
function slug(t){return t.toLowerCase().replace(/&amp;|&/g," and ").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
GL.forEach(function(it){it.id=slug(it.t)});
var GURL=HUB+"glossary/";
window.NQG={groups:GG,terms:GL,slug:slug,url:GURL};
if(window.NQG_NOLINK)return;

/* One pass finds every candidate word: case-sensitive for short capitals, case-insensitive for the rest. */
function rx(s){return s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}
var CS={},CI={};
GL.forEach(function(it,i){if(it.x)return;it.a.forEach(function(a){if(/[A-Z]/.test(a))CS[a]=i;else CI[a.toLowerCase()]=i})});
function build(o,fl){var k=Object.keys(o).sort(function(a,b){return b.length-a.length});
 return k.length?new RegExp("(^|[^A-Za-z0-9])("+k.map(rx).join("|")+")(?![A-Za-z0-9])",fl):null}
var RCS=build(CS,"g"),RCI=build(CI,"gi");
function finds(t){var out=[];
 [[RCS,CS,0],[RCI,CI,1]].forEach(function(r){if(!r[0])return;r[0].lastIndex=0;var m;
  while((m=r[0].exec(t))){var w=m[2],i=r[1][r[2]?w.toLowerCase():w];out.push({i:i,st:m.index+m[1].length,len:w.length});r[0].lastIndex=m.index+m[1].length+w.length}});
 return out.sort(function(a,b){return a.st-b.st||b.len-a.len})}

var F="ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";
var css=
/* !important so a page's own styles for spans (sizes, colours, block layout) never change the word itself */
".nqg-t{display:inline!important;position:static!important;float:none!important;width:auto!important;height:auto!important;margin:0!important;padding:0!important;font:inherit!important;color:inherit!important;letter-spacing:inherit!important;text-transform:inherit!important;opacity:1!important;background:none!important;border:0!important;border-bottom:1.5px dotted var(--accent,#00E0FF)!important;cursor:help!important;border-radius:0!important}"+
".nqg-t:hover,.nqg-t:focus,.nqg-t.nqg-on{background:rgba(0,224,255,.14)!important;outline:none;border-radius:2px!important}"+
"#nqg-tip{position:fixed;z-index:70;display:none;background:var(--card,#0D0E15);color:var(--text,#fff);border:1px solid var(--line,#22242E);border-radius:12px;box-shadow:0 8px 28px rgba(0,0,0,.28);padding:12px 14px;font:400 13px/1.45 "+F+";text-align:left;text-transform:none;letter-spacing:normal;white-space:normal}"+
"#nqg-tip b{display:block;font-size:14px;font-weight:700;margin:0 0 4px;padding-right:22px;color:var(--text,#fff)}"+
"#nqg-tip p{margin:0 0 8px;color:var(--text2,#CBD5E1)}"+
"#nqg-tip a{color:var(--accent,#00E0FF);font-size:12px;font-weight:600;text-decoration:none}#nqg-tip a:hover{text-decoration:underline}"+
":root.light #nqg-tip{box-shadow:0 8px 28px rgba(11,13,20,.14)}"+
"#nqg-tip .nqg-x{position:absolute;top:4px;right:6px;border:0;background:transparent;font:400 20px/1 "+F+";padding:2px 6px;color:var(--muted,#8A8FA3);cursor:pointer}";

/* Where not to underline: menus, buttons, links, form fields, headings, charts, and anything clickable. */
var SKIPTAG=/^(A|BUTTON|SELECT|OPTION|INPUT|TEXTAREA|LABEL|SCRIPT|STYLE|NOSCRIPT|TEMPLATE|H1|H2|H3|SVG|CODE|PRE|SUMMARY|TITLE|CANVAS)$/;
var SKIPROLE=/^(button|tab|link|menuitem|option|switch|checkbox|radio)$/;
function skipEl(el){
 if(SKIPTAG.test(el.nodeName.toUpperCase()))return true;
 if(el.id==="nqg-tip")return true;
 var c=el.classList;if(c&&(c.contains("nqg-t")||c.contains("nq-hd")||c.contains("term")))return true;
 if(el.hasAttribute("data-nogloss")||el.hasAttribute("onclick")||el.isContentEditable||el.getAttribute("aria-hidden")==="true")return true;
 var r=el.getAttribute("role");return !!(r&&SKIPROLE.test(r))}
function shown(el){if(!el.getClientRects().length)return false;var s=getComputedStyle(el);return s.visibility!=="hidden"&&s.cursor!=="pointer"}

var busy=false;
function scan(){
 if(!document.body||document.documentElement.hasAttribute("data-nogloss"))return;
 busy=true;
 var used={};
 document.querySelectorAll(".nqg-t").forEach(function(s){if(s.getClientRects().length)used[s.getAttribute("data-g")]=1});
 var nodes=[],w=document.createTreeWalker(document.body,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT,{acceptNode:function(n){
  if(n.nodeType===1)return skipEl(n)?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_SKIP;
  return /[A-Za-z]{2}/.test(n.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_SKIP}});
 while(w.nextNode())nodes.push(w.currentNode);
 nodes.forEach(function(n){wrap(n,used)});
 busy=false;if(mo)mo.takeRecords()}
function wrap(n,used){
 var t=n.nodeValue,f=finds(t),best=null;
 for(var k=0;k<f.length;k++){if(!used[f[k].i]){best=f[k];break}}
 if(!best)return;
 var p=n.parentNode;if(!p||!shown(p))return;
 used[best.i]=1;
 var sp=document.createElement("span");sp.className="nqg-t";sp.tabIndex=0;sp.setAttribute("data-g",best.i);sp.setAttribute("aria-label",t.substr(best.st,best.len)+", glossary term");sp.textContent=t.substr(best.st,best.len);
 var after=document.createTextNode(t.substr(best.st+best.len));
 n.nodeValue=t.substr(0,best.st);p.insertBefore(sp,n.nextSibling);p.insertBefore(after,sp.nextSibling);wrap(after,used)}

/* The pop-up */
var tip,cur=null,pinned=false,tOpen=0,tClose=0,sy0=0;
function esc(s){return s.replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function open(el,pin){
 clearTimeout(tClose);
 var i=+el.getAttribute("data-g"),it=GL[i];if(!it)return;
 if(cur&&cur!==el)cur.classList.remove("nqg-on");
 cur=el;pinned=!!pin;el.classList.add("nqg-on");
 tip.innerHTML='<button class="nqg-x" type="button" aria-label="Close">×</button><b>'+it.t+'</b><p>'+it.d+'</p><a href="'+GURL+'#'+it.id+'">See it in the glossary →</a>';
 tip.style.display="block";tip.style.visibility="hidden";
 var r=el.getBoundingClientRect(),wd=Math.min(300,innerWidth-24);tip.style.width=wd+"px";
 tip.style.left=Math.max(12,Math.min(innerWidth-wd-12,r.left+r.width/2-wd/2))+"px";
 var h=tip.offsetHeight,top=r.bottom+8;if(top+h>innerHeight-8&&r.top-h-8>8)top=r.top-h-8;
 tip.style.top=Math.max(8,top)+"px";tip.style.visibility="visible";sy0=pageYOffset;
 tip.querySelector(".nqg-x").onclick=close}
function close(){clearTimeout(tOpen);clearTimeout(tClose);if(tip)tip.style.display="none";if(cur)cur.classList.remove("nqg-on");cur=null;pinned=false}
function later(){clearTimeout(tClose);if(!pinned)tClose=setTimeout(close,250)}
var hover=matchMedia("(hover:hover) and (pointer:fine)");

var mo=null,tScan=0;
function start(){
 if(document.getElementById("nqg-tip"))return;
 var st=document.createElement("style");st.textContent=css;document.head.appendChild(st);
 tip=document.createElement("div");tip.id="nqg-tip";tip.setAttribute("role","tooltip");document.body.appendChild(tip);
 document.addEventListener("click",function(e){
  var t=e.target.closest&&e.target.closest(".nqg-t");
  if(t){e.preventDefault();e.stopPropagation();if(cur===t&&pinned)close();else open(t,true);return}
  if(!(e.target.closest&&e.target.closest("#nqg-tip")))close()},true);
 document.addEventListener("mouseover",function(e){if(!hover.matches)return;
  var t=e.target.closest&&e.target.closest(".nqg-t");
  if(t){if(cur===t){clearTimeout(tClose);return}if(pinned)return;clearTimeout(tOpen);tOpen=setTimeout(function(){open(t,false)},120);return}
  if(e.target.closest&&e.target.closest("#nqg-tip")){clearTimeout(tClose);return}
  clearTimeout(tOpen);if(cur)later()});
 document.addEventListener("keydown",function(e){
  if(e.key==="Escape")close();
  if((e.key==="Enter"||e.key===" ")&&e.target.classList&&e.target.classList.contains("nqg-t")){e.preventDefault();open(e.target,true)}});
 addEventListener("scroll",function(){if(cur&&Math.abs(pageYOffset-sy0)>30)close()},{passive:true});
 addEventListener("resize",close);
 NQG.scan=scan;NQG.close=close;
 scan();
 // Pages draw some text after loading (tables, tabs, live data), so look again when the page changes.
 mo=new MutationObserver(function(rs){if(busy)return;
  if(rs.every(function(r){var n=r.target;n=n.nodeType===1?n:n.parentNode;return !n||(n.closest&&(n.closest("#nqg-tip")||n.closest(".nqg-t")))}))return;
  clearTimeout(tScan);tScan=setTimeout(scan,400)});
 mo.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:["class","hidden","style","open"]});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();
