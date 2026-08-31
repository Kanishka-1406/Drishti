export const WEIGHTS={rainfall:.40,slope:.25,soil:.20,historical:.15}
export const HISTORICAL_SCORES={Low:20,Moderate:50,High:80,'Very High':100}
const clamp=(v,min,max)=>Math.min(max,Math.max(min,v))
const tierFromScore=s=>s>=80?'CRITICAL':s>=60?'HIGH':s>=35?'MODERATE':'LOW'
export function computeRisk({rainfall,slope,soil,historical}){
 const n={rainfall:clamp(rainfall/300,0,1)*100,slope:clamp(slope/60,0,1)*100,soil:clamp(soil,0,100),historical:HISTORICAL_SCORES[historical]??0}
 const w={rainfall:n.rainfall*.40,slope:n.slope*.25,soil:n.soil*.20,historical:n.historical*.15}
 const score=Math.round(clamp(Object.values(w).reduce((a,b)=>a+b,0),0,100)); const tier=tierFromScore(score)
 const labels={rainfall:'Rainfall',slope:'Slope',soil:'Soil Saturation',historical:'Historical Susceptibility'}
 const total=score||1
 const contributions=Object.keys(w).map(key=>({key,label:labels[key],contribution:w[key]/total*100,weightedValue:w[key],normalizedValue:n[key]})).sort((a,b)=>b.contribution-a.contribution)
 const primaryDriver=contributions[0].label
 return {score,tier,contributions,primaryDriver,explanation:`The estimated risk score of ${score}/100 is driven primarily by ${primaryDriver.toLowerCase()}. This is a transparent, rule-based calculation — not a trained prediction.`}
}
export const RECOMMENDATIONS={
 LOW:'Routine monitoring. Continue standard seasonal observation.',
 MODERATE:'Increase monitoring of vulnerable slopes and rainfall conditions.',
 HIGH:'Review local preparedness measures and vulnerable zones. Alert relevant field teams.',
 CRITICAL:'Consider escalation to relevant local disaster-management authorities and emergency preparedness measures.'
}
export function tierColor(t){return t==='CRITICAL'?'#ef5b52':t==='HIGH'?'#f2924a':t==='MODERATE'?'#eec24d':'#55d18a'}
