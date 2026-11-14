import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parseSnapshot} from '../teacher-viewer/model';
import {totals} from '../local-viewer/model';
const row={assessmentId:'test',assessmentTitle:'Fictional test',questionId:'q1',questionNumber:'1',nodeId:'node',score:4,maxScore:5,status:'graded'};
const snapshot={classId:'class',studentId:'learner',evidence:[row],unassignedGradedParts:0};
const known=new Set(['node']);
test('teacher result validation binds one learner and preserves earned/possible marks',()=>{
 assert.deepEqual(totals(parseSnapshot(snapshot,'class','learner',known).evidence),{score:4,maximum:5});
 assert.throws(()=>parseSnapshot(snapshot,'class','someone-else',known));
 assert.throws(()=>parseSnapshot(snapshot,'other-class','learner',known));
});
test('teacher results reject duplicated, unknown, absent or out-of-range evidence',()=>{
 for(const evidence of [[row,row],[{...row,nodeId:'unknown'}],[{...row,status:'absent',score:0}],[{...row,score:6}]]){
  assert.throws(()=>parseSnapshot({...snapshot,evidence},'class','learner',known));
 }
 assert.equal(totals(parseSnapshot({...snapshot,evidence:[{...row,score:0}]},'class','learner',known).evidence).score,0);
});
