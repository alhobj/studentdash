import React, {useEffect, useRef, useState} from 'react';

function HelpDialog({onClose, onStart}: {onClose: () => void; onStart: () => void}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {dialog.current?.showModal();}, []);
  return <dialog ref={dialog} aria-labelledby="help-title" onCancel={e => {e.preventDefault(); onClose();}}>
    <div className="dialog-heading"><h2 id="help-title">Using Chemistree</h2><button onClick={onClose} aria-label="Close help">×</button></div>
    <p>Explore a statement, try some practice, then reflect on your confidence. Every statement stays open.</p>
    <h3>Find your way</h3><p>Open a section in the left panel to see its controls. Structure &amp; Reactivity highlights chapters; Arrows &amp; connections controls arrows and dependency depth. Layout &amp; view contains zoom, sorting and map/list options. Selected node contains the statement and practice.</p>
    <ul><li>Search by a statement code or an idea. Choose <b>SL</b> for shared content, <b>SL + HL</b> for everything, or <b>HL additions</b> for the extra HL statements.</li>
      <li>Use Map to pan and zoom through the trees. Fit map shows the current results. List gives you the same statements as keyboard-operable buttons.</li>
      <li>Selected connections are teaching suggestions. Read direct foundations, expand the prerequisite chain, or follow later connections in the details.</li></ul>
    <h3>Practise and reflect</h3>
    <p>The guided-exercises filter finds statements with worked examples. Try on paper or mentally before revealing hints or explanations. These exercises are editorial, not official IB questions.</p>
    <p>Choose Not reviewed, Needs practice, Developing or Confident yourself. Confidence is a personal reflection, not documented achievement. Practice never changes it automatically.</p>
    <button onClick={onStart}>Find guided exercises</button>
    <h3>Keep or transfer your self-assessment</h3>
    <p>Saved in this browser only. It does not sync automatically and may be lost if browser data is cleared.</p>
    <p>Export a file and transfer it manually to another browser. Import previews entries before applying them: merge keeps existing entries unless you accept a replacement; replace asks for confirmation. Export files are not encrypted. Clear all local progress also asks for confirmation.</p>
    <h3>Keyboard and AI instructions</h3>
    <p>Use <kbd>Tab</kbd> to move between controls and <kbd>Enter</kbd> or <kbd>Space</kbd> to activate buttons and explanations. <kbd>Escape</kbd> closes this help or the import dialog. List is the simplest alternative to navigating the spatial map.</p>
    <p>AI instructions are visible text you may choose to copy. They use statement content and the Practice level selector, never your self-assessment. Nothing is sent to an AI service automatically.</p>
    <p className="muted">No account is required. Someone sharing this browser profile may see local confidence values. The site host can still process connection metadata such as IP addresses.</p>
    <button onClick={onClose}>Close help</button>
  </dialog>;
}
export function Help({onStart}: {onStart: () => void}) {
  const [open, setOpen] = useState(false);
  const launcher = useRef<HTMLButtonElement>(null);
  function close() {setOpen(false); requestAnimationFrame(() => launcher.current?.focus());}
  return <><button ref={launcher} onClick={() => setOpen(true)}>Help</button>{open && <HelpDialog onClose={close} onStart={() => {setOpen(false); onStart();}}/>}</>;
}
