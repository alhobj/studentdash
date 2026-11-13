/** Builds the minimal tree from unchanged curriculum metadata and a separate editorial review. */
export function buildSimpleMap(source,review) {
 const short=code=>code.replace('Structure ','S').replace('Reactivity ','R');
 const nodes=source.nodes.map(n=>({id:n.id,title:n.title,group:n.group,level:n.level,code:n.official.code}));
 const byCode=new Map(nodes.map(n=>[short(n.code),n]));
 if(byCode.size!==nodes.length)throw Error('Duplicate curriculum code');
 if(review.nodes.length!==nodes.length||new Set(review.nodes.map(n=>n.code)).size!==nodes.length)throw Error('Dependency review must cover every curriculum node exactly once');
 const prerequisites=[];
 for(const entry of review.nodes) {
  const target=byCode.get(entry.code);
  if(!target||!entry.reason?.trim())throw Error('Missing node or teaching rationale: '+entry.code);
  if(new Set(entry.requires).size!==entry.requires.length)throw Error('Duplicate prerequisite for '+entry.code);
  for(const code of entry.requires) {
   const parent=byCode.get(code);
   if(!parent||parent.id===target.id)throw Error('Invalid prerequisite '+code+' for '+entry.code);
   if(target.level==='shared'&&parent.level==='HL')throw Error('A shared SL node cannot require HL-only content: '+entry.code);
   prerequisites.push({id:`prerequisite:${parent.id}:${target.id}`,source:parent.id,target:target.id,type:'prerequisite',provenance:'Editorial; see prerequisites.json'});
  }
 }
 const parents=new Map(nodes.map(n=>[n.id,prerequisites.filter(e=>e.target===n.id).map(e=>e.source)]));
 const active=new Set(),done=new Set();
 function visit(id){if(active.has(id))throw Error('Prerequisite cycle at '+id);if(done.has(id))return;active.add(id);for(const p of parents.get(id))visit(p);active.delete(id);done.add(id);}
 for(const n of nodes)visit(n.id);
 return {version:source.version,groups:source.groups,nodes,edges:[...source.edges.filter(e=>e.type!=='prerequisite'),...prerequisites]};
}
