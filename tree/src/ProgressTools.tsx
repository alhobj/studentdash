import React, {useEffect, useRef, useState} from 'react';
import {map} from './curriculum';
import {applyImport, exportProgress, importConflicts, parseProgressFile, EXPORT_FILENAME, MAX_IMPORT_BYTES, STATUS_LABELS, type Progress} from './progress';

function ImportDialog({progress, onCommit, onClose}: {progress: Progress; onCommit: (next: Progress) => void; onClose: () => void}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [incoming, setIncoming] = useState<Progress | null>(null);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'merge' | 'replace'>('merge');
  const [accepted, setAccepted] = useState<string[]>([]);
  const readAttempt = useRef(0);
  useEffect(() => {dialog.current?.showModal(); return () => {readAttempt.current++;};}, []);
  const conflicts = incoming ? importConflicts(progress, incoming) : [];
  async function readFile(file?: File) {
    const attempt = ++readAttempt.current;
    setIncoming(null); setAccepted([]); setError('');
    if (!file) return;
    if (file.size > MAX_IMPORT_BYTES) {setError('File too large. Choose a self-assessment JSON file no larger than 128 KB.'); return;}
    try {
      const next = parseProgressFile(await file.text());
      if (attempt === readAttempt.current) setIncoming(next);
    } catch (e) {if (attempt === readAttempt.current) setError(e instanceof Error ? e.message : 'The file could not be read. No progress changed.');}
  }
  function apply() {
    if (!incoming) return;
    if (mode === 'replace' && !window.confirm(`Replace all current self-assessment with these ${Object.keys(incoming).length} entries? Entries not in the file will be removed.`)) return;
    onCommit(applyImport(progress, incoming, mode, accepted)); onClose();
  }
  return <dialog ref={dialog} aria-labelledby="import-title" onCancel={e => {e.preventDefault(); onClose();}}>
    <div className="dialog-heading"><h2 id="import-title">Import self-assessment</h2><button onClick={onClose} aria-label="Close import">×</button></div>
    <p>Manual file transfer. Only self-assessment for this curriculum is accepted. Nothing changes until you apply the preview.</p>
    <label className="file-label">Choose self-assessment JSON<input type="file" accept=".json,application/json" onChange={e => void readFile(e.target.files?.[0])}/></label>
    <p className="muted">Maximum 128 KB. The file is read in this browser and is not uploaded.</p>
    {error && <p role="alert" className="import-error">Import rejected. {error} Current progress is unchanged.</p>}
    {incoming && <section className="import-preview" aria-label="Import preview">
      <h3>{Object.keys(incoming).length} self-assessment entries</h3>
      <p>{conflicts.length} different existing entries. Current local entries: {Object.keys(progress).length}.</p>
      <fieldset><legend>How should this file be applied?</legend>
        <label><input type="radio" name="import-mode" value="merge" checked={mode === 'merge'} onChange={() => setMode('merge')}/> Merge with current progress</label>
        <label><input type="radio" name="import-mode" value="replace" checked={mode === 'replace'} onChange={() => setMode('replace')}/> Replace all current progress</label>
      </fieldset>
      {mode === 'merge' ? <><p>New entries are added. Existing entries are kept unless you accept a replacement below.</p>
        {conflicts.length > 0 && <fieldset className="conflict-list"><legend>Accept individual replacements</legend>{conflicts.map(id => {
          const node = map.nodes.find(n => n.id === id)!;
          return <label key={id}><input type="checkbox" checked={accepted.includes(id)} onChange={e => setAccepted(old => e.target.checked ? [...old, id] : old.filter(x => x !== id))}/><span>{node.official.code} · {node.title}<small>Current: {STATUS_LABELS[progress[id]]} → Imported: {STATUS_LABELS[incoming[id]]}</small></span></label>;
        })}</fieldset>}
      </> : <p className="import-warning">Replacement removes current entries that are absent from the file. You will be asked to confirm.</p>}
      <button className="primary" onClick={apply}>{mode === 'merge' ? 'Apply merge' : 'Replace progress'}</button>
    </section>}
    <button className="cancel-import" onClick={onClose}>Cancel import</button>
  </dialog>;
}

export function ProgressTools({progress, onCommit, onClear, onMessage}: {progress: Progress; onCommit: (next: Progress) => void; onClear: () => void; onMessage: (message: string) => void}) {
  const [showImport, setShowImport] = useState(false);
  const importButton = useRef<HTMLButtonElement>(null);
  function closeImport() {setShowImport(false); requestAnimationFrame(() => importButton.current?.focus());}
  function download() {
    try {
      const blob = new Blob([exportProgress(progress)], {type: 'application/json'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = EXPORT_FILENAME; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      onMessage('Self-assessment exported. Transfer the file manually to another device if needed. The file is not encrypted.');
    } catch {onMessage('Export could not be created. Your current progress is unchanged.');}
  }
  return <>
    <div className="progress-tools" aria-label="Manual self-assessment transfer">
      <button onClick={download}>Export self-assessment</button>
      <button ref={importButton} onClick={() => setShowImport(true)}>Import self-assessment</button>
      <button className="clear-progress" onClick={() => {if (window.confirm('Clear all self-assessment in this browser? Export a file first if you want to keep it.')) onClear();}}>Clear all local progress</button>
    </div>
    {showImport && <ImportDialog progress={progress} onCommit={onCommit} onClose={closeImport}/>}
  </>;
}
