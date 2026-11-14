import {z} from 'zod';
export const MAX_RESULTS_BYTES=2*1024*1024;
export const MAX_RING_SLICES=500;
export const CONFIDENCE_LABELS={'not-reviewed':'Not reviewed','needs-practice':'Needs practice',developing:'Developing',confident:'Confident'} as const;
export type Confidence=Record<string,Exclude<keyof typeof CONFIDENCE_LABELS,'not-reviewed'>>;
const short=z.string().min(1).max(200);
const row=z.object({assessmentId:short,assessmentTitle:short,questionId:short,questionNumber:short,nodeId:short,score:z.number().finite().nonnegative().max(1000000),maxScore:z.number().finite().positive().max(1000000),status:z.literal('graded'),assessmentDate:z.iso.date().optional()}).strict().refine(r=>r.score<=r.maxScore,'Marks exceed the available marks');
const schema=z.object({schemaVersion:z.literal('1.0'),mapId:z.literal('chemistree'),mapVersion:z.literal('2.0'),packageId:z.uuid(),revision:z.number().int().positive(),generatedAt:z.iso.datetime(),evidence:z.array(row).max(10000),assessments:z.array(z.object({id:short,title:short,date:z.iso.date()}).strict()).max(10000).optional()}).strict();
export type Results=z.infer<typeof schema>;
export function parseResults(text:string,known:ReadonlySet<string>,packageId:string):Results{
 if(new TextEncoder().encode(text).length>MAX_RESULTS_BYTES)throw Error('Results file exceeds 2 MB.');
 const result=schema.parse(JSON.parse(text));
 if(result.packageId!==packageId)throw Error('This results file belongs to a different student package.');
 const catalog=new Map<string,string>();
 for(const a of result.assessments||[]){if(catalog.has(a.id))throw Error('Duplicate assessment date record.');catalog.set(a.id,a.date);}
 const seen=new Set<string>();
 for(const r of result.evidence){if(r.assessmentDate&&catalog.has(r.assessmentId)&&catalog.get(r.assessmentId)!==r.assessmentDate)throw Error('Inconsistent assessment date.');if(!known.has(r.nodeId))throw Error('Unknown curriculum node. Update the application before loading these results.');const key=JSON.stringify([r.assessmentId,r.questionId]);if(seen.has(key))throw Error('A question is counted more than once.');seen.add(key);}
 return result;
}
export function acceptResults(current:Results|null,incoming:Results):Results{
 if(current&&incoming.packageId!==current.packageId)throw Error('The student package changed. Restart the viewer.');
 if(current&&incoming.revision<current.revision)throw Error('An older results file arrived. Keeping the newer results.');
 if(current&&incoming.revision===current.revision&&JSON.stringify(current)!==JSON.stringify(incoming))throw Error('Two different results files have the same revision. Ask your teacher to re-export.');
 return incoming;
}
export function totals(rows:Results['evidence']){return rows.reduce((t,r)=>({score:Number((t.score+r.score).toFixed(6)),maximum:Number((t.maximum+r.maxScore).toFixed(6))}),{score:0,maximum:0});}
export function formatMarks(value:number){return Number(value.toFixed(6)).toString();}
/** One slice per mark; fractional final marks have proportional angular width. */
export function slices(score:number,maximum:number){
 if(!Number.isFinite(maximum)||maximum<=0||!Number.isFinite(score)||score<0||score>maximum)return [];
 // Dense totals use one continuous ring, explicitly labelled; never invent fewer mark slices.
 if(maximum>MAX_RING_SLICES)return null;
 return Array.from({length:Math.ceil(maximum)},(_,i)=>({start:i/maximum,end:Math.min(i+1,maximum)/maximum,earned:Math.max(0,Math.min(score-i,Math.min(1,maximum-i)))/Math.min(1,maximum-i)}));
}
export function confidenceKey(packageId:string){return 'chemistree-local-confidence-v1:'+packageId;}
export function parseConfidence(text:string,known:ReadonlySet<string>,packageId:string):Confidence{
 const schema=z.object({schemaVersion:z.literal('1.0'),mapVersion:z.literal('2.0'),packageId:z.literal(packageId),confidence:z.record(z.string(),z.enum(['needs-practice','developing','confident']))}).strict();
 if(new TextEncoder().encode(text).length>128*1024)throw Error('Confidence backup exceeds 128 KB.');
 const file=schema.parse(JSON.parse(text));for(const id of Object.keys(file.confidence))if(!known.has(id))throw Error('Unknown confidence node.');return file.confidence;
}
export function confidenceFile(confidence:Confidence,packageId:string){return JSON.stringify({schemaVersion:'1.0',mapVersion:'2.0',packageId,confidence});}
