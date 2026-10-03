/* Numerical checkpoints and local-only working notes for multi-part challenges. */
(() => {
  'use strict';
  document.querySelectorAll('[data-challenge]').forEach(section => {
    section.querySelectorAll('.challenge-part').forEach(form => {
      const input = form.querySelector('input');
      const feedback = form.querySelector('.feedback');
      form.addEventListener('submit', event => {
        event.preventDefault();
        const n = input.valueAsNumber, answer = Number(form.dataset.answer);
        if (!Number.isFinite(n)) {
          feedback.textContent = 'Enter a finite number first, using the units requested.';
          input.setAttribute('aria-invalid', 'true');
          return;
        }
        const correct = Math.abs(n - answer) <= Math.max(1e-8, Math.abs(answer) * 0.001);
        input.setAttribute('aria-invalid', String(!correct));
        feedback.textContent = correct
          ? 'Numerical answer accepted. Check your method and complete the written reasoning as well.'
          : 'Not yet. Check your model, units and intermediate values. A hint is available.';
      });
      input.addEventListener('input', () => {
        feedback.textContent = '';
        input.removeAttribute('aria-invalid');
      });
    });
    section.querySelector('.challenge-reset').addEventListener('click', () => {
      section.querySelectorAll('form').forEach(form => form.reset());
      section.querySelectorAll('textarea').forEach(e => { e.value = ''; });
      section.querySelectorAll('.feedback').forEach(e => { e.textContent = ''; });
      section.querySelectorAll('input').forEach(e => e.removeAttribute('aria-invalid'));
      section.querySelectorAll('details').forEach(e => { e.open = false; });
      section.querySelector('input').focus();
    });
  });
})();
