/* Pure paste/validation functions are also exercised by the JavaScript tests. */
const ScoreGrid = (() => {
  function parse(value, maximum) {
    const raw = String(value).trim().toLowerCase();
    const aliases = {'': 'pending', a: 'absent', e: 'exempt', m: 'missing', p: 'pending'};
    const status = aliases[raw] || raw;
    if (['absent', 'exempt', 'missing', 'pending'].includes(status)) return {status, score: null};
    const normalized = raw.replace(',', '.');
    const score = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(normalized) ? Number(normalized) : NaN;
    if (!Number.isFinite(score) || score < 0 || score > maximum) return {error: `Enter 0–${maximum}, or A, E, M, P.`};
    return {status: 'graded', score};
  }
  function paste(text, rows, columns, startRow, startCol) {
    let lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    if (lines.at(-1) === '') lines.pop(); // Excel's trailing line terminator is not an extra student.
    const block = lines.map(line => line.split('\t'));
    if (!block.length || !block[0].length || block.some(row => row.length !== block[0].length)) throw Error('Paste a rectangular block with the same number of columns in every row.');
    if (startRow + block.length > rows || startCol + block[0].length > columns) throw Error('The pasted block extends beyond the grid. No cells were changed.');
    return block;
  }
  return {parse, paste};
})();
if (typeof module !== 'undefined') module.exports = ScoreGrid;
if (typeof document !== 'undefined') (() => {
  const table = document.querySelector('#score-grid'), form = document.querySelector('#scores-form');
  const rows = [...table.tBodies[0].rows].map(row => [...row.querySelectorAll('input')]);
  const state = document.querySelector('#save-state'), message = document.querySelector('#grid-message');
  let dirty = form.dataset.unsaved === 'true';
  function validate(input) {
    const result = ScoreGrid.parse(input.value, Number(input.dataset.max));
    input.setAttribute('aria-invalid', result.error ? 'true' : 'false');
    document.getElementById(input.getAttribute('aria-describedby')).textContent = result.error || '';
    return result;
  }
  function totals() {
    rows.forEach((row, i) => {
      const values = row.map(input => ScoreGrid.parse(input.value, Number(input.dataset.max)));
      let label = 'Incomplete';
      if (values.some(v => v.error)) label = 'Invalid entry';
      else if (values.every(v => v.status === 'exempt')) label = 'Exempt';
      else if (values.every(v => ['absent', 'exempt'].includes(v.status))) label = 'Absent';
      else if (values.every(v => ['missing', 'exempt'].includes(v.status))) label = 'Missing';
      else if (values.every(v => ['graded', 'exempt'].includes(v.status))) {
        const earned = values.reduce((sum, v) => sum + (v.score || 0), 0);
        const max = values.reduce((sum, v, c) => sum + (v.status === 'exempt' ? 0 : Number(row[c].dataset.max)), 0);
        label = `${Number(earned.toFixed(8))}/${Number(max.toFixed(8))}`;
      }
      table.tBodies[0].rows[i].querySelector('.row-total').textContent = label;
    });
  }
  function changed() { dirty = true; state.textContent = 'Unsaved changes — save before generating dashboards'; totals(); }
  table.addEventListener('input', e => { if (e.target.matches('input')) { validate(e.target); changed(); } });
  table.addEventListener('paste', e => {
    if (!e.target.matches('input')) return;
    e.preventDefault();
    const r = Number(e.target.dataset.row), c = Number(e.target.dataset.col);
    try {
      const block = ScoreGrid.paste(e.clipboardData.getData('text/plain'), rows.length, rows[0].length, r, c);
      for (let dr = 0; dr < block.length; dr++) for (let dc = 0; dc < block[dr].length; dc++) {
        rows[r + dr][c + dc].value = block[dr][dc].trim(); validate(rows[r + dr][c + dc]);
      }
      message.textContent = `Pasted ${block.length} rows × ${block[0].length} columns. Review and save.`; changed();
    } catch (error) { message.textContent = error.message; }
  });
  table.addEventListener('keydown', e => {
    if (!e.target.matches('input')) return;
    let r = Number(e.target.dataset.row), c = Number(e.target.dataset.col);
    if (e.key === 'Enter') r += e.shiftKey ? -1 : 1;
    else if (e.key === 'ArrowDown') r++;
    else if (e.key === 'ArrowUp') r--;
    else if (e.key === 'ArrowLeft') c--;
    else if (e.key === 'ArrowRight') c++;
    else return;
    e.preventDefault(); const next = rows[r]?.[c]; if (next) { next.focus(); next.select(); }
  });
  form.addEventListener('submit', e => {
    const invalid = rows.flat().filter(input => validate(input).error);
    if (invalid.length) { e.preventDefault(); invalid[0].focus(); message.textContent = 'Correct the highlighted cells before saving.'; return; }
    document.querySelector('#payload').value = JSON.stringify(rows.map(row => row.map(input => input.value)));
    dirty = false;
  });
  document.querySelector('#generate-form').addEventListener('submit', e => {
    if (dirty) { e.preventDefault(); message.textContent = 'Save scores before generating dashboards.'; }
  });
  window.addEventListener('beforeunload', e => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
  totals();
})();
