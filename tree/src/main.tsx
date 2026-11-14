import React, {useState, useEffect, useMemo, lazy, Suspense} from 'react';
import {createRoot} from 'react-dom/client';
import '@xyflow/react/dist/style.css';
import {map, ancestors, prompt} from './curriculum';
import {loadProgress, saveProgress, clearProgress, setSelfAssessment, STATUS_LABELS, type Progress, type SelfAssessment} from './progress';
import {readNodeLink, nodeFragment} from './links';
import {ProgressTools} from './ProgressTools';
import {practiceNodeIds, practiceCount} from './practice';
import {Help} from './Help';
import './style.css';
import '../simple/src/highlights.css';
import {useHighlightSettings} from '../simple/src/HighlightControls';
import {maximumDepth} from '../simple/src/highlighting';
import {reducePrerequisiteEdges} from '../simple/src/dependencies';
const dependencyEdges=reducePrerequisiteEdges(map.edges);

function OfficialText({parts, statement}: {parts: {text: string; script: string}[] | null; statement: string}) {
  return <>{(parts ?? [{text: statement, script: 'normal'}]).map((part, i) => part.script === 'sub' ? <sub key={i}>{part.text}</sub> : part.script === 'super' ? <sup key={i}>{part.text}</sup> : <React.Fragment key={i}>{part.text}</React.Fragment>)}</>;
}

const MapView = lazy(() => import('./MapView'));
const PracticeSection = lazy(() => import('./PracticeSection'));
const initialId = 'ib-2025-structure-2.2.6';
function browserStorage() {try {return window.localStorage;} catch {return null;}}
class FeatureBoundary extends React.Component<{children: React.ReactNode; onList?: () => void}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() {return {failed: true};}
  render() {return this.state.failed ? <div role="status" className="empty"><p>This feature could not load. Your self-assessment is unchanged. Reload to try again.</p>{this.props.onList && <button onClick={this.props.onList}>Use list instead</button>}</div> : this.props.children;}
}

