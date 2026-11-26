/* Plain release names and "how big" tiers, shared by the homepage "Next big release" tile and the
   calendar page's "Next up" box. relName({c,name,t}) -> {t, name, tier}.
   The feed's own "high importance" flag lets odd series through (e.g. "DE Unemployed Persons NSA") and its
   names are jargon. So each release gets a plain, title-case name ("German Unemployment") and a tier:
   1 = genuinely moves markets, 2 = worth knowing, 3 = everything else, 0 = never shown (regional or duplicate). */
var CTRY={US:"US",EU:"Eurozone",DE:"German",GB:"UK",JP:"Japan",CN:"China",CA:"Canada",AU:"Australia",NZ:"New Zealand",CH:"Swiss",NO:"Norway",SE:"Sweden"};
var JOBS1={US:1,GB:1,CA:1,AU:1,NZ:1},SHOP1={US:1,GB:1,CA:1,AU:1,CN:1};
/* [pattern, plain name ({C} = country), tier (number, or function of country)] - first match wins */
var RULES=[
 [/rate decision/i,null,1],
 [/non ?farm payrolls/i,"US jobs report",1],
 [/tokyo cpi/i,"Tokyo inflation",1],
 [/\bPCE\b/i,"US PCE inflation",1],
 [/^(hesse|lower saxony|brandenburg|bavaria|baden|north rhine|saxony)/i,null,0],
 [/\bPPI\b|producer price/i,"{C} producer prices",2],
 [/expectations/i,null,0],
 [/inflation|\bCPI|HICP/i,"{C} inflation",1],
 [/GDP price index|GDP deflator/i,null,0],
 [/GDP/,"{C} GDP",function(c){return c==="CH"||c==="NO"||c==="SE"?2:1}],
 [/\bADP\b/,"US ADP jobs estimate",2],
 [/initial jobless claims/i,"US weekly jobless claims",2],
 [/employment change|claimant/i,"{C} jobs report",function(c){return JOBS1[c]?1:2}],
 [/unemploy|jobless rate/i,"{C} unemployment",function(c){return JOBS1[c]?1:2}],
 [/average (hourly )?earnings|wage/i,"{C} wage growth",function(c){return c==="GB"?1:2}],
 [/large retailers/i,null,0],
 [/retail sales/i,"{C} retail sales",function(c){return SHOP1[c]?1:2}],
 [/ISM manufacturing PMI/i,"US ISM factory survey",1],
 [/ISM (services|non-manufacturing) PMI/i,"US ISM services survey",1],
 [/chicago PMI/i,"Chicago business survey",2],
 [/NBS manufacturing PMI/i,"China official factory survey (PMI)",1],
 [/(RatingDog|Caixin) manufacturing PMI/i,"China private factory survey (PMI)",2],
 [/PMI.*flash|flash.*PMI/i,"{C} business surveys (flash PMIs)",function(c){return c==="US"||c==="EU"||c==="GB"||c==="DE"?1:2}],
 [/ifo/i,"German Ifo business survey",1],
 [/ZEW/,"German ZEW investor survey",2],
 [/GfK/,"German consumer confidence",2],
 [/michigan/i,"US consumer sentiment",2],
 [/consumer confidence/i,"{C} consumer confidence",2],
 [/economic sentiment/i,"{C} economic sentiment",2],
 [/durable goods/i,"US durable goods orders",2],
 [/personal (income|spending)/i,"US income and spending",2],
 [/JOLT/i,"US job openings",2],
 [/industrial production/i,"{C} industrial production",2],
 [/NBS non manufacturing PMI/i,"China official services survey (PMI)",2],
 [/philadelphia fed|empire state/i,"US regional factory survey",2],
 [/MPC vote/i,null,0],
 [/balance of trade|trade balance/i,"{C} trade balance",3],
 [/housing starts|home sales|building permits|building approvals/i,"{C} housing data",3]
];
/* Fallback for anything else: the feed's name with the jargon (SA, NSA, MoM, Prel, Adv...) taken off. */
function plain(name){return name.replace(/\b(s\.a|n\.s\.a|SA|NSA|MoM|YoY|QoQ|m\/m|y\/y|q\/q|Prel|Flash|Final|Adv|2nd Est|3rd Est|1st Est)\b\.?/g,"").replace(/\s+/g," ").trim()}
/* Release names in title case (Mike, 26 Nov): "German Unemployment", "US PCE Inflation". Small joining words stay lower case. */
function tc(s){return s.replace(/\b([a-z])([a-z]*)/g,function(w,a,b){return /^(and|of|the|in|on|at|for|to|vs)$/.test(w)?w:a.toUpperCase()+b})}
function relName(e){
 for(var i=0;i<RULES.length;i++){var r=RULES[i];if(r[0].test(e.name)){
  var tier=typeof r[2]==="function"?r[2](e.c):r[2];
  return {t:e.t,name:tc(r[1]?r[1].replace("{C}",CTRY[e.c]||e.c):e.name),tier:tier}}}
 return {t:e.t,name:tc((CTRY[e.c]||e.c)+" "+plain(e.name)),tier:3};
}
