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

for(const game of ['chemistry-game','math-game']){
 const base=path.join(dir,'..',game);els.clear();store.clear();
 const files=game==='chemistry-game'?['profile.js','fieldwork-profile.js','fieldwork.js','adventures.js','expansion.js','further-investigations.js','remaining-sections.js','molecules.js','lab-room.js','adventures-engine.js','periodic-profile.js','periodic-album.js']:['profile.js','fieldwork-profile.js','fieldwork.js','engine.js'];
 for(const name of [...files,'world-profile.js','village-art.js','screen-world.js','walking-controls.js','route-atlas.js','practice-circuit.js','challenge-profile.js'])vm.runInThisContext(fs.readFileSync(path.join(base,name),'utf8'),{filename:name});
 const p=game==='chemistry-game'?window.GAME_PROFILE:window.MATH_GAME_PROFILE;
 const reverse={left:'right',right:'left',up:'down',down:'up'},vectors={left:[-1,0],right:[1,0],up:[0,-1],down:[0,1]};
 let entered,interaction;
 const world=window.createScreenWorld({canvas:new Element('canvas'),rooms:p.rooms,start:p.rooms[0].id,coat:'#fff',reducedMotion:true,onChange:r=>entered=r.id,onInteract:(id,room)=>interaction=[id,room]});
 const seen=new Set();function visit(id){if(seen.has(id))return;seen.add(id);const r=p.rooms.find(r=>r.id===id);assert.ok(r);Object.values(r.exits).forEach(visit);}visit(p.rooms[0].id);assert.equal(seen.size,p.rooms.length);
 for(const r of p.rooms){
  world.travel(r.id);world.paint();
  assert.ok(world.visited().includes(r.id));
  for(const destination of p.rooms){const route=world.routeTo(destination.id);assert.ok(Array.isArray(route));let id=r.id;for(const hop of route){assert.equal(p.rooms.find(n=>n.id===id).exits[hop.direction],hop.id);id=hop.id;}assert.equal(id,destination.id);}
  assert.equal(world.routeTo('missing-room'),null);

  // Flood-fill actual walkable footprints: every signed edge, front door and guide
  // must be accessible from the arrival square despite solid scenery.
  const queue=[[480,380]],reachable=new Set(['480,380']);
  for(let i=0;i<queue.length;i++){
   const [x,y]=queue[i];
   for(const [dx,dy]of [[8,0],[-8,0],[0,8],[0,-8]]){const nx=x+dx,ny=y+dy,k=nx+','+ny;if(nx<16||nx>944||ny<20||ny>540||reachable.has(k)||!world.walkable(nx,ny))continue;reachable.add(k);queue.push([nx,ny]);}
  }
  for(const edge of Object.keys(r.exits))assert.ok(queue.some(([x,y])=>edge==='left'?x===16:edge==='right'?x===944:edge==='up'?y===20:y===540),r.id+' reachable '+edge);
  assert.ok(queue.some(([x,y])=>y>=260&&Math.hypot(x-480,y-290)<60),r.id+' front door reachable');
  for(const actor of r.actors)assert.ok(queue.some(([x,y])=>Math.hypot(x-actor.x,y-actor.y)<65),r.id+' guide reachable');
  Object.assign(world.player,{x:480,y:300});for(let i=0;i<30;i++)world.step(0,-1,.05);
  assert.ok(world.player.y>=262&&world.player.y<300,'wall blocks walking through main building');assert.ok(world.walkable(world.player.x,world.player.y));
  Object.assign(world.player,{x:480,y:140});assert.equal(world.interact(),false,'cannot enter from inside roof');
  Object.assign(world.player,{x:480,y:290});assert.ok(world.interact(),'front door opens activity menu');

  for(const [edge,target]of Object.entries(r.exits)){
   assert.equal(p.rooms.find(r=>r.id===target).exits[reverse[edge]],r.id,'routes are reciprocal');
   world.travel(r.id);world.player.x=edge==='left'?12:edge==='right'?948:480;world.player.y=edge==='up'?20:edge==='down'?546:360;
   world.step(...vectors[edge],.04);assert.equal(world.room().id,target);assert.equal(entered,target);assert.ok(world.walkable(world.player.x,world.player.y),'arrival footprint is clear');
   assert.ok(world.player.x>=30&&world.player.x<=930&&world.player.y>=40&&world.player.y<=536,'safe arrival away from trigger');
   world.step(0,0,.04);assert.equal(world.room().id,target,'no bounce on arrival');
  }
  for(const edge of Object.keys(vectors).filter(e=>!r.exits[e])){world.travel(r.id);world.player.x=edge==='left'?12:edge==='right'?948:480;world.player.y=edge==='up'?20:edge==='down'?546:360;world.step(...vectors[edge],.04);assert.equal(world.room().id,r.id,'closed boundary clamps');}
  world.travel(r.id);Object.assign(world.player,{x:r.actors[0].x,y:r.actors[0].y});assert.ok(world.interact());assert.equal(interaction[1],r.id,'only local actor interacts');
 }

 // Pointer controls: hold, release, cancellation, keyboard nudge and blocked dialogs.
 const pad=new Element('nav'),pressed=new Set();let blocked=false;
 world.travel(p.rooms[0].id);
 const controls=window.attachWalkingControls({container:pad,keys:pressed,world,interact:()=>{},blocked:()=>blocked});
 const east=pad.children.find(b=>b.className==='walk-arrowright');
 east.onpointerdown({pointerId:1,button:0,preventDefault(){}});assert.ok(pressed.has('arrowright'));
 east.onpointerup({pointerId:1});assert.ok(!pressed.size);
 east.onpointerdown({pointerId:2,button:0,preventDefault(){}});east.onpointercancel({pointerId:2});assert.ok(!pressed.size);
 const beforeX=world.player.x;east.onclick({detail:0});assert.ok(world.player.x>beforeX);assert.equal(world.pose().facing,'right');assert.ok(world.pose().moving);world.step(0,0,.04);assert.equal(world.pose().moving,false);world.step(-1,0,.04);assert.equal(world.pose().facing,'left');
 blocked=true;east.onpointerdown({pointerId:3,button:0,preventDefault(){}});assert.ok(!pressed.size);const blockedX=world.player.x;east.onclick({detail:0});assert.equal(world.player.x,blockedX);blocked=false;
 east.onpointerdown({pointerId:4,button:0,preventDefault(){}});controls.stop();assert.ok(!pressed.size);
 // Arrival fade locks movement briefly, then allows continued walking.
 const fading=window.createScreenWorld({canvas:new Element('canvas'),rooms:p.rooms,start:p.rooms[0].id,coat:'#fff'});
 fading.player.x=948;fading.step(1,0,.04);const arrivalX=fading.player.x;fading.step(1,0,.04);assert.equal(fading.player.x,arrivalX);
 for(let i=0;i<7;i++)fading.step(1,0,.04);assert.ok(fading.player.x>arrivalX);fading.paint();
 vm.runInThisContext(fs.readFileSync(path.join(base,'game.js'),'utf8'),{filename:game+'/game.js'});paintFrame(16);
 const start=p.rooms[0];assert.equal(document.getElementById('location-name').textContent,start.name);
 const travelButtons=document.getElementById('travel-buttons').children;
 travelButtons[travelButtons.length-1].click();assert.equal(document.getElementById('location-name').textContent,p.rooms.at(-1).name);
 // Move one screen using actual key handlers and animation callbacks.
 travelButtons[0].click();const map=document.getElementById('map'),target=start.exits.right;
 map.listeners.keydown({key:'ArrowRight',preventDefault(){},repeat:false});for(let i=1;i<=90;i++)paintFrame(i*40);
 assert.equal(document.getElementById('location-name').textContent,p.rooms.find(r=>r.id===target).name);
 document.getElementById('atlas').click();
 const atlasPanel=document.getElementById('panel');
 function descendants(n){return [n,...n.children.flatMap(descendants)];}
 const targetRoom=p.rooms.at(-1);
 const tile=descendants(atlasPanel).find(n=>n.tagName==='BUTTON'&&n.children.some(c=>c.textContent===targetRoom.name));assert.ok(tile);tile.click();
 assert.ok(descendants(atlasPanel).some(n=>n.tagName==='LI'),'atlas describes a walking route');
 const go=descendants(atlasPanel).find(n=>n.tagName==='BUTTON'&&n.textContent==='Travel to '+targetRoom.name);assert.ok(go);go.click();
 assert.equal(document.getElementById('location-name').textContent,targetRoom.name);assert.equal(document.getElementById('dialog').open,false);
 assert.equal(store.size,0,'walking and atlas travel do not overwrite or create academic progress');
 // Collection is available without movement, but cannot unlock outfits without study.
 document.getElementById('fieldwork').click();
 const findButton=text=>descendants(document.getElementById('panel')).find(n=>n.tagName==='BUTTON'&&n.textContent.includes(text));
 findButton('Inspect this location').click();const keep=findButton('Keep discovery card');assert.ok(keep);keep.click();keep.click();
 const storageKey=game==='chemistry-game'?'studentdash-element-quest-v1':p.storageKey;
 let saved=JSON.parse(store.get(storageKey));assert.equal(saved.discoveries.length,1,'duplicate collection grants nothing');assert.equal(saved.credits,0);
 findButton('Open field satchel').click();assert.ok(findButton('Fern explorer coat').disabled,'outfit requires investigations as well as cards');
 assert.throws(()=>window.validateFieldwork(p,{discoveries:['unknown'],outfit:'classic'},0));
 assert.throws(()=>window.validateFieldwork(p,{discoveries:p.discoveryCards.map(c=>c.id),outfit:'midnight'},0));
 assert.throws(()=>window.validateFieldwork(p,{discoveries:[],outfit:'unknown'},0));
 // Independently check generated tasks and the five-round UI state machine.
 if(game==='math-game'){
  assert.deepEqual(p.makeChallengeSet(()=>0).map(q=>q.answer),[38,-3,5,6,2]);
  assert.deepEqual(p.makeChallengeSet(()=>0.999999).map(q=>q.answer),[120,38,25,16,60]);
 }else{
  const gold=p.makeChallengeSet([79],()=>0);assert.deepEqual(gold.map(q=>q.answer),[79,79,6,79,79]);
  assert.equal(p.makeChallengeSet([],()=>0).length,5);
 }
 document.getElementById('circuit').click();assert.ok(document.getElementById('panel').textContent.includes('ROUND 1 / 5'));
 const practicePanel=document.getElementById('panel'),beforePractice=JSON.stringify([...store]);
 let made=0;
 const circuit=window.createPracticeCircuit({parent:practicePanel,open:()=>practicePanel.replaceChildren(),makeSet:()=>{made++;return Array.from({length:5},(_,i)=>({topic:'Fictional fixture',title:'Round '+i,prompt:'Enter the specified count.',label:'Count',answer:i+2,hint:'Use the given count.',explanation:'The count is '+(i+2)}));}});
 circuit.start();
 const action=text=>descendants(practicePanel).find(n=>n.tagName==='BUTTON'&&n.textContent===text);
 for(let i=0;i<5;i++){
  let number=descendants(practicePanel).find(n=>n.tagName==='INPUT');
  if(i===0){action('Check answer').click();assert.ok(practicePanel.textContent.includes('Enter a number first'));number.value='99';number.oninput();action('Check answer').click();circuit.start();number=descendants(practicePanel).find(n=>n.tagName==='INPUT');assert.equal(number.value,'99','circuit retains input when reopened');}
  number.value=String(i+2);number.oninput();action('Check answer').click();assert.ok(action('Check answer').disabled);action(i===4?'Review circuit':'Next round').click();
 }
 assert.ok(practicePanel.textContent.includes('5 rounds reviewed · 4 solved'));
 assert.equal(JSON.stringify([...store]),beforePractice,'circuit does not alter saved progress or credits');
 action('Try a new circuit').click();assert.equal(made,2);assert.ok(practicePanel.textContent.includes('ROUND 1 / 5'));
 console.log('PASS: '+game+' connected screens, reciprocal edge warps, safe arrival, closed edges, local interaction, rendering, travel buttons and keyboard integration.');
}
assert.equal(fs.readFileSync(path.join(dir,'route-atlas.js'),'utf8'),fs.readFileSync(path.join(dir,'../math-game/route-atlas.js'),'utf8'),'portable atlas copies match');
assert.equal(fs.readFileSync(path.join(dir,'screen-world.js'),'utf8'),fs.readFileSync(path.join(dir,'../math-game/screen-world.js'),'utf8'),'portable controller copies match');

// Run the mathematics smoke test's pure engine section; browser iframe checks are excluded.
const mathSmoke=fs.readFileSync(path.join(dir,'../math-game/smoke-test.js'),'utf8').split("  const frame=document.getElementById('game');")[0]+'})();';
vm.runInThisContext(mathSmoke,{filename:'math-engine-smoke'});
assert.ok(!document.getElementById('result').textContent.includes('FAIL'),document.getElementById('result').textContent);
console.log(document.getElementById('result').textContent);

assert.equal(fs.readFileSync(path.join(dir,'village-art.js'),'utf8'),fs.readFileSync(path.join(dir,'../math-game/village-art.js'),'utf8'),'portable art renderers match');
