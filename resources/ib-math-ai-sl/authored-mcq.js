/* The authored workbook MCQs: every A-D button checks immediately, offline. */
(() => {
  'use strict';
  document.querySelectorAll('[data-authored-mcq]').forEach(card => {
    const buttons=[...card.querySelectorAll('[data-choice]')], feedback=card.querySelector('.mcq-feedback');
    const explanation=card.querySelector('.mcq-explanation'), key=card.dataset.authoredMcq;
    let assisted=false;
    function show(letter, restored=false) {
      const correct=letter===card.dataset.correct;
      buttons.forEach(button=>{
        const selected=button.dataset.choice===letter;
        button.setAttribute('aria-pressed',String(selected));
        button.classList.toggle('mcq-right',selected&&correct);
        button.classList.toggle('mcq-wrong',selected&&!correct);
      });
      feedback.textContent=(restored?'Saved answer: ':'')+(correct
        ? `Correct — ${letter}. ${card.querySelector('.mcq-working').textContent}`
        : `Not correct — you chose ${letter}. Try another option, or open the explanation.`);
      return correct;
    }
    const saved=window.StudentPractice?.choiceDraft(key);
    if(saved)assisted=saved.assisted;
    if(saved && 'ABCD'.includes(saved.answer) && saved.answer.length===1)show(saved.answer,true);
    explanation.addEventListener('toggle',()=>{if(explanation.open){assisted=true;window.StudentPractice?.saveChoiceHelp(key);}});
    buttons.forEach(button=>button.addEventListener('click',()=>{
      assisted ||= explanation.open;
      const letter=button.dataset.choice, correct=show(letter);
      window.StudentPractice?.recordChoice(key,letter,correct,assisted);
      // Immediate feedback reveals the answer on success; a later selection is a retry.
      assisted=true;
    }));
    card.querySelector('.mcq-retry').addEventListener('click',()=>{
      explanation.open=false;assisted=false;feedback.textContent='Choose an answer to start a fresh attempt.';
      buttons.forEach(button=>{button.setAttribute('aria-pressed','false');button.classList.remove('mcq-right','mcq-wrong');});
      window.StudentPractice?.clearChoice(key);buttons[0].focus();
    });
  });
})();
