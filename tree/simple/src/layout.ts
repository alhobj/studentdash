/** Prerequisite-ranked nodes and obstacle-aware orthogonal routes, in flow coordinates.
 * Geometry uses the full map, so filtering does not move cards or invalidate routes.
 * Placement is a reading aid, never a declaration of prerequisite relationships.
 */
export const CARD_WIDTH = 264;
export const CARD_HEIGHT = 172;
export const ROUTE_CLEARANCE = 18;
export type Point = {x:number;y:number};
export type Rect = Point & {id:string;width:number;height:number};
export type LayoutNode = {id:string;group:number;prerequisites?:string[]};
export type LayoutEdge = {id:string;source:string;target:string;type?:string};
export type BranchLabel = Rect & {group:number;text:string};
export type Layout = {
  positions:Record<string,Point>; labels:BranchLabel[]; obstacles:Rect[];
  bounds:{x:number;y:number;width:number;height:number};
};

/** Top ranks use longest incoming paths. Bottom ranks align sinks by longest outgoing paths. */
export type SortMode = 'top' | 'bottom';
export function buildLayout(nodes:readonly LayoutNode[], edges:readonly LayoutEdge[], sort:SortMode='top',geometry:{width?:number;height?:number;gapX?:number;gapY?:number}={}):Layout {
 const cardWidth=geometry.width??CARD_WIDTH,cardHeight=geometry.height??CARD_HEIGHT;
 const positions:Record<string,Point>={}, ids=new Set(nodes.map(n=>n.id));
 const parents=new Map(nodes.map(n=>[n.id,[] as string[]]));
 const children=new Map(nodes.map(n=>[n.id,[] as string[]]));
 for(const e of edges.filter(e=>e.type==='prerequisite')) {
  if(!ids.has(e.source)||!ids.has(e.target))throw Error('Unknown prerequisite endpoint: '+e.id);
  if(!parents.get(e.target)!.includes(e.source)){parents.get(e.target)!.push(e.source);children.get(e.source)!.push(e.target);}
 }
 const depth=new Map<string,number>(), active=new Set<string>();
 function rank(id:string):number {
  if(active.has(id))throw Error('Prerequisite cycle at '+id);
  if(depth.has(id))return depth.get(id)!;
  active.add(id);const d=Math.max(-1,...(sort==='bottom'?children:parents).get(id)!.map(rank))+1;
  active.delete(id);depth.set(id,d);return d;
 }
 for(const n of nodes)rank(n.id);
 // Distance from a sink counts remaining edges, not the number of descendants.
 // Reverse the ranks so dependencies still point downwards in both modes.
 if(sort==='bottom'){const height=Math.max(0,...depth.values());for(const [id,d] of depth)depth.set(id,height-d);}
 const rows=new Map<number,string[]>();
 for(const n of nodes){const d=depth.get(n.id)!;if(!rows.has(d))rows.set(d,[]);rows.get(d)!.push(n.id);}
 const deepest=Math.max(0,...depth.values());
 const gapX=cardWidth+(geometry.gapX??56),gapY=cardHeight+(geometry.gapY??104);
 // Barycentric sweeps reduce crossings across the whole dependency network.
 // All rows share a centre, preventing cumulative rightward drift on long chains.
 for(const row of rows.values())row.sort((a,b)=>a.localeCompare(b));
 const fractions=()=>new Map([...rows.values()].flatMap(row=>row.map((id,i)=>[id,(i+.5)/row.length] as [string,number])));
 for(let pass=0;pass<8;pass++) {
  for(const forward of [true,false]) {
   const levels=Array.from({length:deepest+1},(_,i)=>forward?i:deepest-i);
   for(const d of levels) {
    const row=rows.get(d)||[],order=fractions();
    const neighbours=forward?parents:children;
    const weight=(id:string)=>{const links=neighbours.get(id)!;return links.length?links.reduce((sum,p)=>sum+order.get(p)!,0)/links.length:order.get(id)!;};
    row.sort((a,b)=>weight(a)-weight(b)||a.localeCompare(b));
   }
  }
 }
 const widest=Math.max(1,...[...rows.values()].map(r=>r.length));
 const offsets=new Map([...rows].map(([d,row])=>[d,(widest-row.length)/2]));
 const x=new Map<string,number>();
 const update=(d:number)=>rows.get(d)!.forEach((id,i)=>x.set(id,offsets.get(d)!+i));
 for(const d of rows.keys())update(d);
 const links=[...children].flatMap(([source,targets])=>targets.map(target=>[source,target]));
 const siblings=[...children.values()].filter(c=>c.length>1);
 // Minimise horizontal edge travel and sibling spread. Vertical ranks are fixed.
 // This is deterministic local optimisation, not a claim of a global minimum.
 const cost=()=>links.reduce((sum,[a,b])=>sum+Math.abs(x.get(a)!-x.get(b)!),0)
  +siblings.reduce((sum,c)=>sum+.65*(Math.max(...c.map(id=>x.get(id)!))-Math.min(...c.map(id=>x.get(id)!))),0);
 const isLeaf=(id:string)=>children.get(id)!.length===0;
 // Terminal nodes flank the continuing branches; pick their cheaper left/right split.
 for(const [d,row] of rows) {
  const leaves=row.filter(isLeaf),through=row.filter(id=>!isLeaf(id));
  if(!leaves.length||!through.length)continue;
  let best=[...row],score=Infinity;
  const start=leaves.length>1?1:0,end=leaves.length>1?leaves.length-1:leaves.length;
  for(let split=start;split<=end;split++) {
   row.splice(0,row.length,...leaves.slice(0,split),...through,...leaves.slice(split));update(d);
   const value=cost();if(value<score){score=value;best=[...row];}
  }
  row.splice(0,row.length,...best);update(d);
 }
 const valid=(row:string[])=>{const inner=row.map((id,i)=>!isLeaf(id)?i:-1).filter(i=>i>=0);return !inner.length||row.slice(inner[0],inner.at(-1)!+1).every(id=>!isLeaf(id));};
 for(let pass=0;pass<12;pass++) {
  let improved=false;
  for(const d of [...rows.keys()].sort((a,b)=>pass%2?b-a:a-b)) {
   const row=rows.get(d)!;
   let score=cost();
   for(let i=0;i<row.length;i++)for(let j=i+1;j<row.length;j++) {
    [row[i],row[j]]=[row[j],row[i]];
    if(valid(row)) {
     update(d);const candidate=cost();
     if(candidate<score-1e-8){score=candidate;improved=true;continue;}
    }
    [row[i],row[j]]=[row[j],row[i]];update(d);
   }
   // Shift whole rows towards their neighbours without collisions or widening the map.
   let best=offsets.get(d)!;
   for(let offset=0;offset<=widest-row.length;offset+=.5) {
    offsets.set(d,offset);update(d);const candidate=cost();
    if(candidate<score-1e-8){score=candidate;best=offset;improved=true;}
   }
   offsets.set(d,best);update(d);
  }
  if(!improved)break;
 }
 for(const [id,value] of x)positions[id]={x:40+value*gapX,y:40+depth.get(id)!*gapY};
 const obstacles=nodes.map(n=>({id:n.id,...positions[n.id],width:cardWidth,height:cardHeight}));
 return {positions,labels:[],obstacles,bounds:{x:0,y:0,width:Math.max(1,...obstacles.map(r=>r.x+r.width))+40,height:Math.max(1,...obstacles.map(r=>r.y+r.height))+40}};
}

