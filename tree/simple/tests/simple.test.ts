import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import data from '../src/data/map.json';
import {buildLayout,routeEdges,segmentHitsRect,CARD_WIDTH,CARD_HEIGHT} from '../src/layout';
test('all 165 stable curriculum nodes, with correct filter allocations',()=>{assert.equal(data.nodes.length,165);assert.equal(data.nodes.filter(n=>n.level==='shared').length,104);assert.equal(data.nodes.filter(n=>n.level==='HL').length,61);assert.equal(new Set(data.nodes.map(n=>n.id)).size,165);});
test('routing avoids unrelated cards and headings for every level filter',()=>{const layout=buildLayout(data.nodes,data.edges);const routes=routeEdges(layout,data.edges);for(const e of data.edges){const pts=routes[e.id].points;for(let i=1;i<pts.length;i++){for(const r of layout.obstacles.filter(r=>r.id!==e.source&&r.id!==e.target))assert.ok(!segmentHitsRect(pts[i-1],pts[i],r),`${e.id} crosses ${r.id}`);}}for(const a of data.nodes)for(const b of data.nodes){if(a.id===b.id)continue;const p=layout.positions[a.id],q=layout.positions[b.id];assert.ok(!(p.x<q.x+CARD_WIDTH&&p.x+CARD_WIDTH>q.x&&p.y<q.y+CARD_HEIGHT&&p.y+CARD_HEIGHT>q.y));}});
test('entry point and map contain no progress, identity or supporting-content features',()=>{const src=readFileSync('src/main.tsx','utf8');assert.ok(!/localStorage|sessionStorage|fetch\(|ProgressTools|GuidedPractice|explanation|assessment/i.test(src));for(const n of data.nodes)assert.deepEqual(Object.keys(n).sort(),['code','group','id','level','title']);});
test('longest prerequisite chain sets rows, with multi-parent merges and unrelated roots',()=>{
 const nodes=['a','b','c','d','e','f'].map((id,i)=>({id,group:i%3}));
 const edges=[['a','b'],['b','c'],['a','d'],['c','e'],['d','e']].map(([source,target],i)=>({id:String(i),source,target,type:'prerequisite'}));
 edges.push({id:'sequence',source:'e',target:'f',type:'sequence'});
 const p=buildLayout(nodes,edges).positions;
 assert.equal(p.a.y,p.f.y);assert.equal(p.b.y,p.d.y);assert.equal(p.c.y-p.b.y,p.b.y-p.a.y);assert.equal(p.e.y-p.c.y,p.b.y-p.a.y);
 const changed=buildLayout(nodes.map(n=>({...n,group:99})),edges).positions;assert.deepEqual(p,changed);
 assert.throws(()=>buildLayout(nodes,[...edges,{id:'cycle',source:'e',target:'a',type:'prerequisite'}]),/cycle/);
});
test('every actual prerequisite is above its dependent; every recorded root is top row',()=>{
 const l=buildLayout(data.nodes,data.edges);const incoming=new Set(data.edges.filter(e=>e.type==='prerequisite').map(e=>e.target));
 const top=Math.min(...Object.values(l.positions).map(p=>p.y));
 for(const n of data.nodes)assert.equal(l.positions[n.id].y===top,!incoming.has(n.id));
 for(const e of data.edges.filter(e=>e.type==='prerequisite'))assert.ok(l.positions[e.source].y+CARD_HEIGHT<l.positions[e.target].y);
});
