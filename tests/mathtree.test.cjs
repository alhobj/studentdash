const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={window:{}};vm.runInNewContext(fs.readFileSync('resources/ib-math-ai-sl/mathtree-layout.js','utf8'),ctx);const {buildLayout,routeEdges,segmentHitsRect}=ctx.window.MathtreeLayout;
const data=JSON.parse(fs.readFileSync('resources/ib-math-ai-sl/syllabus-graph.json'));
const nodes=data.nodes.map(n=>({...n,group:0})),edges=data.edges.map((e,i)=>({...e,id:'e'+i,type:e.kind==='prerequisite'?'prerequisite':'related'}));
for(const mode of ['top','bottom'])test(mode+' sort preserves prerequisite order and routes around every card',()=>{
 const layout=buildLayout(nodes,edges,mode),routes=routeEdges(layout,edges);
 for(const e of edges){if(e.type==='prerequisite')assert.ok(layout.positions[e.source].y<layout.positions[e.target].y);const pts=routes[e.id].points;
 for(let i=1;i<pts.length;i++)for(const r of layout.obstacles)if(r.id!==e.source&&r.id!==e.target)assert.ok(!segmentHitsRect(pts[i-1],pts[i],r));}
 if(mode==='bottom'){const sources=new Set(edges.filter(e=>e.type==='prerequisite').map(e=>e.source));assert.equal(new Set(nodes.filter(n=>!sources.has(n.id)).map(n=>layout.positions[n.id].y)).size,1);}
});
test('authored prerequisites, guide references and hierarchy remain distinct',()=>{
 assert.equal(data.nodes.filter(n=>n.kind==='section').length,39);assert.equal(data.nodes.filter(n=>n.kind==='skill').length,12);
 assert.ok(edges.some(e=>e.type==='prerequisite'));assert.ok(data.edges.some(e=>e.kind==='reference'));
 assert.equal(new Set(data.nodes.map(n=>n.id)).size,data.nodes.length);
});
test('controls combine topic highlights, distance sliders, sorting and session marks',()=>{
 class El{constructor(tag='div'){this.tag=tag;this.children=[];this.attrs={};this.dataset={};this.style={};this.events={};this.value='';this.checked=false;this.clientWidth=1000;this.clientHeight=700;}
 append(...els){this.children.push(...els.filter(e=>typeof e!=='string'));} replaceChildren(){this.children=[];}setAttribute(k,v){this.attrs[k]=v;if(k==='data-node')this.dataset.node=v;}addEventListener(k,f){this.events[k]=f;}closest(){return this;}focus(){}scrollIntoView(){}scrollTo(){}querySelectorAll(){return this.children.filter(e=>e.attrs.class?.startsWith('node'));}get options(){return this.children;}}
 const elements=new Map();for(const id of ['#graph-data','#syllabus-graph','#graph-viewport','#graph-inspector','#graph-search','#graph-picker','#graph-group','#graph-detail','#graph-neighbours','#graph-status','.toolbar','header','.graph-layout','#graph-in','#graph-out','#graph-fit','#graph-clear'])elements.set(id,new El());
 elements.get('#graph-data').textContent=JSON.stringify(data);
 const context={window:{MathtreeLayout:ctx.window.MathtreeLayout,addEventListener(){}},document:{querySelector:s=>elements.get(s),createElement:t=>new El(t),createElementNS:(_,t)=>new El(t)},innerWidth:1200,location:{hash:''},history:{replaceState(){}}};
 vm.runInNewContext(fs.readFileSync('resources/ib-math-ai-sl/syllabus-graph.js','utf8'),context);
 const panel=elements.get('.graph-layout').children[0],buttons=panel.children.find(e=>e.tag==='div').children;
 assert.equal(buttons.length,5);buttons[0].onclick();assert.equal(buttons[0].attrs['aria-pressed'],'true');
 const svg=elements.get('#syllabus-graph');let node=svg.querySelectorAll().find(n=>n.dataset.node==='1.7');node.events.click();node=svg.querySelectorAll().find(n=>n.dataset.node==='1.7');node.events.dblclick();assert.ok(svg.querySelectorAll().find(n=>n.dataset.node==='1.7').attrs.class.includes('marked'));
 const sliders=panel.children.flatMap(e=>e.children).filter(e=>e.type==='range');assert.equal(sliders.length,2);sliders[0].value='9';sliders[0].oninput();
 const sort=panel.children.at(-1);sort.onclick();assert.equal(sort.textContent,'top sort');assert.ok(svg.querySelectorAll().find(n=>n.dataset.node==='1.7').attrs.class.includes('marked'));sort.onclick();assert.equal(sort.textContent,'botton sort');
 const toggle=panel.children.flatMap(e=>e.children).find(e=>e.type==='checkbox');toggle.checked=true;toggle.onchange();assert.ok(svg.querySelectorAll().some(n=>n.dataset.node.includes('prior-')));
});