/** True only when a straight segment enters the rectangle's interior.
 * Boundary contact is allowed; routes are calculated with expanded obstacles.
 */
export function segmentHitsRect(a:Point,b:Point,r:Rect):boolean {
  if(a.y===b.y)return a.y>r.y && a.y<r.y+r.height && Math.max(a.x,b.x)>r.x && Math.min(a.x,b.x)<r.x+r.width;
  if(a.x===b.x)return a.x>r.x && a.x<r.x+r.width && Math.max(a.y,b.y)>r.y && Math.min(a.y,b.y)<r.y+r.height;
  throw Error('Routing segments must be horizontal or vertical');
}

function expanded(r:Rect):Rect {
  return {...r,x:r.x-ROUTE_CLEARANCE,y:r.y-ROUTE_CLEARANCE,width:r.width+2*ROUTE_CLEARANCE,height:r.height+2*ROUTE_CLEARANCE};
}
function simplify(points:Point[]):Point[] {
  const out:Point[]=[];
  for(const p of points) {
    if(out.length && out.at(-1)!.x===p.x && out.at(-1)!.y===p.y)continue;
    while(out.length>1) {
      const a=out[out.length-2],b=out[out.length-1];
      if((a.x===b.x&&b.x===p.x)||(a.y===b.y&&b.y===p.y))out.pop();else break;
    }
    out.push(p);
  }
  return out;
}
/** Corner radius is smaller than obstacle clearance: each curve remains inside
 * the safe corridor even where it cuts a corner of an expanded rectangle.
 */
