/** Transitive reduction of prerequisite arrows only. Authored graph data stays intact. */
export type DependencyEdge={id:string;source:string;target:string;type?:string};
export function reducePrerequisiteEdges<T extends DependencyEdge>(edges:readonly T[]):T[]{
 const children=new Map<string,Set<string>>();
 for(const edge of edges)if(edge.type==='prerequisite'){
  if(!children.has(edge.source))children.set(edge.source,new Set());
  if(!children.has(edge.target))children.set(edge.target,new Set());
  children.get(edge.source)!.add(edge.target);
 }
 const cache=new Map<string,Set<string>>(),active=new Set<string>();
 function reachable(id:string):Set<string>{
  if(cache.has(id))return cache.get(id)!;
  if(active.has(id))throw Error('Prerequisite cycle at '+id);
  active.add(id);const result=new Set<string>();
  for(const next of children.get(id)||[]){result.add(next);for(const later of reachable(next))result.add(later);}
  active.delete(id);cache.set(id,result);return result;
 }
 for(const id of children.keys())reachable(id);
 const seen=new Map<string,Set<string>>();
 return edges.filter(edge=>{
  if(edge.type!=='prerequisite')return true;
  if(!seen.has(edge.source))seen.set(edge.source,new Set());
  if(seen.get(edge.source)!.has(edge.target))return false;
  seen.get(edge.source)!.add(edge.target);
  return ![...children.get(edge.source)!].some(other=>other!==edge.target&&reachable(other).has(edge.target));
 });
}
/** Reduce after visibility filtering: keep an existing shortcut if its alternative path is hidden. */
export function visibleDependencyEdges<T extends DependencyEdge>(edges:readonly T[],visible:ReadonlySet<string>):T[]{
 return reducePrerequisiteEdges(edges.filter(edge=>visible.has(edge.source)&&visible.has(edge.target)));
}
