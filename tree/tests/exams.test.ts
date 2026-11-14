import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parseExamBank,examEvidence} from '../teacher-viewer/exams';
const known=new Set(['a','b']);
const make=(allocations:any[])=>({schemaVersion:'1.0',papers:[{id:'fictional',title:'Fictional paper',year:2025,level:'SL',kind:'exam',questions:[{number:'2a',marks:3,allocations}]}]});
test('exam marks split across topics without multiplying question marks',()=>{
 const bank=parseExamBank(make([{nodeId:'a',marks:2},{nodeId:'b',marks:1}]),known);
 assert.equal(examEvidence(bank,'a')[0].marks,2);assert.equal(examEvidence(bank,'b')[0].marks,1);
 assert.equal(examEvidence(bank,'c').length,0);
});
test('exam imports reject duplicate, unknown and overallocated marks; allow unmapped parts',()=>{
 for(const allocations of [[{nodeId:'a',marks:4}],[{nodeId:'c',marks:1}],[{nodeId:'a',marks:1},{nodeId:'a',marks:1}],[{nodeId:'a',marks:-1}]])assert.throws(()=>parseExamBank(make(allocations),known));
 assert.equal(parseExamBank(make([]),known).papers.length,1);
 const duplicate=make([]);duplicate.papers.push(duplicate.papers[0]);assert.throws(()=>parseExamBank(duplicate,known));
});
