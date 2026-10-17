/* Local presentation for Pattern Quest. All quest content is supplied by profile.js. */
(() => {
  'use strict';
  const P = window.MATH_GAME_PROFILE, $ = id => document.getElementById(id);
  const engine = window.createQuestEngine(P, {getItem:key => localStorage.getItem(key), setItem:(key, value) => localStorage.setItem(key, value)});
  const dialog = $('dialog'), panel = $('panel'), keys = new Set();
  const quest = id => P.quests.find(q => q.id === id);
  const district = id => P.districts.find(d => d.id === id);
  function el(tag, text, parent = panel) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; parent.append(node); return node; }
  function button(text, action, parent = panel, className = '') { const node = el('button', text, parent); node.className = className; node.onclick = action; return node; }
  function open(title, eyebrow = '') {
    keys.clear(); panel.replaceChildren();
    if (eyebrow) el('small', eyebrow);
    el('h2', title).id = 'panel-title';
    if (!dialog.open) dialog.showModal();
  }
  function feedback(parent = panel) { const node = el('p', '', parent); node.className = 'feedback'; node.setAttribute('role', 'status'); return node; }
  function attempt(fn, target) { try { fn(); refresh(); } catch (error) { target.textContent = error.message; } }
  function refresh() {
    const s = engine.read(), next = P.quests.find(q => !s.completed.includes(q.id) && !engine.missing(q.id).length);
    $('wallet').textContent = `${s.credits} discovery credits · ${s.completed.length}/${P.quests.length} quests`;
    $('quest-title').textContent = next ? next.title : 'Meridian is open again';
    $('quest-description').textContent = next ? `${district(next.district).guide}: ${next.story}` : 'Revisit an investigation, experiment with graphs, or record what you can now explain.';
    $('progress').max = P.quests.length; $('progress').value = s.completed.length;
    $('progress-label').textContent = `${s.completed.length} of ${P.quests.length} investigations complete`;
    $('continue').textContent = next ? (s.drafts[next.id] ? 'Resume investigation →' : 'Meet your guide →') : 'Revisit the town →';
    $('continue').onclick = () => next ? offer(next.id) : journal();
    $('collection').replaceChildren();
    const cards = P.quests.filter(q => s.completed.includes(q.id)).map(q => q.reward.card);
    if (!cards.length) el('p', 'Help a guide to collect your first idea card and studio tool.', $('collection'));
    cards.forEach(card => el('span', card, $('collection')).className = 'badge');
    if (engine.error()) $('notice').textContent = engine.error();
    paintMap();
  }
  function offer(id) {
    const q = quest(id), s = engine.read(), missing = engine.missing(id);
    open(q.title, `${district(q.district).name} / ${district(q.district).guide}`);
    el('p', q.story);
    if (missing.length) {
      el('p', 'This route opens after:'); missing.forEach(required => button(quest(required).title, () => offer(required), panel, 'wide'));
    } else {
      el('p', `First completion: ${q.reward.credits} discovery credits, the “${q.reward.card}” idea card${q.reward.tool ? ', and a ' + P.equipment[q.reward.tool] : ''}. Hints are free; all completion rewards are the same.`);
      if (s.completed.includes(id)) el('p', 'Already restored. Replays provide practice without another reward. An independent replay uses the same tasks, so it is not a new mastery test.');
      button(s.drafts[id] ? 'Resume investigation' : s.completed.includes(id) ? 'Replay investigation' : 'Accept quest and begin', () => {engine.start(id); run(id); refresh();}, panel, 'primary');
    }
    button('Other investigations', () => journal());
  }
  function journal(mode = 'ready', districtId = null) {
    const s = engine.read();
    open(districtId ? district(districtId).name : 'People to help · patterns to discover', 'QUEST JOURNAL');
    if (districtId) el('p', `Meet ${district(districtId).guide}, ${district(districtId).role.toLowerCase()}.`);
    button('Ready to start', () => journal('ready', districtId)); button('All quests', () => journal('all', districtId)); button('Completed', () => journal('done', districtId));
    const visible = P.quests.filter(q => (!districtId || q.district === districtId) &&
      (mode === 'all' || (mode === 'done' ? s.completed.includes(q.id) : !s.completed.includes(q.id) && !engine.missing(q.id).length)));
    if (!visible.length) el('p', 'No investigations in this view. Choose All quests to see the routes and their requirements.');
    visible.forEach(q => {
      const row = el('div'); row.className = 'quest-row';
      const done = s.completed.includes(q.id), missing = engine.missing(q.id);
      button(`${done ? '✓' : missing.length ? '◇' : '→'} ${q.title}`, () => offer(q.id), row, 'wide');
      el('p', s.drafts[q.id] ? `In progress · step ${s.drafts[q.id].stage + 1} of ${q.steps.length}` : done ?
        (s.independent.includes(q.id) ? 'Completed · includes an unhinted, correct run' : 'Completed with support') :
        missing.length ? 'Requires: ' + missing.map(id => quest(id).title).join(', ') : `${district(q.district).guide} · Ready to begin`, row);
    });
    if (districtId) { const a = el('a', 'Explore the existing topic practice →'); a.href = '../../resources/ib-math-ai-sl/' + district(districtId).resource; }
  }
  function run(id) {
    const q = quest(id), draft = engine.read().drafts[id], step = q.steps[draft.stage];
    open(step.title, `${q.title} / STEP ${draft.stage + 1} OF ${q.steps.length}`);
    el('p', step.prompt);
    const grid = el('div'); grid.className = 'form-grid';
    const inputs = step.fields.map((f, index) => {
      const label = el('label', f.label + (f.unit ? ` / ${f.unit}` : ''), grid); label.className = 'field';
      const input = el('input', undefined, label); input.type = 'number'; input.step = 'any'; input.inputMode = 'decimal'; input.value = draft.values[index];
      input.setAttribute('aria-label', f.label + (f.unit ? ' in ' + f.unit : ''));
      input.oninput = () => { engine.record(id, inputs.map(n => n.value)); next.disabled = true; result.textContent = 'Values changed. Check your answer again.'; updateModel(); refresh(); };
      return input;
    });
    let model = null;
    if (step.model) {model = el('div'); model.className = 'model';}
    const updateModel = () => {if (model) renderModel(model, step.model, inputs.map(n => n.value.trim() === '' ? NaN : Number(n.value)));};
    const result = feedback();
    const check = button('Check model', () => {
      engine.record(id, inputs.map(n => n.value));
      const correct = engine.check(id); next.disabled = !correct;
      result.textContent = correct ? `Correct. ${step.explanation}` : `Not quite yet. ${step.hint} This run is now recorded as supported practice; you can keep trying.`;
      refresh();
    }, panel, 'primary');
    button('Free hint', () => {engine.hint(id); result.textContent = step.hint + ' This run is recorded as supported practice.'; refresh();});
    button('Worked explanation', () => {engine.hint(id); result.textContent = step.explanation + ' Enter the values and check them to continue.'; refresh();});
    const next = button(draft.stage + 1 === q.steps.length ? 'Finish quest' : 'Next step →', () => {
      if (engine.advance(id)) complete(id); else run(id); refresh();
    }); next.disabled = !draft.passed;
    if (draft.passed) result.textContent = 'Correct. ' + step.explanation;
    inputs.forEach(input => input.addEventListener('keydown', event => {if (event.key === 'Enter') {event.preventDefault(); check.click();}}));
    button('Save and return to journal', () => journal()); updateModel();
  }
  function complete(id) {
    const q = quest(id); open('A little more of Meridian, restored.', 'INVESTIGATION COMPLETE');
    el('h3', q.title); el('p', `Idea card collected: ${q.reward.card}. The first-completion reward is paid only once.`);
    q.steps.forEach(step => el('p', step.explanation));
    button('Write a field note', () => notebook(id), panel, 'primary'); button('Find the next investigation', () => journal()); button('Visit your studio', studio);
  }
  function notebook(id) {
    const s = engine.read(); open('Your field notebook', 'PATTERNS WORTH KEEPING');
    if (!id) {
      el('p', 'Completed investigations and personal notes live here. Notes are included in exported saves.');
      if (!s.completed.length) el('p', 'Complete an investigation to collect your first notebook entry.');
      s.completed.forEach(id => button(quest(id).title + (s.notes[id] ? ' · note saved' : ''), () => notebook(id), panel, 'wide')); return;
    }
    const q = quest(id); el('h3', q.title); q.steps.forEach(step => {el('h3', step.title); el('p', step.explanation);});
    const label = el('label', 'What pattern did you notice? What can you now explain?');
    const input = el('textarea', undefined, label); input.rows = 5; input.maxLength = 2000; input.value = s.notes[id] || '';
    const status = feedback(); input.oninput = () => {engine.note(id, input.value); status.textContent = engine.error() || 'Saved in this browser.'; refresh();};
    button('Notebook contents', () => notebook());
  }
  function shop() {
    const s = engine.read(); open('The supply desk', 'OPTIONAL STUDIO DECORATIONS');
    el('p', `You have ${s.credits} discovery credits. Hints and investigations never cost credits. These items decorate your studio.`);
    const status = feedback();
    P.shop.forEach(item => {
      const b = button(`${s.tools.includes(item.id) ? 'Owned' : 'Buy'} ${P.equipment[item.id]} · ${item.cost} credits`, () => attempt(() => {engine.buy(item.id); shop();}, status), panel, 'wide');
      b.disabled = s.tools.includes(item.id);
    }); button('Arrange the studio', studio);
  }
  function studio() {
    const s = engine.read(); open('Your mathematics studio', 'A SPACE BUILT FROM YOUR DISCOVERIES');
    const canvas = el('canvas'); canvas.width = 600; canvas.height = 240; canvas.className = 'studio-canvas'; canvas.setAttribute('aria-label', 'Studio illustration; the equipped items are listed below.');
    const c = canvas.getContext('2d'); c.fillStyle = '#273d47'; c.fillRect(0,0,600,240);
    c.fillStyle = '#344e52'; c.fillRect(0,160,600,80); c.fillStyle = '#536b69';
    for(let x=0;x<600;x+=50) c.fillRect(x,161,2,79);
    c.fillStyle='#83afb8'; c.fillRect(35,30,100,90); c.fillStyle='#dfc68b'; c.fillRect(81,30,8,90); c.fillRect(35,71,100,8);
    c.fillStyle='#142d35'; c.fillRect(180,25,320,100); c.strokeStyle='#8dada1'; c.strokeRect(180,25,320,100); c.fillStyle='#a8c6ac'; c.font='16px monospace'; c.fillText('A place for your next idea.',202,58); c.fillText(`${s.completed.length} discoveries / ${P.quests.length}`,202,91);
    c.fillStyle='#a78058'; c.fillRect(100,173,420,14); c.fillRect(115,187,12,40); c.fillRect(493,187,12,40);
    s.placed.forEach((id,i)=>{const x=145+i*135;c.fillStyle=id==='lamp'?'#ebca72':id==='plant'?'#82ae7c':'#9cbfc0';c.fillRect(x,135,35,37);c.fillStyle='#eff0d8';c.font='11px monospace';c.fillText(P.equipment[id],x-25,211);});
    el('p', 'Choose up to three items. Removing an item keeps it in your collection. Equipment is a reward, not a requirement to receive help.');
    const slots = el('div'); slots.className = 'slots';
    for(let i=0;i<3;i++) el('div', `Slot ${i+1}: ${P.equipment[s.placed[i]] || 'Empty'}`, slots).className='slot';
    const status = feedback();
    if (!s.tools.length) el('p','Help Nia, Mira or Sol to collect your first tool.');
    s.tools.forEach(id => button(`${s.placed.includes(id) ? 'Remove' : 'Place'} ${P.equipment[id]}`, () => attempt(() => {engine.place(id); studio();},status)));
    button('Visit the supply desk', shop); button('Find an investigation', () => journal());
  }
  function graph(container, fn, xmin=-2, xmax=8, ymin=-4, ymax=16, second=null) {
    const canvas=el('canvas',undefined,container); canvas.width=600;canvas.height=260;
    canvas.setAttribute('aria-label','Graph of the current model. A numerical description follows.');
    const c=canvas.getContext('2d'), px=x=>35+(x-xmin)/(xmax-xmin)*540, py=y=>225-(y-ymin)/(ymax-ymin)*200;
    c.font='11px monospace'; c.strokeStyle='#2d4850'; c.lineWidth=1;
    for(let x=Math.ceil(xmin);x<=xmax;x++){c.beginPath();c.moveTo(px(x),20);c.lineTo(px(x),225);c.stroke();c.fillStyle='#98b4b8';c.fillText(String(x),px(x)-4,245);}
    for(let y=Math.ceil(ymin/2)*2;y<=ymax;y+=2){c.beginPath();c.moveTo(35,py(y));c.lineTo(575,py(y));c.stroke();c.fillStyle='#98b4b8';c.fillText(String(y),5,py(y)+4);}
    c.strokeStyle='#95aaa6';c.beginPath();c.moveTo(px(0),20);c.lineTo(px(0),225);c.moveTo(35,py(0));c.lineTo(575,py(0));c.stroke();
    c.save();c.beginPath();c.rect(35,20,540,205);c.clip();
    for(const [f,color] of [[fn,'#e8ce8a'],[second,'#93d5ca']]) if(f){c.strokeStyle=color;c.lineWidth=2.5;c.beginPath();for(let i=0;i<=300;i++){const x=xmin+(xmax-xmin)*i/300,y=f(x);i?c.lineTo(px(x),py(y)):c.moveTo(px(x),py(y));}c.stroke();}c.restore();
  }
  function renderModel(container, type, values) {
    container.replaceChildren();
    if (values.some(v => !Number.isFinite(v) || Math.abs(v)>10000)) {el('p','Enter finite values between −10,000 and 10,000 to preview the model. Answers are checked separately.',container);return;}
    const [a,b]=values;
    if(type==='line'){graph(container,x=>a*x+b);el('p',`y = ${a}x + ${b}. At x = 0: ${b}; at x = 4: ${4*a+b}.`,container).className='readout';}
    if(type==='quadratic'){graph(container,x=>-((x-a)**2)+b);el('p',`y = −(x − ${a})² + ${b}. Vertex: (${a}, ${b}).`,container).className='readout';}
    if(type==='tangent'){graph(container,x=>x*x,-2,6,-4,20,x=>b*(x-a)+a*a);el('p',`Gold: y = x². Mint: your line with gradient ${b} through (${a}, ${a*a}).`,container).className='readout';}
    if(type==='enclosure'){
      const canvas=el('canvas',undefined,container);canvas.width=600;canvas.height=170;canvas.setAttribute('aria-label','Enclosure diagram; dimensions and totals follow below.');
      const c=canvas.getContext('2d');c.fillStyle='#6d9e85';c.fillRect(50,30,Math.max(0,Math.min(b*12,500)),Math.max(0,Math.min(a*10,120)));c.fillStyle='#dfcba0';c.fillRect(50,24,500,6);
      el('p',`Two widths + length = ${2*a+b} m. Area = ${a*b} m². Only positive dimensions describe an enclosure. Wall at the top; drawing is scaled to fit.`,container).className='readout';
    }
  }
  function builder() {
    open('The graph workbench','FREE EXPLORATION / NO SCORE');
    el('p','Change a linear model and watch the graph respond. No unlock, credits or correct answer required.');
    const controls=el('div');controls.className='form-grid';
    const inputs=[['Gradient m',-4,4,0.25,1],['Intercept b',-4,10,0.5,0]].map(([name,min,max,step,value])=>{
      const label=el('label',name,controls);label.className='field';const input=el('input',undefined,label);input.type='range';input.min=min;input.max=max;input.step=step;input.value=value;input.setAttribute('aria-label',name);const out=el('output',String(value),label);input.oninput=()=>{out.textContent=input.value;update();};return input;
    });
    const model=el('div');model.className='model';const update=()=>renderModel(model,'line',inputs.map(i=>Number(i.value)));update();
    el('p','What changes when only the gradient moves? Which point stays fixed? Try making a horizontal line, then a decreasing line.');
    button('Investigate linear models with Jun',()=>offer('clock'));
  }
  $('close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>keys.clear());
  $('journal').onclick=()=>journal();$('notebook').onclick=()=>notebook();$('shop').onclick=shop;$('studio').onclick=studio;$('builder').onclick=builder;
  $('reset').onclick=()=>{open('Start a new expedition?');el('p','This replaces only Pattern Quest progress in this browser. Export first to keep a copy.');button('Cancel',()=>dialog.close());button('Reset this game save',()=>{engine.reset();refresh();dialog.close();$('notice').textContent=engine.error()||'New expedition ready.';});};
  $('export').onclick=()=>{const url=URL.createObjectURL(new Blob([engine.exportSave()],{type:'application/json'}));const a=el('a',undefined,document.body);a.href=url;a.download='pattern-quest-save.json';a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);$('notice').textContent='Save prepared for download. Keep the JSON file to restore your progress.';};
  $('import').onchange=async event=>{
    const input=event.target,file=input.files[0];if(!file)return;
    try{if(file.size>500000)throw Error('Save file is too large.');const text=await file.text();engine.validate(JSON.parse(text));if(confirm('Replace this browser’s Pattern Quest progress with the selected save?')){engine.importSave(text);dialog.close();refresh();$('notice').textContent=engine.error()||'Save imported.';}}
    catch(error){$('notice').textContent='Import failed. Current progress is unchanged. '+error.message;}finally{input.value='';}
  };
  P.districts.forEach(d=>{
    button(`${d.guide} · ${d.name}`,()=>{travel(d.id);journal('all',d.id);},$('destinations'));
    const a=el('a',d.name+' →',$('routes'));a.href='../../resources/ib-math-ai-sl/'+d.resource;
  });
  const canvas=$('map');
  const world=window.createScreenWorld({canvas,rooms:P.rooms,reducedMotion:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||false,start:'number',coat:()=>P.explorerStyles.find(s=>s.id===engine.read().outfit).color,discovered:id=>engine.read().discoveries.includes(id+'-card'),
    onHint:text=>$('interaction-hint').textContent=text,
 status:id=>`${P.quests.filter(q=>q.district===id&&engine.read().completed.includes(q.id)).length} investigations restored`,
    onChange:r=>{for(const b of $('travel-buttons').children)b.setAttribute('aria-current',b.textContent==='Travel to '+r.name?'location':'false');$('location-name').textContent=r.name;$('travel-status').textContent='Arrived at '+r.name+'. Exits: '+Object.entries(r.exits).map(([direction,id])=>direction+' to '+P.rooms.find(room=>room.id===id).name).join('; ')+'.';canvas.setAttribute('aria-label',r.name+'. Walk with arrows or WASD; E near a guide or entrance.');},
    onInteract:(id,room)=>id==='discovery'?fieldwork.inspect():journal('all',room)});
  function paintMap(){world.paint();}
  function travel(id){keys.clear();world.travel(id);world.paint();canvas.focus?.();}
  P.districts.forEach(d=>button('Travel to '+d.name,()=>travel(d.id),$('travel-buttons')));
  function interact(){if(!world.interact())$('travel-status').textContent='Move near the guide or central entrance and press E.';}
  const fieldwork=window.createFieldwork({profile:P,read:()=>({discoveries:engine.read().discoveries,outfit:engine.read().outfit}),write:data=>{engine.fieldwork(data);refresh();},completed:()=>P.quests.filter(q=>engine.read().completed.includes(q.id)),room:()=>world.room().id,open:()=>open('Fieldwork','EXPLORATION'),parent:panel});
$('fieldwork').onclick=fieldwork.menu;
const circuit=window.createPracticeCircuit({makeSet:()=>P.makeChallengeSet(),open:()=>open('Field practice','UNSCORED PRACTICE'),parent:panel});
$('circuit').onclick=circuit.start;
$('atlas').onclick=()=>{keys.clear();walking.stop();open('Meridian route map','EXPLORE THE TOWN');window.renderWorldAtlas({parent:panel,world,rooms:P.rooms,travel:id=>{dialog.close();travel(id);}});};
const walking=window.attachWalkingControls({container:$('walking-controls'),keys,world,interact,blocked:()=>dialog.open});dialog.addEventListener('close',()=>walking.stop());
canvas.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d','e'].includes(k)){e.preventDefault();if(k==='e'){if(!e.repeat)interact();}else keys.add(k);}});
  window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));canvas.addEventListener('blur',()=>keys.clear());window.addEventListener('blur',()=>keys.clear());
  let previous=0;function frame(time){const dt=Math.min((time-previous)/1000,.04);previous=time;if(!dialog.open){const dx=Number(keys.has('d')||keys.has('arrowright'))-Number(keys.has('a')||keys.has('arrowleft')),dy=Number(keys.has('s')||keys.has('arrowdown'))-Number(keys.has('w')||keys.has('arrowup'));world.step(dx,dy,dt);}else keys.clear();paintMap();requestAnimationFrame(frame);}
  travel('number');refresh();requestAnimationFrame(frame);
})();
