/* Local practice checks; optional portable progress is provided by learning.js. */
(() => {
  'use strict';
  const normalize = text => text.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.!?]+$/, '').trim();
  document.querySelectorAll('[data-similar]').forEach(host => {
    const bank = JSON.parse(host.dataset.similar), form = host.querySelector('form');
    const input = form.querySelector('input'), feedback = host.querySelector('.similar-feedback');
    const previous = host.querySelector('.similar-previous'), next = host.querySelector('.similar-next');
    const positionKey = host.closest('[data-foundation]').id;
    let index = Math.min(window.StudentPractice?.position(positionKey) || 0, bank.questions.length - 1);
    host.querySelector('.similar-controls').hidden = false;
    host.querySelector('.similar-check').hidden = false;
    function show() {
      window.StudentPractice?.move(positionKey, index);
      const q = bank.questions[index];
      form.querySelector('label').textContent = q.prompt;
      input.type = Array.isArray(q.answer) ? 'text' : 'number';
      input.value = ''; feedback.textContent = ''; input.removeAttribute('aria-invalid');
      host.querySelector('.similar-position').textContent = `Question ${index + 1} of ${bank.questions.length}`;
      host.querySelector('.similar-hint p').textContent = q.hint;
      host.querySelector('.similar-working p').textContent = q.working;
      host.querySelectorAll('details').forEach(d => { d.open = false; });
      previous.disabled = index === 0;
      next.textContent = index === bank.questions.length - 1 ? 'Repeat this set' : 'Another like this';
    }
    show();
    form.addEventListener('submit', event => {
      event.preventDefault();
      const answer = bank.questions[index].answer, words = Array.isArray(answer);
      if (!input.value.trim() || (!words && !Number.isFinite(input.valueAsNumber))) {
        feedback.textContent = words ? 'Enter a short word answer first.' : 'Enter a number first, in the requested units.';
        input.setAttribute('aria-invalid', 'true'); return;
      }
      const correct = words ? answer.some(a => normalize(a) === normalize(input.value)) : Math.abs(input.valueAsNumber - answer) < 1e-8;
      input.setAttribute('aria-invalid', String(!correct));
      window.StudentPractice?.recordForm(form, correct);
      feedback.textContent = correct ? 'That’s right. When you are ready, try another using the same method.' : (window.StudentPractice?.feedbackFor(form) || 'Not quite yet. Use the hint, check your steps and try again.');
    });
    input.addEventListener('input', () => { feedback.textContent = ''; input.removeAttribute('aria-invalid'); });
    previous.addEventListener('click', () => { index = Math.max(0, index - 1); show(); input.focus(); });
    next.addEventListener('click', () => { index = (index + 1) % bank.questions.length; show(); input.focus(); });
    host.closest('[data-foundation]').querySelector('.foundation-reset').addEventListener('click', () => { index = 0; show(); });
  });
})();
