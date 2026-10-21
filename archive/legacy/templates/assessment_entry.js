(() => {
  const body = document.querySelector('#questions'), form = document.querySelector('#assessment-form');
  let dirty = form.dataset.unsaved === 'true';
  function changed() { dirty = true; document.querySelector('#save-state').textContent = 'Unsaved changes'; }
  function add(q = {}) {
    const row = document.querySelector('#question-row').content.firstElementChild.cloneNode(true);
    row.dataset.id = q.id || '';
    row.querySelector('.question-number').value = q.number || '';
    row.querySelector('.maximum').value = q.marks ?? '';
    row.querySelector('.question-text').value = q.text || '';
    row.querySelector('.curriculum').value = q.curriculum || '';
    for (const [category, tags] of Object.entries(categories)) {
      const group = document.createElement('details'), title = document.createElement('summary');
      title.textContent = category.replace(/([a-z])([A-Z])/g, '$1 $2'); group.append(title);
      for (const tag of tags) {
        const label = document.createElement('label'), input = document.createElement('input');
        input.type = 'checkbox'; input.dataset.category = category; input.value = tag;
        input.checked = (q.tags?.[category] || []).includes(tag);
        label.append(input, document.createTextNode(' ' + tag)); group.append(label);
      }
      row.querySelector('.tag-fields').append(group);
    }
    function count() { row.querySelector('.tag-count').textContent = `(${row.querySelectorAll('.tag-fields input:checked').length})`; }
    row.addEventListener('change', count); count();
    row.addEventListener('click', event => {
      const action = event.target.dataset.action;
      if (action === 'up' && row.previousElementSibling) body.insertBefore(row, row.previousElementSibling);
      else if (action === 'down' && row.nextElementSibling) body.insertBefore(row.nextElementSibling, row);
      else if (action === 'remove' && confirm('Remove this question? Saved marks prevent removal until cleared.')) row.remove();
      else return;
      changed();
    });
    body.append(row); return row;
  }
  for (const question of initialAssessment.questions || []) add(question);
  document.querySelector('#add-question').addEventListener('click', () => { add().querySelector('input').focus(); changed(); });
  form.addEventListener('input', changed);
  form.addEventListener('submit', event => {
    if (!body.children.length) { event.preventDefault(); alert('Add at least one question.'); return; }
    const questions = [...body.children].map(row => {
      const tags = {};
      for (const input of row.querySelectorAll('.tag-fields input:checked')) (tags[input.dataset.category] ||= []).push(input.value);
      return {id: row.dataset.id, number: row.querySelector('.question-number').value, marks: row.querySelector('.maximum').value,
        text: row.querySelector('.question-text').value, curriculum: row.querySelector('.curriculum').value, tags};
    });
    document.querySelector('#payload').value = JSON.stringify({name: document.querySelector('#assessment-name').value,
      date: document.querySelector('#assessment-date').value, description: document.querySelector('#description').value,
      participants: [...document.querySelectorAll('.participant:checked')].map(i => i.value), questions});
    dirty = false;
  });
  window.addEventListener('beforeunload', e => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
})();