export function roundedPath(points:readonly Point[],radius=8):string {
  if(!points.length)return '';
  let path=`M ${points[0].x} ${points[0].y}`;
  for(let i=1;i<points.length-1;i++) {
    const a=points[i-1],b=points[i],c=points[i+1];
    const ab=Math.hypot(b.x-a.x,b.y-a.y),bc=Math.hypot(c.x-b.x,c.y-b.y);
    const r=Math.min(radius,ab/2,bc/2);
    const before={x:b.x+(a.x-b.x)*r/ab,y:b.y+(a.y-b.y)*r/ab};
    const after={x:b.x+(c.x-b.x)*r/bc,y:b.y+(c.y-b.y)*r/bc};
    path+=` L ${before.x} ${before.y} Q ${b.x} ${b.y} ${after.x} ${after.y}`;
  }
  if(points.length>1)path+=` L ${points.at(-1)!.x} ${points.at(-1)!.y}`;
  return path;
}

// Small binary min-heap used by A*; avoids sorting the whole frontier per step.
class Queue {
  private heap:{id:number;cost:number}[]=[];
  push(id:number,cost:number) {
    const item={id,cost};let i=this.heap.length;this.heap.push(item);
    while(i){const p=(i-1)>>1;if(this.heap[p].cost<=cost)break;this.heap[i]=this.heap[p];i=p;}this.heap[i]=item;
  }
  pop() {
    const first=this.heap[0],last=this.heap.pop();
    if(this.heap.length&&last){let i=0;while(i*2+1<this.heap.length){let c=i*2+1;if(c+1<this.heap.length&&this.heap[c+1].cost<this.heap[c].cost)c++;if(this.heap[c].cost>=last.cost)break;this.heap[i]=this.heap[c];i=c;}this.heap[i]=last;}
    return first;
  }
  get size(){return this.heap.length;}
}

type Grid = {xs:number[];ys:number[];links:Map<number,{id:number;distance:number}[]>;xIndex:Map<number,number>;yIndex:Map<number,number>};
function makeGrid(layout:Layout):Grid {
  const obstacles=layout.obstacles.map(expanded);
  const xSet=new Set<number>([-80,layout.bounds.width+80]);
  const ySet=new Set<number>([-80,layout.bounds.height+80]);
  for(const r of obstacles) {
    xSet.add(r.x);xSet.add(r.x+r.width);ySet.add(r.y);ySet.add(r.y+r.height);
  }
  for(const [id,p] of Object.entries(layout.positions)){const card=layout.obstacles.find(r=>r.id===id);xSet.add(p.x+(card?.width??CARD_WIDTH)/2);}
  const xs=[...xSet].sort((a,b)=>a-b),ys=[...ySet].sort((a,b)=>a-b);
  const xIndex=new Map(xs.map((x,i)=>[x,i])),yIndex=new Map(ys.map((y,i)=>[y,i]));
  const width=xs.length,height=ys.length;
  const blocked=new Uint8Array(width*height);
  // Mark interiors in one pass per rectangle, then connect neighbouring free
  // points only when the entire segment is clear (thin headings also count).
  for(const r of obstacles)for(let yi=yIndex.get(r.y)!+1;yi<yIndex.get(r.y+r.height)!;yi++) {
    for(let xi=xIndex.get(r.x)!+1;xi<xIndex.get(r.x+r.width)!;xi++)blocked[yi*width+xi]=1;
  }
  const links=new Map<number,{id:number;distance:number}[]>();
  function connect(a:number,b:number,p:Point,q:Point) {
    if(blocked[a]||blocked[b]||obstacles.some(r=>segmentHitsRect(p,q,r)))return;
    const distance=Math.abs(p.x-q.x)+Math.abs(p.y-q.y);
    if(!links.has(a))links.set(a,[]);if(!links.has(b))links.set(b,[]);
    links.get(a)!.push({id:b,distance});links.get(b)!.push({id:a,distance});
  }
  for(let yi=0;yi<height;yi++)for(let xi=0;xi<width;xi++) {
    const id=yi*width+xi,p={x:xs[xi],y:ys[yi]};
    if(xi+1<width)connect(id,id+1,p,{x:xs[xi+1],y:p.y});
    if(yi+1<height)connect(id,id+width,p,{x:p.x,y:ys[yi+1]});
  }
  return {xs,ys,links,xIndex,yIndex};
}

