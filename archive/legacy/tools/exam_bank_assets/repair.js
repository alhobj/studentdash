'use strict';
const $ = id => document.getElementById(id);
const fields = ['Specification', 'Question', 'Markscheme', 'Examiners report'];
const known = new Set(catalog.map(q => q.id));
const storageKey = `exam-repairs-${bankFingerprint}`;
let corrections = {}, current = null, draft = null, dirty = false, requested = null;
const tell = message => { $('message').textContent = message; };
function validate(data) {
  if (!data || data.schema !== 1 || data.bank !== bankFingerprint || !data.corrections || Array.isArray(data.corrections)) throw Error('This file does not match this question bank.');
  for (const [id, item] of Object.entries(data.corrections)) {
    if (!known.has(id) || !item || !item.fields || !fields.every(f => typeof item.fields[f] === 'string') ||
        !['draft', 'needs-source', 'approved'].includes(item.status) || typeof item.notes !== 'string') throw Error('Invalid correction record. Nothing was imported.');
  }
  return data.corrections;
}
try {
  const saved = localStorage.getItem(storageKey);
  if (saved) corrections = validate(JSON.parse(saved));
} catch (e) { tell('Browser storage could not be loaded. Import your exported corrections file. '+e.message); }
function packageData() { return {schema:1, bank:bankFingerprint, corrections}; }
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify(packageData())); tell('Saved in this browser. Export corrections for a portable backup.'); }
  catch { tell('Browser storage is unavailable or full. Your edits are in memory: export corrections now before closing.'); }
}
function safeHtml(raw) {
  const template = document.createElement('template');
  template.innerHTML = raw;
  const allowed = new Set('p br sub sup strong em b i u table thead tbody tr td th ul ol li span div math mrow mi mn mo mtext msub msup msubsup mfrac msqrt mroot mfenced mtable mtr mtd munder mover munderover mmultiscripts mprescripts none mspace'.split(' '));
  const result = document.createElement('div');
  function copy(node, target) {
    if (node.nodeType === 3) { target.append(document.createTextNode(node.textContent)); return; }
    if (node.nodeType !== 1) return;
    const tag = node.localName.toLowerCase();
    if (tag === 'img') {
      const src = node.getAttribute('src') || '';
      if (/^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(src)) {
        const img = document.createElement('img'); img.src = src; img.alt = 'Source diagram'; target.append(img);
      } else target.append(document.createTextNode('[Diagram unavailable]'));
      return;
    }
    if (!allowed.has(tag)) {
      if (!['script','style','iframe','object','svg','form','input','button','link','meta'].includes(tag)) for (const child of node.childNodes) copy(child, target);
      return;
    }
    const el = node.namespaceURI === 'http://www.w3.org/1998/Math/MathML' ? document.createElementNS(node.namespaceURI, tag) : document.createElement(tag);
    for (const child of node.childNodes) copy(child, el);
    target.append(el);
  }
  for (const node of template.content.childNodes) copy(node, result);
  return result.innerHTML;
}
function documentHtml(content) {
  return '<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><style>body{font:16px/1.6 system-ui;padding:1rem}img{max-width:100%}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:.4rem}</style><body>'+content+'</body></html>';
}
function preview() { $('preview').srcdoc = documentHtml(safeHtml($('source').value)); }
function fieldView() {
  $('source').value = draft.fields[$('field').value];
  $('original').textContent = current.original[$('field').value]; preview();
}
function save() {
  if (!current) return;
  draft.notes = $('repairNotes').value; draft.status = $('status').value;
  corrections[current.id] = structuredClone(draft); dirty = false; persist();
}
function canLeave() { return !dirty || confirm('Discard unsaved changes? Save first to keep them.'); }
function select(id) {
  if (!known.has(id) || !canLeave()) return;
  requested = id; dirty = false; $('work').hidden = true;
  const script = document.createElement('script'); script.src = `repair-data/${id}.js`;
  script.onerror = () => tell('Could not load the question. Keep repair-data beside this page.');
  script.onload = () => script.remove(); document.body.append(script);
}
window.receiveQuestion = q => {
  if (q.id !== requested) return;
  current = q; draft = structuredClone(corrections[q.id] || {fields:q.fields, notes:'', status:'draft'});
  const item = catalog.find(r => r.id === q.id);
  $('title').textContent = `${item.title}${q.part ? ' · Suggested part '+q.part : ''}`;
  $('provenance').textContent = `${q.provenance.source_file} / ${q.provenance.source_sheet} / row ${q.provenance.source_row} / ID ${q.provenance.source_id}`;
  $('notes').replaceChildren();
  for (const note of [...q.notes, ...q.issues]) { const p = document.createElement('p'); p.textContent = note; $('notes').append(p); }
  $('siblings').replaceChildren(document.createTextNode('Related source rows: '));
  for (const id of q.siblings) {
    const a = document.createElement('a'); a.href = '#'+id; a.textContent = String(q.siblings.indexOf(id)+1);
    a.onclick = event => {event.preventDefault(); select(id);}; $('siblings').append(a);
  }
  $('repairNotes').value = draft.notes; $('status').value = draft.status; $('work').hidden = false;
  $('questions').value = q.id; history.replaceState(null, '', '#'+q.id); fieldView();
};
function listing() {
  const needle = $('find').value.toLowerCase(); const mode = $('filter').value;
  $('questions').replaceChildren();
  for (const q of catalog) {
    if (!`${q.title} ${q.topic} ${q.text}`.toLowerCase().includes(needle) ||
        (mode === 'warning' && !q.review) || (mode === 'saved' && !corrections[q.id]) ||
        (mode === 'unreviewed' && corrections[q.id]?.status === 'approved')) continue;
    const label = repairLabels[q.id];
    $('questions').add(new Option(`${q.title}${label.part ? ' · inferred '+label.part : ''} · source ${label.source}${corrections[q.id] ? ' · '+corrections[q.id].status : ''}`, q.id));
  }
  if (current && [...$('questions').options].some(o => o.value === current.id)) $('questions').value = current.id;
}
function download(name, content, type) {
  const url = URL.createObjectURL(new Blob([content], {type})); const a = document.createElement('a');
  a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 10000);
}
$('source').oninput = () => { draft.fields[$('field').value] = $('source').value; dirty = true; preview(); };
$('field').onchange = fieldView;
for (const id of ['repairNotes','status']) $(id).oninput = () => { dirty = true; };
$('save').onclick = () => {save(); listing();};
$('suggestion').onclick = () => { draft.fields[$('field').value] = current.fields[$('field').value]; dirty = true; fieldView(); };
$('restore').onclick = () => { draft.fields[$('field').value] = current.original[$('field').value]; dirty = true; fieldView(); };
$('questions').onchange = () => select($('questions').value);
for (const id of ['find','filter']) $(id).oninput = listing;
for (const [id, direction] of [['previous',-1],['next',1]]) $(id).onclick = () => {
  const options = [...$('questions').options]; const i = options.findIndex(o => o.value === current?.id);
  const next = options[i + direction]; if (next) select(next.value);
};
$('export').onclick = () => { if (dirty) save(); download('chemistry-exam-corrections.json', JSON.stringify(packageData(), null, 2), 'application/json'); };
$('import').onchange = async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    const incoming = validate(JSON.parse(await file.text()));
    if (!canLeave()) return;
    const overlap = Object.keys(incoming).some(id => corrections[id]);
    if (overlap && !confirm('Replace existing corrections for matching questions with this file?')) return;
    corrections = {...corrections, ...incoming}; dirty = false; persist(); listing();
    if (current) select(current.id);
  } catch (e) { tell(e.message); }
  finally { event.target.value = ''; }
};
$('download').onclick = () => {
  const title = document.createElement('h1'); title.textContent = $('title').textContent;
  let body = title.outerHTML+'<p>Teacher correction. Review status: '+$('status').value+'.</p>';
  for (const field of fields) body += '<h2>'+field+'</h2>'+safeHtml(draft.fields[field]);
  download(`${current.id}-corrected.html`, documentHtml(body), 'text/html');
};
window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
listing(); select(known.has(location.hash.slice(1)) ? location.hash.slice(1) : catalog[0].id);
