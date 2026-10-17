/* Five-round, ungraded practice. Session state is intentionally separate from saved progression. */
window.createPracticeCircuit=function({makeSet,open,parent}){
 let session=null;
 const add=(tag,text,into=parent)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;into.append(n);return n;};
 const button=(text,fn,into=parent)=>{const b=add('button',text,into);b.onclick=fn;return b;};
 function start(){if(!session)session={questions:makeSet(),stage:0,unaided:0,values:[],supported:false,passed:false};render();}
 function render(){open();add('h2','Field practice circuit');add('p','Five short rounds. No timer, cost, quest rewards or assessment marks. You can close and resume during this page session; reloading starts a new circuit.');
  if(session.stage===session.questions.length){add('h3',`${session.questions.length} rounds reviewed · ${session.unaided} solved without hints or incorrect checks`);add('p','This is practice, not a mastery certificate. Use the explanations to decide what to revisit.');
   for(const q of session.questions){const section=add('section','');section.className='notebook-entry';add('h3',q.title,section);add('p',q.explanation,section);}
   button('Try a new circuit',()=>{session=null;start();});return;
  }
  const q=session.questions[session.stage];add('small',`ROUND ${session.stage+1} / ${session.questions.length} · ${q.topic}`);add('h3',q.title);add('p',q.prompt);
  const label=add('label',q.label),input=add('input',undefined,label);input.type='number';input.step='any';input.value=session.values[0]??'';input.setAttribute('aria-label',q.label);input.className='circuit-answer';input.disabled=session.passed;
  input.oninput=()=>{session.values=[input.value];};
  const feedback=add('p',session.passed?'Correct. '+q.explanation:'');feedback.setAttribute('role','status');feedback.className='feedback';
  const hint=button('Free hint',()=>{session.supported=true;feedback.textContent=q.hint;});hint.disabled=session.passed;
  const check=button('Check answer',()=>{
   if(session.passed)return;session.values=[input.value];const n=Number(input.value);
   if(input.value.trim()===''||!Number.isFinite(n)){feedback.textContent='Enter a number first.';return;}
   if(Math.abs(n-q.answer)>(q.tolerance??0.000001)){session.supported=true;feedback.textContent='Not yet. '+q.hint;return;}
   if(!session.supported)session.unaided++;session.passed=true;render();
  });check.disabled=session.passed;
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();check.click();}});
  if(session.passed)button(session.stage+1===session.questions.length?'Review circuit':'Next round',()=>{session.stage++;session.values=[];session.supported=false;session.passed=false;render();});
 }
 return {start};
};
