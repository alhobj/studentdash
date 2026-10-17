/* Standalone collectible reference album. No random rewards or score changes. */
window.validateElementPacks=function(profile,state){
 const ids=state.elementPacks??[];
 if(!Array.isArray(ids)||new Set(ids).size!==ids.length||ids.some(id=>{
  const pack=profile.periodic.packs.find(p=>p.id===id),q=pack&&profile.adventures.find(q=>q.id===pack.quest);
  return !q||!state.completedActivities.includes(q.id)||!state.discoveries.includes(q.district+'-card');
 }))throw Error('Invalid element collection.');return [...ids];
};
window.createPeriodicAlbum=function({profile,read,save,open,parent,visit,satchel,molecules}){
 const data=profile.periodic;
 const add=(tag,text,into=parent)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;into.append(e);return e;};
 const button=(text,fn,into=parent)=>{const b=add('button',text,into);b.onclick=fn;return b;};
 const quest=pack=>profile.adventures.find(q=>q.id===pack.quest);
 function ready(pack){const s=read(),q=quest(pack);return s.completedActivities.includes(q.id)&&s.discoveries.includes(q.district+'-card');}
 function numbers(){return data.packs.filter(p=>read().elementPacks.includes(p.id)).flatMap(p=>p.elements);}
 function claim(id){const pack=data.packs.find(p=>p.id===id);if(!pack||!ready(pack)||read().elementPacks.includes(id))return false;read().elementPacks.push(id);save();return true;}
 function menu(selected=1){
  open();const shell=add('div');shell.className='periodic-album';const owned=new Set(numbers());
  add('h2','The element collection',shell);add('p',`${owned.size} / 118 element cards collected`,shell);
  if(owned.size===118)add('h3','Collection complete · Periodic explorer!',shell);
  add('p','These are reference cards, not samples of elements. Fixed sets reward completed investigations plus the discovery card from their district. Supported completion counts. Replays give no duplicate cards.',shell);
  const available=data.packs.filter(p=>ready(p)&&!read().elementPacks.includes(p.id));
  if(available.length)button(`Collect all ${available.length} ready sets`,()=>{available.forEach(p=>claim(p.id));menu(selected);},shell);
  add('p','✓ Collected · + Ready to collect · ○ Locked. All reference information is readable. Scroll the table sideways on small screens.',shell);
  const label=add('label','Find an element by name, symbol or atomic number',shell),search=add('input',undefined,label);search.type='search';search.setAttribute('aria-label','Find an element');
  const scroll=add('div',undefined,shell);scroll.className='periodic-scroll';scroll.tabIndex=0;scroll.setAttribute('aria-label','Periodic table; scroll horizontally to see all groups');
  const table=add('div',undefined,scroll);table.className='periodic-grid';
  for(let g=1;g<=18;g++){const n=add('span',String(g),table);n.style.gridColumn=String(g);n.style.gridRow='1';}
  for(const [period,range]of [[6,'57–71'],[7,'89–103']]){const n=add('span',range+' ↓',table);n.className='series-slot';n.style.gridColumn='3';n.style.gridRow=String(period+1);}
  const tiles=[];
  for(const e of data.elements){const pack=data.packs.find(p=>p.elements.includes(e.z));const state=owned.has(e.z)?'collected':ready(pack)?'ready':'locked';
   const b=button('',()=>show(e.z),table);b.className='element-tile '+state;b.style.gridColumn=String(e.col);b.style.gridRow=String(e.row);b.setAttribute('aria-label',`${e.z} ${e.name}, ${e.symbol}, ${state}`);
   add('small',`${e.z} ${state==='collected'?'✓':state==='ready'?'+':'○'}`,b);add('strong',e.symbol,b);tiles.push([e,b]);
  }
  add('p','The detached rows are La–Lu (period 6) and Ac–Lr (period 7). They are displayed separately to keep the table compact.',shell);
  const results=add('p','118 elements shown',shell);results.setAttribute('role','status');
  search.oninput=()=>{const term=search.value.trim().toLowerCase();const exact=data.elements.find(e=>e.symbol.toLowerCase()===term||String(e.z)===term);let count=0;for(const [e,b]of tiles){b.hidden=!!term&&(exact?e.z!==exact.z:!e.name.toLowerCase().includes(term));if(!b.hidden)count++;}results.textContent=count+' elements shown';};
  const details=add('section',undefined,shell);details.className='element-detail';details.setAttribute('aria-live','polite');
  function show(z){const e=data.elements.find(e=>e.z===z),pack=data.packs.find(p=>p.elements.includes(z)),q=quest(pack);details.replaceChildren();
   add('h3',`${e.z} · ${e.symbol} · ${e.name}`,details);add('p',`Atomic number ${e.z}: every atom of this element has ${e.z} protons. A neutral atom has ${e.z} electrons.`,details);
   add('p',`Period ${e.period} · ${e.series||'Group '+e.group}. Neutron count depends on the isotope; it cannot be inferred from atomic number alone.`,details);
   if(owned.has(z))add('p','Collected in your album.',details);
   else{add('p',`Reward set: ${q.section} · ${q.title}. Includes ${pack.elements.map(z=>data.elements[z-1].symbol).join(', ')}.`,details);
    if(ready(pack))button('Collect this element set',()=>{claim(pack.id);menu(z);},details);
    else{if(!read().completedActivities.includes(q.id))button('Open required investigation',()=>visit(q.id),details);if(!read().discoveries.includes(q.district+'-card')){add('p',`Find the discovery card in ${q.district}. Travel there, then inspect its field chest or satchel.`,details);button('Open field satchel',satchel,details);}}
   }
  }
  show(selected);button('Build with your molecule cards',molecules,shell);
  const source=add('a','Element reference: IUPAC periodic table',shell);source.href='https://iupac.org/what-we-do/periodic-table-of-elements/';source.target='_blank';source.rel='noopener noreferrer';
 }
 return {menu,claim,numbers,ready};
};
