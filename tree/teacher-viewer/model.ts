import {z} from 'zod';
const row=z.object({assessmentId:z.string(),assessmentTitle:z.string(),questionId:z.string(),questionNumber:z.string(),nodeId:z.string(),score:z.number().finite().nonnegative(),maxScore:z.number().finite().positive(),status:z.literal('graded'),assessmentDate:z.iso.date().optional()}).strict().refine(r=>r.score<=r.maxScore);
const snapshot=z.object({classId:z.string(),studentId:z.string(),evidence:z.array(row),assessments:z.array(z.object({id:z.string(),title:z.string(),date:z.iso.date()}).strict()).optional(),unassignedGradedParts:z.number().int().nonnegative()}).strict();
export type Snapshot=z.infer<typeof snapshot>;
export function parseSnapshot(value:unknown,classId:string,studentId:string,known:ReadonlySet<string>){
 const result=snapshot.parse(value);
 if(result.classId!==classId||result.studentId!==studentId)throw Error('The response belongs to another selection.');
 const catalog=new Map<string,string>();
 for(const a of result.assessments||[]){if(catalog.has(a.id))throw Error('Duplicate assessment date record.');catalog.set(a.id,a.date);}
 const seen=new Set<string>();
 for(const r of result.evidence){if(r.assessmentDate&&catalog.has(r.assessmentId)&&catalog.get(r.assessmentId)!==r.assessmentDate)throw Error('Inconsistent assessment date.');const key=JSON.stringify([r.assessmentId,r.questionId]);if(!known.has(r.nodeId)||seen.has(key))throw Error('Invalid or duplicated evidence.');seen.add(key);}
 return result;
}
