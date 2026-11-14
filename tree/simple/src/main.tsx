import React, {useMemo, useState, useEffect, useRef} from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow, ReactFlowProvider, Handle, Position, BaseEdge, MarkerType, useReactFlow} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import data from './data/map.json';
import {buildLayout, routeEdges, CARD_WIDTH, CARD_HEIGHT} from './layout';
import './style.css';
import './highlights.css';
import {ControlPanel,ControlSection} from '../../shared/ControlPanel';
import '../../shared/control-panel.css';
import {HighlightControls,useHighlightSettings} from './HighlightControls';
import {trace,traceStyle,maximumDepth,SECTION_NAMES,sectionStyle,nodeAvailability,availabilityLabel} from './highlighting';

import {reducePrerequisiteEdges,visibleDependencyEdges} from './dependencies';

const prerequisites=data.edges.filter(e=>e.type==='prerequisite');
const dependencyEdges=reducePrerequisiteEdges(prerequisites);
const maxDepth=maximumDepth(dependencyEdges);
const topLayout=buildLayout(data.nodes,prerequisites);
const topRoutes=routeEdges(topLayout,prerequisites);
function Card({data:node}:any){return <><Handle type="target" position={Position.Top}/><div className={'node-shell'+(node.marked?' marked':'')}><button className={'node-card nodrag nopan'+(node.selected?' selected':'')+(node.connected?' connected':'')+(node.marked?' marked':'')+(node.traced?' traced':'')+(node.section?' section-highlight':'')+(node.availability?' availability-'+node.availability:'')} style={{...traceStyle(node.strength),...sectionStyle(node.group)} as React.CSSProperties} aria-description={[node.traceLabel,availabilityLabel(node.availability)].filter(Boolean).join(' ')||undefined} aria-pressed={node.selected} aria-label={`${node.code}: ${node.title}`} title="Click to highlight connections. Double-click to mark or unmark." onClick={e=>{e.stopPropagation();node.select();}}><span className="meta"><span>{node.code}</span><span className="level">{node.level==='HL'?'HL only':'SL / HL'}</span></span><strong>{node.title}</strong>{node.section&&<span className="section-tag">{SECTION_NAMES[node.group]}</span>}</button><label className="mark-control nodrag nopan" onClick={e=>e.stopPropagation()} onDoubleClick={e=>e.stopPropagation()}><input type="checkbox" checked={node.marked} onChange={node.toggleMark} aria-label={`Mark ${node.code}: ${node.title}`}/><span>{node.marked?'Marked':'Mark'}</span></label></div><Handle type="source" position={Position.Bottom}/></>;}
function Edge({id,data,style,markerEnd}:any){return <BaseEdge id={id} path={data.path} style={style} markerEnd={markerEnd}/>;}
const nodeTypes={skill:Card},edgeTypes={routed:Edge};
function Tree(){const highlight=useHighlightSettings();const [sort,setSort]=useState<'top'|'bottom'>('top');const {layout,routes}=useMemo(()=>{if(sort==='top')return {layout:topLayout,routes:topRoutes};const layout=buildLayout(data.nodes,prerequisites,'bottom');return {layout,routes:routeEdges(layout,prerequisites)};},[sort]);const [level,setLevel]=useState('all');const [selected,setSelected]=useState<string|null>(null);const [marked,setMarked]=useState<Set<string>>(()=>new Set());const flow=useReactFlow();const viewport=useRef<HTMLDivElement>(null);const [arrowMode,setArrowMode]=useState('all');const [q,setQ]=useState('');
 const toggleMark=(id:string)=>setMarked(previous=>{const next=new Set(previous);if(next.has(id))next.delete(id);else next.add(id);return next;});
 const visible=useMemo(()=>data.nodes.filter(n=>(level==='all'||(level==='SL'?n.level==='shared':n.level==='HL'))&&`${n.code} ${n.title}`.toLowerCase().includes(q.toLowerCase())),[level,q]);
 const ids=new Set(visible.map(n=>n.id));
 const connections=visibleDependencyEdges(prerequisites,ids);
 const traced=trace(selected,dependencyEdges,highlight.before,highlight.after,connections);
 const availability=useMemo(()=>nodeAvailability(data.nodes,prerequisites,marked),[marked]);
 const nodes=visible.map(n=>({id:n.id,type:'skill',position:layout.positions[n.id],data:{...n,availability:highlight.showUnlocked?availability.get(n.id):undefined,marked:marked.has(n.id),toggleMark:()=>toggleMark(n.id),selected:selected===n.id,connected:traced.strength.has(n.id),traced:traced.strength.has(n.id),strength:traced.strength.get(n.id),traceLabel:traced.labels.get(n.id),section:highlight.sections.has(n.group),select:()=>setSelected(n.id)},focusable:false,style:{width:CARD_WIDTH,height:CARD_HEIGHT},sourcePosition:Position.Bottom,targetPosition:Position.Top}));
 const edges=connections.filter(e=>arrowMode!=='none'&&(arrowMode==='all'||traced.edgeStrength.has(e.id))).map(e=>{const strength=traced.edgeStrength.get(e.id);const active=strength!==undefined;return {...e,type:'routed',data:{path:routes[e.id].path},zIndex:active?2:0,style:{stroke:active?'#215b45':e.type==='prerequisite'?'#639d83':e.type==='sequence'?'#c39a50':'#a096b7',strokeWidth:active?3:1.5,opacity:selected?(active?.25+.75*strength!:.12):.75,strokeDasharray:e.type==='prerequisite'?undefined:'6 5'},markerEnd:e.type==='related'?undefined:{type:MarkerType.ArrowClosed,color:active?'#215b45':'#78997d'}};});
 useEffect(()=>{const t=setTimeout(()=>{const first=layout.positions['ib-2025-structure-1.1.1'];if(level==='all'&&sort==='top'){const zoom=window.innerWidth<700?.55:.6;flow.setViewport({x:(viewport.current?.clientWidth||window.innerWidth)/2-(first.x+CARD_WIDTH/2)*zoom,y:window.innerWidth<700?128:70,zoom});}else flow.fitView({padding:.08,maxZoom:.7,duration:0});},80);return()=>clearTimeout(t);},[level,sort]);
 useEffect(()=>{const handler=(e:KeyboardEvent)=>{if(e.key==='Escape'){setSelected(null);return;}if((e.target as HTMLElement).closest('select,button,input'))return;if(e.key==='0')flow.fitView({padding:.05,duration:200});if(e.key==='+'||e.key==='=')flow.zoomIn();if(e.key==='-')flow.zoomOut();};window.addEventListener('keydown',handler);return()=>window.removeEventListener('keydown',handler);},[flow]);
 return <main className="tree-shell simple-tree-shell">
  <ControlPanel>
   <ControlSection title="Find topics"><label>Search<input aria-label="Search nodes" placeholder="Code or topic…" value={q} onChange={e=>setQ(e.target.value)}/></label><label>Curriculum level<select aria-label="Curriculum level" value={level} onChange={e=>{setLevel(e.target.value);setSelected(null);}}><option value="SL">SL</option><option value="all">SL + HL</option><option value="HL">HL only</option></select></label></ControlSection>
   <HighlightControls settings={highlight} max={maxDepth} connectionOptions={<label>Show arrows<select aria-label="Connections" value={arrowMode} onChange={e=>setArrowMode(e.target.value)}><option value="all">All connections</option><option value="selected">Selected connections</option><option value="none">Hide connections</option></select></label>}/>
   <ControlSection title="Layout & view"><button aria-pressed={sort==='bottom'} onClick={()=>setSort(current=>current==='top'?'bottom':'top')}>{sort==='top'?'Bottom sort':'Top sort'}</button><button onClick={()=>flow.fitView({padding:.05,duration:0})}>Fit map</button><button aria-label="Zoom in" onClick={()=>flow.zoomIn({duration:0})}>Zoom in +</button><button aria-label="Zoom out" onClick={()=>flow.zoomOut({duration:0})}>Zoom out −</button></ControlSection>
   <span className="tree-panel-count">{visible.length} statements</span>
  </ControlPanel>
  <div className="tree-stage" ref={viewport}><ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} minZoom={.01} maxZoom={1.7} zoomOnDoubleClick={false} autoPanOnNodeFocus={false} nodesDraggable={false} nodesConnectable={false} edgesFocusable={false} elementsSelectable={false} proOptions={{hideAttribution:true}} onNodeClick={(_,n)=>{if(ids.has(n.id))setSelected(n.id);}} onNodeDoubleClick={(_,n)=>{if(ids.has(n.id))toggleMark(n.id);}} onPaneClick={()=>setSelected(null)} aria-label="IB Chemistry curriculum tree"/></div>
 </main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><ReactFlowProvider><Tree/></ReactFlowProvider></React.StrictMode>);
