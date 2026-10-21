
'use strict';
const el = id => document.getElementById(id);
const fmt = value => Number(value.toPrecision(4)).toString();
function number(id) { const field=el(id); return field.value.trim() !== '' && field.checkValidity() ? Number(field.value) : NaN; }
function stoichiometry(h,o) { const extent=Math.min(h/2,o); return {water:2*extent,h:h-2*extent,o:o-extent,limiting:h/2===o?'Neither reactant is in excess':h/2<o?'H₂ is limiting':'O₂ is limiting'}; }
function updateStoich() { const h=number('hydrogen'),o=number('oxygen'),r=stoichiometry(h,o);el('hydrogen-value').textContent=h.toFixed(1);el('oxygen-value').textContent=o.toFixed(1);el('stoich-result').textContent=`${r.limiting}. Compare ${fmt(h/2)} with ${fmt(o)} mol of reaction extent. Theoretical water yield: ${fmt(r.water)} mol.`;[['h-left','h-bar',r.h],['o-left','o-bar',r.o],['water','water-bar',r.water]].forEach(([out,bar,n])=>{el(out).textContent=fmt(n)+' mol';el(bar).style.width=n*10+'%';}); }
function updateDilution() { const c=number('concentration'),v=number('initial-volume'),f=number('factor');el('factor-value').textContent=fmt(f);if(!Number.isFinite(c)||!Number.isFinite(v)){el('dilution-result').textContent='Enter a concentration from 0.001 to 5 and an initial volume from 1 to 1000.';el('solution').setAttribute('opacity','0');return;}el('solution').setAttribute('opacity',1/f);el('dilution-result').textContent=`Final volume: ${fmt(v*f)} cm³. Solute amount: ${fmt(c*v/1000)} mol. Final concentration: ${fmt(c/f)} mol dm⁻³. The concentration is 1/${fmt(f)} of its initial value.`; }
function equilibrium(h,i,hi,k) {const q=hi*hi/(h*i);return {q,direction:Math.abs(q-k)<=1e-9*Math.max(q,k)?'equal':q<k?'forward':'reverse'};}
function eqValues(){const values=['eq-h','eq-i','eq-hi','eq-k'].map(number);return values.every(Number.isFinite)?equilibrium(...values):null;}
function updateEq(){el('eq-feedback').textContent='';const r=eqValues();if(!r){el('eq-result').textContent='Enter valid concentrations (H₂ and I₂: 0.001–10; HI: 0–10) and K from 0.001–1000.';el('eq-marker').hidden=true;return;}el('eq-marker').hidden=false;el('eq-result').textContent=`Q = ${fmt(r.q)}. K = ${fmt(number('eq-k'))}. Compare the values, then check your prediction.`;const ratio=r.q/number('eq-k');el('eq-marker').style.left=(50+25*Math.max(-2,Math.min(2,Math.log10(ratio))))+'%';}
function checkNumeric(input,feedback,expected,hint){const value=number(input);el(feedback).textContent=!Number.isFinite(value)?'Enter a non-negative numerical answer first.':Math.abs(value-expected)<=expected*0.01?'Correct. '+hint:'Try again. '+hint;}
if(el('hydrogen')) { ['hydrogen','oxygen'].forEach(id=>el(id).addEventListener('input',updateStoich)); }
if(el('concentration')) { ['concentration','initial-volume','factor'].forEach(id=>el(id).addEventListener('input',updateDilution)); }
if(el('eq-h')) { ['eq-h','eq-i','eq-hi','eq-k'].forEach(id=>el(id).addEventListener('input',updateEq)); }
if(el('eq-prediction')) { el('eq-prediction').addEventListener('change',()=>el('eq-feedback').textContent=''); }
if(el('stoich-reset')) { el('stoich-reset').addEventListener('click',()=>{el('hydrogen').value=4;el('oxygen').value=3;el('stoich-answer').value='';el('stoich-feedback').textContent='';updateStoich();}); }
if(el('stoich-check')) { el('stoich-check').addEventListener('click',()=>checkNumeric('stoich-answer','stoich-feedback',3,'Compare 3/2 with 2/1; multiply the smaller value by the water coefficient, 2.')); }
if(el('dilution-check')) { el('dilution-check').addEventListener('click',()=>checkNumeric('dilution-answer','dilution-feedback',0.02,'Use c₂ = 0.300 × 10.0 / 150.0, with both volumes in the same units.')); }
['stoich','dilution'].forEach(key=>el(key+'-answer')?.addEventListener('input',()=>el(key+'-feedback').textContent=''));
if(el('eq-check')) { el('eq-check').addEventListener('click',()=>{const r=eqValues(),answer=el('eq-prediction').value;const reason={forward:'Q < K: the net reaction forms more HI.',reverse:'Q > K: the net reaction forms more H₂ and I₂.',equal:'Q = K: forward and reverse rates are equal.'};el('eq-feedback').textContent=!r?'Correct the numerical inputs first.':!answer?'Choose a prediction first.':(answer===r.direction?'Correct. ':'Reconsider your prediction. ')+reason[r.direction];}); }
if(el('eq-reset')) { el('eq-reset').addEventListener('click',()=>{['eq-h','eq-i','eq-hi'].forEach(id=>el(id).value=1);el('eq-k').value=4;el('eq-prediction').value='';updateEq();}); }
if(el('stoichiometry')) updateStoich(); if(el('dilution')) updateDilution(); if(el('equilibrium')) updateEq();
// Chemistry-specific content stays in this standalone resource, outside the core.
const bondingCases = {
  salt: {name:'NaCl',type:'ionic',solid:false,liquid:true,model:'An extended array of Na⁺ and Cl⁻ ions.',reason:'In the solid the ions are fixed; in the melt they move and carry charge.',particles:['Na⁺','Cl⁻','Na⁺','Cl⁻','Na⁺','Cl⁻']},
  copper: {name:'Cu',type:'metallic',solid:true,liquid:true,model:'Positive metal ions surrounded by delocalized electrons.',reason:'Delocalized electrons carry charge in both solid and molten copper.',particles:['Cu⁺','e⁻','Cu⁺','e⁻','Cu⁺','e⁻']},
  water: {name:'H₂O',type:'covalent',solid:false,liquid:false,model:'Discrete water molecules with covalent O–H bonds; attractions also act between molecules.',reason:'Pure water and ice do not conduct appreciably; liquid pure water has only a very small concentration of ions.',particles:['H₂O','H₂O','H₂O','H₂O']},
  diamond: {name:'Diamond',type:'covalent',solid:false,model:'An extended 3D network: each carbon forms four covalent bonds.',reason:'Electrons are localized in bonds; there are no freely mobile charge carriers.',particles:['C—C','│ │','C—C']},
  graphite: {name:'Graphite',type:'covalent',solid:true,model:'Covalently bonded carbon layers with electrons delocalized within each layer.',reason:'Delocalized electrons allow electrical conduction along the layers.',particles:['C—C—C','e⁻  e⁻','C—C—C']}
};
function updateBonding(){const b=bondingCases[el('bond-material').value];const liquid=el('bond-state').querySelector('[value="liquid"]');liquid.disabled=b.liquid===undefined;if(liquid.disabled)el('bond-state').value='solid';el('bond-model').textContent=b.model;el('bond-particles').textContent=b.particles.join('   ');el('bond-feedback').textContent='';el('bond-type').value='';el('bond-conduction').value='';}
if(el('bond-material')) { ['bond-material','bond-state'].forEach(id=>el(id).addEventListener('change',updateBonding)); }
if(el('bond-type')) { ['bond-type','bond-conduction'].forEach(id=>el(id).addEventListener('change',()=>el('bond-feedback').textContent='')); }
if(el('bond-check')) { el('bond-check').addEventListener('click',()=>{const b=bondingCases[el('bond-material').value],type=el('bond-type').value,prediction=el('bond-conduction').value;if(!type||!prediction){el('bond-feedback').textContent='Choose both bonding type and conduction prediction.';return;}const correct=type===b.type&&(prediction==='yes')===b[el('bond-state').value];el('bond-feedback').textContent=(correct?'Correct. ':'Reconsider. ')+`${b.name}: ${b.type} bonding. ${b.reason}`;}); }
const atomCases=[{name:'Carbon-12',symbol:'C',z:6,a:12,q:0},{name:'Carbon-14',symbol:'C',z:6,a:14,q:0},{name:'Sodium-23 ion',symbol:'Na',z:11,a:23,q:1},{name:'Chlorine-35 ion',symbol:'Cl',z:17,a:35,q:-1},{name:'Magnesium-24 ion',symbol:'Mg',z:12,a:24,q:2}];
if(el('atom-species')) { atomCases.forEach((atom,index)=>el('atom-species').add(new Option(atom.name,String(index)))); }
function atomCounts(atom){return {protons:atom.z,neutrons:atom.a-atom.z,electrons:atom.z-atom.q};}
function updateAtom(){const a=atomCases[el('atom-species').value];el('atom-notation').textContent=`${a.symbol}: A = ${a.a}, Z = ${a.z}, charge = ${a.q>0?'+':''}${a.q}`;['protons','neutrons','electrons'].forEach(key=>el('atom-'+key).value='');el('atom-feedback').textContent='';el('atom-model').hidden=true;}
if(el('atom-species')) { el('atom-species').addEventListener('change',updateAtom); }
if(el('atom-protons')) { ['protons','neutrons','electrons'].forEach(key=>el('atom-'+key).addEventListener('input',()=>el('atom-feedback').textContent='')); }
if(el('atom-check')) { el('atom-check').addEventListener('click',()=>{const counts=atomCounts(atomCases[el('atom-species').value]);const keys=Object.keys(counts);if(keys.some(key=>!Number.isFinite(number('atom-'+key)))){el('atom-feedback').textContent='Enter three non-negative whole numbers.';return;}const wrong=keys.filter(key=>number('atom-'+key)!==counts[key]);el('atom-feedback').textContent=wrong.length?'Recheck '+wrong.join(', ')+'. Use p = Z, n = A − Z, e = Z − signed charge.':'Correct. Your proton, neutron and electron counts all match.';}); }
if(el('atom-reveal')) { el('atom-reveal').addEventListener('click',()=>{const c=atomCounts(atomCases[el('atom-species').value]);el('atom-model').hidden=false;el('atom-model').textContent=`Nucleus: ${c.protons} protons (+) and ${c.neutrons} neutrons (neutral). Surrounding electron region: ${c.electrons} electrons (−). The nucleus contains almost all the mass; it is much smaller than the atom.`;}); }
if(el('isotope-prediction')) { el('isotope-prediction').addEventListener('change',()=>el('isotope-feedback').textContent=''); }
if(el('isotope-check')) { el('isotope-check').addEventListener('click',()=>{const v=el('isotope-prediction').value;el('isotope-feedback').textContent=!v?'Choose a particle first.':v==='neutrons'?'Correct. Both have 6 protons; carbon-12 has 6 neutrons and carbon-14 has 8.':'Reconsider: isotopes have the same proton count. Neutral atoms of the same element also have the same electron count.';}); }
function isotopeMean(percent){return (12*(100-percent)+13*percent)/100;}
function updateIsotope(){const p=number('isotope-abundance');el('isotope-percent').textContent=p;el('isotope-average').textContent=`Aᵣ = [12 × ${100-p} + 13 × ${p}] / 100 = ${isotopeMean(p).toFixed(2)}`;}
if(el('isotope-abundance')) { el('isotope-abundance').addEventListener('input',updateIsotope); }
const cores={He:{'1s':2},Ne:{'1s':2,'2s':2,'2p':6},Ar:{'1s':2,'2s':2,'2p':6,'3s':2,'3p':6}};
const electronCases=[
 {name:'N (7 electrons)',z:7,q:0,config:'1s2 2s2 2p3',note:'The three 2p orbitals each contain one unpaired electron.'},
 {name:'O (8 electrons)',z:8,q:0,config:'1s2 2s2 2p4',note:'One 2p orbital is paired; two contain one electron each.'},
 {name:'Na⁺ (10 electrons)',z:11,q:1,config:'[Ne]',note:'Sodium loses its 3s electron to form Na⁺.'},
 {name:'Cl⁻ (18 electrons)',z:17,q:-1,config:'[Ar]',note:'Chlorine gains one electron to complete its 3p subshell.'},
 {name:'Ca (20 electrons)',z:20,q:0,config:'[Ar] 4s2',note:'For neutral calcium, 4s is occupied before 3d.'},
 {name:'Cr (24 electrons)',z:24,q:0,config:'[Ar] 3d5 4s1',note:'Chromium is an exception to the simple filling pattern: 3d⁵ 4s¹.'},
 {name:'Cu (29 electrons)',z:29,q:0,config:'[Ar] 3d10 4s1',note:'Copper is an exception to the simple filling pattern: 3d¹⁰ 4s¹.'},
 {name:'Fe (26 electrons)',z:26,q:0,config:'[Ar] 3d6 4s2',note:'Neutral iron has six 3d electrons and two 4s electrons.'},
 {name:'Fe²⁺ (24 electrons)',z:26,q:2,config:'[Ar] 3d6',note:'Remove both 4s electrons first. Fe²⁺ is not configured like neutral Cr.'},
 {name:'Fe³⁺ (23 electrons)',z:26,q:3,config:'[Ar] 3d5',note:'Remove the two 4s electrons, then one 3d electron.'}
];
const subshellOrder=['1s','2s','2p','3s','3p','4s','3d'];
function parseConfiguration(text){const supers='⁰¹²³⁴⁵⁶⁷⁸⁹';let s=text.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g,c=>supers.indexOf(c)).replace(/\^/g,'').trim();let values={};const core=s.match(/^\[(He|Ne|Ar)\]/i);if(core){const name=core[1][0].toUpperCase()+core[1].slice(1).toLowerCase();values={...cores[name]};s=s.slice(core[0].length).trim();}if(!s&&!core)return null;for(const token of s?s.split(/\s+/):[]){const match=token.match(/^([1-4][spd])(\d+)$/i);if(!match)return null;const key=match[1].toLowerCase(),n=Number(match[2]);if(!subshellOrder.includes(key)||key in values||n<1||n>({s:2,p:6,d:10}[key[1]]))return null;values[key]=n;}return values;}
function orbitalSpins(n,boxes){return Array.from({length:boxes},(_,i)=>i<n?(i<n-boxes?'↑↓':'↑'):'·');}
if(el('electron-species')) { electronCases.forEach((species,index)=>el('electron-species').add(new Option(species.name,String(index)))); }
function updateElectron(){el('electron-answer').value='';el('electron-feedback').textContent='';el('electron-model').hidden=true;}
if(el('electron-species')) { el('electron-species').addEventListener('change',updateElectron);el('electron-answer').addEventListener('input',()=>el('electron-feedback').textContent=''); }
if(el('electron-check')) { el('electron-check').addEventListener('click',()=>{const species=electronCases[el('electron-species').value],answer=parseConfiguration(el('electron-answer').value),expected=parseConfiguration(species.config);if(!answer){el('electron-feedback').textContent='Use valid subshell tokens separated by spaces, e.g. 1s2 2s2 2p3, or a He, Ne or Ar core. Do not repeat subshells.';return;}const correct=subshellOrder.every(key=>(answer[key]||0)===(expected[key]||0));const count=Object.values(answer).reduce((a,b)=>a+b,0);el('electron-feedback').textContent=correct?'Correct. '+species.note:`Not yet. Your configuration has ${count} electrons; this species needs ${species.z-species.q}. Check subshell occupancies as well as the total. For transition-metal ions, remove 4s before 3d.`;}); }
if(el('electron-reveal')) { el('electron-reveal').addEventListener('click',()=>{const s=electronCases[el('electron-species').value],config=parseConfiguration(s.config);el('electron-model').hidden=false;el('electron-orbitals').replaceChildren();subshellOrder.filter(key=>config[key]).forEach(key=>{const row=document.createElement('div');row.className='orbital-row';row.textContent=key+' ';orbitalSpins(config[key],{s:1,p:3,d:5}[key[1]]).forEach(spin=>{const box=document.createElement('span');box.className='orbital-box';box.textContent=spin;row.append(box);});el('electron-orbitals').append(row);});el('electron-explanation').textContent=s.config+'. '+s.note;}); }
if(el('bonding')) updateBonding(); if(el('nuclear-atom')) {updateAtom();updateIsotope();} if(el('electron-configurations')) updateElectron();

