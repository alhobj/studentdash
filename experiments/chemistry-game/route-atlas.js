/* Accessible local route atlas; spatial metadata comes from each game's profile. */
window.renderWorldAtlas=function({parent,world,rooms,travel}){
 const add=(tag,text,into=parent)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;into.append(n);return n;};
 add('p','Choose a location to see the walking route, or travel there directly. Visiting a location does not unlock its investigations. Exploration markers last for this session.');
 const grid=add('div');grid.className='route-atlas';const tiles=[];
 for(const r of rooms){
  const tile=add('button',undefined,grid);tile.style.gridColumn=String(r.atlas.x*2+1);tile.style.gridRow=String(r.atlas.y*2+1);tile.style.borderColor=r.palette.accent;
  add('strong',r.name,tile);add('span',r.id===world.room().id?'You are here':world.visited().includes(r.id)?'Visited':'Not visited yet',tile);
  tile.setAttribute('aria-pressed','false');tile.setAttribute('aria-current',r.id===world.room().id?'location':'false');tile.onclick=()=>select(r.id);tiles.push([r.id,tile]);
  for(const edge of ['right','down'])if(r.exits[edge]){const line=add('span',edge==='right'?'↔':'↕',grid);line.className='route-connector';line.setAttribute('aria-hidden','true');line.style.gridColumn=String(r.atlas.x*2+1+(edge==='right'?1:0));line.style.gridRow=String(r.atlas.y*2+1+(edge==='down'?1:0));}
 }
 const detail=add('section');detail.className='route-detail';detail.setAttribute('aria-live','polite');
 function select(id){detail.replaceChildren();for(const [tileId,tile]of tiles)tile.setAttribute('aria-pressed',String(id===tileId));
  const r=rooms.find(r=>r.id===id),route=world.routeTo(id);add('h3',r.name,detail);
  if(route===null){add('p','There is no walking route from here.',detail);return;}
  if(!route.length)add('p','You are already here. Close the map to explore.',detail);
  else{add('p','From '+world.room().name+':',detail);const list=add('ol',undefined,detail);
   for(const step of route)add('li','Go '+({up:'north',down:'south',left:'west',right:'east'}[step.direction])+' to '+rooms.find(r=>r.id===step.id).name+'.',list);
   const go=add('button','Travel to '+r.name,detail);go.onclick=()=>travel(id);
  }
 }
 select(world.room().id);
};
