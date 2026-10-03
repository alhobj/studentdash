/* Guided to independent practice. Content and diagnostic feedback are profile data. */
(() => {
  'use strict';
  const near = (a, b) => Math.abs(a - b) <= Math.max(1e-8, Math.abs(b) * .001);
  document.querySelectorAll('[data-booklet-task]').forEach(host => {
    const pack = JSON.parse(host.dataset.bookletTask), form = host.querySelector('form');
    const reference = host.querySelector('.lookup-reference'), unit = host.querySelector('.lookup-unit');
    const answer = host.querySelector('.lookup-answer'), feedback = host.querySelector('.lookup-feedback');
    const previous = host.querySelector('.lookup-previous'), next = host.querySelector('.lookup-next');
    const fields = [reference, unit, answer];
    let index = 0;
    host.querySelector('.lookup-controls').hidden = false;
    form.querySelector('button').hidden = false;
    function clear() {
      feedback.textContent = '';
      fields.forEach(field => field.removeAttribute('aria-invalid'));
    }
    function show() {
      const q = pack.questions[index];
      form.reset(); clear();
      host.querySelector('.lookup-position').textContent = `Question ${index + 1} of 3 · ${['Guided setup', 'Short cue', 'Independent attempt'][index]}`;
      host.querySelector('.lookup-prompt').textContent = q.prompt;
      host.querySelector('.lookup-guidance').textContent = index === 0 ? q.hint : index === 1 ? q.cue : 'Try choosing and setting up the calculation yourself. Open More support whenever you need it.';
      host.querySelector('.lookup-support p').textContent = q.hint;
      host.querySelector('.lookup-working p').textContent = q.working;
      host.querySelectorAll('details').forEach(d => { d.open = false; });
      previous.disabled = index === 0;
      next.textContent = index === 2 ? 'Repeat set' : 'Next question';
    }
    function report(field, message) {
      field.setAttribute('aria-invalid', 'true');
      feedback.textContent = message;
    }
    form.addEventListener('submit', event => {
      event.preventDefault(); clear();
      if (!reference.value) return report(reference, 'Choose a booklet entry first. You can browse the possible entries above.');
      if (reference.value !== pack.reference) return report(reference, pack.choices.find(c => c.id === reference.value).feedback);
      if (!unit.value) return report(unit, 'Choose the requested unit or answer type.');
      if (unit.value !== pack.unit) return report(unit, pack.units.find(u => u.label === unit.value).feedback);
      if (!answer.value.trim() || !Number.isFinite(answer.valueAsNumber)) return report(answer, 'Enter a finite number in the requested units.');
      const q = pack.questions[index];
      if (near(answer.valueAsNumber, q.answer)) {
        feedback.textContent = 'Your entry, unit and numerical answer match. Compare your method with the worked answer, then try the next question.';
      } else {
        const mistake = q.mistakes.find(m => near(answer.valueAsNumber, m.value));
        report(answer, mistake ? mistake.feedback : 'The entry and unit fit. Check substitution, arithmetic and signs, or open More support.');
      }
    });
    fields.forEach(field => { field.addEventListener('input', clear); field.addEventListener('change', clear); });
    function move(value) { index = value; show(); host.querySelector('h2').focus(); }
    previous.addEventListener('click', () => move(Math.max(0, index - 1)));
    next.addEventListener('click', () => move((index + 1) % 3));
    host.querySelector('.lookup-reset').addEventListener('click', () => move(0));
    show();
  });
})();