export type EdgeRoute={points:Point[];path:string};
const gridCache=new WeakMap<Layout,Grid>();
const routeCache=new WeakMap<Layout,Map<string,EdgeRoute>>();
export function routeEdges(layout:Layout,edges:readonly LayoutEdge[]):Record<string,EdgeRoute> {
  let grid=gridCache.get(layout);if(!grid){grid=makeGrid(layout);gridCache.set(layout,grid);}
  let cache=routeCache.get(layout);if(!cache){cache=new Map();routeCache.set(layout,cache);}
  const {xs,ys,links,xIndex,yIndex}=grid,width=xs.length;
  const at=(id:number):Point=>({x:xs[id%width],y:ys[Math.floor(id/width)]});
  const result:Record<string,EdgeRoute>={};
  for(const edge of edges) {
    const key=edge.source+'\0'+edge.target;
    if(cache.has(key)){result[edge.id]=cache.get(key)!;continue;}
    const source=layout.positions[edge.source],target=layout.positions[edge.target];
    if(!source||!target)throw Error('Unknown routing endpoint: '+edge.id);
    const sourceCard=layout.obstacles.find(r=>r.id===edge.source),targetCard=layout.obstacles.find(r=>r.id===edge.target);
    const a={x:source.x+(sourceCard?.width??CARD_WIDTH)/2,y:source.y+(sourceCard?.height??CARD_HEIGHT)};
    const b={x:target.x+(targetCard?.width??CARD_WIDTH)/2,y:target.y};
    const start=yIndex.get(a.y+ROUTE_CLEARANCE)!*width+xIndex.get(a.x)!;
    const goal=yIndex.get(b.y-ROUTE_CLEARANCE)!*width+xIndex.get(b.x)!;
    const costs=new Map<number,number>([[start,0]]),previous=new Map<number,number>();
    const queue=new Queue();queue.push(start,0);const closed=new Set<number>();
    while(queue.size) {
      const {id}=queue.pop()!;if(closed.has(id))continue;if(id===goal)break;closed.add(id);
      for(const next of links.get(id)||[]) {
        const cost=costs.get(id)!+next.distance;
        if(cost>=(costs.get(next.id)??Infinity))continue;
        costs.set(next.id,cost);previous.set(next.id,id);
        const p=at(next.id);queue.push(next.id,cost+Math.abs(p.x-b.x)+Math.abs(p.y-(b.y-ROUTE_CLEARANCE)));
      }
    }
    if(start!==goal&&!previous.has(goal))throw Error('No obstacle-free route: '+edge.id);
    const points:Point[]=[];let cursor=goal;
    while(cursor!==start){points.push(at(cursor));cursor=previous.get(cursor)!;}points.push(at(start));points.reverse();
    const simplified=simplify([a,...points,b]);
    const route={points:simplified,path:roundedPath(simplified)};cache.set(key,route);result[edge.id]=route;
  }
  return result;
}
