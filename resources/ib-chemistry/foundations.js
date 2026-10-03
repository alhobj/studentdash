/* Profile-local starter tasks. No storage, requests, timers or scores. */
(() => {
  'use strict';
  const normalize = value => value.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.!?]+$/, '').trim();
  document.querySelectorAll('[data-foundation]').forEach(lesson => {
    lesson.querySelectorAll('.foundation-step').forEach(form => {
      const input = form.querySelector('input');
      const feedback = form.querySelector('.feedback');
      const answer = JSON.parse(form.dataset.answer);
      form.addEventListener('submit', event => {
        event.preventDefault();
        const words = Array.isArray(answer);
        if (!input.value.trim() || (!words && !Number.isFinite(input.valueAsNumber))) {
          feedback.textContent = words ? 'Enter a short word answer first. A hint can help you start.' : 'Enter a number first. A hint can help you start.';
          input.setAttribute('aria-invalid', 'true');
          return;
        }
        const correct = words ? answer.some(a => normalize(a) === normalize(input.value)) : Math.abs(input.valueAsNumber - answer) < 1e-8;
        feedback.textContent = correct
          ? 'That’s right. Open the worked step to compare your reasoning.'
          : 'Not quite yet. Open a hint, check your reasoning and try again.';
        input.setAttribute('aria-invalid', String(!correct));
      });
      input.addEventListener('input', () => {
        feedback.textContent = '';
        input.removeAttribute('aria-invalid');
      });
    });
    lesson.querySelector('.foundation-reset').addEventListener('click', () => {
      lesson.querySelectorAll('form').forEach(form => form.reset());
      lesson.querySelectorAll('.feedback').forEach(e => { e.textContent = ''; });
      lesson.querySelectorAll('input').forEach(e => e.removeAttribute('aria-invalid'));
      lesson.querySelectorAll('details').forEach(e => { e.open = false; });
      lesson.querySelector('input').focus();
    });
  });
})();
