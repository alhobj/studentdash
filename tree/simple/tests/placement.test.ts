import {test} from 'node:test';
import assert from 'node:assert/strict';
import data from '../src/data/map.json';
import {buildLayout,routeEdges} from '../src/layout';
const edges=data.edges.filter(e=>e.type==='prerequisite');
for(const mode of ['top','bottom'] as const)test(`${mode}: shorter routes and terminal nodes outside continuing branches`,()=>{
 const layout=buildLayout(data.nodes,edges,mode),routes=routeEdges(layout,edges);
 const length=Object.values(routes).reduce((sum,r)=>sum+r.points.slice(1).reduce((s,p,i)=>s+Math.abs(p.x-r.points[i].x)+Math.abs(p.y-r.points[i].y),0),0);
 // Previous measured totals: 469996 top, 734751 bottom. Require a meaningful reduction.
 assert.ok(length<(mode==='top'?400000:600000),`route length ${length}`);
 const continuing=new Set(edges.map(e=>e.source));
 const rows=new Map<number,string[]>();
 for(const [id,p] of Object.entries(layout.positions)){if(!rows.has(p.y))rows.set(p.y,[]);rows.get(p.y)!.push(id);}
 for(const row of rows.values()) {
  row.sort((a,b)=>layout.positions[a].x-layout.positions[b].x);
  const through=row.filter(id=>continuing.has(id));
  if(through.length)assert.ok(row.slice(row.indexOf(through[0]),row.indexOf(through.at(-1)!)+1).every(id=>continuing.has(id)),'terminal nodes must flank continuing branches');
 }
 assert.deepEqual(buildLayout([...data.nodes].reverse(),edges,mode).positions,layout.positions,'input order does not change layout');
});
test('two successors stay adjacent instead of interleaving separate families',()=>{
 const nodes=['a','b','a1','a2','b1','b2'].map(id=>({id,group:0}));
 const edges=[['a','a1'],['a','a2'],['b','b1'],['b','b2']].map(([source,target],i)=>({id:String(i),source,target,type:'prerequisite'}));
 const p=buildLayout(nodes,edges).positions;
 const order=['a1','a2','b1','b2'].sort((a,b)=>p[a].x-p[b].x);
 assert.equal(Math.abs(order.indexOf('a1')-order.indexOf('a2')),1);
 assert.equal(Math.abs(order.indexOf('b1')-order.indexOf('b2')),1);
});
