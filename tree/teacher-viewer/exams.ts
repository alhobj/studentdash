import {z} from 'zod';
const text=z.string().trim().min(1).max(200);
const allocation=z.object({nodeId:text,marks:z.number().positive().finite()}).strict();
const question=z.object({number:text,marks:z.number().positive().finite(),allocations:z.array(allocation)}).strict();
const paper=z.object({id:text,title:text,year:z.number().int().min(1900).max(2200),level:z.enum(['SL','HL']),kind:z.enum(['exam','specimen']),questions:z.array(question).max(1000)}).strict();
const schema=z.object({schemaVersion:z.literal('1.0'),papers:z.array(paper).max(500)}).strict();
export type ExamBank=z.infer<typeof schema>;
export function parseExamBank(raw:unknown,known:ReadonlySet<string>):ExamBank{
 const bank=schema.parse(raw),ids=new Set<string>();
 for(const p of bank.papers){
  if(ids.has(p.id))throw Error('Duplicate paper ID: '+p.id);ids.add(p.id);
  const numbers=new Set<string>();
  for(const q of p.questions){
   if(numbers.has(q.number))throw Error('Duplicate question in '+p.title);numbers.add(q.number);
   const nodes=new Set<string>();let total=0;
   for(const a of q.allocations){if(!known.has(a.nodeId)||nodes.has(a.nodeId))throw Error('Unknown or repeated topic in '+p.title+' question '+q.number);nodes.add(a.nodeId);total+=a.marks;}
   if(total>q.marks+1e-8)throw Error('Allocated marks exceed question marks in '+p.title+' question '+q.number);
  }
 }
 return bank;
}
export function examEvidence(bank:ExamBank,nodeId:string){return bank.papers.flatMap(p=>p.questions.flatMap(q=>q.allocations.filter(a=>a.nodeId===nodeId).map(a=>({paperId:p.id,title:p.title,year:p.year,level:p.level,kind:p.kind,question:q.number,marks:a.marks}))));}
