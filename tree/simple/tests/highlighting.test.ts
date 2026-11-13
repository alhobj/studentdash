import {test} from 'node:test';
import assert from 'node:assert/strict';
import {renderToStaticMarkup} from 'react-dom/server';
import React from 'react';
import {trace,distances,maximumDepth,traceStyle,SECTION_NAMES} from '../src/highlighting';
import data from '../src/data/map.json';
import {HighlightControls,useHighlightSettings} from '../src/HighlightControls';
const edges=[['a','b'],['b','c'],['c','d'],['a','x'],['x','c']].map(([source,target],i)=>({id:String(i),source,target,type:'prerequisite'}));
test('defaults trace one successor level and no predecessors; sections do not affect reachability',()=>{
 const result=trace('b',edges,0,1);
 assert.deepEqual([...result.strength.keys()],['c']);assert.equal(result.strength.get('c'),1);
 assert.deepEqual([...result.edgeStrength.keys()],['1']);
 assert.equal(result.strength.has('a'),false);assert.equal(result.strength.has('x'),false);
});
test('before and after walk links across chapters, use shortest distance and progressively fade',()=>{
 const result=trace('a',edges,0,3);
 assert.equal(result.strength.get('b'),1);assert.equal(result.strength.get('c'),Math.sqrt(.42));assert.equal(result.strength.get('d'),.42);
 assert.ok(result.strength.get('d')!<result.strength.get('c')!);
 assert.equal(result.labels.get('d'),'3 levels after');
 assert.deepEqual([...distances('c',edges,true)].sort(),[['a',2],['b',1],['c',0],['x',1]]);
 assert.equal(trace('c',edges,maximumDepth(edges),0).strength.size,3);
 assert.equal(trace('b',edges,0,0).strength.size,0);assert.equal(trace(null,edges,10,10).strength.size,0);
});
test('all-before includes redundant and cross-depth prerequisite connections, but no related links',()=>{
 const graph=[...edges,{id:'shortcut',source:'a',target:'c',type:'prerequisite'},{id:'related',source:'z',target:'c',type:'related'}];
 const result=trace('c',graph,maximumDepth(graph),0);
 for(const id of ['0','1','3','4','shortcut'])assert.ok(result.edgeStrength.has(id));
 assert.equal(result.edgeStrength.has('related'),false);assert.equal(result.strength.has('z'),false);
 assert.equal(distances('a',[...edges,{id:'loop',source:'d',target:'a',type:'prerequisite'}]).size,5);
 assert.throws(()=>maximumDepth([...edges,{id:'loop',source:'d',target:'a',type:'prerequisite'}]),/cycle/);
});
test('section intersection reveals existing cross-topic links without inventing prerequisites',()=>{
 const max=maximumDepth(data.edges);assert.ok(max>=3);
 const sections=new Set([2]);
 for(const selected of data.nodes.filter(n=>n.group===4)){
  const result=trace(selected.id,data.edges,max,0);
  const expected=new Set<string>();
  const visit=(id:string)=>{for(const e of data.edges.filter(e=>e.type==='prerequisite'&&e.target===id)){if(!expected.has(e.source)){expected.add(e.source);visit(e.source);}}};
  visit(selected.id);
  assert.deepEqual(new Set(result.strength.keys()),expected);
  const intersection=data.nodes.filter(n=>sections.has(n.group)&&result.strength.has(n.id));
  assert.ok(intersection.every(n=>expected.has(n.id)));
 }
 // A known S3 → R2 fixture verifies the user's proposed combined highlighting workflow.
 const result=trace('r2',[{id:'cross',source:'s3',target:'r2',type:'prerequisite'}],1,0);
 assert.ok(result.strength.has('s3'));assert.equal(SECTION_NAMES[2],'Structure 3');assert.equal(SECTION_NAMES[4],'Reactivity 2');
 assert.notEqual(traceStyle(.08)['--trace-fill'],'rgb(255, 255, 255)');
});
test('controls expose six independent section buttons and labelled native sliders with correct defaults',()=>{
 function Controls(){const settings=useHighlightSettings();assert.equal(settings.showUnlocked,false);return React.createElement(HighlightControls,{settings,max:14});}
 const html=renderToStaticMarkup(React.createElement(Controls));
 for(const name of SECTION_NAMES)assert.ok(html.includes(name));
 assert.ok(html.includes('Unlocked nodes'));assert.ok(html.includes('class="unlock-toggle"'));
 assert.equal((html.match(/aria-pressed="false"/g)||[]).length,7);
 assert.ok(html.includes('See 0 levels before'));assert.ok(html.includes('See 1 levels after'));
 assert.equal((html.match(/type="range"/g)||[]).length,2);
 assert.ok(html.includes('aria-label="Levels before"'));assert.ok(html.includes('All (14)'));
});
