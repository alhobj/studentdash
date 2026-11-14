/** Assessment dates filter current saved marks; they do not reconstruct edit history. */
export type AssessmentMoment={id:string;title:string;date:string};
export type DatedEvidence={assessmentId?:string;assessmentDate?:string};
export function assessmentDates(rows:readonly DatedEvidence[],assessments:readonly AssessmentMoment[]=[]){
 return [...new Set([...assessments.map(a=>a.date),...rows.flatMap(r=>r.assessmentDate?[r.assessmentDate]:[])])].sort();
}
export function throughDate<T extends DatedEvidence>(rows:readonly T[],cutoff:string|null,assessments:readonly AssessmentMoment[]=[]):readonly T[]{
 if(cutoff===null)return rows;
 const dates=new Map(assessments.map(a=>[a.id,a.date]));
 return rows.filter(row=>{const date=row.assessmentDate||dates.get(row.assessmentId||'');return Boolean(cutoff&&date&&date<=cutoff);});
}
/** null means unrestricted; an empty set means the timeline has revealed no nodes. */
export function revealedNodes<T extends DatedEvidence&{nodeId:string}>(rows:readonly T[],cutoff:string|null,assessments:readonly AssessmentMoment[]=[]):ReadonlySet<string>|null{
 if(cutoff===null)return null;
 return new Set(throughDate(rows,cutoff,assessments).map(row=>row.nodeId));
}

export function undatedCount(rows:readonly DatedEvidence[],assessments:readonly AssessmentMoment[]=[]){
 const dated=new Set(assessments.map(a=>a.id));
 return rows.filter(r=>!r.assessmentDate&&!dated.has(r.assessmentId||'')).length;
}
export function timeLabel(cutoff:string|null){
 if(cutoff===null)return 'All results';
 if(!cutoff)return 'Before first assessment';
 return 'Through '+new Intl.DateTimeFormat(undefined,{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(cutoff+'T00:00:00Z'));
}
