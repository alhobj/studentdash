import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import data from '../src/data/map.json';
import review from '../src/data/prerequisites.json';
import {buildLayout,CARD_HEIGHT} from '../src/layout';
const moduleUrl=pathToFileURL(process.cwd()+'/scripts/build-map.mjs').href;
const {buildSimpleMap}=await import(moduleUrl);
const id=(code:string)=>'ib-2025-'+(code[0]==='S'?'structure-':'reactivity-')+code.slice(1);
const pre=data.edges.filter(e=>e.type==='prerequisite');
function before(a:string,b:string){const seen=new Set<string>();function visit(x:string):boolean{if(x===id(a))return true;if(seen.has(x))return false;seen.add(x);return pre.filter(e=>e.target===x).some(e=>visit(e.source));}return visit(id(b));}
const source={...data,nodes:data.nodes.map(n=>({...n,official:{code:n.code}}))};
test('dependency review covers all 165 nodes and survives a data resync',()=>{assert.equal(review.nodes.length,165);assert.deepEqual(new Set(review.nodes.map(n=>id(n.code))),new Set(data.nodes.map(n=>n.id)));assert.deepEqual(buildSimpleMap(source,review),data);});
test('named chemistry prerequisites precede advanced topics across chapters',()=>{for(const [a,b] of [['S3.2.6','S3.2.7'],['S2.2.1','S3.2.9'],['S2.2.5','S3.2.9'],['S3.2.2','S3.2.9'],['S1.3.5','S3.1.10'],['S3.1.8','S3.1.10'],['R3.4.8','S3.1.10'],['S2.2.3','S3.1.10'],['S1.3.1','S3.1.10'],['S3.2.9','S3.2.12'],['S3.2.10','S3.2.12'],['R2.3.2','R3.1.10'],['R3.2.2','R3.2.6'],['S2.2.2','S2.4.5'],['R2.2.4','R2.2.12']])assert.ok(before(a,b),a+' must precede '+b);});
test('only the introductory elements/compounds/mixtures statement is an entry root',()=>{const incoming=new Set(pre.map(e=>e.target));assert.deepEqual(data.nodes.filter(n=>!incoming.has(n.id)).map(n=>n.id),[id('S1.1.1')]);for(const edge of pre){const parent=data.nodes.find(n=>n.id===edge.source)!;const child=data.nodes.find(n=>n.id===edge.target)!;assert.ok(!(parent.level==='HL'&&child.level==='shared'));}});
test('all three filtered modes retain correct full-course prerequisite depths',()=>{const layout=buildLayout(data.nodes,pre);for(const level of ['all','SL','HL']){const visible=data.nodes.filter(n=>level==='all'||(level==='SL'?n.level==='shared':n.level==='HL'));const ids=new Set(visible.map(n=>n.id));for(const e of pre.filter(e=>ids.has(e.source)&&ids.has(e.target)))assert.ok(layout.positions[e.source].y+CARD_HEIGHT<layout.positions[e.target].y);}});
test('bad dependency revisions fail before replacing the generated map',()=>{const edit=structuredClone(review);edit.nodes.find(n=>n.code==='S1.1.1')!.requires=['S3.1.10'];assert.throws(()=>buildSimpleMap(source,edit));const missing=structuredClone(review);missing.nodes.pop();assert.throws(()=>buildSimpleMap(source,missing),/every/);});
test('simple app does not import the full editorial review into the browser bundle',()=>{assert.ok(!readFileSync('src/main.tsx','utf8').includes('prerequisites.json'));});
