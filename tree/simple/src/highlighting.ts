/** Highlighting follows prerequisite links, never visual rows or syllabus numbering. */
export type TraceEdge = {id:string;source:string;target:string;type?:string};
export const SECTION_NAMES=['Structure 1','Structure 2','Structure 3','Reactivity 1','Reactivity 2','Reactivity 3'];
export const SECTION_COLORS=['#2563a6','#16806a','#8750a4','#94560d','#bd4558','#576b2c'];
export function sectionStyle(group:number){return {'--section-color':SECTION_COLORS[group]||'#52665b'};}
export function distances(selected:string|null,edges:readonly TraceEdge[],reverse=false):Map<string,number> {
 const found=new Map<string,number>();if(!selected)return found;
 const adjacency=new Map<string,string[]>();
 for(const e of edges)if(e.type==='prerequisite'){
  const from=reverse?e.target:e.source,to=reverse?e.source:e.target;
  if(!adjacency.has(from))adjacency.set(from,[]);adjacency.get(from)!.push(to);
 }
 found.set(selected,0);const queue=[selected];
 for(let i=0;i<queue.length;i++)for(const next of adjacency.get(queue[i])||[]){
  if(found.has(next))continue;found.set(next,found.get(queue[i])!+1);queue.push(next);
 }
 return found;
}
export function maximumDepth(edges:readonly TraceEdge[]):number {
 const children=new Map<string,string[]>();
 for(const e of edges)if(e.type==='prerequisite'){if(!children.has(e.source))children.set(e.source,[]);children.get(e.source)!.push(e.target);}
 const depths=new Map<string,number>(),active=new Set<string>();
 function depth(id:string):number{
  if(active.has(id))throw Error('Prerequisite cycle at '+id);
  if(depths.has(id))return depths.get(id)!;active.add(id);
  const value=Math.max(0,...(children.get(id)||[]).map(c=>1+depth(c)));
  active.delete(id);depths.set(id,value);return value;
 }
 return Math.max(1,...[...children.keys()].map(depth));
}
export function trace(selected:string|null,edges:readonly TraceEdge[],before:number,after:number,displayEdges:readonly TraceEdge[]=edges){
 const upstream=distances(selected,edges,true),downstream=distances(selected,edges);
 const strength=new Map<string,number>(),labels=new Map<string,string>(),edgeStrength=new Map<string,number>();
 // A one-hop neighbour is dark; more distant levels fade towards the unmarked fill.
 const fade=(distance:number)=>Math.max(.16,Math.pow(.42,(distance-1)/2));
 for(const [direction,found,limit] of [['before',upstream,before],['after',downstream,after]] as const){
  for(const [id,d] of found)if(d>0&&d<=limit){strength.set(id,fade(d));labels.set(id,`${d} ${d===1?'level':'levels'} ${direction}`);}
  for(const e of displayEdges)if(e.type==='prerequisite'){
   const near=found.get(direction==='before'?e.target:e.source),far=found.get(direction==='before'?e.source:e.target);
   if(near!==undefined&&far!==undefined&&far>0&&near<=limit&&far<=limit)edgeStrength.set(e.id,fade(far));
  }
 }
 return {strength,labels,edgeStrength};
}
export function traceStyle(strength:number|undefined):{'--trace-fill'?:string}{
 if(!strength)return {};
 const shade=Math.round(255-100*strength);
 return {'--trace-fill':`rgb(${shade}, ${shade+Math.round(3*strength)}, ${shade+Math.round(5*strength)})`};
}

export type Availability='marked'|'unlocked'|'locked';
/** Use the full prerequisite graph: filters, trace sliders and selected nodes do not change readiness. */
export function nodeAvailability(nodes:readonly {id:string}[],edges:readonly TraceEdge[],marked:ReadonlySet<string>):Map<string,Availability>{
 const parents=new Map(nodes.map(n=>[n.id,[] as string[]]));
 for(const edge of edges)if(edge.type==='prerequisite'){
  if(!parents.has(edge.source)||!parents.has(edge.target))throw Error('Unknown prerequisite endpoint.');
  parents.get(edge.target)!.push(edge.source);
 }
 const ready=new Map<string,boolean>(),active=new Set<string>();
 function visit(id:string):boolean{
  if(ready.has(id))return ready.get(id)!;
  if(active.has(id))throw Error('Prerequisite cycle at '+id);
  active.add(id);let allMarked=true;
  for(const parent of parents.get(id)!){const earlier=visit(parent);allMarked=allMarked&&marked.has(parent)&&earlier;}
  active.delete(id);ready.set(id,allMarked);return allMarked;
 }
 const states=new Map<string,Availability>();
 for(const node of nodes){const unlocked=visit(node.id);states.set(node.id,marked.has(node.id)?'marked':unlocked?'unlocked':'locked');}
 return states;
}
export function availabilityLabel(state:Availability|undefined):string{
 return state==='unlocked'?'Unlocked: all prerequisite nodes are marked.':state==='locked'?'Locked: one or more prerequisite nodes are not marked.':state==='marked'?'Temporarily marked.':'';
}
