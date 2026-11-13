import {test} from 'node:test';
import assert from 'node:assert/strict';
import {reducePrerequisiteEdges,visibleDependencyEdges} from '../simple/src/dependencies';
import {distances,nodeAvailability,trace} from '../simple/src/highlighting';
import map from '../simple/src/data/map.json';
import {buildLayout,routeEdges,segmentHitsRect} from '../src/layout';
const edges=[['a','b'],['b','c'],['a','c']].map(([source,target],i)=>({id:String(i),source,target,type:'prerequisite'}));
test('A to B to C removes A to C, preserving non-prerequisite links and input data',()=>{
 const input=[...edges,{id:'related',source:'a',target:'c',type:'related'}],before=JSON.stringify(input);
 const reduced=reducePrerequisiteEdges(input);
 assert.deepEqual(reduced.map(e=>e.id),['0','1','related']);assert.equal(JSON.stringify(input),before);
 assert.deepEqual(reducePrerequisiteEdges(reduced),reduced);
 assert.deepEqual(reducePrerequisiteEdges([...edges,edges[0]]),edges.slice(0,2));
 assert.throws(()=>reducePrerequisiteEdges([...edges,{id:'loop',source:'c',target:'a',type:'prerequisite'}]),/cycle/);
});
test('the entropy shortcut disappears while the complete course retains exactly the same reachability',()=>{
 const full=map.edges.filter(e=>e.type==='prerequisite'),reduced=reducePrerequisiteEdges(full);
 const states=map.nodes.find(n=>n.code==='Structure 1.1.2')!.id,system=map.nodes.find(n=>n.code==='Reactivity 1.1.1')!.id,entropy=map.nodes.find(n=>n.code==='Reactivity 1.4.1')!.id;
 const has=(source:string,target:string)=>reduced.some(e=>e.source===source&&e.target===target);
 assert.ok(full.some(e=>e.source===states&&e.target===entropy));assert.equal(has(states,entropy),false);
 assert.ok(has(states,system));assert.ok(has(system,entropy));assert.ok(reduced.length<full.length);
 for(const node of map.nodes)assert.deepEqual(new Set(distances(node.id,full).keys()),new Set(distances(node.id,reduced).keys()));
 for(const edge of reduced)assert.equal(distances(edge.source,reduced.filter(e=>e!==edge)).has(edge.target),false,'every remaining arrow is essential');
});
test('filtering restores an existing shortcut only when its visible alternative disappears',()=>{
 assert.deepEqual(visibleDependencyEdges(edges,new Set(['a','b','c'])).map(e=>e.id),['0','1']);
 const projected=visibleDependencyEdges(edges,new Set(['a','c']));assert.deepEqual(projected.map(e=>e.id),['2']);
 assert.deepEqual(visibleDependencyEdges(edges.slice(0,2),new Set(['a','c'])),[],'never invent a new edge');
 const traced=trace('a',reducePrerequisiteEdges(edges),0,2,projected);
 assert.equal(traced.labels.get('c'),'2 levels after');assert.ok(traced.edgeStrength.has('2'));
 assert.deepEqual([...trace('a',reducePrerequisiteEdges(edges),0,1).strength.keys()],['b']);
});
test('unlocked states stay identical after reduction, including out-of-order and partial marks',()=>{
 const reduced=reducePrerequisiteEdges(map.edges);
 const scenarios=[new Set<string>(),new Set(map.nodes.map(n=>n.id)),...map.nodes.map(n=>new Set([n.id])),...map.nodes.map(n=>new Set([...distances(n.id,map.edges,true).keys()].filter(id=>id!==n.id)))];
 for(const marked of scenarios)assert.deepEqual(nodeAvailability(map.nodes,map.edges,marked),nodeAvailability(map.nodes,reduced,marked));
});
test('reduced visible routes remain safe in both sort modes and each SL/HL filter',()=>{
 for(const mode of ['top','bottom'] as const){
  const layout=buildLayout(map.nodes,map.edges,mode),positions=JSON.stringify(layout.positions);
  for(const nodes of [map.nodes,map.nodes.filter(n=>n.level==='shared'),map.nodes.filter(n=>n.level==='HL')]){
   const visible=visibleDependencyEdges(map.edges,new Set(nodes.map(n=>n.id))),routes=routeEdges(layout,visible);
   for(const edge of visible){const pts=routes[edge.id].points;for(let i=1;i<pts.length;i++)for(const rect of layout.obstacles)if(rect.id!==edge.source&&rect.id!==edge.target)assert.equal(segmentHitsRect(pts[i-1],pts[i],rect),false);}
  }
  assert.equal(JSON.stringify(layout.positions),positions);
 }
});
