/* Curated connectivity models. Coordinates are screen layout, not molecular geometry. */
window.GAME_PROFILE.molecules=[
 {id:'water',name:'Water',formula:'H₂O',counts:{H:2,O:1},atoms:[['H',20,70],['O',50,40],['H',80,70]],bonds:[[0,1,1],[1,2,1]],explanation:'Two single O–H bonds. Water is bent; oxygen also has two lone pairs, omitted from this connectivity sketch.'},
 {id:'carbon-dioxide',name:'Carbon dioxide',formula:'CO₂',counts:{C:1,O:2},atoms:[['O',15,50],['C',50,50],['O',85,50]],bonds:[[0,1,2],[1,2,2]],explanation:'O=C=O: each C–O link is a double bond. The molecule is linear. Oxygen lone pairs are omitted.'},
 {id:'methane',name:'Methane',formula:'CH₄',counts:{C:1,H:4},atoms:[['C',50,50],['H',50,12],['H',88,50],['H',50,88],['H',12,50]],bonds:[[0,1,1],[0,2,1],[0,3,1],[0,4,1]],explanation:'Four single C–H bonds. Methane is tetrahedral in three dimensions, not the flat cross used for this connectivity diagram.'},
 {id:'ammonia',name:'Ammonia',formula:'NH₃',counts:{N:1,H:3},atoms:[['N',50,45],['H',50,10],['H',18,80],['H',82,80]],bonds:[[0,1,1],[0,2,1],[0,3,1]],explanation:'Three single N–H bonds and one lone pair on nitrogen. Ammonia is trigonal pyramidal; this screen layout is not its three-dimensional geometry.'}
];
window.GAME_PROFILE.adventures.find(q=>q.id==='atoms').reward.elements=['C'];
window.GAME_PROFILE.adventures.find(q=>q.id==='patterns').reward.elements=['N'];
window.createMoleculeBench=function({profile,read,save,open,el,button,cards}){
 function menu(){
  open();el('small','DISCOVERY COLLECTION / GUIDED CONSTRUCTION');el('h2','Build a molecular model');
  el('p','Element cards are reusable discoveries. These activities build curated connectivity models; they do not represent mixing chemicals. Bond buttons cycle through no bond, single, double and triple.');
  for(const recipe of profile.molecules){const missing=Object.keys(recipe.counts).filter(symbol=>!cards().includes(symbol));const b=button(`${read().completedModels.includes(recipe.id)?'✓ ':''}${recipe.formula} · ${recipe.name}`,()=>build(recipe));b.disabled=missing.length>0;
   if(missing.length)el('p',`Needs ${missing.join(', ')} cards. H/O: first checkpoint; C: isotope quest or archive checkpoint; N: periodic archive quest.`);
  }
 }
 function build(recipe){
  open();el('small','MOLECULE BENCH');el('h2',`${recipe.name} · ${recipe.formula}`);el('p','Read the formula, add the required atoms, then choose the bond order on every link. Diagram positions are a layout aid, not a test of molecular shape.');
  const counts={},controls=el('div');controls.className='model-inventory';
  for(const symbol of Object.keys(recipe.counts)){counts[symbol]=0;const row=el('div',undefined,controls);row.className='model-counter';const label=el('strong',`${symbol} × 0`,row);button(`Add ${symbol}`,()=>{counts[symbol]=Math.min(8,counts[symbol]+1);label.textContent=`${symbol} × ${counts[symbol]}`;},row);button(`Remove ${symbol}`,()=>{counts[symbol]=Math.max(0,counts[symbol]-1);label.textContent=`${symbol} × ${counts[symbol]}`;},row);}
  const board=el('div');board.className='bond-board';board.setAttribute('aria-label',recipe.name+' connectivity diagram');
  const chosen=recipe.bonds.map(()=>0);
  recipe.bonds.forEach(([a,b],i)=>{const A=recipe.atoms[a],B=recipe.atoms[b],dx=B[1]-A[1],dy=B[2]-A[2];const line=el('div',undefined,board);line.className='bond-track';line.style.left=A[1]+'%';line.style.top=A[2]+'%';line.style.width=Math.hypot(dx,dy)+'%';line.style.transform=`rotate(${Math.atan2(dy,dx)*180/Math.PI}deg)`;const bond=button('○',()=>{chosen[i]=(chosen[i]+1)%4;bond.textContent=['○','—','=','≡'][chosen[i]];bond.setAttribute('aria-label',`Bond ${i+1}: order ${chosen[i]}`);},board);bond.className='bond-control';bond.style.left=((A[1]+B[1])/2)+'%';bond.style.top=((A[2]+B[2])/2)+'%';bond.setAttribute('aria-label',`Bond ${i+1}: order 0`);});
  recipe.atoms.forEach(([symbol,x,y])=>{const atom=el('span',symbol,board);atom.className='model-atom';atom.style.left=x+'%';atom.style.top=y+'%';});
  const feedback=el('p');feedback.className='feedback';feedback.setAttribute('role','status');
  button('Free model guide',()=>{feedback.textContent=recipe.explanation+' Atom counts: '+Object.entries(recipe.counts).map(([s,n])=>`${s} × ${n}`).join(', ');});
  button('Check molecular model',()=>{
   if(!Object.entries(recipe.counts).every(([symbol,target])=>counts[symbol]===target)){feedback.textContent='Check the formula subscripts and atom inventory first.';return;}
   if(!recipe.bonds.every((bond,i)=>chosen[i]===bond[2])){feedback.textContent='The atom counts match. Check the bond orders; the free guide explains this molecule.';return;}
   const first=!read().completedModels.includes(recipe.id);if(first){read().completedModels.push(recipe.id);read().credits+=6;if(recipe.id==='water')read().water=true;save();}
   feedback.textContent=recipe.explanation+(first?' Model added to your shelf · +6 credits.':' This model is already on your shelf; no additional credits.');
  });
  button('Back to model collection',menu);
 }
 return {menu};
};