// Activities 7–16. All quantities and challenge examples are original practice data.
const GAS_R = 8.314;
const AVOGADRO = 6.02214076e23;
function massToMoles(mass, molarMass) { return mass / molarMass; }
function particleCounts(n, atoms) { return {molecules:n*AVOGADRO, atoms:n*AVOGADRO*atoms}; }
function idealPressure(n, celsius, volume) { return n*GAS_R*(celsius+273.15)/volume; }
function changedVolume(v, p1, p2, t1, t2) { return v*(p1/p2)*(t2/t1); }
function gasMolarMass(m, p, v, t) { return m*GAS_R*t/(p*v); }
const numericExplorers = {
 'mole-mass': {
  fields:[['mass','Mass / g',11,0,10000],['molar','Molar mass / g mol⁻¹',44,0.001,10000]],
  result:([m,M])=>`n = ${fmt(m)} / ${fmt(M)} = ${fmt(massToMoles(m,M))} mol.`,
  challenge:'A 5.85 g NaCl sample has M = 58.5 g mol⁻¹. Calculate its amount.', unit:'Amount / mol',answer:0.1,
  working:'n = 5.85 / 58.5 = 0.100 mol. Divide mass by molar mass; multiplying gives the wrong units.'
 },
 'mole-entities': {
  fields:[['amount','Amount of molecules / mol',0.5,0,100],['atoms','Atoms per molecule',3,1,100,'1']],
  result:([n,a])=>{const r=particleCounts(n,a);return `${fmt(n)} mol contains ${r.molecules.toExponential(4)} molecules and ${r.atoms.toExponential(4)} atoms (${a} per molecule).`;},
  challenge:'How many oxygen atoms are in 0.250 mol CO₂? Enter a number; scientific notation such as 3.01e23 is accepted.',unit:'Oxygen atoms',answer:0.5*AVOGADRO,
  working:'Each CO₂ molecule contains two O atoms: 0.250 × 2 × Nₐ = 3.01107038 × 10²³ O atoms.'
 },
 'gas-pressure': {
  fields:[['amount','Amount / mol',0.1,0.0001,10],['temperature','Temperature / °C',26.85,-273.14,2000],['volume','Volume / dm³',2,0.001,1000]],
  result:([n,t,v])=>`T = ${fmt(t+273.15)} K. p = nRT/V = ${fmt(idealPressure(n,t,v))} kPa.`,
  challenge:'Find the pressure of 0.200 mol ideal gas in 5.00 dm³ at 300 K. Use R = 8.314.',unit:'Pressure / kPa',answer:99.768,
  working:'p = 0.200 × 8.314 × 300 / 5.00 = 99.768 kPa. Use kelvin, not degrees Celsius.'
 },
 'gas-change': {
  fields:[['volume','Initial volume / dm³',2,0.001,1000],['p1','Initial pressure / kPa',100,0.001,10000],['p2','Final pressure / kPa',200,0.001,10000],['t1','Initial temperature / K',300,0.01,3000],['t2','Final temperature / K',450,0.01,3000]],
  result:([v,p1,p2,t1,t2])=>`V₂ = ${fmt(v)} × (${fmt(p1)}/${fmt(p2)}) × (${fmt(t2)}/${fmt(t1)}) = ${fmt(changedVolume(v,p1,p2,t1,t2))} dm³.`,
  challenge:'A fixed amount occupies 3.00 dm³ at 100 kPa and 300 K. Find its volume at 150 kPa and 300 K.',unit:'Final volume / dm³',answer:2,
  working:'V₂ = 3.00 × (100/150) × (300/300) = 2.00 dm³. At fixed temperature, volume is inversely proportional to pressure.'
 },
 'gas-molar-mass': {
  fields:[['mass','Mass of gas / g',0.88,0.0001,1000],['pressure','Pressure / kPa',100,0.001,10000],['volume','Volume / dm³',0.5,0.001,1000],['temperature','Temperature / K',300,0.01,3000]],
  result:([m,p,v,t])=>`n = pV/RT = ${fmt(p*v/(GAS_R*t))} mol. M = mRT/pV = ${fmt(gasMolarMass(m,p,v,t))} g mol⁻¹.`,
  challenge:'1.20 g ideal gas occupies 1.00 dm³ at 100.0 kPa and 300.0 K. Find M using R = 8.314.',unit:'Molar mass / g mol⁻¹',answer:29.9304,
  working:'M = 1.20 × 8.314 × 300.0 / (100.0 × 1.00) = 29.9304 g mol⁻¹. Volume and pressure units must match R.'
 }
};
function buildNumericExplorer(host) {
 const key=host.dataset.explorer, config=numericExplorers[key];
 const grid=document.createElement('div');grid.className='grid';
 const controls=document.createElement('div'), panel=document.createElement('div');
 const output=document.createElement('p');output.className='result';output.id=key+'-result';output.setAttribute('aria-live','polite');
 const inputs=config.fields.map(([suffix,title,value,min,max,step='any'])=>{
  const label=document.createElement('label');label.textContent=title;
  const input=document.createElement('input');input.id=key+'-'+suffix;input.type='number';input.min=min;input.max=max;input.step=step;input.value=value;
  label.htmlFor=input.id;label.append(input);controls.append(label);return input;
 });
 const reset=document.createElement('button');reset.type='button';reset.textContent='Reset explorer';reset.id=key+'-reset';controls.append(reset);
 const title=document.createElement('h3');title.textContent='Predict, then check';
 const prompt=document.createElement('p');prompt.textContent=config.challenge;
 const label=document.createElement('label');label.textContent=config.unit;
 const answer=document.createElement('input');answer.type='number';answer.step='any';answer.min='0';answer.id=key+'-answer';label.htmlFor=answer.id;label.append(answer);
 const check=document.createElement('button');check.type='button';check.textContent='Check answer';check.id=key+'-check';
 const feedback=document.createElement('p');feedback.id=key+'-feedback';feedback.className='feedback';feedback.setAttribute('role','status');
 panel.append(output,title,prompt,label,check,feedback);grid.append(controls,panel);host.append(grid);
 const update=()=>{const values=inputs.map(input=>number(input.id));output.textContent=values.every(Number.isFinite)?config.result(values):'Enter a valid number within the stated range for every field.';inputs.forEach(input=>{input.setAttribute('aria-invalid',String(!Number.isFinite(number(input.id))));});};
 // Bounds are stated beside each control, not only in browser validation bubbles.
 inputs.forEach(input=>{const note=document.createElement('small');note.textContent=`Range: ${input.min} to ${input.max}${input.step==='1'?'; whole numbers':''}.`;input.after(note);input.addEventListener('input',update);});
 check.addEventListener('click',()=>checkNumeric(answer.id,feedback.id,config.answer,config.working));
 answer.addEventListener('input',()=>feedback.textContent='');
 reset.addEventListener('click',()=>{inputs.forEach((input,i)=>input.value=config.fields[i][2]);answer.value='';feedback.textContent='';update();});
 update();
}
document.querySelectorAll('.numeric-explorer').forEach(buildNumericExplorer);
const empiricalSamples=[
 {symbols:['C','H'],masses:[2.4,0.6],molars:[12,1],ratio:[1,3],formula:'CH₃'},
 {symbols:['Fe','O'],masses:[11.2,4.8],molars:[56,16],ratio:[2,3],formula:'Fe₂O₃'},
 {symbols:['C','H','O'],masses:[3.6,0.6,4.8],molars:[12,1,16],ratio:[1,2,1],formula:'CH₂O'}
];
function empiricalAmounts(sample){return sample.masses.map((mass,i)=>mass/sample.molars[i]);}
function showEmpirical(){const s=empiricalSamples[el('empirical-sample').value];el('empirical-data').textContent=s.symbols.map((symbol,i)=>`${symbol}: ${s.masses[i]} g; M = ${s.molars[i]} g mol⁻¹`).join(' | ')+'. Use these rounded molar masses for this exercise.';el('empirical-answer').value='';el('empirical-feedback').textContent='';el('empirical-working').hidden=true;}
if(el('empirical-sample')) { el('empirical-sample').addEventListener('change',showEmpirical);el('empirical-answer').addEventListener('input',()=>el('empirical-feedback').textContent=''); }
if(el('empirical-check')) { el('empirical-check').addEventListener('click',()=>{const s=empiricalSamples[el('empirical-sample').value],text=el('empirical-answer').value.trim(),values=text.split(':').map(Number);const valid=/^\d+(\s*:\s*\d+)+$/.test(text)&&values.length===s.ratio.length&&values.every(v=>Number.isSafeInteger(v)&&v>0);el('empirical-feedback').textContent=!valid?'Enter positive whole numbers separated by colons, one per element.':values.every((v,i)=>v===s.ratio[i])?'Correct. Empirical formula: '+s.formula+'.':'Not yet. Convert masses to amounts, divide by the smallest, then use the simplest whole-number ratio.';}); }
if(el('empirical-reveal')) { el('empirical-reveal').addEventListener('click',()=>{const s=empiricalSamples[el('empirical-sample').value],amounts=empiricalAmounts(s),smallest=Math.min(...amounts);el('empirical-working').hidden=false;el('empirical-working').textContent=`Amounts / mol: ${amounts.map(fmt).join(' : ')}. Divide by ${fmt(smallest)}: ${amounts.map(n=>fmt(n/smallest)).join(' : ')}. Whole-number ratio ${s.ratio.join(':')}; empirical formula ${s.formula}.`;}); }
function trianglePosition(a,b){const mean=(a+b)/2,difference=Math.abs(a-b);return {mean,difference,x:50+mean*90,y:290-difference*60};}
function updateTriangle(){const a=number('triangle-a'),b=number('triangle-b'),p=trianglePosition(a,b);el('triangle-result').textContent=`χA = ${a.toFixed(1)}, χB = ${b.toFixed(1)}. Mean = ${p.mean.toFixed(2)}; Δχ = ${p.difference.toFixed(2)}.`;el('triangle-dot').setAttribute('cx',p.x);el('triangle-dot').setAttribute('cy',p.y);}
if(el('triangle-a')) { ['triangle-a','triangle-b'].forEach(id=>el(id).addEventListener('input',updateTriangle)); }
function choiceCheck(prefix,expected,reason){el(prefix+'-answer').addEventListener('change',()=>el(prefix+'-feedback').textContent='');el(prefix+'-check').addEventListener('click',()=>{const value=el(prefix+'-answer').value;el(prefix+'-feedback').textContent=!value?'Choose an answer first.':(value===expected?'Correct. ':'Reconsider. ')+reason;});}
if(el('triangle-answer')) { choiceCheck('triangle','metallic','A low mean and small difference lies toward the metallic corner; a large difference moves upward toward the ionic model.'); }
let alloySheared=false;
function updateAlloy(){const kind=el('alloy-kind').value,svg=el('alloy-svg'),ns='http://www.w3.org/2000/svg';svg.replaceChildren();for(let row=0;row<3;row++)for(let col=0;col<6;col++){const guest=kind==='substitutional'&&((row===1&&col===2)||(row===2&&col===4));const circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',55+col*60+(alloySheared&&row===0?(kind==='pure'?25:5):0));circle.setAttribute('cy',40+row*60);circle.setAttribute('r',guest?27:21);circle.setAttribute('fill',guest?'#f2c886':'#8ddbc9');svg.append(circle);}if(kind==='interstitial'){[[145,70],[265,130]].forEach(([x,y])=>{const circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',x);circle.setAttribute('cy',y);circle.setAttribute('r',10);circle.setAttribute('fill','#f2c886');svg.append(circle);});}el('alloy-result').textContent=(kind==='pure'?'Mint circles: equal-sized host atoms.':'Mint: host atoms. Gold: added atoms of a different size.')+(alloySheared?(kind==='pure'?' The upper row slides in this simple model.':' The upper row moves less to illustrate obstruction. Distances are illustrative, not a predicted deformation.'):' Apply shear to compare the schematic response.');}
if(el('alloy-kind')) { el('alloy-kind').addEventListener('change',()=>{alloySheared=false;el('alloy-feedback').textContent='';updateAlloy();});el('alloy-shear').addEventListener('click',()=>{alloySheared=true;updateAlloy();});el('alloy-reset').addEventListener('click',()=>{alloySheared=false;updateAlloy();}); }
if(el('alloy-answer')) { choiceCheck('alloy','obstruct','Distortion can make dislocation motion more difficult, so plastic deformation needs more stress. Metallic bonding remains.'); }
const additionUnits={ethene:'CH₂–CH₂',propene:'CH₂–CH(CH₃)',chloroethene:'CH₂–CHCl'};
function buildAddition(){const count=number('addition-length'),unit=additionUnits[el('addition-monomer').value];el('addition-chain').textContent=`${count} repeat unit${count===1?'':'s'} (terminal groups omitted): …–`+Array(count).fill(unit).join('–')+'–…';}
if(el('addition-monomer')) { el('addition-monomer').addEventListener('change',()=>{el('addition-answer').value='';el('addition-feedback').textContent='';el('addition-chain').hidden=true;});el('addition-answer').addEventListener('change',()=>el('addition-feedback').textContent='');el('addition-length').addEventListener('input',buildAddition); }
if(el('addition-check')) { el('addition-check').addEventListener('click',()=>{const answer=el('addition-answer').value;el('addition-feedback').textContent=!answer?'Choose a repeat unit first.':answer===el('addition-monomer').value?'Correct. The backbone is single-bonded and the original side group is retained.':'Recheck the two backbone carbons and their side groups. The original C=C double bond is not retained in the chain.';});el('addition-reveal').addEventListener('click',()=>{el('addition-chain').hidden=false;buildAddition();}); }
function condensationLinks(molecules){return molecules-1;}
function updateCondensationCount(){const n=number('condensation-count');el('condensation-water').textContent=`${n} monomer molecules joined into one open chain need ${condensationLinks(n)} links and eliminate ${condensationLinks(n)} H₂O molecules. Joining two chains adds one link and eliminates one further water molecule.`;}
const condensationText={ester:'Diol + dicarboxylic acid → polyester. Link: –C(=O)–O–. The acid contributes OH and the alcohol contributes H to the eliminated H₂O.',amide:'Diamine + dicarboxylic acid → polyamide. Link: –C(=O)–NH–. The acid contributes OH and the amine contributes H to the eliminated H₂O.'};
if(el('condensation-kind')) { el('condensation-kind').addEventListener('change',()=>{el('condensation-answer').value='';el('condensation-feedback').textContent='';el('condensation-link').hidden=true;});el('condensation-answer').addEventListener('change',()=>el('condensation-feedback').textContent=''); }
if(el('condensation-check')) { el('condensation-check').addEventListener('click',()=>{const value=el('condensation-answer').value;el('condensation-feedback').textContent=!value?'Choose a linkage first.':(value===el('condensation-kind').value?'Correct. ':'Reconsider the reacting functional groups. ')+condensationText[el('condensation-kind').value];});el('condensation-reveal').addEventListener('click',()=>{el('condensation-link').hidden=false;el('condensation-link').textContent=condensationText[el('condensation-kind').value];});el('condensation-count').addEventListener('input',updateCondensationCount); }
if(el('empirical-formula')) showEmpirical(); if(el('bonding-triangle')) updateTriangle(); if(el('alloy-model')) updateAlloy(); if(el('condensation-polymer')) updateCondensationCount();

