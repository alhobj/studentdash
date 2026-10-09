/* Generic offline graph: explicit hierarchy, directed source references. */
(()=>{'use strict';
const data=JSON.parse(document.querySelector('#graph-data').textContent),all=new Map(data.nodes.map(n=>[n.id,n]));
const svg=document.querySelector('#syllabus-graph'),viewport=document.querySelector('#graph-viewport'),inspector=document.querySelector('#graph-inspector');
const search=document.querySelector('#graph-search'),picker=document.querySelector('#graph-picker'),group=document.querySelector('#graph-group'),detail=document.querySelector('#graph-detail'),near=document.querySelector('#graph-neighbours'),status=document.querySelector('#graph-status');
const colours=['#256b8c','#587636','#8a4e82','#a75335','#346d66','#6857a2','#697783'];
const groups=data.nodes.filter(n=>n.kind==='group');let selected=null,scale=.85,width=1000,height=900,visible=[],positions=new Map();
const html=(tag,text,parent)=>{const e=document.createElement(tag);e.textContent=text;if(parent)parent.append(e);return e;};
const shape=(tag,attrs,parent)=>{const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e;};
groups.forEach(n=>{const o=html('option',n.code+' · '+n.title,group);o.value=n.id;});
if(!data.nodes.some(n=>n.kind==='statement')){detail.checked=false;detail.closest('label').hidden=true;}
const progressLabel=html('label','',document.querySelector('.toolbar')),progressToggle=html('input','',progressLabel);progressToggle.type='checkbox';progressToggle.checked=true;progressLabel.append(' Show practice progress');
const progressColours=['#94a3b8','#dc2626','#d97706','#16803c'];
const progressNames=['Not attempted','Needs another attempt','Completed with help or retry','Correct independently'];
const legend=html('p','Progress rings: grey = not attempted; red = needs another attempt; amber = help or retry; green = independent. Counts describe latest checked answers, not mastery. No ring means no directly mapped questions.',document.querySelector('header'));
const mapped=new Map(data.nodes.map(n=>[n.id,[]]));
for(const q of window.PRACTICE_CATALOG?.questions||[]){const n=data.nodes.find(n=>n.code===q.topic && n.kind==='section');if(!n)continue;let id=n.id;const seen=new Set();while(id && !seen.has(id)){seen.add(id);mapped.get(id)?.push(q.id);id=all.get(id)?.parent;}}
let recentProgress=new Map();
function refreshProgress(){recentProgress=new Map();for(const a of window.StudentPractice?.snapshot().attempts||[]){const old=recentProgress.get(a.question);if(!old||a.at>old.at||(a.at===old.at&&a.id>old.id))recentProgress.set(a.question,a);}}
function progress(id){const counts=[0,0,0,0];for(const qid of new Set(mapped.get(id)||[])){const a=recentProgress.get(qid);counts[!a?0:!a.correct?1:a.assisted?2:3]++;}return counts;}
function progressText(id){const counts=progress(id);return counts.some(Boolean)?counts.map((n,i)=>progressNames[i]+': '+n).join(' · '):'No directly mapped questions. Section-level results are not assigned to individual statements.';}
progressToggle.onchange=()=>{legend.hidden=!progressToggle.checked;draw();inspect();};
function neighbours(){const ids=new Set(selected?[selected]:[]);data.edges.forEach(e=>{if(e.source===selected)ids.add(e.target);if(e.target===selected)ids.add(e.source);});return ids;}
function refreshPicker(){const query=search.value.trim().toLowerCase();picker.replaceChildren();const o=html('option','Choose a syllabus part',picker);o.value='';data.nodes.filter(n=>(!group.value||n.group===group.value)&&(n.code+' '+n.title).toLowerCase().includes(query)).forEach(n=>{const o=html('option',n.code+' · '+n.title,picker);o.value=n.id;});picker.value=selected||'';}
function zoom(value){scale=Math.max(.2,Math.min(2,value));svg.style.width=width*scale+'px';svg.style.height=height*scale+'px';}
function draw(){
 refreshProgress();
 const connected=neighbours();visible=data.nodes.filter(n=>(detail.checked||n.kind!=='statement')&&(!group.value||n.group===group.value)&&(!near.checked||!selected||connected.has(n.id)));
 positions=new Map();let column=0,maxY=0;const step=detail.checked?370:160,centre=detail.checked?120:40;
 for(const g of [...groups,{id:'other',title:'Other guide references'}]){
  const rows=visible.filter(n=>n.group===g.id);if(!rows.length)continue;const x=50+column*step;let y=75;
  const heading=rows.find(n=>n.kind==='group');if(heading){positions.set(heading.id,{x:x+centre,y});y+=95;}
  for(const section of rows.filter(n=>n.kind==='section')){
   positions.set(section.id,{x:x+centre,y});y+=75;const children=rows.filter(n=>n.parent===section.id);
   children.forEach((n,i)=>positions.set(n.id,{x:x+(i%4)*80,y:y+Math.floor(i/4)*80}));
   y+=Math.ceil(children.length/4)*80+(detail.checked?40:10);
  }
  const remaining=rows.filter(n=>!positions.has(n.id));remaining.forEach((n,i)=>positions.set(n.id,{x:x+(i%(detail.checked?4:2))*75,y:y+Math.floor(i/(detail.checked?4:2))*80}));
  y+=Math.ceil(remaining.length/(detail.checked?4:2))*80;maxY=Math.max(maxY,y);column++;
 }
 width=Math.max(420,column*step+60);height=Math.max(350,maxY+60);svg.replaceChildren();svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
 const defs=shape('defs',{},svg),marker=shape('marker',{id:'graph-arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'},defs);shape('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#a86524'},marker);
 let edgeCount=0;
 for(const e of data.edges){const a=positions.get(e.source),b=positions.get(e.target);if(!a||!b)continue;edgeCount++;const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1;const active=selected&&(e.source===selected||e.target===selected);const attrs={x1:a.x+dx/len*31,y1:a.y+dy/len*31,x2:b.x-dx/len*34,y2:b.y-dy/len*34,class:'edge '+e.kind+(selected?(active?' active':' dim'):'')};if(e.kind==='reference')attrs['marker-end']='url(#graph-arrow)';shape('line',attrs,svg);}
 for(const n of visible){const p=positions.get(n.id);if(!p)continue;const idx=groups.findIndex(g=>g.id===n.group),g=shape('g',{transform:`translate(${p.x},${p.y})`,class:'node'+(selected===n.id?' selected':selected&&!connected.has(n.id)?' dim':''),role:'button',tabindex:0,'aria-label':n.code+' · '+n.title,'aria-pressed':String(selected===n.id),'data-node':n.id},svg);shape('circle',{r:n.kind==='group'?35:31,fill:colours[idx<0?6:idx%6]},g);if(progressToggle.checked){const counts=progress(n.id),total=counts.reduce((a,b)=>a+b,0),r=n.kind==='group'?41:37,length=2*Math.PI*r;let offset=0;if(total)counts.forEach((count,i)=>{if(count){shape('circle',{r,fill:'none',style:`stroke:${progressColours[i]};stroke-width:5;pointer-events:none`,'stroke-dasharray':`${length*count/total} ${length-length*count/total}`,'stroke-dashoffset':-offset,transform:'rotate(-90)','aria-hidden':'true'},g);offset+=length*count/total;}});g.setAttribute('aria-label',n.code+' · '+n.title+' · '+progressText(n.id));}const t=shape('text',n.code.length>8?{style:'font-size:9px'}:{},g);t.textContent=n.code.length>12?n.code.slice(0,11)+'…':n.code;shape('title',{},g).textContent=n.code+' · '+n.title;g.addEventListener('click',()=>choose(n.id));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(n.id);}});}
 zoom(scale);status.textContent=`${visible.length} circles · ${edgeCount} connections shown. Solid arrows: guide references. Dashed: part of a topic.`;
}
function choose(id,centre=false){selected=id;if(all.get(id)?.kind==='statement')detail.checked=true;location.hash=encodeURIComponent(id);draw();refreshPicker();inspect();const node=[...svg.querySelectorAll('.node')].find(e=>e.dataset.node===id);if(centre)node?.scrollIntoView({block:'center',inline:'center'});node?.focus({preventScroll:true});}
function inspect(){inspector.replaceChildren();const n=all.get(selected);if(!n){html('h2','Choose a syllabus part',inspector);html('p','Select a circle to highlight its incoming and outgoing connections.',inspector);return;}html('h2',n.code,inspector);if(progressToggle.checked)html('p',progressText(n.id),inspector);html('p',n.title,inspector);if(n.level)html('p',n.level,inspector);for(const [label,url]of [['Open related practice',n.href],['Read the guide',n.guide]]){const p=html('p','',inspector),a=html('a',label,p);a.href=url;}
 for(const [name,edges]of [['Guide references from this part',data.edges.filter(e=>e.kind==='reference'&&e.source===n.id)],['Referenced by',data.edges.filter(e=>e.kind==='reference'&&e.target===n.id)],['Syllabus hierarchy',data.edges.filter(e=>e.kind==='hierarchy'&&(e.source===n.id||e.target===n.id))]]){
 html('h3',name,inspector);if(!edges.length){html('p','None recorded at this level.',inspector);continue;}const ul=html('ul','',inspector);for(const edge of edges){const id=edge.source===n.id?edge.target:edge.source,other=all.get(id),li=html('li','',ul),b=html('button',other.code+' · '+other.title,li);b.type='button';b.addEventListener('click',()=>{group.value='';choose(id,true);});if(edge.qualifier)html('span',' '+edge.qualifier,li);for(const page of edge.pages||[]){const a=html('a',' PDF p. '+page,li);a.href=data.guide+'#page='+page;}}}
}
search.addEventListener('input',()=>{refreshPicker();status.textContent=`${picker.options.length-1} matching parts. Choose one from the list.`;});picker.addEventListener('change',()=>{if(picker.value)choose(picker.value,true);});group.addEventListener('change',()=>{refreshPicker();draw();});detail.addEventListener('change',draw);near.addEventListener('change',draw);
document.querySelector('#graph-in').onclick=()=>zoom(scale*1.25);document.querySelector('#graph-out').onclick=()=>zoom(scale/1.25);document.querySelector('#graph-fit').onclick=()=>{zoom(Math.min(viewport.clientWidth/width,viewport.clientHeight/height));viewport.scrollTo(0,0);};document.querySelector('#graph-clear').onclick=()=>{selected=null;near.checked=false;search.value='';history.replaceState(null,'',location.pathname+location.search);refreshPicker();draw();inspect();};
window.addEventListener('studentdash-progress',()=>{draw();if(selected)inspect();});
refreshPicker();draw();let hash;try{hash=decodeURIComponent(location.hash.slice(1));}catch{}if(all.has(hash))choose(hash,true);
})();