export function App({tools,nodeExtras,audienceLabel='STUDENT'}:{tools?:React.ReactNode;nodeExtras?:Record<string,React.ReactNode>;audienceLabel?:string}={}) {
  const highlight = useHighlightSettings();
  const [simpleMode,setSimpleMode]=useState(false);
  const [initialLink] = useState(() => readNodeLink(window.location.hash));
  const [initialProgress] = useState(() => loadProgress(browserStorage()));
  const [selected, setSelected] = useState(initialLink.nodeId || initialId);
  const [q, setQ] = useState('');
  const [level, setLevel] = useState('all');
  const [area, setArea] = useState('all');
  const [guidedOnly, setGuidedOnly] = useState(false);
  const [practiceLevel, setPracticeLevel] = useState<'SL' | 'HL'>('SL');
  const [view, setView] = useState('map');
  const [links, setLinks] = useState('selected');
  const [chain, setChain] = useState(false);
  const [sort, setSort] = useState<'top' | 'bottom'>('top');
  const [progress, setProgress] = useState<Progress>(initialProgress.progress);
  const [storageMessage, setStorageMessage] = useState(initialProgress.message || '');
  const [message, setMessage] = useState(initialLink.error || '');
  const [copied, setCopied] = useState(false);
  const [fitRequest, setFitRequest] = useState(0);

  function commit(next: Progress) {
    setProgress(next);
    const result = saveProgress(browserStorage(), next);
    setStorageMessage(result.message || '');
  }
  function clear() {
    setProgress({});
    const result = clearProgress(browserStorage());
    setStorageMessage(result.message || '');
    setMessage(result.ok ? 'All local self-assessment cleared.' : 'Self-assessment cleared for this session. See the storage warning.');
  }
  function openNode(id: string, fromLink = false) {
    setMessage(''); setFitRequest(0); setSelected(id); setChain(false); setCopied(false);
    // A linked objective must be visible even when an old search or filter excludes it.
    if (fromLink || !visibleIds.has(id)) {setQ(''); setArea('all'); setLevel('all'); setGuidedOnly(false);}
    if (!fromLink) history.replaceState(null, '', `${location.pathname}${nodeFragment(id)}`);

  }
  useEffect(() => {
    function followLink() {
      const link = readNodeLink(window.location.hash);
      if (link.error) setMessage(link.error);
      if (link.nodeId) {setMessage(''); openNode(link.nodeId, true);}
    }
    window.addEventListener('hashchange', followLink);
    if (initialLink.nodeId) followLink();
    return () => window.removeEventListener('hashchange', followLink);
  }, []);
  useEffect(() => setCopied(false), [selected, practiceLevel]);
  const n = map.nodes.find(n => n.id === selected)!;
  const hasExercise = practiceNodeIds.has(selected);
  const directPrerequisites=dependencyEdges.filter(e=>e.type==='prerequisite'&&e.target===n.id).map(e=>e.source);
  const visible = useMemo(() => map.nodes.filter(n =>
    (level !== 'SL' || n.level === 'shared') && (level !== 'HL-only' || n.level === 'HL') &&
    (simpleMode || area === 'all' || n.group === Number(area)) && (simpleMode || !guidedOnly || practiceNodeIds.has(n.id)) &&
    (simpleMode || `${n.official.code} ${n.official.statement} ${n.title} ${n.explanation}`.toLowerCase().includes(q.toLowerCase()))), [q, level, area, guidedOnly,simpleMode]);
  const visibleIds = new Set(visible.map(n => n.id));


  function nodeLinks(ids: string[]) {
    return ids.length ? ids.map(id => {const target = map.nodes.find(x => x.id === id)!; return <button className="link-node" key={id} onClick={() => openNode(id)}><span>{target.official.code}<br/>{target.title}</span><span aria-hidden="true">→</span></button>;}) : <p className="muted">No specific prior statements suggested.</p>;
  }
  const hiddenSelection = !visibleIds.has(selected);
  return <div className={simpleMode?'app simple-mode':'app'}>
    <a className="skip-link" href="#main">Skip to curriculum</a>
    <header><a className="brand" href="#main"><span className="brand-mark" aria-hidden="true">✳</span>ArborSynapse<span className="beta">{audienceLabel}</span></a>
      <div className="header-right"><span>IB DP CHEMISTRY · 2025</span><Help onStart={() => {setQ(''); setLevel('all'); setArea('all'); setGuidedOnly(true); setView('list'); requestAnimationFrame(() => document.getElementById('guided-filter')?.focus());}}/><label>Practice level <select aria-label="Practice level" value={practiceLevel} onChange={e => setPracticeLevel(e.target.value as 'SL' | 'HL')}><option value="SL">SL</option><option value="HL">HL</option></select></label></div>
    </header>
    <main id="main" tabIndex={-1}><h1 className="sr-only">IB Chemistry curriculum</h1>
      {tools}
      <ProgressTools progress={progress} onCommit={next => {commit(next); setMessage('Self-assessment imported. No automatic synchronisation is enabled.');}} onClear={clear} onMessage={setMessage}/>
      {storageMessage && <div className="storage-warning" role="alert">{storageMessage}</div>}
      {message && <div className="message" role="status">{message}<button onClick={() => setMessage('')} aria-label="Dismiss message">×</button></div>}
      <section className="workspace" aria-label="Chemistry learning explorer"><div className="explorer">
        <div className="toolbar"><label className="search"><span aria-hidden="true">⌕</span><input placeholder="Search statement codes or ideas…" aria-label="Search nodes" value={q} onChange={e => setQ(e.target.value)}/></label>
          <select aria-label="Level filter" value={level} onChange={e => setLevel(e.target.value)}><option value="SL">SL</option><option value="all">SL + HL</option><option value="HL-only">HL additions</option></select>
          <button className="mode-toggle" aria-pressed={simpleMode} onClick={()=>setSimpleMode(value=>!value)}>Simple mode</button>
          <button className="view-toggle" aria-pressed={view === 'map'} onClick={() => setView('map')}>Map</button><button className="view-toggle" aria-pressed={view === 'list'} onClick={() => setView('list')}>List</button>
        </div>
        <div className="map-options"><select aria-label="Subject area" value={area} onChange={e => setArea(e.target.value)}><option value="all">All subject areas</option>{map.groups.map((g, i) => <option value={i} key={g}>{g}</option>)}</select>
          <select aria-label="Connections" value={links} onChange={e => setLinks(e.target.value)}><option value="selected">Selected connections</option><option value="all">All connections</option><option value="none">Hide connections</option></select>
          <button aria-pressed={sort === 'bottom'} onClick={() => setSort(value => value === 'top' ? 'bottom' : 'top')}>{sort === 'top' ? 'Bottom sort' : 'Top sort'}</button>
          <button onClick={() => {setView('map'); setFitRequest(value => value + 1);}}>⛶ Fit map</button>
          <label className="guided-filter"><input id="guided-filter" type="checkbox" checked={guidedOnly} onChange={e => setGuidedOnly(e.target.checked)}/> Guided exercises ({practiceCount})</label>
          <span aria-live="polite">{visible.length} statements</span><a className="mobile-detail" href="#node-details">Open selected details ↓</a>
        </div>
        {simpleMode || view === 'map' ? <FeatureBoundary key="map" onList={() => setView('list')}><Suspense fallback={<div className="canvas" role="status"><p className="empty">Loading map… You can use List while it loads.</p></div>}><MapView nodeExtras={nodeExtras} simple={simpleMode} highlight={highlight} sort={sort} visible={visible} selected={selected} connections={simpleMode?'all':links} progress={progress} onSelect={openNode} fitRequest={fitRequest}/></Suspense></FeatureBoundary> :
          <div className="list-view" role="region" aria-label="Curriculum statement list">{map.groups.map((g, i) => <section key={g}><h3>{g}</h3>{visible.filter(x => x.group === i).map(s => <button key={s.id} data-node-id={s.id} onClick={() => openNode(s.id)} className={selected === s.id ? 'chosen' : ''} aria-pressed={selected === s.id}>
            <span><b>{s.official.code}</b><br/>{s.title}</span><small>{s.level === 'HL' ? 'HL addition' : 'SL / HL'} · Self: {STATUS_LABELS[progress[s.id] || 'not-reviewed']}</small>
          </button>)}</section>)}</div>}
        {!visible.length && <p role="status" className="empty">No matching statements. Try another search or filter.</p>}
        <footer className="legend"><span>Drag to explore · scroll to zoom · Tab to navigate</span><span>Solid → Suggested prerequisite</span><span>Gold ⇢ Suggested sequence</span><span>Purple ┄ Related idea</span></footer>
      </div>
      <aside hidden={simpleMode} id="node-details" aria-label="Node details" className="details" tabIndex={-1}>
        <div className="detail-heading"><span className="eyebrow">{n.level === 'HL' ? 'ADDITIONAL HIGHER LEVEL' : 'SL / HL SHARED'}</span><h2>{n.title}</h2><span className="sr-only" role="status">Selected {n.official.code}: {n.title}</span>
          <div className="official-statement"><h3>Official guide statement</h3><b>{n.official.code}</b><p><OfficialText parts={n.official.statementParts} statement={n.official.statement}/></p></div>
          <p className="source-note">Chemistry guide · February 2023 · first assessment 2025<br/>Guide p. {n.official.printedPages.join(', ')} · PDF p. {n.official.pdfPages.join(', ')}</p>
          {hiddenSelection && <p className="selection-note">This selected statement is outside the current filters. Its details remain open.</p>}
        </div>
        <div className="detail-body"><section className="self-assessment" aria-labelledby="self-title"><h3 id="self-title">Self-assessment</h3><p>Your own confidence about this statement. This is not a documented result or confirmation of achievement.</p>
            <label htmlFor="self-assessment">How do you feel about this statement?</label><select id="self-assessment" value={progress[n.id] || 'not-reviewed'} onChange={e => commit(setSelfAssessment(progress, n.id, e.target.value as SelfAssessment | 'not-reviewed'))}>
              {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select><button onClick={() => commit(setSelfAssessment(progress, n.id, 'not-reviewed'))}>Reset this node</button>
          </section>{hasExercise && <FeatureBoundary key={n.id}><Suspense fallback={<p role="status">Loading guided practice…</p>}><PracticeSection nodeId={n.id}/></Suspense></FeatureBoundary>}
          <h3>Suggested foundations <span>{directPrerequisites.length}</span></h3><p className="muted">Teaching suggestions, not official IB prerequisite requirements. Every statement stays open.</p>
          {nodeLinks(chain ? ancestors(n.id) : directPrerequisites)}
          {directPrerequisites.length > 0 && <button className="text-button" aria-pressed={chain} onClick={() => {setChain(!chain); highlight.setBefore(chain ? 1 : maximumDepth(map.edges));}}>{chain ? 'Show direct prerequisites' : 'Expand full prerequisite chain'}</button>}
          <h3>This helps you with</h3>{nodeLinks(dependencyEdges.filter(e => e.source === n.id && e.type === 'prerequisite').map(e => e.target))}
          <details><summary>Suggested sequence & related ideas</summary>{nodeLinks(map.edges.filter(e => e.type !== 'prerequisite' && (e.source === n.id || e.target === n.id)).map(e => e.source === n.id ? e.target : e.source))}</details>
          {!hasExercise && <><h3>Independent practice · editorial</h3><div className="practice">{n.practice}</div><p className="muted">A guided exercise is not available for this statement yet. The guided-exercises filter finds the first {practiceCount} exercises; other statements remain open.</p></>}
          <h3>Practise with an AI tutor</h3><p className="muted">Copy these instructions to an AI service only if you choose. They use statement content and practice level, without your self-assessment. Nothing is sent automatically.</p>
          <textarea aria-label="AI instruction" className="prompt" readOnly value={prompt(n, practiceLevel)}/><button className="primary" onClick={async () => {try {await navigator.clipboard.writeText(prompt(n, practiceLevel)); setCopied(true);} catch {setMessage('Copy unavailable. Select the instruction text and copy manually.');}}}>{copied ? '✓ Copied' : 'Copy AI instruction ↗'}</button>
          <p><a href={`${location.pathname}${nodeFragment(n.id)}`} onClick={e => {e.preventDefault(); openNode(n.id);}}>Link to this statement</a></p><h3>Syllabus context</h3>{n.syllabusRefs.map(ref => <p key={ref} className="syllabus">{ref}<small>{map.syllabus.find(s => s.id === ref)?.title}</small></p>)}
        </div>
      </aside></section>
      <details className="curriculum"><summary>Official framework & source scope</summary><div>{map.syllabus.map(s => <p key={s.id}><b>{s.id}</b> — {s.title}</p>)}</div><p>All numbered Structure and Reactivity statements from the supplied first-assessment-2025 guide. Consult the guide for full applications, skills, practical work and assessment requirements.</p></details>
    </main><div className="bottom">CHEMISTREE <span>{audienceLabel==='TEACHER'?'Teacher view · official statement map 2.0':'Student release · official statement map 2.0'}</span><span>Local self-assessment · no automatic sync</span></div>
  </div>;
}
if(!document.getElementById('root')?.hasAttribute('data-teacher'))createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
