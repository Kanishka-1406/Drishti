import React from 'react'
export default function ContributionBars({contributions}){return <div className="contribs">{contributions.map(c=><div className="contrib" key={c.key}><div><span>{c.label}</span><b>{c.contribution.toFixed(0)}%</b></div><div className="bar"><i style={{width:`${c.contribution}%`}}/></div></div>)}</div>}
