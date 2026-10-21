/* Each explorer owns its values and locks; the combined explorer shares n. */
(() => {
 'use strict';
 const NA = 6.02214076e23;
 const fields = {
  n: ['Amount', 'mol', 1], m: ['Mass', 'g', 18], M: ['Molar mass', 'g mol⁻¹', 18],
  c: ['Concentration', 'mol dm⁻³', 0.5], V: ['Solution volume', 'dm³', 2],
  N: ['Number of particles', 'particles', NA], A: ['Avogadro’s constant', 'mol⁻¹', NA]
 };
 const branches = {mass: ['m', 'M'], solution: ['c', 'V'], particles: ['N', 'A']};
 const close = (a,b) => Math.abs(a-b) <= 1e-12 * Math.max(Math.abs(a),Math.abs(b));
 const display = value => Number(value.toPrecision(10)).toString();
 function solve(previous, locked, pairs, key, value) {
  const next = {...previous, [key]:value};
  const fixed = k => locked.has(k) || k === key;
  let amount = fixed('n') ? next.n : null;
  for (const [y,f] of pairs) {
   if (!fixed(y) || !fixed(f)) continue;
   const required = f === 'V' ? next[y]*next[f] : next[y]/next[f];
   if (amount !== null && !close(amount,required)) return null;
   amount = required;
  }
  next.n = amount === null ? previous.n : amount;
  for (const [y,f] of pairs) {
   if (fixed(y) && fixed(f)) continue;
   if (fixed(y)) next[f] = f === 'V' ? next.n/next[y] : next[y]/next.n;
   else next[y] = f === 'V' ? next.n/next[f] : next.n*next[f];
  }
  if (!Object.values(next).every(v => Number.isFinite(v) && v > 0)) return null;
  return next;
 }
 const ns = 'http://www.w3.org/2000/svg';
 function svgElement(tag, attributes, text) {
  const node = document.createElementNS(ns,tag);
  Object.entries(attributes).forEach(([key,value]) => node.setAttribute(key,value));
  if (text) node.textContent = text;
  return node;
 }
 document.querySelectorAll('[data-moly]').forEach(section => {
  const kind = section.dataset.moly, combined = kind === 'all';
  const pairs = combined ? Object.values(branches) : [branches[kind]];
  const keys = ['n',...pairs.flat()];
  const initial = Object.fromEntries(keys.map(k => [k,fields[k][2]]));
  let values = {...initial};
  const locked = new Set(keys.includes('A') ? ['A'] : []);
  const host = section.querySelector('.moly-host');
  const diagram = svgElement('svg',{viewBox:combined?'0 0 780 480':'0 0 600 300',role:'img','aria-labelledby':section.id+'-diagram-title',class:'moly-diagram'});
  diagram.append(svgElement('title',{id:section.id+'-diagram-title'},combined?'Three upright triangles: particles on the left, mass on the right, solution below. Their mole positions overlap in the centre.':'Quantity triangle with current values; editable controls follow below.'));
  const positions = combined ? {n:[390,260],m:[550,95],M:[645,260],c:[285,420],V:[495,420],N:[230,95],A:[135,260]} :
   kind === 'mass' ? {m:[300,85],n:[160,245],M:[440,245]} :
   kind === 'solution' ? {n:[300,85],c:[160,245],V:[440,245]} : {N:[300,85],n:[440,245],A:[160,245]};
  (combined ? ['230,15 20,305 440,305','550,15 340,305 760,305','390,175 180,465 600,465'] : ['300,10 30,285 570,285']).forEach(points=>diagram.append(svgElement('polygon',{points})));
  if (!combined) {
   diagram.append(svgElement('path',{d:'M165 148 H435 M300 148 V285',fill:'none',stroke:'#8ddbc9','stroke-width':2}));
  } else {
   diagram.append(svgElement('path',{d:'M121 165 H339 M230 165 V305 M441 165 H659 M550 165 V305 M281 325 H499 M390 325 V465',fill:'none',stroke:'#8ddbc9','stroke-width':2}));
   diagram.append(svgElement('circle',{cx:390,cy:260,r:48,fill:'#111a2b',stroke:'#8ddbc9','stroke-width':2}));
  }
  const readings = {};
  keys.forEach(k => {
   const [x,y] = positions[k];
   diagram.append(svgElement('text',{x,y:y-8},`${k === 'A'?'Nₐ':k} / ${fields[k][1]}`));
   readings[k] = svgElement('text',{x,y:y+17,class:'moly-value'});
   diagram.append(readings[k]);
  });
  host.append(diagram);
  const controls = document.createElement('div'); controls.className='moly-controls';
  const inputs = {}, checks = {};
  const status = document.createElement('p'); status.className='result moly-status'; status.setAttribute('role','status');
  function render() {
   keys.forEach(k => {
    inputs[k].value = display(values[k]); inputs[k].disabled = locked.has(k);
    inputs[k].removeAttribute('aria-invalid'); checks[k].checked = locked.has(k);
    readings[k].textContent = display(values[k]);
   });
  }
  function constantNote() { return keys.includes('A') && values.A !== NA ? ' Hypothetical constant: real Nₐ is exactly 6.02214076e23 mol⁻¹.' : ''; }
  keys.forEach(k => {
   const card = document.createElement('div'); card.className='moly-field';
   const label = document.createElement('label'); label.htmlFor=section.id+'-'+k; label.textContent=fields[k][0]+' / '+fields[k][1];
   const input = document.createElement('input'); input.type='number'; input.step='any'; input.min='0'; input.id=label.htmlFor;
   const lockLabel = document.createElement('label'); lockLabel.className='moly-lock';
   const checkbox = document.createElement('input'); checkbox.type='checkbox'; checkbox.setAttribute('aria-label','Keep '+fields[k][0].toLowerCase()+' fixed');
   lockLabel.append(checkbox,document.createTextNode('Keep fixed'));
   inputs[k]=input; checks[k]=checkbox;
   input.addEventListener('input',()=> {
    const value=input.valueAsNumber;
    if (!Number.isFinite(value) || value <= 0) {
     input.setAttribute('aria-invalid','true'); status.textContent='Enter a finite number greater than zero. The diagram retains the last valid values.'; return;
    }
    const next=solve(values,locked,pairs,k,value);
    if (!next) {
     render(); status.textContent='Change rejected: unlock another quantity to keep the equations consistent, or use a less extreme number.'+constantNote(); return;
    }
    const changed=keys.filter(other=>other!==k && !close(next[other],values[other]));
    values=next;
    // Preserve the active field text so decimals and scientific notation remain easy to type.
    const typed=input.value; render(); input.value=typed;
    status.textContent=(changed.length?'Updated '+changed.map(other=>fields[other][0].toLowerCase()+' = '+display(values[other])+' '+fields[other][1]).join('; ')+'.':'Values already satisfy the equations.')+constantNote();
   });
   input.addEventListener('change',()=> { render(); });
   checkbox.addEventListener('change',()=> {
    if (checkbox.checked) locked.add(k); else locked.delete(k);
    render(); status.textContent=fields[k][0]+(checkbox.checked?' is now fixed.':' can now change.')+(k==='A'&&!checkbox.checked?' Changing Nₐ is a hypothetical maths experiment; its real value is constant.':'')+constantNote();
   });
   card.append(label,input,lockLabel); controls.append(card);
  });
  host.append(controls);
  if(keys.includes('A')) {
   const note=document.createElement('p'); note.className='muted';
   note.textContent='Nₐ = 6.02214076e23 mol⁻¹ exactly. It starts locked because it is a physical constant. Unlock only for a hypothetical maths experiment. Particle counts refer to the chosen entities (atoms, molecules or ions). Scientific notation, e.g. 6.02214076e23, is accepted.';
   host.append(note);
  }
  const reset=document.createElement('button');reset.type='button';reset.textContent='Reset triangle'+(combined?'s':'');
  reset.addEventListener('click',()=> {values={...initial};locked.clear();if(keys.includes('A'))locked.add('A');render();status.textContent='Starting values and locks restored.';});
  host.append(reset,status);render();status.textContent='Ready. Choose values to keep fixed, then edit another value. All values must be greater than zero.';
 });
})();
