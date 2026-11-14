import React, {useEffect, useMemo, useState} from 'react';
import {ReactFlow, Background, Handle, Position, ReactFlowProvider, useReactFlow, MarkerType, BaseEdge} from '@xyflow/react';
import {map, type Skill} from './curriculum';
import {STATUS_LABELS, type Progress} from './progress';
import {buildLayout, routeEdges, CARD_WIDTH, CARD_HEIGHT, type SortMode} from './layout';

import {type HighlightSettings} from '../simple/src/HighlightControls';
import {trace,traceStyle,SECTION_NAMES,sectionStyle,nodeAvailability,availabilityLabel} from '../simple/src/highlighting';
import {reducePrerequisiteEdges,visibleDependencyEdges} from '../simple/src/dependencies';
const dependencyEdges=reducePrerequisiteEdges(map.edges);

type MapProps = {marked: Set<string>; toggleMark:(id:string)=>void;zoomRequest?:{sequence:number;direction:"in"|"out"};nodeExtras?:Record<string,React.ReactNode>; simple?: boolean; highlight: HighlightSettings; sort: SortMode; visible: Skill[]; selected: string; connections: string; progress: Progress; onSelect: (id: string) => void; fitRequest: number};
export function Card({data}: any) {
  return <><Handle type="target" position={Position.Top}/><button aria-label={`${data.official.code} · ${data.title}${data.simple ? '' : ` · Self-assessment: ${data.status}`}`} aria-pressed={data.active} title="Double-click or press M to mark or unmark temporarily" onMouseDown={e => {if(e.button===0)e.preventDefault();}} onDoubleClick={e => {e.stopPropagation(); data.toggleMark();}} onKeyDown={e => {if(e.key.toLowerCase()==='m'){e.preventDefault();e.stopPropagation();data.toggleMark();}}}
    style={{...traceStyle(data.strength),...sectionStyle(data.group)} as React.CSSProperties} aria-description={[data.traceLabel,availabilityLabel(data.availability)].filter(Boolean).join(' ')||undefined} className={`skill-card nodrag ${data.simple ? 'simple-card' : ''} ${data.availability ? `availability-${data.availability}` : ''} ${data.marked ? 'marked' : ''} ${data.traced ? 'traced' : ''} ${data.section ? 'section-highlight' : ''} ${data.connected ? 'connected' : ''} ${data.active ? 'active' : ''} self-${data.self || 'not-reviewed'}`} onClick={e => {e.stopPropagation(); data.open();}}>
    <span className="node-meta"><span>{data.official.code}</span><b>{data.level === 'HL' ? 'HL addition' : 'SL / HL'}</b></span><strong>{data.title}</strong>{!data.simple&&<><span className="node-status">{data.marked ? '✓ Marked · Self-assessment' : 'Self-assessment'}</span><span className="self-dot">{data.status}</span></>}{data.section&&<span className="section-tag">{SECTION_NAMES[data.group]}</span>}
  </button>{data.extra&&<div className="node-extra nodrag nopan" role="group" aria-label={`${data.official.code} results`}>{data.extra}</div>}<Handle type="source" position={Position.Bottom}/></>;
}
function RoutedEdge({id, data, style, markerEnd}: any) {return <g><title>{data.description}</title><BaseEdge id={id} path={data.path} style={style} markerEnd={markerEnd}/></g>;}
const nodeTypes = {skill: Card}, edgeTypes = {routed: RoutedEdge};
function MapCanvas({marked,toggleMark,zoomRequest,nodeExtras,simple=false, highlight, sort, visible, selected, connections, progress, onSelect, fitRequest}: MapProps) {
  const flow = useReactFlow();
  const {layout, routes} = useMemo(() => {
    const layout = buildLayout(map.nodes, map.edges, sort);
    return {layout, routes: routeEdges(layout, map.edges)};
  }, [sort]);
  const availability=useMemo(()=>nodeAvailability(map.nodes,map.edges,marked),[marked]);
  const visibleIds = new Set(visible.map(node => node.id));
  const visibleEdges=visibleDependencyEdges(map.edges,visibleIds);
  const traced=trace(selected,dependencyEdges,highlight.before,highlight.after,visibleEdges);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const nodes = visible.map(node => ({id: node.id, type: 'skill', position: layout.positions[node.id], sourcePosition: Position.Bottom, targetPosition: Position.Top,
    data: {...node, extra:nodeExtras?.[node.id], simple, availability:highlight.showUnlocked?availability.get(node.id):undefined, marked: marked.has(node.id), toggleMark: () => toggleMark(node.id), status: STATUS_LABELS[progress[node.id] || 'not-reviewed'], self: progress[node.id], active: node.id === selected, connected: traced.strength.has(node.id), traced: traced.strength.has(node.id), strength: traced.strength.get(node.id), traceLabel: traced.labels.get(node.id), section: highlight.sections.has(node.group), open: () => onSelect(node.id)},
    style: {width: CARD_WIDTH, height: CARD_HEIGHT}, focusable: false, ariaLabel: `${node.official.code}: ${node.title}`}));
  const labels = layout.labels.filter(label => visible.some(node => node.group === label.group)).map(label => ({id: label.id, position: {x: label.x, y: label.y}, data: {label: label.text}, draggable: false, selectable: false, focusable: false, className: 'branch-heading', style: {width: label.width, height: label.height}}));
  const edges = visibleEdges.filter(edge => (!simple || edge.type === 'prerequisite') && visibleIds.has(edge.source) && visibleIds.has(edge.target) && (connections === 'all' || (connections === 'selected' && (traced.edgeStrength.has(edge.id) || (edge.type !== 'prerequisite' && (edge.source === selected || edge.target === selected))))))
    .map(edge => ({...edge, type: 'routed', data: {path: routes[edge.id].path, description: `Suggested ${edge.type}: ${edge.source} to ${edge.target}`},
      style: {stroke: edge.type === 'prerequisite' ? '#3b7c68' : edge.type === 'sequence' ? '#b48234' : '#7e70a5', strokeWidth: traced.edgeStrength.has(edge.id)?3:1.5, opacity: traced.edgeStrength.has(edge.id) ? .25+.75*traced.edgeStrength.get(edge.id)! : connections === 'all' ? .18 : .7, strokeDasharray: edge.type === 'prerequisite' ? undefined : '6 5'},
      markerEnd: edge.type === 'related' ? undefined : {type: MarkerType.ArrowClosed, color: '#3b7c68'}}));
  // Initial framing is fixed for this map instance; selection never controls the viewport.
  const [initialViewport]=useState(()=>{const p=layout.positions[selected]||layout.positions[visible[0]?.id]||{x:0,y:0};return {x:240-p.x*.9,y:60-p.y*.9,zoom:.9};});
  useEffect(() => {
    if(fitRequest===0||!visible.length)return;
    const timer=setTimeout(()=>flow.fitView({nodes:visible.map(node=>({id:node.id})),padding:.2,maxZoom:1,duration:reducedMotion?0:250}),120);
    return ()=>clearTimeout(timer);
  },[fitRequest]);
  useEffect(()=>{if(zoomRequest?.sequence){if(zoomRequest.direction==='in')flow.zoomIn({duration:0});else flow.zoomOut({duration:0});}},[zoomRequest?.sequence]);
  return <div className="canvas" aria-label="Chemistry skill map"><ReactFlow nodes={[...nodes, ...labels]} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} minZoom={.01} maxZoom={1.5} zoomOnDoubleClick={false} autoPanOnNodeFocus={false} defaultViewport={initialViewport}
    panOnDrag={[0,1]} paneClickDistance={5} selectionOnDrag={false} selectionKeyCode={null} elementsSelectable={false} nodesDraggable={false} nodesConnectable={false} edgesFocusable={false} onNodeClick={(_, node) => {if (map.nodes.some(candidate => candidate.id === node.id)) onSelect(node.id);}}>
    <Background color="#cbd8cd" gap={24}/>
  </ReactFlow></div>;
}
export default function MapView(props: MapProps) {return <ReactFlowProvider><MapCanvas {...props}/></ReactFlowProvider>;}
