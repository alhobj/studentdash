/* Shared offline backup and class snapshot tools. Imported files never become assessment marks. */
(()=>{'use strict';
const catalog=window.PRACTICE_CATALOG,api=window.StudentPractice,manifest=window.STUDENT_RECORD_PROFILES;
if(!catalog||!api||!manifest)return;
const KEY='studentdash.practice.v1',prefix='studentdash.skills.v1:';
const el=(tag,text,parent)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;parent?.append(n);return n;};
const button=(p,text,fn)=>{const b=el('button',text,p);b.type='button';b.onclick=fn;return b;};
const download=(name,data)=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function notes(raw,profile){
 if(!raw||raw.schema!==1||raw.profile!==profile||!raw.notes||typeof raw.notes!=='object'||Array.isArray(raw.notes))throw Error('Invalid skills notes.');
 const allowed=new Set(manifest[profile]),clean={};
 for(const [id,n]of Object.entries(raw.notes)){if(!allowed.has(id)||!n||typeof n.answer!=='string'||n.answer.length>12000||typeof n.reviewed!=='boolean')throw Error('Unrecognized or invalid skills note.');clean[id]={answer:n.answer,reviewed:n.reviewed};}
 return {schema:1,profile,notes:clean};
}
function validate(raw){
 if(raw?.type!=='studentdash-student-backup'||raw.schema!==1||typeof raw.name!=='string'||raw.name.length>100||!raw.skills||typeof raw.skills!=='object'||Array.isArray(raw.skills))throw Error('Choose a combined student backup.');
 const skills={};for(const [profile,value]of Object.entries(raw.skills)){if(!Object.hasOwn(manifest,profile))throw Error('Backup contains an unsupported subject.');skills[profile]=notes(value,profile);}
 const learning={};for(const [profile,value]of Object.entries(raw.learning||{})){if(!Object.hasOwn(manifest,profile))throw Error('Backup contains an unsupported learning collection.');learning[profile]=StudentLearningState.validate(value);}return {schema:1,type:raw.type,name:raw.name,progress:api.validate(raw.progress),skills,learning};
}
function merge(a,b){
 const attempts=new Map(a.attempts.map(x=>[x.id,x]));for(const x of b.attempts){const old=attempts.get(x.id);if(old&&['question','answer','correct','assisted','at'].some(k=>old[k]!==x[k]))throw Error('Conflicting attempt IDs. Nothing imported.');attempts.set(x.id,x);}
 const assignments={...a.assignments};for(const [profile,items]of Object.entries(b.assignments||{})){const rows=new Map((assignments[profile]||[]).map(x=>[x.id,x]));items.forEach(x=>rows.set(x.id,x));assignments[profile]=[...rows.values()];}
 return api.validate({schema:1,attempts:[...attempts.values()],drafts:{...a.drafts,...b.drafts},positions:{...a.positions,...b.positions},sessions:{...a.sessions,...b.sessions},assignments});
}
function snapshot(name){const skills={};for(const profile of Object.keys(manifest)){const raw=localStorage.getItem(prefix+profile);if(raw)skills[profile]=notes(JSON.parse(raw),profile);}const learning={};for(const profile of Object.keys(manifest)){if(localStorage.getItem(StudentLearningState.prefix+profile))learning[profile]=StudentLearningState.read(profile);}return {schema:1,type:'studentdash-student-backup',learning,exported:new Date().toISOString(),name,progress:api.validate(JSON.parse(localStorage.getItem(KEY)||JSON.stringify(api.snapshot()))),skills};}
function fileInput(host,label,fn,multiple=false){const l=el('label',label,host),input=el('input',undefined,l);input.type='file';input.accept='.json,application/json';input.multiple=multiple;input.onchange=async()=>{try{const files=[...input.files];if(files.length>40)throw Error('Choose at most 40 files at once.');for(const file of files){if(file.size>15*1024*1024)throw Error('File is too large (15 MB maximum).');await fn(JSON.parse(await file.text()),file.name);}}catch(e){message.textContent=e.message;}finally{input.value='';}};}
const host=document.querySelector('#student-records');if(!host)return;let message=el('p','',host);message.setAttribute('role','status');
if(host.dataset.mode==='backup'){
 el('h2','One file for your practice',host);el('p','Includes checked attempts, saved answers and guided steps, sessions, saved assignments and written skills notes, investigation notebooks and revision plans for both subjects that are available in this browser. It excludes teacher editorial notes. Files are not synchronized automatically.',host);
 const l=el('label','Name or alias (optional)',host),name=el('input',undefined,l);name.maxLength=100;
 button(host,'Export combined backup',()=>{try{download('student-practice-backup.json',snapshot(name.value.trim()));message.textContent='Backup exported. Keep the downloaded file somewhere safe.';}catch(e){message.textContent=e.message;}});
 let pending=null;const preview=el('p','',host),apply=button(host,'Import previewed backup',()=>{if(!pending)return;try{
  const current=snapshot(name.value),writes=new Map([[KEY,JSON.stringify(merge(current.progress,pending.progress))]]);
  for(const [profile,value]of Object.entries(pending.skills)){const combined={schema:1,profile,notes:{...current.skills[profile]?.notes,...value.notes}};writes.set(prefix+profile,JSON.stringify(notes(combined,profile)));}
  for(const [profile,value]of Object.entries(pending.learning||{})){const previous=current.learning?.[profile];const combined={...value,plans:{...previous?.plans,...value.plans},notebooks:{...previous?.notebooks,...value.notebooks}};writes.set(StudentLearningState.prefix+profile,JSON.stringify(StudentLearningState.validate(combined)));}
  const old=new Map([...writes.keys()].map(k=>[k,localStorage.getItem(k)]));
  try{for(const [k,v]of writes)localStorage.setItem(k,v);}catch(e){for(const [k,v]of old){if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v);}throw Error('Browser could not save the backup. Existing records were restored.');}
  name.value=pending.name;pending=null;apply.disabled=true;message.textContent='Backup merged. Matching drafts, notes and assignments use the imported version. Reopen other practice tabs to load the restored records.';
 }catch(e){message.textContent=e.message;}});apply.disabled=true;
 fileInput(host,'Preview combined backup',raw=>{pending=null;apply.disabled=true;preview.textContent='';const incoming=validate(raw);merge(snapshot('').progress,incoming.progress);pending=incoming;preview.textContent=`${incoming.name||'Unnamed student'}: ${incoming.progress.attempts.length} attempts, ${Object.keys(incoming.progress.drafts).length} saved answers, ${Object.values(incoming.skills).reduce((n,s)=>n+Object.keys(s.notes).length,0)} skills notes, ${Object.values(incoming.progress.assignments||{}).reduce((n,a)=>n+a.length,0)} assignments. Attempts merge; imported drafts and notes replace matching ones.`;apply.disabled=false;});
 button(host,'Clear shared practice records in this browser',()=>{if(!confirm('Export a combined backup first. Clear practice answers, assignments, skills notes, subject revision plans and investigation notebooks in this browser? Personal snapshot plans are cleared from their own page.'))return;try{localStorage.removeItem(KEY);for(const profile of Object.keys(manifest)){localStorage.removeItem(prefix+profile);localStorage.removeItem(StudentLearningState.prefix+profile);}location.reload();}catch(e){message.textContent=e.message;}});
}else{
 el('h2','Class practice snapshots',host);el('p','Import each student’s combined backup or older progress JSON. These editable, self-reported snapshots are practice evidence, not verified marks or mastery. No student files are sent anywhere or merged into your own progress. This view is cleared when you leave; keep the original files.',host);
 const students=[],output=el('div','',host);let counter=0;
 fileInput(host,'Import student files', (raw,filename)=>{
  const data=raw?.type==='studentdash-student-backup'?validate(raw):{name:'',progress:api.validate(raw),skills:{}};
  if(students.length>=100)throw Error('Class limit reached (100 snapshots).');
  if(students.some(s=>s.filename===filename))throw Error('This filename is already loaded. Remove its old snapshot before importing it again.');
  students.push({key:++counter,filename,...data,name:data.name||filename.replace(/\.json$/i,'')});render();
 },true);
 button(host,'Clear class view',()=>{students.length=0;render();});host.append(output);
 const labels=['Not attempted','Needs another attempt','Completed with help or retry','Correct independently'];
 function counts(questions,progress){const recent=new Map();for(const a of progress.attempts){const old=recent.get(a.question);if(!old||a.at>old.at||(a.at===old.at&&a.id>old.id))recent.set(a.question,a);}const out=[0,0,0,0];for(const q of questions){const a=recent.get(q.id);out[!a?0:!a.correct?1:a.assisted?2:3]++;}return out;}
 function table(title,rows){el('h3',title,output);const t=el('table','',output),caption=el('caption','Latest result per question per student. Unattempted questions stay in the denominator.',t),thead=el('thead','',t),head=el('tr','',thead);for(const label of ['Area','Questions per student',...labels])el('th',label,head).scope='col';const body=el('tbody','',t);for(const [label,questions]of rows){const row=el('tr','',body);el('th',label,row).scope='row';el('td',String(questions.length),row);const totals=[0,0,0,0];students.forEach(s=>counts(questions,s.progress).forEach((n,i)=>totals[i]+=n));totals.forEach(n=>el('td',String(n),row));}}
 function render(){output.replaceChildren();el('p',`${students.length} student snapshots loaded. Give each student a distinct alias; remove an earlier snapshot before adding their newer one.`,output);const known=new Set(catalog.questions.map(q=>q.id));for(const s of students){const row=el('section','',output),l=el('label','Student alias',row),input=el('input','',l);input.value=s.name;input.maxLength=100;input.oninput=()=>s.name=input.value;el('p',s.filename+' · '+counts(catalog.questions,s.progress).map((n,i)=>`${labels[i]}: ${n}`).join(' · '),row);const unknown=new Set(s.progress.attempts.filter(a=>!known.has(a.question)).map(a=>a.question));if(unknown.size)el('p',`${unknown.size} question IDs outside this collection are excluded (other subjects or older versions).`,row);button(row,'Remove '+s.name,()=>{students.splice(students.indexOf(s),1);render();});}
  if(!students.length)return;
  table('By syllabus section',[...new Set(catalog.questions.map(q=>q.topic))].map(topic=>[topic,catalog.questions.filter(q=>q.topic===topic)]));
  table('By skill',[...new Set(catalog.questions.flatMap(q=>q.skills||[]))].map(id=>[catalog.skill_labels?.[id]||id,catalog.questions.filter(q=>q.skills?.includes(id))]));
  el('p','A question can contribute to several skills; do not add skill rows together. Written self-review notes are retained in backups but are not scored here.',output);
 }
 render();
}
})();
