/* Short, untimed foundation exercises. All state stays in the open page. */
(() => {
  'use strict';
  document.querySelectorAll('[data-foundation]').forEach(lesson => {
    lesson.querySelectorAll('.foundation-step').forEach(form => {
      const input = form.querySelector('input');
      const feedback = form.querySelector('.feedback');
      form.addEventListener('submit', event => {
        event.preventDefault();
        const value = input.valueAsNumber;
        if (!Number.isFinite(value)) {
          feedback.textContent = 'Enter a number first. You can open a hint to help you start.';
          return;
        }
        const correct = Math.abs(value - Number(form.dataset.answer)) < 1e-8;
        feedback.textContent = correct
          ? 'That’s right. You can open the worked step to compare your method.'
          : 'Not quite yet. Open a hint, check your calculation, and try again.';
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
