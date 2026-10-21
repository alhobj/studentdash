(() => {
  const form = document.querySelector('#review-form'), list = document.querySelector('#review-questions');
  const state = document.querySelector('#review-state'), profile = importDraft.profile;
  const initialIds = new Set(importDraft.nodes.map(n => n.id));
  let dirty = form.dataset.unsaved === 'true';
  let nodes = structuredClone(importDraft.nodes);
  if (importSubmitted && Array.isArray(importSubmitted.nodes)) {
    nodes = importSubmitted.nodes.map(n => ({...(nodes.find(old => old.id === n.id) || {}), ...n}));
    for (const [id, field] of [['review-title', 'title'], ['review-date', 'date'], ['review-description', 'description'], ['review-note', 'warning_note']]) {
      if (typeof importSubmitted[field] === 'string') document.getElementById(id).value = importSubmitted[field];
    }
  }
  const newId = () => crypto.randomUUID().replaceAll('-', '');
  function changed() { dirty = true; state.textContent = 'Unsaved review changes'; }
  function selected(n, s) { return s.kind === 'curriculum' ? (n.curriculum_nodes || []).includes(s.value) : (n.tags?.[s.category] || []).includes(s.value); }
  function choose(n, kind, category, value, checked) {
    const values = kind === 'curriculum' ? (n.curriculum_nodes ||= []) : ((n.tags ||= {})[category] ||= []);
    if (checked && kind === 'tag' && profile.category_options?.[category]?.multiple === false) values.splice(0);
    const at = values.indexOf(value);
    if (checked && at < 0) values.push(value);
    else if (!checked && at >= 0) values.splice(at, 1);
    for (const s of n.suggestions || []) if (s.kind === kind && s.category === category && s.value === value) {
      s.decision = checked ? 'accepted' : 'rejected'; (n.decisions ||= {})[s.key] = s.decision;
    }
    changed();
  }
  function nodeOrigins(n) { return [...new Set([...(n.origins || []), ...(initialIds.has(n.id) ? [n.id] : [])])]; }
  function render() {
    const openDetails = new Map([...list.children].map(card => [card.dataset.node, [...card.querySelectorAll('details')].map(d => d.open)]));
    list.replaceChildren();
    nodes.forEach((n, index) => {
      n.id ||= newId(); n.tags ||= {}; n.curriculum_nodes ||= [];
      const card = document.querySelector('#review-question-template').content.firstElementChild.cloneNode(true);
      card.dataset.node = n.id;
      card.querySelector('.question-heading').textContent = `${n.scorable ? 'Question' : 'Shared context'} ${n.number || '(label needed)'}`;
      const confidence = n.confidence || {number: 0, marks: 0};
      card.querySelector('.extraction-strength').textContent = `Original extraction signals: number ${Math.round(confidence.number * 100)}%, marks ${Math.round(confidence.marks * 100)}%.`;
      const warning = card.querySelector('.question-warning');
      warning.textContent = (n.warnings || []).join(' '); warning.hidden = !warning.textContent;
      const number = card.querySelector('.import-number'), marks = card.querySelector('.import-marks'), text = card.querySelector('.import-text');
      number.value = n.number || ''; marks.value = n.marks ?? ''; text.value = n.text || '';
      number.addEventListener('input', () => {
        n.number = number.value; changed();
        card.querySelector('.question-heading').textContent = `${n.scorable ? 'Question' : 'Shared context'} ${n.number || '(label needed)'}`;
        for (const option of list.querySelectorAll('.import-parent option')) if (option.value === n.id) option.textContent = n.number || '(unlabelled context)';
      });
      marks.addEventListener('input', () => { n.marks = marks.value; n.reviewed = false; card.querySelector('.question-reviewed').checked = false; changed(); });
      text.addEventListener('input', () => { n.text = text.value; n.reviewed = false; card.querySelector('.question-reviewed').checked = false; changed(); });
      const parent = card.querySelector('.import-parent');
      parent.append(new Option('No parent', ''));
      for (const other of nodes) if (other.id !== n.id) parent.append(new Option(other.number || '(unlabelled context)', other.id));
      parent.value = n.parent || '';
      parent.addEventListener('change', () => { n.parent = parent.value || null; n.reviewed = false; changed(); render(); });
      const scorable = card.querySelector('.import-scorable'); scorable.checked = n.scorable !== false;
      scorable.addEventListener('change', () => { n.scorable = scorable.checked; n.reviewed = false; changed(); render(); });
      const reviewed = card.querySelector('.question-reviewed'); reviewed.checked = n.reviewed === true;
      reviewed.addEventListener('change', () => { n.reviewed = reviewed.checked; changed(); });
      card.querySelector('.source-location').textContent = [...(n.source_pages || []).map(p => `Page ${p}`), ...(n.source_locations || [])].join(' · ') || 'Source location needs review';
      card.querySelector('.source-text').textContent = n.source_text || 'Teacher-added question; compare with the original document.';
      card.querySelector('.source-figures').textContent = (n.figures || []).join('\n');
      for (const table of n.tables || []) {
        const pre = document.createElement('pre'); pre.style.whiteSpace = 'pre-wrap'; pre.textContent = table.text;
        card.querySelector('.source-tables').append(pre);
      }
      const suggestionBox = card.querySelector('.import-suggestions');
      for (const s of n.suggestions || []) {
        const row = document.createElement('p'), accept = document.createElement('button'), reject = document.createElement('button');
        const label = s.kind === 'curriculum' ? (importCurriculum[s.value]?.code || importCurriculum[s.value]?.label || s.value) : `${s.category}: ${s.value}`;
        const provenance = s.source === 'inferred' ? 'Inferred' : s.source === 'teacher' ? 'Teacher' : 'Detected';
        row.append(document.createTextNode(`${label} · ${provenance} · ${Math.round(s.confidence * 100)}% — ${s.reason} `));
        accept.type = reject.type = 'button';
        accept.textContent = selected(n, s) ? 'Accepted' : 'Accept'; reject.textContent = s.decision === 'rejected' ? 'Rejected' : 'Reject';
        accept.addEventListener('click', () => { choose(n, s.kind, s.category, s.value, true); s.decision = 'accepted'; render(); });
        reject.addEventListener('click', () => { choose(n, s.kind, s.category, s.value, false); s.decision = 'rejected'; render(); });
        row.append(accept, document.createTextNode(' '), reject); suggestionBox.append(row);
      }
      card.querySelector('.suggestion-note').textContent = n.suggestion_note || (n.suggestions?.length ? '' : 'Needs review: no supported matches yet.');
      function choice(container, kind, category, value, labelText) {
        const label = document.createElement('label'), input = document.createElement('input');
        input.type = 'checkbox'; input.checked = selected(n, {kind, category, value});
        input.addEventListener('change', () => { choose(n, kind, category, value, input.checked); render(); });
        label.append(input, document.createTextNode(' ' + labelText)); container.append(label);
      }
      for (const [category, values] of Object.entries(profile.categories)) {
        const group = document.createElement('details'), heading = document.createElement('summary');
        heading.textContent = `${category.replace(/([a-z])([A-Z])/g, '$1 $2')} (${(n.tags[category] || []).length} selected)`;
        group.append(heading);
        for (const value of values) choice(group, 'tag', category, value, value);
        card.querySelector('.import-tags').append(group);
      }
      const curriculum = card.querySelector('.import-curriculum');
      const heading = document.createElement('h4'); heading.textContent = 'Curriculum'; curriculum.append(heading);
      for (const [id, node] of Object.entries(importCurriculum)) choice(curriculum, 'curriculum', null, id, [node.code, node.label].filter(Boolean).join(' — '));
      if (!Object.keys(importCurriculum).length) curriculum.append(document.createTextNode('Needs review: no configured curriculum nodes.'));
      card.addEventListener('click', event => {
        const action = event.target.dataset.action;
        if (!action) return;
        const children = nodes.filter(other => other.parent === n.id);
        if (action === 'delete') {
          if (children.length) { alert('Move or delete the child questions before deleting their shared context.'); return; }
          if (!confirm('Delete this detected question? The original document will remain available.')) return;
          nodes.splice(index, 1);
        } else if (action === 'split') {
          if (children.length) { alert('Split a scorable question, not a shared parent context.'); return; }
          const at = text.selectionStart;
          if (at <= 0 || at >= n.text.length) { alert('Place the text cursor where the second question should begin, then click Split question.'); return; }
          const next = {...structuredClone(n), id: newId(), number: '', text: n.text.slice(at).trim(), marks: null,
            origins: nodeOrigins(n), reviewed: false, tags: {}, curriculum_nodes: [], suggestions: [], confidence: {number: 0, text: 0, marks: 0},
            warnings: ['Split question: enter its label and marks, and check its classifications.']};
          n.text = n.text.slice(0, at).trim(); n.marks = null; n.reviewed = false;
          nodes.splice(index + 1, 0, next);
        } else if (action === 'combine') {
          const next = nodes[index + 1];
          if (!next || children.length || nodes.some(other => other.parent === next.id) || (next.parent || null) !== (n.parent || null)) {
            alert('Combine adjacent questions with the same parent and no child questions. Edit shared context separately.'); return;
          }
          if (!confirm('Combine with the next question? Review the combined text and marks before confirming.')) return;
          n.text = `${n.text}\n\n${next.text}`;
          n.marks = n.marks !== null && n.marks !== '' && next.marks !== null && next.marks !== '' ? Number(n.marks) + Number(next.marks) : null;
          n.origins = [...new Set([...nodeOrigins(n), ...nodeOrigins(next)])];
          n.reviewed = false; n.tags = {}; n.curriculum_nodes = []; n.suggestions = [];
          n.warnings = [...(n.warnings || []), 'Combined content: check the labels, marks and classifications.'];
          nodes.splice(index + 1, 1);
        } else if (action === 'up' && index > 0) [nodes[index - 1], nodes[index]] = [nodes[index], nodes[index - 1]];
        else if (action === 'down' && index + 1 < nodes.length) [nodes[index], nodes[index + 1]] = [nodes[index + 1], nodes[index]];
        else return;
        changed(); render();
      });
      list.append(card);
      [...card.querySelectorAll('details')].forEach((d, i) => { d.open = openDetails.get(n.id)?.[i] || false; });
    });
  }
  document.querySelector('#accept-high').addEventListener('click', () => {
    let count = 0;
    for (const n of nodes) for (const s of n.suggestions || []) {
      if (s.confidence >= .9 && ['existing', 'rule'].includes(s.source) && s.decision !== 'rejected') {
        if (s.kind === 'tag' && profile.category_options?.[s.category]?.multiple === false) {
          const alternatives = n.suggestions.filter(other => other.kind === 'tag' && other.category === s.category &&
            other.confidence >= .9 && ['existing', 'rule'].includes(other.source) && other.decision !== 'rejected');
          if (alternatives.length > 1 || (n.tags?.[s.category] || []).some(value => value !== s.value)) continue;
        }
        choose(n, s.kind, s.category, s.value, true); s.decision = 'accepted'; count++;
      }
    }
    render(); state.textContent = `${count} explicit high-confidence suggestions selected. Review text and marks separately, then save.`;
  });
  document.querySelector('#add-import-question').addEventListener('click', () => {
    nodes.push({id: newId(), number: '', parent: null, text: '', marks: null, scorable: true, reviewed: false, tags: {}, curriculum_nodes: [], suggestions: []});
    changed(); render(); list.lastElementChild.querySelector('.import-number').focus();
  });
  form.addEventListener('input', changed);
  form.addEventListener('submit', event => {
    if (event.submitter?.value === 'finalize' && (!document.querySelector('#review-ack').checked || nodes.some(n => !n.reviewed))) {
      event.preventDefault(); state.textContent = 'Check each question/context and confirm the final review before creating the assessment.'; return;
    }
    const payload = {title: document.querySelector('#review-title').value, date: document.querySelector('#review-date').value,
      description: document.querySelector('#review-description').value, warning_note: document.querySelector('#review-note').value,
      participants: [...document.querySelectorAll('.review-participant:checked')].map(i => i.value),
      review_ack: document.querySelector('#review-ack').checked,
      nodes: nodes.map(n => ({id: n.id, number: n.number || '', text: n.text || '', marks: n.marks ?? null, parent: n.parent || null,
        scorable: n.scorable !== false, tags: n.tags || {}, curriculum_nodes: n.curriculum_nodes || [], reviewed: n.reviewed === true,
        decisions: n.decisions || {}, origins: n.origins || []}))};
    document.querySelector('#review-payload').value = JSON.stringify(payload); dirty = false;
  });
  window.addEventListener('beforeunload', e => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
  render();
})();
