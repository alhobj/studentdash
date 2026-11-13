import React from 'react';
import {slices,formatMarks,MAX_RING_SLICES} from './model';
const GREEN='#18794e',YELLOW='#e6b930';
function arc(start:number,end:number){const a=start*2*Math.PI-Math.PI/2,b=end*2*Math.PI-Math.PI/2;return `M ${50+40*Math.cos(a)} ${50+40*Math.sin(a)} A 40 40 0 ${end-start>.5?1:0} 1 ${50+40*Math.cos(b)} ${50+40*Math.sin(b)}`;}
export function Ring({score,maximum,onOpen,available=true}:{score:number;maximum:number;onOpen:()=>void;available?:boolean}){
 const parts=slices(score,maximum),label=!available?'Results unavailable':maximum?`Results ${formatMarks(score)}/${formatMarks(maximum)}`:'Not assessed';
 return <button className="result-ring nodrag nopan" onClick={e=>{e.stopPropagation();onOpen();}} onDoubleClick={e=>e.stopPropagation()} aria-label={`${label}. Show contributing tests and questions.`} title={maximum>MAX_RING_SLICES?`Continuous ring for totals over ${MAX_RING_SLICES} marks. Open for exact question marks.`:label}>
 <svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="40" fill="none" stroke="#d7deda" strokeWidth="10"/>{parts===null?<><circle cx="50" cy="50" r="40" fill="none" stroke={YELLOW} strokeWidth="10"/><circle cx="50" cy="50" r="40" fill="none" stroke={GREEN} strokeWidth="10" strokeDasharray={`${score/maximum*251.327} 251.327`} transform="rotate(-90 50 50)"/></>:parts.map((p,i)=>{const gap=Math.min(.008,(p.end-p.start)*.12),start=p.start+gap,end=p.end-gap;return <g key={i}><path d={arc(start,end)} fill="none" stroke={YELLOW} strokeWidth="10"/>{p.earned>0&&<path d={arc(start,start+(end-start)*p.earned)} fill="none" stroke={GREEN} strokeWidth="10"/>}</g>;})}</svg>
 <span>{!available?<small>Results<br/>unavailable</small>:maximum?<><small>Results</small><b>{formatMarks(score)}/{formatMarks(maximum)}</b></>:<small>Not<br/>assessed</small>}</span></button>;
}
