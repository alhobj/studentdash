import {test} from 'node:test';
import assert from 'node:assert/strict';
import {nodeAvailability,distances,availabilityLabel} from '../simple/src/highlighting';
import map from '../simple/src/data/map.json';
const nodes=['a','b','c','d'].map(id=>({id}));
const edges=[['a','b'],['b','c'],['a','d'],['c','d']].map(([source,target],i)=>({source,target,id:String(i),type:'prerequisite'}));
test('roots are available, marked cards stay neutral, and every earlier prerequisite must be marked',()=>{
 const empty=nodeAvailability(nodes,edges,new Set());assert.equal(empty.get('a'),'unlocked');assert.equal(empty.get('b'),'locked');
 const ready=nodeAvailability(nodes,edges,new Set(['a','b','c']));assert.equal(ready.get('d'),'unlocked');assert.equal(ready.get('a'),'marked');
 // Marking a direct prerequisite out of order does not bypass its own prerequisites.
 const outOfOrder=nodeAvailability(nodes,edges,new Set(['b','c']));assert.equal(outOfOrder.get('c'),'marked');assert.equal(outOfOrder.get('d'),'locked');
 assert.equal(nodeAvailability(nodes,edges,new Set(['a','c'])).get('d'),'locked');
});
test('Entropy and Molar volume follow the complete real graph, independently of selection and filters',()=>{
 for(const code of ['Reactivity 1.4.1','Structure 1.5.3']){
  const node=map.nodes.find(n=>n.code===code)!;assert.ok(node);
  const ancestors=[...distances(node.id,map.edges,true).keys()].filter(id=>id!==node.id);
  assert.ok(ancestors.length>0);
  const marked=new Set(ancestors),copy=[...marked];
  assert.equal(nodeAvailability(map.nodes,map.edges,marked).get(node.id),'unlocked');
  assert.deepEqual([...marked],copy);
  for(const missing of ancestors){const partial=new Set(marked);partial.delete(missing);assert.equal(nodeAvailability(map.nodes,map.edges,partial).get(node.id),'locked');}
 }
});
test('only prerequisites affect readiness; cycles and unknown endpoints fail explicitly',()=>{
 const related=[...edges,{id:'related',source:'unknown',target:'a',type:'related'}];
 assert.equal(nodeAvailability(nodes,related,new Set()).get('a'),'unlocked');
 assert.throws(()=>nodeAvailability(nodes,[...edges,{id:'bad',source:'unknown',target:'a',type:'prerequisite'}],new Set()),/Unknown/);
 assert.throws(()=>nodeAvailability(nodes,[...edges,{id:'cycle',source:'d',target:'a',type:'prerequisite'}],new Set()),/cycle/);
});
test('readiness descriptions distinguish locked, available and already marked nodes',()=>{
 assert.equal(availabilityLabel('locked'),'Locked: one or more prerequisite nodes are not marked.');
 assert.equal(availabilityLabel('unlocked'),'Unlocked: all prerequisite nodes are marked.');
 assert.equal(availabilityLabel('marked'),'Temporarily marked.');
 assert.equal(availabilityLabel(undefined),'');
});
