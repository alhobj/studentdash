/* Portable, self-reported practice evidence. No network or assessment writes. */
(function practiceRuntime() {
  'use strict';
  window.StudentPracticeRuntime = practiceRuntime;
  const catalog = window.PRACTICE_CATALOG;
  if (!catalog) return;
  const KEY = 'studentdash.practice.v1', index = new Map(catalog.questions.map(q => [q.id, q]));
  let state = {schema:1, attempts:[], drafts:{}, positions:{}, sessions:{}}, storageOK = true, assignment = null, queue = [];
  const el = (tag, text, parent) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if(parent) parent.append(n); return n; };
  const normalize = s => String(s).trim().toLowerCase().replace(/−/g,'-').replace(/\s+/g,' ').replace(/[.!?]+$/,'');
  const uid = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const validKey = s => typeof s === 'string' && /^[\w.:-]{1,220}$/.test(s) && !['__proto__','constructor','prototype'].includes(s);
  function validate(raw) {
    if (!raw || raw.schema !== 1 || !Array.isArray(raw.attempts) || raw.attempts.length > 20000) throw Error('Unsupported or oversized progress file.');
    const ids = new Set();
    const attempts = raw.attempts.map(a => {
      if (!a || !validKey(a.id) || !validKey(a.question) || ids.has(a.id) || typeof a.correct !== 'boolean' || typeof a.assisted !== 'boolean' || typeof a.answer !== 'string' || a.answer.length > 500 || typeof a.at !== 'string' || !Number.isFinite(Date.parse(a.at))) throw Error('Invalid practice record.');
      ids.add(a.id); return {id:a.id,question:a.question,correct:a.correct,assisted:a.assisted,answer:a.answer,at:new Date(a.at).toISOString()};
    });
    const drafts = {}, positions = {};
    for (const [key,value] of Object.entries(raw.drafts || {})) {
      if (!validKey(key) || !value || typeof value.answer !== 'string' || value.answer.length > 500 || typeof value.assisted !== 'boolean') throw Error('Invalid saved answer.');
      drafts[key] = {answer:value.answer, assisted:value.assisted};
    }
    for (const [key,value] of Object.entries(raw.positions || {})) {
      if (!validKey(key) || !Number.isInteger(value) || value < 0 || value > 10000) throw Error('Invalid saved position.');
      positions[key] = value;
    }
    const sessions = {};
    for (const [key,ids] of Object.entries(raw.sessions || {})) {
      if(!validKey(key) || !Array.isArray(ids) || ids.length>1000 || ids.some(id=>!validKey(id))) throw Error('Invalid saved session.');
      sessions[key]=ids;
    }
    return {schema:1,attempts,drafts,positions,sessions};
  }
  try { const saved = localStorage.getItem(KEY); if(saved) state = validate(JSON.parse(saved)); } catch (_) { storageOK = false; }
  function save() {
    try { localStorage.setItem(KEY,JSON.stringify(state)); } catch (_) { storageOK = false; }
    document.querySelectorAll('[data-storage-message]').forEach(n => n.textContent = storageOK
      ? 'Saved on this browser. Export progress before moving files or changing computer. On a shared computer, export then clear your progress.'
      : 'Browser saving is unavailable. Export progress before closing this page.');
  }
  function download(name, data, type='application/json') {
    const url = URL.createObjectURL(new Blob([typeof data === 'string' ? data : JSON.stringify(data,null,2)],{type}));
    const a = el('a'); a.href=url; a.download=name; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  function latest(id) { return state.attempts.filter(a => a.question === id).sort((a,b) => b.at.localeCompare(a.at) || b.id.localeCompare(a.id))[0]; }
  function status(id) { const a=latest(id); return !a ? 'Not attempted' : !a.correct ? 'Needs another attempt' : a.assisted ? 'Completed with help or retry' : 'Correct independently'; }
  function record(q,answer,correct,assisted) {
    if(state.attempts.length >= 20000) throw Error('Progress is full. Export it, then clear this browser to start a new record.');
    state.attempts.push({id:uid(),question:q.id,answer:String(answer).slice(0,500),correct,assisted,at:new Date().toISOString()}); save();
  }
  function check(q,raw) {
    if(!raw.trim()) return {valid:false,correct:false,message:'Enter an answer first.'};
    if(Array.isArray(q.answer)) { const correct=q.answer.some(a=>normalize(a)===normalize(raw)); return {valid:true,correct,message:correct?'That’s right.':'Check the term used in the reminder or hint.'}; }
    const match=raw.trim().replace(/−/g,'-').match(/^([+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:e[+-]?\d+)?)\s*(.*)$/i);
    if(!match || !Number.isFinite(Number(match[1].replace(',','.')))) return {valid:false,correct:false,message:'Enter a number, using e for powers of ten, followed by the requested unit if shown.'};
    const value=Number(match[1].replace(',','.')), unit=normalize(match[2]);
    if(unit && !(q.units || []).some(u => normalize(u)===unit)) return {valid:true,correct:false,message:q.units?.length ? `Use the requested unit: ${q.units[0]}. Convert the value as well if needed.` : 'Enter only the numerical answer in the units requested in the question.'};
    const error=Math.abs(value-q.answer), tolerance=q.tolerance ?? 1e-8;
    if(error<=tolerance) return {valid:true,correct:true,message:'That’s right. Explain the method before moving on.'};
    const mistake=q.mistakes?.find(m=>Math.abs(m.value-value)<1e-8);
    const message=mistake?.feedback || (q.answer !== 0 && Math.abs(value+q.answer)<1e-8 ? 'The magnitude matches, but check the sign and the order of subtraction.'
      : Math.abs(q.answer)>0 && error/Math.abs(q.answer)<.01 ? 'You are close. Keep more digits during the calculation and check the requested rounding.'
      : q.answer !== 0 && [100,1000,.01,.001].some(k=>Math.abs(value/q.answer-k)<1e-8) ? 'Check the scale: a percentage or unit conversion may be missing. Follow the units in the prompt.'
      : 'Check your substitution and operation order, then try the hint.');
    return {valid:true,correct:false,message};
  }
  const helped = new WeakMap();
  function hostFor(form) { return form.closest('[data-similar]') || form; }
  function questionFor(form) { const anchor=form.closest('[data-foundation]')?.id; return catalog.questions.find(q=>q.prompt===form.querySelector('label')?.textContent && (!anchor || q.path.endsWith('#'+anchor))); }
  function restoreForm(form) {
    const q=questionFor(form), input=form.querySelector('input'), d=q && state.drafts[q.id];
    if(input && d) {input.value=d.answer; if(d.assisted) helped.set(hostFor(form),q.id);}
  }
  window.StudentPractice = {
    check, status,
    choiceDraft(id) {return index.has(id) ? state.drafts[id] : null;},
    saveChoiceHelp(id) {if(index.has(id)){state.drafts[id]={answer:state.drafts[id]?.answer || '',assisted:true};save();}},
    clearChoice(id) {delete state.drafts[id];save();},
    recordChoice(id,answer,correct,assisted) {
      const q=index.get(id);if(!q)return;
      try {record(q,answer,correct,assisted);}catch(error){alert(error.message);return;}
      state.drafts[id]={answer,assisted:true};save();
    },
    feedbackFor(form) {const q=questionFor(form);return q ? check(q,form.querySelector('input').value).message : null;},
    clearLesson(lesson) {lesson.querySelectorAll('form').forEach(form=>{const q=questionFor(form);if(q)delete state.drafts[q.id];helped.delete(hostFor(form));});save();},
    position(key) {return state.positions[catalog.profile+':'+key] || 0;},
    move(key,value) {state.positions[catalog.profile+':'+key]=value;save();},
    restore:restoreForm,
    recordForm(form,correct) {
      const q=questionFor(form); if(!q) return;
      const host=hostFor(form), assisted=helped.get(host)===q.id || [...host.querySelectorAll('details')].some(d=>d.open);
      try {record(q,form.querySelector('input').value,correct,assisted);} catch(error) {alert(error.message);}
      if(!correct) helped.set(host,q.id);
      state.drafts[q.id]={answer:form.querySelector('input').value,assisted:assisted || !correct};save();
    }
  };
  function button(parent,text,fn) { const b=el('button',text,parent);b.type='button';b.addEventListener('click',fn);return b; }
  function inputFile(parent,label,handler) {
    const l=el('label',label,parent), f=el('input',undefined,l);f.type='file';f.accept='.json,application/json';f.className='learning-file';
    f.addEventListener('change',async()=>{try {const file=f.files[0]; if(!file)return;if(file.size>5*1024*1024)throw Error('File is too large (maximum 5 MB).');handler(JSON.parse(await file.text()));}catch(e){message.textContent=e.message;}finally{f.value='';}});
  }
  let message;
  function renderWorkspace() {
    const root=document.querySelector('#learning-workspace'); if(!root)return;
    root.replaceChildren(); el('h1','My practice · '+catalog.label,root);
    if(catalog.hub){const back=el('a','Practice hub',root);back.href=catalog.hub;}
    el('p','Save your place, revisit mistakes and build independence. These are self-reported practice records, not assessment marks. This journal covers small-step, repeat and authored multiple-choice questions; explorers and longer written tasks remain available in the hub.',root);
    const storage=el('p','',root);storage.dataset.storageMessage='';
    message=el('p','',root);message.setAttribute('role','status');message.className='learning-status';
    const actions=el('div',undefined,root);actions.className='learning-actions';
    button(actions,'Export my progress',()=>download('my-practice-progress.json',state));
    button(actions,'Clear this browser',()=>{if(confirm('Export first if you want to keep your progress. Clear this browser’s practice records for all subjects?')){state={schema:1,attempts:[],drafts:{},positions:{},sessions:{}};save();renderWorkspace();}});
    inputFile(root,'Import my progress',raw=>{
      const incoming=validate(raw), combined=new Map(state.attempts.map(a=>[a.id,a]));
      incoming.attempts.forEach(a=>{if(combined.has(a.id) && ['question','answer','correct','assisted','at'].some(key=>combined.get(a.id)[key]!==a[key]))throw Error('Conflicting attempt IDs; no records imported.');combined.set(a.id,a);});
      if(combined.size>20000)throw Error('Combined progress is too large.');
      state={schema:1,attempts:[...combined.values()],drafts:{...state.drafts,...incoming.drafts},positions:{...state.positions,...incoming.positions},sessions:{...state.sessions,...incoming.sessions}};save();renderWorkspace();message.textContent='Progress merged. Imported saved answers replace matching drafts; previous attempts are retained.';
    });
    const counts={};catalog.questions.forEach(q=>counts[status(q.id)]=(counts[status(q.id)]||0)+1);
    el('p',Object.entries(counts).map(([k,v])=>`${k}: ${v}`).join(' · '),root);
    const sessions=el('div',undefined,root);sessions.className='learning-actions';
    const focusTopic=new URLSearchParams(location.hash.slice(1)).get('topic');
    if(focusTopic && catalog.questions.some(q=>q.topic===focusTopic)) button(sessions,'Practise recommended topic',()=>start(catalog.questions.filter(q=>q.topic===focusTopic).sort((a,b)=>Number(status(a.id)==='Correct independently')-Number(status(b.id)==='Correct independently')).slice(0,6)));
    button(sessions,'Resume saved session',()=>start((state.sessions[catalog.profile] || []).map(id=>index.get(id)).filter(Boolean)));
    button(sessions,'Practise my mistakes',()=>start(catalog.questions.filter(q=>latest(q.id) && status(q.id)!=='Correct independently').slice(0,6)));
    button(sessions,'Start mixed revision (up to 6)',()=>{
      const chosen=[], used=new Set();
      const add=q=>{if(q && !used.has(q.id) && chosen.length<6){chosen.push(q);used.add(q.id);}};
      catalog.questions.filter(q=>latest(q.id)&&status(q.id)!=='Correct independently').slice(0,2).forEach(add);
      const recent=state.attempts.filter(a=>index.has(a.question)).sort((a,b)=>b.at.localeCompare(a.at));
      const recentTopic=recent[0]&&index.get(recent[0].question).topic;
      catalog.questions.filter(q=>q.topic===recentTopic && !latest(q.id)).slice(0,2).forEach(add);
      const topics=new Set(chosen.map(q=>q.topic));
      [...catalog.questions].sort((a,b)=>(latest(a.id)?.at || '').localeCompare(latest(b.id)?.at || '')).forEach(q=>{if(!topics.has(q.topic)){add(q);topics.add(q.topic);}});
      catalog.questions.forEach(add);start(chosen);
    });
    const session=el('section',undefined,root);session.id='learning-session';session.className='learning-card';session.setAttribute('aria-live','polite');el('p','Choose a session or a question below.',session);
    const assignmentBox=el('section',undefined,root);assignmentBox.className='learning-card';el('h2','Assignments',assignmentBox);
    inputFile(assignmentBox,'Open an assignment file',raw=>{assignment=validateAssignment(raw);renderAssignment();});
    inputFile(assignmentBox,'Review a student completion report',raw=>{
      if(!raw || raw.schema!==1 || raw.type!=='studentdash-completion' || typeof raw.title!=='string' || !Array.isArray(raw.questions) || raw.questions.length>1000) throw Error('Invalid completion report.');
      const rows=raw.questions.map(row=>{
        if(!row || !index.has(row.id) || !Array.isArray(row.attempts)) throw Error('The report contains unknown questions. Open its original subject/version.');
        const attempts=validate({schema:1,attempts:row.attempts}).attempts;
        if(attempts.some(a=>a.question!==row.id))throw Error('Report question and attempts do not match.');
        const last=attempts.sort((a,b)=>b.at.localeCompare(a.at))[0];
        return {q:index.get(row.id),last,count:attempts.length};
      });
      const host=document.querySelector('#report-review');host.replaceChildren();el('h3',raw.title,host);
      el('p','Self-reported practice only. This report is not authenticated and does not change marks or local progress.',host);
      rows.forEach(({q,last,count})=>el('p',`${q.prompt} — ${count} attempt(s); ${!last?'not attempted':!last.correct?'needs another attempt':last.assisted?'completed with help or retry':'correct independently'}${last?' · Last answer: '+last.answer:''}`,host));
    });
    const review=el('div',undefined,assignmentBox);review.id='report-review';
    const assigned=el('div',undefined,assignmentBox);assigned.id='assigned';
    const details=el('details',undefined,root);el('summary','Choose questions or create a teacher assignment',details);
    const searchLabel=el('label','Filter by topic or question',details), search=el('input',undefined,searchLabel);search.type='search';
    const titleLabel=el('label','Assignment title',details), title=el('input',undefined,titleLabel);title.value='Practice assignment';title.maxLength=160;
    const noteLabel=el('label','Instructions',details), note=el('textarea',undefined,noteLabel);note.maxLength=4000;
    const list=el('div',undefined,details);list.className='learning-list';
    catalog.questions.forEach(q=>{
      const row=el('div',undefined,list), l=el('label',undefined,row), box=el('input',undefined,l);box.type='checkbox';box.value=q.id;
      l.append(document.createTextNode(` ${q.topic} · ${q.prompt} — ${status(q.id)}`));
      button(row,'Practise this question',()=>start([q]));
      row.dataset.search=(q.topic+' '+q.title+' '+q.prompt).toLowerCase();
    });
    search.addEventListener('input',()=>{for(const row of list.children)row.hidden=!row.dataset.search.includes(search.value.toLowerCase());});
    function makeAssignment(){const ids=[...list.querySelectorAll('input:checked')].map(n=>n.value);if(!ids.length)throw Error('Select at least one question.');return {schema:1,type:'studentdash-assignment',id:uid(),profile:catalog.profile,title:title.value.trim()||'Practice assignment',instructions:note.value,questions:ids};}
    button(details,'Export assignment file',()=>{try{download('practice-assignment.json',makeAssignment());}catch(e){message.textContent=e.message;}});
    button(details,'Export standalone assignment page',()=>{try{
      const a=makeAssignment(), data={...catalog,hub:null,questions:a.questions.map(id=>index.get(id))};
      const script='('+window.StudentPracticeRuntime.toString()+')();';
      const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Practice assignment</title><style>body{font:18px system-ui;max-width:900px;margin:auto;padding:1rem}button,input,textarea{font:inherit;max-width:100%}label{display:block;margin:.7rem 0}.learning-list{max-height:20rem;overflow:auto}</style></head><body><main id="learning-workspace"></main><script>window.PRACTICE_CATALOG='+JSON.stringify(data).replace(/</g,'\\u003c')+';window.PRACTICE_ASSIGNMENT='+JSON.stringify(a).replace(/</g,'\\u003c')+';'+script.replace(/<\/script/gi,'<\\/script')+'<\/script></body></html>';
      download('practice-assignment.html',html,'text/html');
    }catch(e){message.textContent=e.message;}});
    if(window.PRACTICE_ASSIGNMENT && !assignment) assignment=validateAssignment(window.PRACTICE_ASSIGNMENT);
    if(assignment)renderAssignment();save();
  }
  function validateAssignment(a){if(!a || a.schema!==1 || a.type!=='studentdash-assignment' || !validKey(a.id) || a.profile!==catalog.profile || typeof a.title!=='string' || a.title.length>160 || typeof a.instructions!=='string' || a.instructions.length>4000 || !Array.isArray(a.questions) || !a.questions.length || a.questions.length>1000 || new Set(a.questions).size!==a.questions.length || a.questions.some(id=>!index.has(id)))throw Error('This assignment is invalid or belongs to a different practice collection/version.');return a;}
  function renderAssignment(){const host=document.querySelector('#assigned');host.replaceChildren();el('h3',assignment.title,host);el('p',assignment.instructions,host);el('p',`${assignment.questions.length} questions. Completion reports are self-reported and may be edited; they do not change assessment marks.`,host);button(host,'Start assignment',()=>start(assignment.questions.map(id=>index.get(id))));button(host,'Export completion report',()=>download('practice-completion.json',{schema:1,type:'studentdash-completion',assignment:assignment.id,title:assignment.title,exported:new Date().toISOString(),selfReported:true,questions:assignment.questions.map(id=>({id,prompt:index.get(id).prompt,status:status(id),attempts:state.attempts.filter(a=>a.question===id)}))}));}
  function start(questions){queue=[...questions];showQuestion();}
  function showQuestion(){state.sessions[catalog.profile]=queue.map(q=>q.id);save();const host=document.querySelector('#learning-session');host.replaceChildren();if(!queue.length){el('p','No questions waiting. Choose another session or review your progress.',host);return;}
    const q=queue[0];host.className='learning-card learning-question';el('h2',q.topic+' · '+q.title,host);el('p',`${queue.length} question(s) left in this session`,host);
    const form=el('form',undefined,host), label=el('label',q.prompt,form), input=el('input',undefined,label);input.type='text';input.maxLength=500;input.autocomplete='off';
    const draft=state.drafts[q.id];input.value=draft?.answer || '';let assisted=Boolean(draft?.assisted);
    const submit=el('button','Check answer',form);submit.type='submit';const feedback=el('p','',form);feedback.setAttribute('role','status');
    if(q.options){
      input.hidden=true;submit.hidden=true;
      const choices=el('div',undefined,form);choices.className='learning-actions';choices.setAttribute('role','group');choices.setAttribute('aria-label','Answer choices');
      q.options.forEach((option,i)=>{const letter='ABCD'[i],b=button(choices,letter+'. '+option,()=>{
        input.value=letter;choices.querySelectorAll('button').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));form.requestSubmit();
      });b.setAttribute('aria-pressed',String(input.value===letter));});
    }
    const current=el('p','Recorded: '+status(q.id),host);
    for(const [title,text] of [['Hint',q.hint],['Worked answer',q.working]]){const d=el('details',undefined,host);el('summary',title,d);el('p',text,d);d.addEventListener('toggle',()=>{if(d.open){assisted=true;persist();}});}
    function persist(){state.drafts[q.id]={answer:input.value,assisted};save();}
    input.addEventListener('input',persist);
    form.addEventListener('submit',e=>{e.preventDefault();assisted ||= [...host.querySelectorAll('details')].some(d=>d.open);const result=check(q,input.value);feedback.textContent=q.options ? (result.correct?'Correct. '+q.working:'Not correct. Try another option or open the worked answer.') : result.message;input.setAttribute('aria-invalid',String(!result.correct));if(!result.valid)return;try{record(q,input.value,result.correct,assisted);}catch(error){feedback.textContent=error.message;return;}if(!result.correct || q.options)assisted=true;persist();current.textContent='Recorded: '+status(q.id);});
    button(host,'Retry independently with a blank answer',()=>{delete state.drafts[q.id];save();showQuestion();});
    button(host,'Next question',()=>{queue.shift();showQuestion();});
    button(host,'Try another using the same method',()=>{const next=catalog.questions.find(n=>n.id!==q.id&&n.topic===q.topic&&n.kind===q.kind&&!latest(n.id));if(next){queue.unshift(next);showQuestion();}else feedback.textContent='No unattempted question of this type remains. Use mixed revision or retry later.';});
    button(host,'Finish session and refresh progress',()=>{queue=[];state.sessions[catalog.profile]=[];save();renderWorkspace();});
    host.scrollIntoView({block:'start'});
  }
  function init(){
    if(document.querySelector('#learning-workspace')){renderWorkspace();return;}
    const bar=el('aside');bar.className='learning-bar';bar.setAttribute('aria-label','Saved practice');const link=el('a','My practice: resume, mistakes & assignments',bar);link.href='my-practice.html';document.body.prepend(bar);
    const p=el('span','',bar);p.dataset.storageMessage='';save();
    document.querySelectorAll('.foundation-step,.similar-form').forEach(form=>{
      restoreForm(form);const host=hostFor(form);
      host.addEventListener('toggle',event=>{if(event.target.open){const q=questionFor(form);if(q){helped.set(host,q.id);state.drafts[q.id]={answer:form.querySelector('input').value,assisted:true};save();}}},true);
      form.querySelector('input').addEventListener('input',()=>{const q=questionFor(form);if(q){state.drafts[q.id]={answer:form.querySelector('input').value,assisted:helped.get(host)===q.id};save();}});
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
