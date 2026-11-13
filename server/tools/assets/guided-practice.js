/* Data-defined stages; choices are checked as strings, never evaluated as code. */
(function guidedRuntime(){'use strict';
window.StudentGuidedRuntime=guidedRuntime;
const root=document.querySelector('#guided-practice'),api=window.StudentPractice,catalog=window.PRACTICE_CATALOG;if(!root||!api)return;
const questions=catalog.questions.filter(q=>q.kind==='guided');
const el=(tag,text,parent)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;parent?.append(e);return e;};
const button=(p,text,fn)=>{const b=el('button',text,p);b.type='button';b.onclick=fn;return b;};
for(const [qi,q]of questions.entries()){
 const host=document.getElementById(q.id)||el('section','',root);host.className='learning-card';host.id=q.id;el('h2',q.topic+' · '+q.title,host);el('p',q.prompt,host);
 const skills=el('p','Skills: ',host);(q.skills||[]).forEach(id=>{const a=el(window.PRACTICE_ASSIGNMENT?'span':'a',catalog.skill_labels[id]||id,skills);if(!window.PRACTICE_ASSIGNMENT)a.href='skills.html#'+encodeURIComponent(id);skills.append(' ');});
 let values=['','','',''],passed=[false,false,false,false],assisted=false;
 const draft=api.choiceDraft(q.id);try{const saved=JSON.parse(draft?.answer||'null');if(Array.isArray(saved?.v)&&saved.v.length===4&&saved.v.every(x=>typeof x==='string'&&x.length<=70)&&Array.isArray(saved.p)&&saved.p.length===4){values=saved.v;assisted=Boolean(draft.assisted);for(let i=0;i<4;i++)passed[i]=saved.p[i]===true&&(i===0||passed[i-1])&&correct(q.steps[i],values[i]);}}catch{}
 const area=el('div','',host),summary=el('p','',host);summary.setAttribute('role','status');
 function correct(step,answer){if(step.options)return answer===step.answer;return api.check({...step,units:[]},answer).correct;}
 function persist(){api.saveDraft(q.id,JSON.stringify({v:values,p:passed}),assisted);}
 function draw(){area.replaceChildren();summary.textContent='Latest completed/check attempt: '+api.status(q.id);q.steps.forEach((step,i)=>{
  const field=el('fieldset','',area);field.disabled=i>0&&!passed[i-1];el('legend',`${i+1}. ${step.label}`,field);const label=el('label',step.options?'Select an expression':'Your answer',field);const input=el(step.options?'select':'input','',label);
  if(step.options){el('option','Choose…',input).value='';const options=[...step.options],rotate=(qi+i+1)%options.length;options.push(...options.splice(0,rotate));options.forEach(x=>el('option',x,input).value=x);}else{input.type='text';input.maxLength=70;}
  input.value=values[i];input.setAttribute('aria-label',step.label);
  const feedback=el('p',passed[i]?'Step correct.':'',field);feedback.setAttribute('role','status');
  if(step.options)input.onchange=()=>{values[i]=input.value;for(let j=i;j<4;j++){passed[j]=false;if(j>i)values[j]='';}persist();draw();};
  if(!step.options)input.oninput=()=>{values[i]=input.value;for(let j=i;j<4;j++){passed[j]=false;if(j>i)values[j]='';}area.querySelectorAll('fieldset').forEach((f,j)=>{if(j>i)f.disabled=true;});feedback.textContent='';persist();};
  button(field,'Check step '+(i+1),()=>{values[i]=input.value;if(!values[i].trim()){feedback.textContent='Enter an answer first.';return;}const ok=correct(step,values[i]);if(!ok){assisted=true;api.recordChoice(q.id,values[i],false,true);persist();feedback.textContent='Not yet. '+step.hint;summary.textContent='Recorded: '+api.status(q.id);return;}passed[i]=true;if(i===3){api.recordChoice(q.id,values.join(' → '),true,assisted);assisted=true;}persist();draw();area.querySelectorAll('fieldset')[Math.min(i+1,3)].querySelector('input,select')?.focus();});
  button(field,'Hint for step '+(i+1),()=>{assisted=true;persist();feedback.textContent=step.hint;});
 });if(passed.every(Boolean))summary.textContent='All four steps correct. Recorded: '+api.status(q.id);}
 button(host,'Start a fresh independent attempt',()=>{values=['','','',''];passed=[false,false,false,false];assisted=false;api.clearChoice(q.id);draw();});draw();
}
try{if(location.hash)document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();}catch{}
})();
