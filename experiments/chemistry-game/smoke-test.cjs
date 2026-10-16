// Dependency-free interaction smoke test: node smoke-test.cjs
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const dir=__dirname,els=new Map(),store=new Map();
let paintFrame;
class Element{
 constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.attributes={};this.value='';this.disabled=false;this.style={};this.className='';this.open=false;this.listeners={};this._text='';}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=[...nodes];this._text='';}
 setAttribute(k,v){this.attributes[k]=v;}
 addEventListener(k,fn){this.listeners[k]=fn;}
 add(node){this.children.push(node);}
 showModal(){this.open=true;}
 close(){this.open=false;}
 get textContent(){return this._text+this.children.map(c=>c.textContent||'').join(' ');}
 set textContent(v){this._text=String(v);this.children=[];}
 click(){if(!this.disabled&&this.onclick)this.onclick({target:this});}
 getContext(){return new Proxy({}, {get:(o,k)=>o[k]||(o[k]=()=>{}),set:(o,k,v)=>(o[k]=v,true)});}
}
const document={getElementById(id){if(!els.has(id))els.set(id,new Element());return els.get(id);},createElement(tag){return new Element(tag);},querySelector(){return new Element('button');}};
global.document=document;global.window={addEventListener(){}};global.localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};global.requestAnimationFrame=fn=>{paintFrame=fn;};global.Option=function(text,value){const e=new Element('option');e.textContent=text;e.value=value;return e;};global.confirm=()=>true;
function load(){vm.runInThisContext(fs.readFileSync(path.join(dir,'profile.js'),'utf8'),{filename:'profile.js'});for(const name of ['adventures.js','expansion.js','molecules.js','lab-room.js','adventures-engine.js'])vm.runInThisContext(fs.readFileSync(path.join(dir,name),'utf8'),{filename:name});vm.runInThisContext(fs.readFileSync(path.join(dir,'game.js'),'utf8'),{filename:'game.js'});}
function find(root,match){if(root.tagName==='BUTTON'&&match(root.textContent))return root;for(const c of root.children){const x=find(c,match);if(x)return x;}return null;}
function click(root,label){const b=find(root,s=>s.includes(label));assert.ok(b,`button containing "${label}" exists`);b.click();}
const panel=document.getElementById('panel'),people=document.getElementById('people'),collection=document.getElementById('collection');
store.set('studentdash-element-quest-v1',JSON.stringify({version:1,credits:4,solved:[],independent:[],lab:false,water:false}));
load();
assert.match(document.getElementById('wallet').textContent,/4 research credits/,'older prototype saves migrate');
click(people,'Nia');click(panel,'Accept');click(panel,'A. Filtration');
let state=JSON.parse(store.get('studentdash-element-quest-v1'));
assert.equal(state.questDone,true);assert.equal(state.parts,1);assert.ok(state.tools.includes('balance'));assert.ok(state.independent.includes('S1.1:separate'));
const afterQuest=state.credits;
click(people,'Nia');click(people,'Jun');click(panel,'Use 1 repair part');
state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.waterSystem,true);assert.equal(state.parts,0);
click(panel,'Run the still activity');
const range=panel.children.find(e=>e.tagName==='INPUT');assert.ok(range);range.value='100';click(panel,'Collect the condensed sample');
state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.distillation,true);const afterSample=state.credits;assert.ok(afterSample>afterQuest);
click(people,'Jun');click(panel,'Run the still activity');const secondRange=panel.children.find(e=>e.tagName==='INPUT');secondRange.value='100';click(panel,'Collect the condensed sample');
state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.credits,afterSample,'still sample reward is one-time');
click(collection,'Arrange equipment');click(panel,'Place Balance');state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.deepEqual(state.bench,['balance']);
click(document.getElementById('destinations'),'S1');click(panel,'S1.1 · Particle training');click(panel,'Which change rearranges particles');click(panel,'A. Melting ice');
click(panel,'Back to stations');click(panel,'A sample is at 25 °C');click(panel,'D. 298 K');
state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.independent.filter(x=>x.startsWith('S1.1:')).length,3);
click(panel,'Back to stations');click(document.getElementById('destinations'),'S1');click(panel,'Water-state model');
const slider=panel.children.find(e=>e.tagName==='INPUT');const check=()=>click(panel,'Check this state');
for(const value of [-10,25,110]){slider.value=String(value);check();}
state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.lab,true);assert.equal(state.independent.filter(x=>x.startsWith('S1.1:')).length,3);
load();assert.match(document.getElementById('quest-title').textContent,/balance|isotope/i);assert.match(collection.textContent,/Balance/);assert.match(collection.textContent,/Slot 1: Balance/);
function descendants(root){return [root,...root.children.flatMap(descendants)];}
function quest(title,answers,{hint=false}={}){
 document.getElementById('journal').click();click(panel,'All quests');click(panel,title);
 click(panel,find(panel,t=>t.includes('Resume activity'))?'Resume activity':find(panel,t=>t.includes('Replay activity'))?'Replay activity':'Accept quest and begin');
 if(hint)click(panel,'Free hint');
 for(let step=0;step<answers.length;step++){
  if(answers[step].order){
   const list=descendants(panel).find(n=>n.className==='ordering-list');assert.ok(list);
   answers[step].order.forEach((label,target)=>{let index=list.children.findIndex(n=>n.textContent.includes(label));assert.ok(index>=0);while(index>target){const up=descendants(panel).find(n=>n.attributes['aria-label']===`Move ${label} up`);assert.ok(up);up.click();index--;}});
   click(panel,'Check order');click(panel,step===answers.length-1?'Finish quest':'Next step');continue;
  }
  const inputs=descendants(panel).filter(n=>n.tagName==='INPUT');assert.equal(inputs.length,answers[step].length);
  inputs.forEach((n,i)=>n.value=String(answers[step][i]));click(panel,'Check model');
  click(panel,step===answers.length-1?'Finish quest':'Next step');
 }
 return JSON.parse(store.get('studentdash-element-quest-v1'));
}
document.getElementById('journal').click();click(panel,'All quests');click(panel,'Restore the materials display');
assert.ok(!find(panel,t=>t==='Accept quest and begin'),'materials quest locked before atom models');
state=quest('A balance for the seed library',[[0],[6.25],[4.8]]);
assert.ok(state.tools.includes('flask'));assert.ok(state.completedActivities.includes('weigh'));
const beforeReplay=state.credits;state=quest('A balance for the seed library',[[0],[6.25],[4.8]]);assert.equal(state.credits,beforeReplay,'quest reward cannot be farmed');
state=quest('Rebuild the isotope display',[[6,6,6],[6,8,6],[11,12,10]],{hint:true});
assert.ok(state.completedActivities.includes('atoms'));assert.ok(!state.independentActivities.includes('atoms'),'hinted run tracked separately');
state=quest('Restore the materials display',[[1,1],[1,2],[2,3]]);assert.ok(state.tools.includes('magneticStirrer'));
click(collection,'Arrange equipment');click(panel,'Place Volumetric flask');click(panel,'Place Magnetic stirrer');
state=quest('Prepare the reference solution',[[0.25],[0.025],[1.461]]);assert.ok(state.completedActivities.includes('solution'));
state=quest('Investigate stirring',[[80],[0.125],[5]]);assert.equal(state.completedActivities.length,5);
state=quest('Put the periodic archive in order',[
 {order:['Na · Z = 11','Mg · Z = 12','Al · Z = 13','Si · Z = 14']},
 {order:['Na⁺ · 11 protons','Mg²⁺ · 12 protons','Al³⁺ · 13 protons']},[1,2,3]
]);assert.ok(state.tools.includes('thermometer'));
click(collection,'Arrange equipment');click(panel,'Remove Balance');click(panel,'Remove Magnetic stirrer');click(panel,'Place Thermometer');
state=quest('Calibrate the energy station',[
 {order:['Add a measured mass of water','Record the initial temperature','Transfer heat to the water','Record the highest final temperature']},[25],[-2090]
]);assert.ok(state.tools.includes('calorimeter'));
state=quest('Investigate the reactor clock',[[0.2],[50,25],[0.001]]);assert.ok(state.tools.includes('stopwatch'));
document.getElementById('shop').click();click(panel,'Buy Pipette');click(panel,'Buy Burette');
click(collection,'Arrange equipment');click(panel,'Remove Thermometer');click(panel,'Remove Volumetric flask');click(panel,'Place Pipette');click(panel,'Place Burette');
state=quest('Restore the titration desk',[
 {order:['Rinse the pipette with the acid solution','Transfer the measured acid aliquot to the flask','Record the initial burette reading','Add titrant while mixing']},[25],[0.074]
]);assert.equal(state.completedActivities.length,9);
assert.equal(window.GAME_PROFILE.models.titration([0]).values.pH,1);
assert.equal(window.GAME_PROFILE.models.titration([25]).values.pH,7);
assert.ok(Math.abs(window.GAME_PROFILE.models.titration([30]).values.pH-11.9586)<0.0001);
assert.equal(window.GAME_PROFILE.models.calorimeter([20]).values.energy,0);
state=quest('Repair the gas-piston display',[[0.125],[400],[298.15]]);assert.ok(state.tools.includes('gasSyringe'));
assert.ok(Math.abs(window.GAME_PROFILE.models.gasVolume([0.125]).values.pressure-199.536)<0.00001);
// A partially answered, supported activity survives a new runtime.
const beforeResumeCredits=state.credits;
click(collection,'Arrange equipment');click(panel,'Place Magnetic stirrer');
document.getElementById('journal').click();click(panel,'All quests');click(panel,'Investigate stirring');click(panel,'Replay activity');
let input=descendants(panel).find(n=>n.tagName==='INPUT');input.value='80';input.oninput();click(panel,'Check model');click(panel,'Next step');
input=descendants(panel).find(n=>n.tagName==='INPUT');input.value='0.125';input.oninput();click(panel,'Free hint');
load();assert.equal(JSON.parse(store.get('studentdash-element-quest-v1')).activityDrafts.mixing.assisted,true);
document.getElementById('journal').click();click(panel,'All quests');click(panel,'Investigate stirring');click(panel,'Resume activity');
input=descendants(panel).find(n=>n.tagName==='INPUT');assert.equal(input.value,'0.125');click(panel,'Check model');click(panel,'Next step');
input=descendants(panel).find(n=>n.tagName==='INPUT');input.value='5';click(panel,'Check model');click(panel,'Finish quest');
state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.credits,beforeResumeCredits);assert.equal(state.activityDrafts.mixing,undefined);
// Card order also survives a reload, without clearing its support flag.
document.getElementById('journal').click();click(panel,'All quests');click(panel,'Put the periodic archive in order');click(panel,'Replay activity');
descendants(panel).find(n=>n.attributes['aria-label']==='Move Na · Z = 11 up').click();click(panel,'Free hint');load();
assert.deepEqual(JSON.parse(store.get('studentdash-element-quest-v1')).activityDrafts.patterns.order,[0,2,3,1]);
state=quest('Put the periodic archive in order',[{order:['Na · Z = 11','Mg · Z = 12','Al · Z = 13','Si · Z = 14']},{order:['Na⁺ · 11 protons','Mg²⁺ · 12 protons','Al³⁺ · 13 protons']},[1,2,3]]);
function molecule(name,counts,bonds){
 document.getElementById('builder').click();click(panel,name);
 const before=JSON.parse(store.get('studentdash-element-quest-v1')).credits;
 click(panel,'Check molecular model');assert.equal(JSON.parse(store.get('studentdash-element-quest-v1')).credits,before,'empty inventory earns nothing');
 for(const [symbol,count]of Object.entries(counts))for(let i=0;i<count;i++)click(panel,`Add ${symbol}`);
 bonds.forEach((order,i)=>{const b=descendants(panel).find(n=>n.attributes['aria-label']===`Bond ${i+1}: order 0`);assert.ok(b);for(let j=0;j<order;j++)b.click();});
 click(panel,'Check molecular model');const after=JSON.parse(store.get('studentdash-element-quest-v1'));click(panel,'Check molecular model');assert.equal(JSON.parse(store.get('studentdash-element-quest-v1')).credits,after.credits);return after;
}
state=molecule('H₂O',{H:2,O:1},[1,1]);assert.ok(state.completedModels.includes('water'));
state=molecule('CO₂',{C:1,O:2},[2,2]);assert.ok(state.completedModels.includes('carbon-dioxide'));
state=molecule('CH₄',{C:1,H:4},[1,1,1,1]);assert.ok(state.completedModels.includes('methane'));
state=molecule('NH₃',{N:1,H:3},[1,1,1]);assert.equal(state.completedModels.length,4);
document.getElementById('lab-room').click();assert.match(descendants(panel).find(n=>n.tagName==='CANVAS').attributes['aria-label'],/Burette/);
paintFrame(16); // Exercise both pixel renderers, without claiming a visual browser test.
load();assert.match(document.getElementById('quest-title').textContent,/restored research lab/);
assert.match(collection.textContent,/10 \/ 10 campus quests complete/);
assert.match(collection.textContent,/NH₃/);
document.getElementById('notebook').click();click(panel,'Repair the gas-piston display');
let note=descendants(panel).find(n=>n.tagName==='TEXTAREA');assert.ok(note);note.value='Half the volume doubled the pressure at constant temperature.';note.oninput();
load();document.getElementById('notebook').click();click(panel,'Repair the gas-piston display');
assert.equal(descendants(panel).find(n=>n.tagName==='TEXTAREA').value,'Half the volume doubled the pressure at constant temperature.');
const fullSave=JSON.parse(store.get('studentdash-element-quest-v1'));
document.getElementById('reset').click();click(panel,'Cancel');assert.equal(JSON.parse(store.get('studentdash-element-quest-v1')).completedActivities.length,10);
document.getElementById('reset').click();click(panel,'Reset this game save');state=JSON.parse(store.get('studentdash-element-quest-v1'));assert.equal(state.credits,0);assert.deepEqual(state.completedActivities,[]);
async function importSave(value){await document.getElementById('import').onchange({target:{files:[{text:async()=>JSON.stringify(value)}],value:'test.json'}});}
(async()=>{
 await importSave(fullSave);assert.equal(JSON.parse(store.get('studentdash-element-quest-v1')).completedModels.length,4);
 assert.match(JSON.parse(store.get('studentdash-element-quest-v1')).fieldNotes['gas-piston'],/doubled the pressure/);
 await importSave({...fullSave,fieldNotes:{'gas-piston':'x'.repeat(2001)}});assert.match(document.getElementById('notice').textContent,/Invalid save/);
 const broken=JSON.parse(JSON.stringify(fullSave));broken.activityDrafts.heat={stage:999,assisted:false};await importSave(broken);
 assert.match(document.getElementById('notice').textContent,/Invalid save/);assert.equal(JSON.parse(store.get('studentdash-element-quest-v1')).credits,fullSave.credits);
 await importSave({...fullSave,completedModels:['unknown-model']});assert.match(document.getElementById('notice').textContent,/Invalid save/);
 await importSave({version:1,credits:20,solved:[],independent:[],lab:false,water:true});assert.deepEqual(JSON.parse(store.get('studentdash-element-quest-v1')).completedModels,['water']);
 console.log('PASS: legacy saves, repair loop, ten quests, ordering, science models, equipment gates, hints, resumable tasks, notebook persistence, four molecules, pixel-renderer execution, one-time rewards, reset, valid imports and corrupt-save rejection.');
})().catch(error=>{console.error(error);process.exitCode=1;});
