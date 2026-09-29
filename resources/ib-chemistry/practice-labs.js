/* Offline, deliberately bounded chemistry models. No answers are saved. */
(() => {
 'use strict';
 const ns='http://www.w3.org/2000/svg';
 const f=n=>Number(n.toPrecision(5)).toString();
 function make(tag,text,cls){const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;}
 function svg(tag,attrs,text){const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text)e.textContent=text;return e;}
 function chart(host,series,xmax,ymin,ymax,xlabel,ylabel){
  const picture=svg('svg',{viewBox:'0 0 600 300',role:'img','aria-label':`${ylabel} against ${xlabel}`,class:'lab-chart'});
  const x=n=>65+n/xmax*510,y=n=>250-(n-ymin)/(ymax-ymin)*215;
  picture.append(svg('path',{d:'M65 30 V250 H580',fill:'none',stroke:'#b2c0d5'}));
  [0,.5,1].forEach(t=>{picture.append(svg('text',{x:55,y:y(ymin+t*(ymax-ymin))+5,'text-anchor':'end'},f(ymin+t*(ymax-ymin))));picture.append(svg('text',{x:x(t*xmax),y:272,'text-anchor':'middle'},f(t*xmax)));});
  picture.append(svg('text',{x:325,y:295,'text-anchor':'middle'},xlabel),svg('text',{x:65,y:18},ylabel));
  series.forEach(s=>{picture.append(svg('polyline',{points:s.points.map(([a,b])=>`${x(a)},${y(b)}`).join(' '),fill:'none',stroke:s.color||'#8ddbc9','stroke-width':3,'stroke-dasharray':s.dash||'none'}));s.points.forEach(([a,b])=>picture.append(svg('circle',{cx:x(a),cy:y(b),r:3,fill:s.color||'#8ddbc9'})));});
  host.replaceChildren(picture);
 }
 function setup(section){
  const host=section.querySelector('.lab-host'),prefix=section.id;
  const controls=make('div',null,'lab-controls'),visual=make('div',null,'lab-visual'),result=make('p',null,'result'),status=make('p',null,'feedback');
  result.setAttribute('aria-live','polite');status.setAttribute('role','status');
  host.append(controls,visual,result,status);
  return {host,controls,visual,result,status,
   button(text,fn,id){const b=make('button',text);b.type='button';if(id)b.id=prefix+'-'+id;b.addEventListener('click',fn);controls.append(b);return b;},
   slider(key,label,min,max,step,value,fn){const wrap=make('div',null,'lab-control'),l=make('label'),out=make('output'),input=make('input');input.type='range';Object.assign(input,{min,max,step,value,id:prefix+'-'+key});l.htmlFor=input.id;l.append(document.createTextNode(label+': '),out);out.value=value;input.addEventListener('input',()=>{out.value=input.value;fn(Number(input.value));});wrap.append(l,input);controls.append(wrap);return input;},
   select(key,label,options,fn){const l=make('label',label),s=make('select');s.id=prefix+'-'+key;l.htmlFor=s.id;options.forEach(([value,text])=>s.add(new Option(text,value)));s.addEventListener('change',()=>fn(s.value));controls.append(l,s);return s;}
  };
 }
 const builders={
  'electron-jumps'(ui){
   const energies=[0,2,3.5,4.2];let level=0,photon=null;
   const buttons=energies.map((energy,i)=>ui.button(`Move electron to level ${i+1}`,()=>{
    const delta=energy-energies[level];photon={delta,from:level,to:i};level=i;draw();
   },'level-'+i));
   ui.button('Reset atom',()=>{level=0;photon=null;draw();},'reset');
   function draw(){const picture=svg('svg',{viewBox:'0 0 600 330',role:'img','aria-label':`Electron in level ${level+1}. Schematic energy levels in electronvolts.`,class:'lab-chart'});
    const y=e=>285-e*55;
    energies.forEach((energy,i)=>{picture.append(svg('line',{x1:95,y1:y(energy),x2:490,y2:y(energy),stroke:'#b2c0d5','stroke-width':2}),svg('text',{x:10,y:y(energy)+5},`${energy} eV`),svg('text',{x:500,y:y(energy)+5},`Level ${i+1}`));buttons[i].disabled=i===level;});
    if(photon)picture.append(svg('line',{x1:330,y1:y(energies[photon.from]),x2:330,y2:y(energies[photon.to]),stroke:'#f2c886','stroke-width':5,'stroke-dasharray':'6 4'}));
    picture.append(svg('circle',{cx:330,cy:y(energies[level]),r:10,fill:'#8ddbc9'}));ui.visual.replaceChildren(picture);
    ui.result.textContent=`Electron energy = ${energies[level]} eV. `+(photon?`Photon ${photon.delta>0?'absorbed':'emitted'}: ${f(Math.abs(photon.delta))} eV. Wavelength ≈ ${f(1240/Math.abs(photon.delta))} nm.`:'Choose a higher level to supply a photon, then a lower level to emit one.');
    ui.status.textContent=photon?(photon.delta>0?'Moving upwards requires an energy input.':'Moving downwards releases the energy difference as a photon.'):'These are fictional bound energy levels, not the hydrogen spectrum.';
   }draw();
  },
  'gas-piston'(ui){
   let volume=2,temperature=300;const n=.1,R=8.314;
   const v=ui.slider('volume','Piston volume / dm³',1,5,.1,2,value=>{volume=value;draw();});
   const t=ui.slider('temperature','Temperature / K',200,600,10,300,value=>{temperature=value;draw();});
   ui.button('Compress to half volume',()=>{v.value=Math.max(1,volume/2);v.dispatchEvent(new Event('input'));},'compress');
   ui.button('Reset gas',()=>{v.value=2;t.value=300;[v,t].forEach(e=>e.dispatchEvent(new Event('input')));},'reset');
   function draw(){const p=n*R*temperature/volume,width=volume/5*450;
    const picture=svg('svg',{viewBox:'0 0 600 280',role:'img','aria-label':`Gas piston: volume ${volume} cubic decimetres, pressure ${f(p)} kilopascals.`,class:'lab-chart'});
    picture.append(svg('rect',{x:50,y:35,width:450,height:190,fill:'#111a2b',stroke:'#b2c0d5','stroke-width':2}),svg('rect',{x:50,y:35,width,height:190,fill:'#203842'}));
    for(let i=0;i<24;i++){const x=60+(i%6+.5)*(width-20)/6,y=50+(Math.floor(i/6)+.5)*40;picture.append(svg('circle',{cx:x,cy:y,r:4,fill:'#8ddbc9'}));}
    picture.append(svg('line',{x1:50+width,y1:35,x2:50+width,y2:225,stroke:'#f2c886','stroke-width':9}),svg('line',{x1:50+width,y1:130,x2:560,y2:130,stroke:'#f2c886','stroke-width':6}),svg('text',{x:50,y:260},`Fixed amount: ${n} mol · particles shown schematically`));ui.visual.replaceChildren(picture);
    ui.result.textContent=`p = nRT/V = ${f(p)} kPa. pV = ${f(p*volume)} kPa dm³. Temperature = ${temperature} K; volume = ${volume} dm³.`;
    ui.status.textContent='At fixed temperature, halving volume doubles pressure. The temperature control represents heat exchange with a reservoir; compression here is not adiabatic.';
   }draw();
  },
  'balance-workbench'(ui){
   const cases={water:{names:['H₂','O₂','H₂O'],atoms:[{H:2},{O:2},{H:2,O:1}],side:[0,0,1]},ammonia:{names:['N₂','H₂','NH₃'],atoms:[{N:2},{H:2},{N:1,H:3}],side:[0,0,1]},combustion:{names:['CH₄','O₂','CO₂','H₂O'],atoms:[{C:1,H:4},{O:2},{C:1,O:2},{H:2,O:1}],side:[0,0,1,1]}};
   let kind='water',coefficients=[1,1,1];const counters=make('div',null,'pair-grid');ui.controls.append(counters);
   ui.select('reaction','Reaction',[['water','Hydrogen + oxygen'],['ammonia','Nitrogen + hydrogen'],['combustion','Complete methane combustion']],value=>{kind=value;coefficients=cases[kind].names.map(()=>1);build();});
   ui.button('Reset coefficients',()=>{coefficients.fill(1);build();},'reset');
   function build(){counters.replaceChildren();cases[kind].names.forEach((name,i)=>{const card=make('div'),label=make('p',name),minus=make('button','−'),plus=make('button','+'),out=make('output');out.id='balance-workbench-count-'+i;
     [minus,plus].forEach(b=>b.type='button');minus.setAttribute('aria-label','Decrease '+name);plus.setAttribute('aria-label','Increase '+name);minus.addEventListener('click',()=>{coefficients[i]--;draw();});plus.addEventListener('click',()=>{coefficients[i]++;draw();});card.append(label,minus,out,plus);counters.append(card);});draw();}
   function draw(){const c=cases[kind],elements=[...new Set(c.atoms.flatMap(a=>Object.keys(a)))],totals=[{},{}];
    c.atoms.forEach((atoms,i)=>Object.entries(atoms).forEach(([element,count])=>{totals[c.side[i]][element]=(totals[c.side[i]][element]||0)+coefficients[i]*count;}));
    [...counters.children].forEach((card,i)=>{card.querySelector('output').value=coefficients[i];const [minus,plus]=card.querySelectorAll('button');minus.disabled=coefficients[i]<=1;plus.disabled=coefficients[i]>=12;});
    const table=make('table');table.className='balance-table';const header=make('tr');['Element','Reactant atoms','Product atoms'].forEach(text=>header.append(make('th',text)));table.append(header);
    elements.forEach(element=>{const row=make('tr');[element,totals[0][element]||0,totals[1][element]||0].forEach(text=>row.append(make('td',String(text))));table.append(row);});ui.visual.replaceChildren(table);
    ui.result.textContent=[0,1].map(side=>c.names.map((name,i)=>c.side[i]===side?`${coefficients[i]}${name}`:null).filter(Boolean).join(' + ')).join(' → ');
    const balanced=elements.every(e=>(totals[0][e]||0)===(totals[1][e]||0)),gcd=(a,b)=>b?gcd(b,a%b):a;
    ui.status.textContent=balanced?(coefficients.reduce(gcd)===1?'Balanced in the simplest whole-number ratio.':'Balanced, but divide every coefficient by their common factor.'):'Not balanced yet. Change coefficients until both columns match for every element.';
   }build();
  },
  'ion-builder'(ui){
   const cases={NaCl:{ions:['Na⁺','Cl⁻'],charges:[1,-1],symbols:['Na','Cl']},MgCl2:{ions:['Mg²⁺','Cl⁻'],charges:[2,-1],symbols:['Mg','Cl']},Al2O3:{ions:['Al³⁺','O²⁻'],charges:[3,-2],symbols:['Al','O']}};
   let counts=[0,0],kind='NaCl';
   const labels=make('div',null,'lab-atoms');ui.visual.append(labels);
   ui.select('salt','Choose ions',Object.keys(cases).map(k=>[k,cases[k].ions.join(' and ')]),v=>{kind=v;counts=[0,0];draw();});
   const buttons=[];
   [0,1].forEach(i=>{buttons.push(ui.button('Add ion',()=>{counts[i]++;draw();},'add-'+i));buttons.push(ui.button('Remove ion',()=>{counts[i]--;draw();},'remove-'+i));});
   ui.button('Reset ions',()=>{counts=[0,0];draw();},'reset');
   function gcd(a,b){return b?gcd(b,a%b):a;}
   function draw(){const c=cases[kind],charge=counts.reduce((sum,n,i)=>sum+n*c.charges[i],0);labels.replaceChildren();counts.forEach((n,i)=>{for(let j=0;j<n;j++)labels.append(make('span',c.ions[i],'lab-ion '+(i?'negative':'')));buttons[2*i].textContent='Add '+c.ions[i];buttons[2*i+1].textContent='Remove '+c.ions[i];buttons[2*i].disabled=n>=12;buttons[2*i+1].disabled=n===0;});
    const formula=counts.map((n,i)=>c.symbols[i]+(n===1?'':n)).join('');
    const neutral=counts.every(n=>n>0)&&charge===0;
    ui.result.textContent=`Counts ${counts.join(' : ')}. Net charge = ${charge>0?'+':''}${charge}.`;
    ui.status.textContent=neutral?(gcd(...counts)===1?`Neutral and simplest: ${formula}. Challenge complete.`:'Neutral, but not the simplest ratio. Remove ions in a balanced group.'):'Add or remove ions to make a non-empty, neutral formula ratio.';
   }draw();
  },
  'carbon-builder'(ui){
   let bonds=new Set(),selected=null;const found=new Set(),positions=[[130,80],[450,80],[130,235],[450,235]];
   const board=make('div',null,'carbon-board'),picture=svg('svg',{viewBox:'0 0 580 315','aria-hidden':'true'});board.append(picture);ui.visual.append(board);
   const atoms=positions.map(([x,y],i)=>{const b=make('button',`C${i+1}`,'carbon-atom');b.type='button';b.style.left=x/580*100+'%';b.style.top=y/315*100+'%';b.setAttribute('aria-label',`Select carbon ${i+1}`);b.addEventListener('click',()=>{if(selected===null){selected=i;draw();return;}if(selected!==i){const edge=[selected,i].sort().join('-');if(bonds.has(edge))bonds.delete(edge);else bonds.add(edge);}selected=null;draw();});board.append(b);return b;});
   ui.button('Clear bonds',()=>{bonds.clear();selected=null;draw();},'clear');ui.button('Reset discoveries',()=>{found.clear();bonds.clear();selected=null;draw();},'reset');
   function draw(){const degrees=[0,0,0,0],adj=[[],[],[],[]];picture.replaceChildren();for(const edge of bonds){const [a,b]=edge.split('-').map(Number);degrees[a]++;degrees[b]++;adj[a].push(b);adj[b].push(a);picture.append(svg('line',{x1:positions[a][0],y1:positions[a][1],x2:positions[b][0],y2:positions[b][1],stroke:'#8ddbc9','stroke-width':5}));}
    atoms.forEach((b,i)=>{b.textContent=`C${i+1} · H${4-degrees[i]}`;b.setAttribute('aria-pressed',String(selected===i));});
    const visited=new Set();function visit(i){if(visited.has(i))return;visited.add(i);adj[i].forEach(visit);}visit(0);
    const h=16-2*bonds.size,connected=visited.size===4;let name='';if(connected&&bonds.size===3){name=Math.max(...degrees)===3?'2-methylpropane':'butane';found.add(name);}
    ui.result.textContent=`${bonds.size} C–C bonds; total composition C₄H${h}. ${connected?'All carbons connected.':'Separate fragments: connect all four carbons.'} ${name?'Built '+name+'.':''}`;
    ui.status.textContent=(selected!==null?`Carbon ${selected+1} selected. Choose another carbon to toggle a bond. `:'')+(connected&&bonds.size>3?'This skeleton contains rings and is not C₄H₁₀. Remove a bond. ': '')+`Chain isomers discovered: ${found.size}/2${found.size?' ('+[...found].join(', ')+')':''}.`;
   }draw();
  },
  'electron-pair-builder'(ui){
   const cases={methane:{label:'CH₄',bonds:4,shape:'tetrahedral',angle:'109.5°'},ammonia:{label:'NH₃',bonds:3,shape:'trigonal pyramidal',angle:'about 107°'},water:{label:'H₂O',bonds:2,shape:'bent',angle:'about 104.5°'}};
   let kind='methane',pairs=[false,false,false,false];const grid=make('div',null,'pair-grid');ui.visual.append(grid);
   ui.select('molecule','Molecule',Object.entries(cases).map(([k,c])=>[k,c.label]),v=>{kind=v;pairs.fill(false);draw();});
   const slots=pairs.map((_,i)=>{const b=make('button');b.type='button';b.addEventListener('click',()=>{pairs[i]=!pairs[i];draw();});grid.append(b);return b;});
   ui.button('Reset domains',()=>{pairs.fill(false);draw();},'reset');
   function draw(){const n=pairs.filter(Boolean).length,c=cases[kind];slots.forEach((b,i)=>{b.textContent=`Domain ${i+1}: ${pairs[i]?'bond → H':'lone pair ••'}`;b.setAttribute('aria-pressed',String(pairs[i]));});ui.result.textContent=`${n} bonding pairs and ${4-n} lone pairs around the central atom. Four domains in total.`;ui.status.textContent=n===c.bonds?`${c.label} complete: ${c.shape}; typical bond angle ${c.angle}. The electron-domain arrangement remains tetrahedral.`:`For ${c.label}, build ${c.bonds} bonding pairs and ${4-c.bonds} lone pairs. This current arrangement is a draft, not a model of ${c.label}.`;}
   draw();
  },
  'isotope-mixer'(ui){
   let percent=25;const atoms=make('div',null,'lab-atoms');ui.visual.append(atoms);
   const slider=ui.slider('heavy','Heavier isotope / %',0,100,1,25,v=>{percent=v;ui.status.textContent='';draw();});
   ui.button('Check target 21.20',()=>{ui.status.textContent=percent===60?'Target reached: 60% heavy and 40% light.':'Not at the target yet. More heavy isotope raises the mean.';},'check');
   ui.button('Reset mixture',()=>{slider.value=25;slider.dispatchEvent(new Event('input'));},'reset');
   function draw(){atoms.replaceChildren();const heavy=Math.round(percent/5);for(let i=0;i<20;i++)atoms.append(make('span',i<heavy?'22':'20','lab-ion '+(i<heavy?'negative':'')));ui.result.textContent=`Light isotope: ${100-percent}%. Heavy isotope: ${percent}%. Relative atomic mass = ${f(20+2*percent/100)} (no unit). Each displayed atom represents about 5%.`;}
   draw();
  },
  'calorimeter-bench'(ui){
   let mass=100,retained=100,q=0;const meter=make('div',null,'lab-thermometer'),fill=make('div');meter.append(fill);ui.visual.append(meter);
   function clear(){q=0;ui.status.textContent='New setup: temperature restored to 20 °C.';draw();}
   ui.slider('mass','Water mass / g',50,250,10,100,v=>{mass=v;clear();});ui.slider('retained','Heat retained / %',20,100,5,100,v=>{retained=v;clear();});
   const heat=ui.button('Supply 1.00 kJ',()=>{q+=1000;draw();},'heat');ui.button('Reset experiment',clear,'reset');
   function draw(){const rise=q*retained/100/(mass*4.18),t=20+rise;fill.style.height=(t-20)/65*100+'%';heat.disabled=q>=12000;ui.result.textContent=`Supplied energy = ${f(q/1000)} kJ; retained = ${f(q*retained/100000)} kJ. Temperature = ${t.toFixed(2)} °C; rise = ${rise.toFixed(2)} K.`;ui.status.textContent=q>=12000?'Run limit reached (12 kJ). Reset to try a different setup.':'The thermometer scale spans 20–85 °C. Predict the next temperature before adding heat.';}
   draw();
  },
  'energy-profile-lab'(ui){
   let dh=-40,barrier=100,catalyst=false;
   const enthalpy=ui.slider('enthalpy','Product energy relative to reactants / kJ mol⁻¹',-80,80,5,-40,v=>{dh=v;draw();});
   const activation=ui.slider('barrier','Uncatalysed forward barrier / kJ mol⁻¹',90,180,5,100,v=>{barrier=v;draw();});
   const toggle=ui.button('Add catalyst',()=>{catalyst=!catalyst;draw();},'catalyst');
   ui.button('Reset profile',()=>{catalyst=false;enthalpy.value=-40;activation.value=100;[enthalpy,activation].forEach(input=>input.dispatchEvent(new Event('input')));},'reset');
   function draw(){const reduction=Math.min(40,(barrier-Math.max(0,dh))/2),peak=barrier-(catalyst?reduction:0);
    const series=[{points:[[0,0],[.2,0],[.5,barrier],[.8,dh],[1,dh]],color:'#b2c0d5',dash:'7 5'}];if(catalyst)series.push({points:[[0,0],[.2,0],[.5,peak],[.8,dh],[1,dh]]});chart(ui.visual,series,1,-90,190,'Reaction coordinate (not time)','Relative energy / kJ mol⁻¹');
    toggle.textContent=catalyst?'Remove catalyst':'Add catalyst';toggle.setAttribute('aria-pressed',String(catalyst));ui.result.textContent=`ΔH = ${dh} kJ mol⁻¹ (${dh<0?'exothermic':dh>0?'endothermic':'zero enthalpy change'}). Forward Ea = ${f(peak)}; reverse Ea = ${f(peak-dh)} kJ mol⁻¹.`;ui.status.textContent=catalyst?'Mint: catalysed path. Dashed: uncatalysed path. Both have identical endpoints.':'Dashed: uncatalysed path. The peak is always above both endpoints; lines are schematic.';
   }draw();
  },
  'kinetics-bench'(ui){
   let initial=1,k=.1,t=0,points=[[0,1]],saved=null;
   function restart(){t=0;points=[[0,initial]];draw();}
   ui.slider('initial','Initial [A] / mol dm⁻³',.2,2,.1,1,v=>{initial=v;restart();});ui.slider('rate','Rate constant k / s⁻¹',.02,.3,.01,.1,v=>{k=v;restart();});
   const step=ui.button('Advance 5 seconds',()=>{t+=5;points.push([t,initial*Math.exp(-k*t)]);draw();},'step');
   ui.button('Save trace for comparison',()=>{saved={points:points.map(p=>[...p]),initial,k};draw();},'save');ui.button('Restart current setup',restart,'reset');ui.button('Clear saved trace',()=>{saved=null;draw();},'clear');
   function draw(){const a=initial*Math.exp(-k*t),series=[{points}];if(saved)series.push({points:saved.points,color:'#f2c886',dash:'5 4'});chart(ui.visual,series,60,0,2,'Time / s','[A] / mol dm⁻³');step.disabled=t>=60;ui.result.textContent=`Time ${t} s. [A] = ${f(a)}, [B] = ${f(initial-a)} mol dm⁻³. Current disappearance rate = ${f(k*a)} mol dm⁻³ s⁻¹. Half-life = ${f(Math.log(2)/k)} s.`;ui.status.textContent=saved?`Mint: current run. Gold dashed: saved [A]₀ = ${saved.initial}, k = ${saved.k}.`:'Advance time to collect points; save a run before changing the setup. Lines connect sampled points.';}
   draw();
  },
  'equilibrium-bench'(ui){
   let a=1,b=0,t=0,speed=1;const bars=make('div');ui.visual.append(bars);
   ui.slider('catalyst','Rate multiplier (catalyst)',1,5,1,1,v=>{speed=v;draw();});
   ui.button('Advance 5 seconds',()=>{const total=a+b,target=total*.8;b=target+(b-target)*Math.exp(-.25*speed*5);a=total-b;t+=5;draw();},'step');
   const addA=ui.button('Add 0.50 mol dm⁻³ A',()=>{a+=.5;draw();},'add-a'),addB=ui.button('Add 0.50 mol dm⁻³ B',()=>{b+=.5;draw();},'add-b');
   ui.button('Reset mixture',()=>{a=1;b=0;t=0;draw();},'reset');
   function draw(){bars.replaceChildren();[['A',a],['B',b]].forEach(([label,n])=>{const row=make('div',`${label}: ${f(n)} mol dm⁻³`,'bar-row'),bar=make('div',null,'bar'),span=make('span');span.style.width=n/10*100+'%';bar.append(span);row.append(bar);bars.append(row);});const forward=.2*speed*a,reverse=.05*speed*b;addA.disabled=addB.disabled=a+b>=10-1e-9;ui.result.textContent=`Time ${t} s. Q = ${f(b/a)}; Kc = 4. Forward rate = ${f(forward)}, reverse rate = ${f(reverse)} mol dm⁻³ s⁻¹. Total concentration = ${f(a+b)} mol dm⁻³.`;ui.status.textContent=Math.abs(forward-reverse)<1e-5?'Approximately at equilibrium: both reactions continue at equal, nonzero rates.':`${forward>reverse?'Net forward change: B increases.':'Net reverse change: A increases.'} Bars share a fixed 0–10 mol dm⁻³ scale. Additions assume negligible volume change.`;}
   draw();
  },
  'titration-bench'(ui){
   let volume=0,history=[0];
   function ph(v){const excess=(.1*.02-.1*v/1000)/(.02+v/1000),root=Math.sqrt(excess*excess+4e-14),h=excess>=0?(excess+root)/2:2e-14/(root-excess);return -Math.log10(h);}
   const additions=[.1,1,5].map(amount=>ui.button(`Add ${amount.toFixed(1)} cm³`,()=>{volume=Math.min(40,Math.round((volume+amount)*10)/10);history.push(volume);draw();},'add-'+String(amount).replace('.','-')));
   const undo=ui.button('Undo last addition',()=>{history.pop();volume=history[history.length-1];draw();},'undo');
   ui.button('Check equivalence',()=>{ui.status.textContent=Math.abs(volume-20)<=.100001?'Within 0.1 cm³ of equivalence. Exact equivalence is 20.0 cm³, with pH 7 in this model.':volume<20?'Acid is still in excess. Add more base; use smaller additions near equivalence.':'Base is in excess. Undo the last addition to approach more carefully.';},'check');
   ui.button('Reset titration',()=>{volume=0;history=[0];draw();},'reset');
   function draw(){chart(ui.visual,[{points:history.map(v=>[v,ph(v)])}],40,0,14,'NaOH added / cm³','pH');const value=ph(volume);ui.result.textContent=`Burette delivered ${volume.toFixed(1)} cm³. Total volume = ${(20+volume).toFixed(1)} cm³. pH = ${value.toFixed(2)}. ${volume<20?'Excess HCl':volume>20?'Excess NaOH':'Equivalence: acid and base amounts match'}.`;ui.result.style.borderLeftColor=`hsl(${value/14*260} 65% 70%)`;ui.status.textContent='The trace joins your measured points; coarse steps can miss the steep part of the curve.';undo.disabled=history.length===1;additions.forEach(b=>b.disabled=volume>=40);}
   draw();
  }
 };
 document.querySelectorAll('[data-lab]').forEach(section=>builders[section.dataset.lab](setup(section)));
})();
