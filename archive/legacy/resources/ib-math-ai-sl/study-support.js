/* Local-only recommendations and accessible filtering; no scores or storage. */
(() => {
  'use strict';
  document.querySelectorAll('[data-readiness]').forEach(section => {
    const data = JSON.parse(section.dataset.readiness);
    const form = section.querySelector('form'), input = form.querySelector('input');
    const feedback = section.querySelector('.feedback'), next = section.querySelector('.recommendation');
    let usedExplanation = false;
    section.querySelector('.ready-working summary').addEventListener('click', () => {
      if (!section.querySelector('.ready-working').open) usedExplanation = true;
    });
    section.querySelector('.ready-working').addEventListener('toggle', event => {
      if (event.target.open) usedExplanation = true;
    });
    form.addEventListener('submit', event => {
      event.preventDefault();
      next.replaceChildren();
      const value = input.valueAsNumber;
      if (!Number.isFinite(value)) {
        feedback.textContent = 'Enter a number, or open the explanation if you would like help starting.';
        input.setAttribute('aria-invalid', 'true');
        return;
      }
      const correct = Math.abs(value - data.answer) < 1e-8;
      usedExplanation ||= section.querySelector('.ready-working').open;
      input.setAttribute('aria-invalid', String(!correct));
      const mistake = data.mistakes.find(m => Math.abs(value - m.value) < 1e-8);
      feedback.textContent = correct
        ? 'That numerical answer is right. Explain your method before moving on.'
        : mistake ? mistake.feedback : 'Not quite yet. Check the quantities and units, then compare with the worked explanation.';
      const link = document.createElement('a');
      if (!correct) {
        next.append('A useful next step: ');
        link.href = data.prior; link.textContent = 'revisit this prerequisite';
      } else if (usedExplanation) {
        next.append('You used the explanation. Build confidence by trying a related question independently: ');
        link.href = data.basic; link.textContent = 'small-step practice';
      } else {
        next.append('Ready to apply this idea in a longer problem? ');
        link.href = data.challenge; link.textContent = 'try the harder task';
      }
      next.append(link);
    });
    input.addEventListener('input', () => {
      feedback.textContent = ''; next.replaceChildren(); input.removeAttribute('aria-invalid');
    });
    section.querySelector('.readiness-reset').addEventListener('click', () => {
      form.reset(); feedback.textContent = ''; next.replaceChildren(); input.removeAttribute('aria-invalid');
      section.querySelectorAll('details').forEach(d => { d.open = false; });
      usedExplanation = false; input.focus();
    });
  });

  const controls = document.querySelector('.finder-controls');
  if (!controls) return;
  controls.hidden = false;
  const search = document.querySelector('#practice-search'), level = document.querySelector('#practice-level');
  const sections = [...document.querySelectorAll('[data-find]')];
  // Ignore spacing and punctuation in codes, so S.1.4 also finds S1.4.
  const normalize = text => text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
  function filter() {
    const terms = search.value.trim().split(/\s+/).map(normalize).filter(Boolean);
    let count = 0;
    sections.forEach(section => {
      section.hidden = !terms.every(t => normalize(section.dataset.find).includes(t));
      if (!section.hidden) count++;
      section.querySelectorAll('[data-level]').forEach(link => {
        link.hidden = level.value !== 'all' && link.dataset.level !== level.value;
      });
    });
    document.querySelector('#finder-status').textContent = `${count} of ${sections.length} sections shown.`;
    document.querySelector('#finder-empty').hidden = count !== 0;
  }
  search.addEventListener('input', filter); level.addEventListener('change', filter);
  document.querySelector('#finder-reset').addEventListener('click', () => {
    search.value = ''; level.value = 'all'; filter(); search.focus();
  });
  filter();
})();
