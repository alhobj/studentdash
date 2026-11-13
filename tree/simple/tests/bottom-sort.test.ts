import {test} from 'node:test';
import assert from 'node:assert/strict';
import data from '../src/data/map.json';
import {buildLayout,routeEdges,segmentHitsRect,CARD_WIDTH,CARD_HEIGHT} from '../src/layout';

test('bottom sort aligns sinks by longest remaining chain, including uneven branches and isolated nodes',()=>{
 const nodes=['a','b','c','d','e','f'].map(id=>({id,group:0}));
 const edges=[['a','b'],['b','c'],['c','d'],['a','e']].map(([source,target],i)=>({id:String(i),source,target,type:'prerequisite'}));
 const top=buildLayout(nodes,edges),bottom=buildLayout(nodes,edges,'bottom');
 const p=bottom.positions;
 assert.equal(p.d.y,p.e.y);assert.equal(p.d.y,p.f.y);
 const gap=p.d.y-p.c.y;
 assert.ok(gap>CARD_HEIGHT);assert.equal(p.c.y-p.b.y,gap);assert.equal(p.b.y-p.a.y,gap);
 assert.notEqual(top.positions.e.y,p.e.y);
 assert.deepEqual(buildLayout(nodes,edges,'top'),top);
 assert.throws(()=>buildLayout(nodes,[...edges,{id:'cycle',source:'d',target:'a',type:'prerequisite'}],'bottom'),/cycle/);
});

test('bottom sort preserves every real connection and routes safely for all filters',()=>{
 const edges=data.edges.filter(e=>e.type==='prerequisite');
 const layout=buildLayout(data.nodes,edges,'bottom');
 const remaining=new Map<string,number>();
 function height(id:string):number{if(remaining.has(id))return remaining.get(id)!;const h=Math.max(-1,...edges.filter(e=>e.source===id).map(e=>height(e.target)))+1;remaining.set(id,h);return h;}
 const longest=Math.max(...data.nodes.map(n=>height(n.id)));
 const bottom=Math.max(...Object.values(layout.positions).map(p=>p.y));
 const top=Math.min(...Object.values(layout.positions).map(p=>p.y));
 for(const n of data.nodes)assert.equal(layout.positions[n.id].y,bottom-height(n.id)*(bottom-top)/longest);
 for(const a of layout.obstacles)for(const b of layout.obstacles)if(a.id!==b.id)assert.ok(!(a.x<b.x+CARD_WIDTH&&a.x+CARD_WIDTH>b.x&&a.y<b.y+CARD_HEIGHT&&a.y+CARD_HEIGHT>b.y));
 const routes=routeEdges(layout,edges);assert.equal(Object.keys(routes).length,edges.length);
 for(const level of ['all','SL','HL']){
  const ids=new Set(data.nodes.filter(n=>level==='all'||n.level===(level==='SL'?'shared':'HL')).map(n=>n.id));
  for(const e of edges.filter(e=>ids.has(e.source)&&ids.has(e.target))){
   assert.ok(layout.positions[e.source].y+CARD_HEIGHT<layout.positions[e.target].y);
   const pts=routes[e.id].points;
   for(let i=1;i<pts.length;i++)for(const r of layout.obstacles)if(r.id!==e.source&&r.id!==e.target)assert.ok(!segmentHitsRect(pts[i-1],pts[i],r),`${e.id} crosses ${r.id}`);
  }
 }
});
