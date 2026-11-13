import {test} from 'node:test';
import assert from 'node:assert/strict';
import {map} from '../src/curriculum';
import {buildLayout,routeEdges,segmentHitsRect,CARD_WIDTH,CARD_HEIGHT,ROUTE_CLEARANCE,type Layout,type LayoutEdge} from '../src/layout';

const layout=buildLayout(map.nodes,map.edges);
function assertClear(layout:Layout,edges:readonly LayoutEdge[]) {
  const routes=routeEdges(layout,edges);
  for(const e of edges) {
    const route=routes[e.id];assert.ok(route.path.startsWith('M '));
    const first=route.points[0],last=route.points.at(-1)!;
    assert.deepEqual(first,{x:layout.positions[e.source].x+CARD_WIDTH/2,y:layout.positions[e.source].y+CARD_HEIGHT});
    assert.deepEqual(last,{x:layout.positions[e.target].x+CARD_WIDTH/2,y:layout.positions[e.target].y});
    assert.equal(route.points[1].x,first.x,'route leaves the bottom handle vertically');
    assert.ok(route.points[1].y>first.y,'route leaves below the source card');
    assert.equal(route.points.at(-2)!.x,last.x,'route enters the top handle vertically');
    assert.ok(route.points.at(-2)!.y<last.y,'route enters from above the target card');
    for(let i=1;i<route.points.length;i++) {
      const a=route.points[i-1],b=route.points[i];
      assert.ok(a.x===b.x||a.y===b.y,'orthogonal route');
      for(const obstacle of layout.obstacles) {
        if(obstacle.id===e.source&&i===1)continue;
        if(obstacle.id===e.target&&i===route.points.length-1)continue;
        // Curve radius 8 and arrow/stroke widths remain clear as well.
        const margin=ROUTE_CLEARANCE/2;
        const protectedRect={...obstacle,x:obstacle.x-margin,y:obstacle.y-margin,width:obstacle.width+2*margin,height:obstacle.height+2*margin};
        assert.ok(!segmentHitsRect(a,b,protectedRect),`${e.id} intersects ${obstacle.id}`);
      }
    }
  }
}

function assertNoOverlap(layout:Layout) {
  for(let i=0;i<layout.obstacles.length;i++)for(let j=i+1;j<layout.obstacles.length;j++) {
    const a=layout.obstacles[i],b=layout.obstacles[j];
    assert.ok(a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y,`${a.id} overlaps ${b.id}`);
  }
}

test('all cards and branch headings have non-overlapping bounding boxes',()=> {
  assertNoOverlap(layout);
  assert.equal(layout.obstacles.filter(r=>r.width===CARD_WIDTH&&r.height===CARD_HEIGHT).length,map.nodes.length);
});

test('compact normal tree keeps the simple tree ordering with smaller cards in both sorts', async()=> {
  const simple=(await import('../simple/src/data/map.json')).default;
  const {buildLayout: simpleLayout}=await import('../simple/src/layout');
  const links=(edges: typeof map.edges)=>edges.filter(e=>e.type==='prerequisite').map(e=>`${e.source}>${e.target}`).sort();
  assert.deepEqual(links(map.edges),links(simple.edges));
  for(const mode of ['top','bottom'] as const) {
    const normal=buildLayout(map.nodes,map.edges,mode);
    const original=simpleLayout(simple.nodes,simple.edges,mode);
    assert.equal(CARD_WIDTH,224);assert.equal(CARD_HEIGHT,112);
    for(const id of Object.keys(normal.positions)){
      assert.ok(Math.abs(normal.positions[id].x-(40+(original.positions[id].x-40)*(264/320)))<1e-8);
      assert.ok(Math.abs(normal.positions[id].y-(40+(original.positions[id].y-40)*(176/276)))<1e-8);
    }
    assert.ok(normal.bounds.width<original.bounds.width);assert.ok(normal.bounds.height<original.bounds.height);
    for(const e of map.edges.filter(e=>e.type==='prerequisite'))assert.ok(normal.positions[e.source].y+CARD_HEIGHT<normal.positions[e.target].y);
    assertClear(normal,map.edges);assertNoOverlap(normal);
  }
});

test('all-connections routes avoid cards and heading labels with stroke/curve clearance',()=>assertClear(layout,map.edges));

test('filtering retains positions and safe routes for level, group, search and selected neighbours',()=> {
  const scenarios=[map.nodes.filter(n=>n.level==='shared'),map.nodes.filter(n=>n.level==='HL'),...map.groups.map((_,i)=>map.nodes.filter(n=>n.group===i)),map.nodes.filter(n=>/bond|atom|Lewis/i.test(n.title))];
  for(const node of map.nodes) {
    const connected=new Set(map.edges.filter(e=>e.source===node.id||e.target===node.id).flatMap(e=>[e.source,e.target]));
    scenarios.push(map.nodes.filter(n=>connected.has(n.id)));
  }
  const before=JSON.stringify(layout.positions);
  for(const visible of scenarios){const ids=new Set(visible.map(n=>n.id));assertClear(layout,map.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)));}
  assert.equal(JSON.stringify(layout.positions),before);
});

test('routing handles backwards edges, unrelated blockers and 200-node branches',()=> {
  const nodes=Array.from({length:200},(_,i)=>({id:'n'+i,group:Math.floor(i/34)}));
  const large=buildLayout(nodes,nodes.slice(1).map((n,i)=>({id:'p'+i,source:nodes[i].id,target:n.id,type:'prerequisite'})));
  const edges=nodes.slice(1).map((n,i)=>({id:'e'+i,source:i%2?n.id:nodes[i].id,target:i%2?nodes[i].id:n.id}));
  assertClear(large,edges);
  assertNoOverlap(large);
  assert.deepEqual(buildLayout(nodes,nodes.slice(1).map((n,i)=>({id:'p'+i,source:nodes[i].id,target:n.id,type:'prerequisite'}))).positions,large.positions);
});
