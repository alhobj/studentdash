/* Small reusable activity runner; curriculum identifiers and answers are profile data. */
window.createAdventureRunner=function(api){
  const {profile,read,save,open,el,button,panel,archiveOpen,arrange,training,supply,modelMenu}=api;
  const quests=profile.adventures, equipment=profile.gameplay.equipment;
  const byId=id=>quests.find(q=>q.id===id);
  function missing(q){
    const s=read(),r=q.requires||{},result=[];
    if(r.archive&&!archiveOpen())result.push('Open the atomic archive: complete the first section checkpoint and water-state model.');
    for(const flag of r.flags||[])if(!s[flag])result.push(flag==='distillation'?'Repair the still and collect a water sample.':`Complete ${flag}.`);
    for(const id of r.completed||[])if(!s.completedActivities.includes(id))result.push(`Complete “${byId(id).title}”.`);
    for(const id of r.bench||[])if(!s.bench.includes(id)){
      if(!s.tools.includes(id)){const source=quests.find(quest=>quest.reward.tool===id),item=profile.gameplay.shop.find(tool=>tool.id===id);result.push(source?`Earn ${equipment[id]} by completing “${source.title}”, then place it.`:item?`Buy ${equipment[id]} at the supply desk for ${item.cost} credits, then place it.`:`Collect and place ${equipment[id]}.`);}
      else result.push(`Place ${equipment[id]} on your workbench.`);
    }
    return result;
  }
  function summary(){
    const remaining=quests.filter(q=>!read().completedActivities.includes(q.id));
    const next=remaining.find(q=>!missing(q).length)||remaining[0];
    return next?{title:next.title,description:missing(next).join(' ')||next.story,run:()=>offer(next)}:{title:'Your restored research lab',description:`All ${quests.length} campus quests are complete. Use your element cards to build molecular models, or replay quests from the journal.`,run:modelMenu};
  }
  function journal(mode='ready'){
    if(!['ready','all','done'].includes(mode))mode='ready';
    open();el('small','QUEST JOURNAL');el('h2','People to help · things to build');
    el('p','Choose any available branch. Rewards are permanent and paid once. Unfinished steps and hints are saved automatically. Completed quests can be replayed.');
    button('Ready to start',()=>journal('ready'));button('All quests',()=>journal('all'));button('Completed',()=>journal('done'));
    const visible=quests.filter(q=>mode==='all'||(mode==='done'?read().completedActivities.includes(q.id):!read().completedActivities.includes(q.id)&&!missing(q).length));
    if(!visible.length)el('p',mode==='ready'?'No new quests are ready. Open All quests to see what equipment or practice opens the next route.':'No completed quests yet.');
    for(const q of visible){
      const done=read().completedActivities.includes(q.id),needs=missing(q);
      button(`${done?'✓':needs.length?'◇':'→'} ${q.section} · ${q.title}`,()=>offer(q));
      el('p',read().activityDrafts[q.id]?`In progress · step ${read().activityDrafts[q.id].stage+1} of ${q.steps.length}`:done?(read().independentActivities.includes(q.id)?'Completed without hints on at least one run.':'Completed with support. You can replay without hints.'):(needs.join(' ')||'Ready to start.'));
    }
  }
  function notebook(id){
    open();el('small','YOUR RESEARCH NOTEBOOK');
    const completed=quests.filter(q=>read().completedActivities.includes(q.id));
    const q=completed.find(q=>q.id===id);
    if(!q){
      el('h2','Discoveries to revisit');el('p','Completed investigations appear here. Your notes stay in this browser and are included in exported saves. They are reflections, not assessed answers.');
      if(!completed.length)el('p','Complete your first campus quest to start your notebook.');
      completed.forEach(q=>button(`${q.section} · ${q.title}${read().fieldNotes[q.id]?' · note saved':''}`,()=>notebook(q.id)));
      button('Find an investigation',journal);return;
    }
    el('h2',q.title);
    for(const step of q.steps){const entry=el('section');entry.className='notebook-entry';el('h3',step.title,entry);el('p',step.explanation,entry);}
    const label=el('label','My field note: what changed, what stayed the same, and what can I explain now?');
    const note=el('textarea',undefined,label);note.className='field-note';note.maxLength=2000;note.rows=5;note.value=read().fieldNotes[q.id]||'';note.setAttribute('aria-label','My field note');
    const status=el('p','Up to 2,000 characters. Changes save automatically.');status.setAttribute('role','status');
    note.oninput=()=>{read().fieldNotes[q.id]=note.value.slice(0,2000);save();status.textContent=`${note.value.length} / 2,000 characters · saved in this game session.`;};
    button('Notebook contents',notebook);button('Revisit this investigation',()=>offer(q));
  }
  function offer(q){
    open();el('small',`${q.section} / ${q.npc}`);el('h2',q.title);el('p',q.story);
    const needs=missing(q);
    if(needs.length){needs.forEach(text=>el('p',text));button('Arrange equipment',arrange);button('Visit supply desk',supply);button('Return to teaching lab',training);button('Other quests',journal);return;}
    el('p',`First completion: ${q.reward.credits} credits${q.reward.tool?' + '+equipment[q.reward.tool]:''}${q.reward.elements?' + '+q.reward.elements.join(', ')+' element cards':''}. Free hints are always available.`);
    button(read().activityDrafts[q.id]?'Resume activity':read().completedActivities.includes(q.id)?'Replay activity':'Accept quest and begin',()=>run(q));
    button('Other quests',journal);
  }
  function run(q){
    let stage=read().activityDrafts[q.id]?.stage||0,assisted=read().activityDrafts[q.id]?.assisted||false;
    function remember(extra={}){read().activityDrafts[q.id]={stage,assisted,...extra};save();}
    function advance(){button(stage+1<q.steps.length?'Next step':'Finish quest',()=>{stage++;if(stage<q.steps.length){remember();render();}else complete();});}
    function orderStep(step){
      let order=[...(read().activityDrafts[q.id]?.order||step.initialOrder)],locked=false;const list=el('div');list.className='ordering-list';
      const feedback=el('p');feedback.className='feedback';feedback.setAttribute('role','status');
      function paint(){list.replaceChildren();order.forEach((item,i)=>{const row=el('div',undefined,list);row.className='ordering-row';el('span',`${i+1}. ${step.items[item]}`,row);const up=button('↑',()=>move(i,-1),row),down=button('↓',()=>move(i,1),row);up.setAttribute('aria-label',`Move ${step.items[item]} up`);down.setAttribute('aria-label',`Move ${step.items[item]} down`);up.disabled=locked||i===0;down.disabled=locked||i===order.length-1;});remember({order});}
      function move(i,delta){if(locked||i+delta<0||i+delta>=order.length)return;[order[i],order[i+delta]]=[order[i+delta],order[i]];paint();}
      const hint=button('Free hint',()=>{assisted=true;remember({order});feedback.textContent=step.hint;});
      const check=button('Check order',()=>{if(!order.every((value,i)=>value===i)){assisted=true;remember({order});feedback.textContent='Not quite yet. '+step.hint;return;}locked=true;hint.disabled=check.disabled=true;feedback.textContent='Correct. '+step.explanation;paint();advance();});
      button('Return to journal',journal);paint();
    }
    function render(){
      open();const step=q.steps[stage];el('small',`${q.section} / STEP ${stage+1} OF ${q.steps.length}`);el('h2',step.title);el('p',step.context);
      if(step.kind==='order'){orderStep(step);return;}
      const form=el('div');form.className='activity-fields';const inputs=[],adjusters=[];
      for(const [fieldIndex,f] of step.fields.entries()){
        const row=el('label',f.label,form);row.className='quantity-field';const control=el('div',undefined,row);control.className='quantity-controls';
        const minus=button('−',()=>adjust(-1),control),input=el('input',undefined,control),plus=button('+',()=>adjust(1),control);
        adjusters.push(minus,plus);
        input.type=f.kind==='range'?'range':'number';input.min=f.min;input.max=f.max;input.step=f.step||1;input.value=String(read().activityDrafts[q.id]?.values?.[fieldIndex]??f.initial??f.min);input.setAttribute('aria-label',f.label);
        minus.setAttribute('aria-label',`Decrease ${f.label}`);plus.setAttribute('aria-label',`Increase ${f.label}`);
        function adjust(sign){const value=Number(input.value);input.value=String(Number(Math.max(f.min,Math.min(f.max,(Number.isFinite(value)?value:f.min)+sign*(f.step||1))).toFixed(6)));update();}
        input.oninput=update;inputs.push(input);
      }
      const visual=el('div');visual.className='activity-model';visual.setAttribute('aria-live','polite');
      for(const action of step.actions||[])adjusters.push(button(action.label,()=>{inputs.forEach((input,i)=>input.value=String(action.values[i]));update();}));
      const feedback=el('p');feedback.className='feedback';feedback.setAttribute('role','status');
      function update(){
        remember({values:inputs.map(i=>String(i.value))});const values=inputs.map(i=>Number(i.value));visual.replaceChildren();
        if(step.model){
          if(values.some(v=>!Number.isFinite(v))){el('p','Enter valid control values.',visual);return;}
          const model=profile.models[step.model](values);for(const line of model.lines)el('p',line,visual);
          if(model.piston!==undefined){const chamber=el('div',undefined,visual);chamber.className='piston-chamber';const gas=el('div','·  ·  ·  ·  ·  ·  ·  ·',chamber);gas.className='piston-gas';gas.style.width=Math.max(10,Math.min(100,model.piston*100))+'%';}
          const gauge=el('div',undefined,visual);gauge.className='experiment-gauge';gauge.setAttribute('aria-label',model.gauge);const fill=el('div',undefined,gauge);fill.style.width=`${Math.max(0,Math.min(1,model.fraction))*100}%`;
        }else if(step.visual==='atom'){
          for(let i=0;i<inputs.length;i++){const row=el('div',undefined,visual);el('span',`${step.fields[i].label}: ${Number.isFinite(values[i])?values[i]:'—'} `,row);const dots=el('span','●'.repeat(Math.max(0,Math.min(20,Math.floor(values[i]||0)))),row);dots.className=['proton-dots','neutron-dots','electron-dots'][i];}
          el('p',`Mass number: ${values[0]+values[1]} · Net charge: ${values[0]-values[2]}`,visual);
        }else if(step.visual==='ions'){
          inputs.forEach((_,i)=>el('p',`${step.fields[i].label}: ${'▣ '.repeat(Math.max(0,Math.min(6,Math.floor(values[i]||0))))}`,visual));
          el('strong',`Net charge: ${values.reduce((sum,v,i)=>sum+v*step.charges[i],0)}`,visual);
        }else if(step.visual==='balance'){el('div','▰',visual).className='balance-pan';el('strong',`${values[0].toFixed(2)} g`,visual).className='balance-reading';}
        else el('p',inputs.map((input,i)=>`${step.fields[i].label}: ${input.value||'—'}`).join(' · '),visual);
      }
      const hint=button('Free hint',()=>{assisted=true;remember({values:inputs.map(i=>String(i.value))});feedback.textContent=step.hint;});
      const check=button('Check model',()=>{
        const valid=inputs.every((input,i)=>{const f=step.fields[i],v=Number(input.value);return input.value.trim()!==''&&Number.isFinite(v)&&v>=f.min&&v<=f.max;});
        const correct=valid&&(step.model?Math.abs(profile.models[step.model](inputs.map(input=>Number(input.value))).values[step.goal.key]-step.goal.target)<=(step.goal.tolerance??0.000001):inputs.every((input,i)=>Math.abs(Number(input.value)-step.fields[i].target)<=(step.fields[i].tolerance??0.000001)));
        if(!correct){assisted=true;remember({values:inputs.map(i=>String(i.value))});feedback.textContent='Not quite yet. '+step.hint;return;}
        feedback.textContent='Correct. '+step.explanation;check.disabled=true;hint.disabled=true;[...inputs,...adjusters].forEach(input=>input.disabled=true);
        advance();
      });
      button('Return to journal',journal);update();
    }
    function complete(){
      const s=read(),first=!s.completedActivities.includes(q.id);
      if(first){s.completedActivities.push(q.id);s.credits+=q.reward.credits;if(q.reward.tool&&!s.tools.includes(q.reward.tool))s.tools.push(q.reward.tool);}
      if(!assisted&&!s.independentActivities.includes(q.id))s.independentActivities.push(q.id);
      delete s.activityDrafts[q.id];save();open();el('small','QUEST COMPLETE');el('h2',q.title);el('p',q.rewardText);
      el('p',first?`Earned ${q.reward.credits} credits${q.reward.tool?' and '+equipment[q.reward.tool]:''}.`:'Practice complete. Your first-completion reward was already collected.');
      if(q.reward.elements)el('p','Element cards available at the molecule bench: '+q.reward.elements.join(', ')+'.');
      el('p',assisted?'Completed with support. Revisit it whenever you want.':'Completed without hints or incorrect checks in this run. Repeated tasks are practice, not a mastery assessment.');
      button('Write a field note',()=>notebook(q.id));button('Choose the next quest',journal);button('Arrange equipment',arrange);
    }
    render();
  }
  function district(id){
    const available=quests.filter(q=>q.district===id);if(!available.length)return false;
    open();el('h2',profile.districts.find(d=>d.id===id).name);el('p','These routes are proposed learning paths. Equipment and completed quests open new activities.');
    available.forEach(q=>button(`${q.section} · ${q.title}`,()=>offer(q)));button('All quests',journal);return true;
  }
  function districtStatus(id){const list=quests.filter(q=>q.district===id);return !list.length?'CONCEPT':list.some(q=>!missing(q).length)?'OPEN':'QUESTS LOCKED';}
  return {journal,notebook,summary,district,missing,districtStatus,visit:id=>offer(byId(id))};
};
