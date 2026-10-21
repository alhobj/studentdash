/* Offline editorial drafts. No server writes or changes to student records. */
(() => {
  'use strict';
  const catalog=window.PRACTICE_CATALOG, root=document.querySelector('#mcq-review');
  if(!root||!catalog)return;
  const questions=catalog.questions.filter(q=>q.options), index=new Map(questions.map(q=>[q.id,q]));
  const key='studentdash.mcq-review.v1:'+catalog.profile;
  let changes={},selected=null;
  const el=(tag,text,parent=root)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;parent.append(n);return n;};
  const message=el('p','');message.setAttribute('role','status');
  const flags=['unreviewed','reviewed','needs correction','too repetitive'];
  function validate(raw){
    if(raw?.schema!==1||raw.profile!==catalog.profile||!raw.changes||typeof raw.changes!=='object'||Array.isArray(raw.changes))throw Error('Wrong profile or unsupported review file.');
    for(const [id,p] of Object.entries(raw.changes)){
      if(!index.has(id)||!p||Object.keys(p).sort().join()!==['prompt','options','answer','working','feedback','flag','notes'].sort().join())throw Error('Unknown question or invalid fields.');
      for(const name of ['prompt','working','notes','flag'])if(typeof p[name]!=='string'||p[name].length>10000)throw Error('Invalid review text.');
      if(!p.prompt.trim()||!p.working.trim()||!flags.includes(p.flag))throw Error('Prompt, explanation and review status are required.');
      if(!Array.isArray(p.options)||p.options.length!==4||p.options.some(x=>typeof x!=='string'||!x.trim()||x.length>10000)||new Set(p.options).size!==4)throw Error('Supply four distinct, nonempty options.');
      if(typeof p.answer!=='string'||!['A','B','C','D'].includes(p.answer)||!p.feedback||Object.keys(p.feedback).sort().join()!=='A,B,C,D'||Object.values(p.feedback).some(x=>typeof x!=='string'||!x.trim()||x.length>10000))throw Error('Supply an answer letter and feedback for every choice.');
    }
    return raw.changes;
  }
  try{const saved=localStorage.getItem(key);if(saved)changes=validate(JSON.parse(saved));}catch(e){message.textContent='Saved review could not be loaded: '+e.message;}
  function persist(){try{localStorage.setItem(key,JSON.stringify({schema:1,profile:catalog.profile,changes}));message.textContent='Draft saved in this browser. Export to keep a portable copy; student pages are unchanged.';}catch(e){message.textContent='Browser storage unavailable. Export the review file before leaving.';}}
  function button(label,fn,parent=root){const b=el('button',label,parent);b.type='button';b.addEventListener('click',fn);return b;}
  button('Export review file',()=>{const blob=new Blob([JSON.stringify({schema:1,profile:catalog.profile,changes},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='mcq-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
  const uploadLabel=el('label','Import review file ');const upload=el('input',undefined,uploadLabel);upload.type='file';upload.accept='.json,application/json';
  upload.addEventListener('change',async()=>{try{const f=upload.files[0];if(!f)return;if(f.size>10000000)throw Error('Review file is too large.');const imported=validate(JSON.parse(await f.text()));changes={...changes,...imported};persist();filter();if(selected)edit(selected);}catch(e){message.textContent='Import rejected: '+e.message;}upload.value='';});
  const searchLabel=el('label','Search questions ');const search=el('input',undefined,searchLabel);search.type='search';
  const topicLabel=el('label','Section ');const topics=el('select',undefined,topicLabel);el('option','All sections',topics).value='';
  [...new Set(questions.map(q=>q.topic))].forEach(t=>el('option',t,topics).value=t);topics.setAttribute('aria-label','Section');
  const flagLabel=el('label','Review status ');const statuses=el('select',undefined,flagLabel);el('option','All statuses',statuses).value='';flags.forEach(f=>el('option',f,statuses).value=f);statuses.setAttribute('aria-label','Filter by review status');
  const summary=el('p','');const layout=el('div');const list=el('div',undefined,layout);const editor=el('section',undefined,layout);editor.setAttribute('aria-label','Question editor');
  function draft(q){return changes[q.id]||{prompt:q.prompt,options:[...q.options],answer:q.answer[0],working:q.working,feedback:{...q.feedback},flag:q.flag||'unreviewed',notes:q.notes||''};}
  function filter(){list.replaceChildren();const matches=questions.filter(q=>{const p=draft(q);return (!topics.value||q.topic===topics.value)&&(!statuses.value||p.flag===statuses.value)&&(p.prompt+' '+q.id+' '+p.notes).toLowerCase().includes(search.value.toLowerCase());});summary.textContent=`${matches.length} matching questions; ${Object.keys(changes).length} saved drafts. Showing the first 60 matches; narrow your search to find more.`;for(const q of matches.slice(0,60))button(q.topic+' · '+draft(q).prompt.slice(0,100),()=>edit(q.id),list);}
  function edit(id){selected=id;const q=index.get(id),p=draft(q);editor.replaceChildren();el('h2',q.topic+' · '+q.source_id,editor);if(q.skills?.length)el('p','Skills: '+q.skills.map(id=>catalog.skill_labels?.[id]||id).join(' · '),editor);el('p','Unsaved form edits are discarded when you select another question. Save draft before switching.',editor);
    const form=el('form',undefined,editor),fields={};
    function field(name,label,value){const l=el('label',label,form),input=el('textarea',undefined,l);input.value=value;input.maxLength=10000;input.rows=3;fields[name]=input;return input;}
    field('prompt','Question wording',p.prompt);
    p.options.forEach((o,i)=>{field('option'+i,'Option '+'ABCD'[i],o);field('feedback'+i,'Feedback for choice '+'ABCD'[i],p.feedback['ABCD'[i]]);});
    const answerLabel=el('label','Correct answer ',form),answer=el('select',undefined,answerLabel);[...'ABCD'].forEach(l=>el('option',l,answer).value=l);answer.value=p.answer;answer.setAttribute('aria-label','Correct answer');
    field('working','Worked explanation',p.working);
    const flagL=el('label','Review status ',form),flag=el('select',undefined,flagL);flags.forEach(f=>el('option',f,flag).value=f);flag.value=p.flag;flag.setAttribute('aria-label','Review status');
    field('notes','Teacher notes (not shown in student questions)',p.notes);
    const preview=el('section',undefined,editor);preview.setAttribute('aria-label','Question preview');
    function read(){return {prompt:fields.prompt.value.trim(),options:[0,1,2,3].map(i=>fields['option'+i].value.trim()),answer:answer.value,working:fields.working.value.trim(),feedback:Object.fromEntries([...'ABCD'].map((l,i)=>[l,fields['feedback'+i].value.trim()])),flag:flag.value,notes:fields.notes.value};}
    button('Preview question',()=>{const p=read();preview.replaceChildren();el('h3','Student preview',preview);el('p',p.prompt,preview);const feedback=el('p','',preview);feedback.setAttribute('role','status');p.options.forEach((o,i)=>button('ABCD'[i]+'. '+o,()=>{feedback.textContent=('ABCD'[i]===p.answer?'Correct. ':'Not correct. ')+p.feedback['ABCD'[i]];},preview));},form);
    const save=el('button','Save draft',form);save.type='submit';form.addEventListener('submit',e=>{e.preventDefault();try{const patch=read();validate({schema:1,profile:catalog.profile,changes:{[id]:patch}});changes[id]=patch;persist();filter();}catch(e){message.textContent=e.message;}});
    button('Discard saved draft',()=>{if(confirm('Discard this saved draft and return to the published question?')){delete changes[id];persist();filter();edit(id);}},form);
  }
  search.addEventListener('input',filter);topics.addEventListener('change',filter);statuses.addEventListener('change',filter);filter();
})();
