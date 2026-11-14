import React from 'react';
import {ControlSection} from './ControlPanel';
import {assessmentDates,timeLabel,undatedCount,type DatedEvidence,type AssessmentMoment} from './timeline';
export function TimeControls({rows,assessments=[],cutoff,onChange,disabled=false}:{rows:readonly DatedEvidence[];assessments?:readonly AssessmentMoment[];cutoff:string|null;onChange:(value:string|null)=>void;disabled?:boolean}){
 const dates=assessmentDates(rows,assessments),position=cutoff===null?dates.length:dates.filter(d=>Boolean(cutoff)&&d<=cutoff!).length;
 const unknown=undatedCount(rows,assessments),label=timeLabel(cutoff);
 const choose=(index:number)=>onChange(index===0?'':dates[index-1]);
 return <ControlSection title={'Time · '+label}>
  <p aria-live="polite">{label}</p>
  <button disabled={disabled||!dates.length} onClick={()=>onChange('')}>{cutoff===null?'Start timeline':'Back to start'}</button>
  <label>Assessments up to this date<input aria-label="Assessment time" type="range" min={0} max={dates.length} step={1} value={position} aria-valuetext={label} disabled={disabled||!dates.length} onChange={e=>choose(Number(e.target.value))}/></label>
  <button disabled={disabled||position===0} onClick={()=>choose(position-1)}>Previous assessment date</button>
  <button disabled={disabled||position>=dates.length} onClick={()=>choose(position+1)}>Next assessment date</button>
  <button disabled={disabled||cutoff===null} onClick={()=>onChange(null)}>All results</button>
  <p>{disabled?'Load a student’s results to use the timeline.':dates.length?`${dates.length} assessment date${dates.length===1?'':'s'}. Nodes appear on their first dated assessment; results accumulate through the selected date.`:'No assessment dates available. Re-export older student folders to include dates.'}</p>
  {unknown>0&&<p>{unknown} question part{unknown===1?' has':'s have'} no assessment date; included only in All results.</p>}
  <p>Uses current saved marks by assessment date, including later corrections. Confidence and temporary marks stay current; they are not historical snapshots.</p>
 </ControlSection>;
}
