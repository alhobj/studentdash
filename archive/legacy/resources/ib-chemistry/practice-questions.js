/* Shared scenario controls; chemistry content lives in the authored JSON data. */
(() => {
 'use strict';
 const dataElement = document.getElementById('practice-question-data');
 if (!dataElement) return;
 const activities = JSON.parse(dataElement.textContent);
 function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
 }
 document.querySelectorAll('[data-practice]').forEach(section => {
  const activity = activities[section.dataset.practice], prefix = section.id;
  const host = section.querySelector('.question-host');
  const scenarioLabel = node('label','Scenario');
  const scenario = node('select'); scenario.id=prefix+'-scenario'; scenarioLabel.htmlFor=scenario.id;
  activity.questions.forEach((question,index)=>scenario.add(new Option(`${index+1}. ${question.name}`,String(index))));
  const prompt = node('p',null,'result'); prompt.id=prefix+'-prompt';
  const answerLabel = node('label');
  const numeric = node('input'); numeric.type='number'; numeric.step='any'; numeric.id=prefix+'-number';
  const choice = node('select'); choice.id=prefix+'-choice';
  numeric.setAttribute('aria-describedby',prompt.id); choice.setAttribute('aria-describedby',prompt.id);
  const feedback = node('p',null,'feedback'); feedback.setAttribute('role','status');
  const progress = node('p',null,'muted'); progress.setAttribute('aria-live','polite');
  const solved = new Set();
  const current = () => activity.questions[Number(scenario.value)];
  const updateProgress = () => {progress.textContent=`${solved.size} of ${activity.questions.length} scenarios answered correctly on this visit.`;};
  function show() {
   const question=current(), isNumeric=typeof question.answer==='number';
   prompt.textContent=question.prompt;
   answerLabel.textContent=isNumeric?question.unit:'Your prediction';
   answerLabel.htmlFor=isNumeric?numeric.id:choice.id;
   numeric.hidden=!isNumeric; numeric.disabled=!isNumeric; numeric.value=''; numeric.removeAttribute('aria-invalid');
   choice.hidden=isNumeric; choice.disabled=isNumeric;
   choice.replaceChildren(new Option('Choose an answer',''));
   (question.options || []).forEach(option=>choice.add(new Option(option,option)));
   feedback.textContent='';updateProgress();
  }
  const check=node('button','Check answer');check.type='button';
  check.addEventListener('click',()=> {
   const question=current(), isNumeric=typeof question.answer==='number';
   const value=isNumeric?numeric.valueAsNumber:choice.value;
   if (isNumeric ? !Number.isFinite(value) : !value) {
    feedback.textContent=isNumeric?'Enter a finite numerical answer first.':'Choose an answer first.';
    if(isNumeric) numeric.setAttribute('aria-invalid','true');
    return;
   }
   numeric.removeAttribute('aria-invalid');
   const correct=isNumeric?Math.abs(value-question.answer)<=Math.max(Math.abs(question.answer)*0.01,1e-9):value===question.answer;
   if(correct) solved.add(Number(scenario.value));
   feedback.textContent=correct?'Correct. '+question.explanation:'Not yet. Reconsider the quantities or particle changes, then try again. Use “Show explanation” if you need a worked answer.';
   updateProgress();
  });
  const reveal=node('button','Show explanation');reveal.type='button';
  reveal.addEventListener('click',()=>{const question=current();feedback.textContent=`Answer: ${question.answer}. ${question.explanation}`;});
  const next=node('button','Next scenario');next.type='button';
  next.addEventListener('click',()=>{scenario.value=String((Number(scenario.value)+1)%activity.questions.length);show();});
  const reset=node('button','Reset practice');reset.type='button';
  reset.addEventListener('click',()=>{solved.clear();scenario.value='0';show();});
  [numeric,choice].forEach(input=>input.addEventListener('input',()=>{feedback.textContent='';numeric.removeAttribute('aria-invalid');}));
  scenario.addEventListener('change',show);
  host.append(scenarioLabel,scenario,prompt,answerLabel,numeric,choice,check,reveal,next,reset,feedback,progress);show();
 });
})();
