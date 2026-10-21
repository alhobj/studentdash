/* The authored workbook MCQs: every A-D button checks immediately, offline. */
(() => {
  'use strict';
  const cards=[...document.querySelectorAll('[data-authored-mcq]')];
  if(cards.length){
    const controls=document.createElement('nav');controls.setAttribute('aria-label','Practice set size');
    const status=document.createElement('p');status.setAttribute('role','status');
    let offset=0;
    function showSet(){cards.forEach((c,i)=>c.hidden=i<offset||i>=offset+5);status.textContent=`Showing questions ${offset+1}–${Math.min(offset+5,cards.length)} of ${cards.length}.`;more.disabled=offset+5>=cards.length;}
    function button(label,fn){const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',fn);controls.append(b);return b;}
    button('Start five-question set',()=>{offset=0;showSet();cards[0].querySelector('button').focus();});
    const more=button('Five more like these',()=>{offset+=5;showSet();cards[offset].querySelector('button').focus();});
    button('Show all 20 questions',()=>{cards.forEach(c=>c.hidden=false);status.textContent='Showing all questions.';offset=0;more.disabled=false;});
    controls.append(status);cards[0].before(controls);
    function revealHash(){const target=cards.find(c=>c.id===location.hash.slice(1));if(target){offset=Math.floor(cards.indexOf(target)/5)*5;showSet();}}
    window.addEventListener('hashchange',revealHash);revealHash();
  }
  cards.forEach(card => {
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
        : `Not correct — you chose ${letter}. ${buttons.find(b=>b.dataset.choice===letter)?.dataset.feedback || "Try another option, or open the explanation."}`);
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
