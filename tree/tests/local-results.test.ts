import {test} from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {parseResults,acceptResults,totals,slices,confidenceKey,parseConfidence,confidenceFile} from '../local-viewer/model';
import {Ring} from '../local-viewer/Ring';
const packageId='480ed739-2eef-4382-84b0-7edc11b46507',known=new Set(['node-a','node-b']);
const source={schemaVersion:'1.0',mapId:'chemistree',mapVersion:'2.0',packageId,revision:1,generatedAt:'2026-11-12T12:00:00Z',evidence:[{assessmentId:'A01',assessmentTitle:'Fictional test',questionId:'Q01',questionNumber:'2(b)',nodeId:'node-a',score:4,maxScore:5,status:'graded'}]};
const parse=(value:any)=>parseResults(JSON.stringify(value),known,packageId);
test('4/5 has exactly five slices, four earned, with accessible label',()=>{
 assert.deepEqual(slices(4,5)?.map(s=>s.earned),[1,1,1,1,0]);
 const html=renderToStaticMarkup(React.createElement(Ring,{score:4,maximum:5,onOpen(){}}));
 assert.match(html,/Results 4\/5/);assert.equal((html.match(/<g>/g)||[]).length,5);
 assert.match(html,/Show contributing tests and questions/);
 assert.match(renderToStaticMarkup(React.createElement(Ring,{score:0,maximum:0,available:false,onOpen(){}})),/Results unavailable/);
});
test('aggregate raw marks, not averages; support zero, fractions and dense totals',()=>{
 const file=parse(source);assert.deepEqual(totals([...file.evidence,{...file.evidence[0],score:1,maxScore:10}]),{score:5,maximum:15});
 assert.deepEqual(slices(0,3)?.map(s=>s.earned),[0,0,0]);assert.equal(slices(2.5,3)?.at(-1)?.earned,.5);
 assert.equal(slices(70,100)?.length,100);assert.equal(slices(700,1000),null);assert.deepEqual(slices(0,0),[]);
 assert.match(renderToStaticMarkup(React.createElement(Ring,{score:0,maximum:0,onOpen(){}})),/Not assessed/);
});
test('reject entire invalid snapshots before replacing results',()=>{
 for(const value of [{...source,mapVersion:'1.0'},{...source,confidence:{}},{...source,packageId:'480ed739-2eef-4382-84b0-7edc11b46508'},{...source,evidence:[...source.evidence,...source.evidence]},...['absent','missing','exempt','pending'].map(status=>({...source,evidence:[{...source.evidence[0],status}]})),{...source,evidence:[{...source.evidence[0],nodeId:'unknown'}]},{...source,evidence:[{...source.evidence[0],score:6}]}])assert.throws(()=>parse(value));
 assert.throws(()=>parseResults('{',known,packageId));assert.throws(()=>parseResults(' '.repeat(2*1024*1024+1),known,packageId));
});
test('new revisions update results without changing separately saved confidence',()=>{
 const current=parse(source),confidence={'node-a':'confident' as const},saved=confidenceFile(confidence,packageId);
 const next=parse({...source,revision:2,evidence:[{...source.evidence[0],score:2}]});
 assert.equal(acceptResults(current,next).evidence[0].score,2);
 assert.deepEqual(parseConfidence(saved,known,packageId),confidence);
 assert.throws(()=>acceptResults(next,current),/older/);
 assert.throws(()=>acceptResults(current,parse({...source,evidence:[]})),/same revision/);
 assert.notEqual(confidenceKey(packageId),confidenceKey('another-package'));
 assert.throws(()=>parseConfidence(saved,known,'another-package'));
});

test('assessment timeline accumulates marks by date and keeps undated legacy evidence separate',async()=>{
 const {assessmentDates,throughDate,undatedCount}=await import('../shared/timeline');
 const records=[{...source.evidence[0],assessmentDate:'2026-09-01'},
  {...source.evidence[0],assessmentId:'B',questionId:'Q2',score:1,maxScore:3,assessmentDate:'2026-10-01'},
  {...source.evidence[0],assessmentId:'C',questionId:'Q3',score:0,maxScore:2,assessmentDate:'2026-09-01'},
  {...source.evidence[0],assessmentId:'legacy',questionId:'Q4',score:2,maxScore:2}];
 const catalog=[{id:'A01',title:'First',date:'2026-09-01'},{id:'B',title:'Second',date:'2026-10-01'},{id:'C',title:'Same day',date:'2026-09-01'},{id:'pending',title:'No graded evidence',date:'2026-11-01'}];
 const file=parse({...source,evidence:records,assessments:catalog}),before=JSON.stringify(file),saved=confidenceFile({'node-a':'confident'},packageId);
 assert.deepEqual(assessmentDates(file.evidence,file.assessments),['2026-09-01','2026-10-01','2026-11-01']);
 assert.equal(throughDate(file.evidence,'',file.assessments).length,0);
 assert.deepEqual(totals([...throughDate(file.evidence,'2026-09-01',file.assessments)]),{score:4,maximum:7});
 assert.deepEqual(totals([...throughDate(file.evidence,'2026-10-01',file.assessments)]),{score:5,maximum:10});
 assert.deepEqual(totals([...throughDate(file.evidence,null,file.assessments)]),{score:7,maximum:12});
 assert.equal(undatedCount(file.evidence,file.assessments),1);
 assert.equal(JSON.stringify(file),before);
 assert.deepEqual(parseConfidence(saved,known,packageId),{'node-a':'confident'});
 const legacy=parse(source);assert.equal(assessmentDates(legacy.evidence).length,0);assert.equal(throughDate(legacy.evidence,'2026-12-01').length,0);
});
test('assessment dates must be real and consistent without rejecting old undated snapshots',()=>{
 assert.doesNotThrow(()=>parse(source));
 assert.throws(()=>parse({...source,evidence:[{...source.evidence[0],assessmentDate:'2026-02-30'}]}));
 assert.throws(()=>parse({...source,evidence:[{...source.evidence[0],assessmentDate:'2026-10-01'}],assessments:[{id:'A01',title:'First',date:'2026-09-01'}]}));
});
