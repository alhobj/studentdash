/* Standalone screen-world controller. Route topology and visual themes are profile data.
   Kept identical in both experiment folders so each game remains portable. */
window.createScreenWorld=function({canvas,rooms,start,coat,onChange,onInteract,status,onHint,reducedMotion=false}){
 const W=960,H=576,player={x:480,y:380};let current=start,arrival=0,lastHint,facing='down',stride=0,moving=false;const visited=new Set([start]);
 const room=()=>rooms.find(r=>r.id===current);
 function travel(id,edge){if(!rooms.some(r=>r.id===id))return false;current=id;visited.add(id);moving=false;stride=0;
  player.x=edge==='left'?W-36:edge==='right'?36:edge==='down'?(room().northExitX||480):480;
  player.y=edge==='up'?H-48:edge==='down'?48:380;
  if(edge)facing=edge;
  arrival=edge&&!reducedMotion ? .18 : 0;onChange?.(room());return true;
 }
 // Collision uses the small footprint at the character's feet, not the head.
 function walkable(x,y){return !(room().solids||[]).some(b=>x+8>b.x&&x-8<b.x+b.w&&y+28>b.y&&y+18<b.y+b.h);}
 function step(dx,dy,dt){moving=false;if(dx||dy)facing=Math.abs(dx)>Math.abs(dy)?(dx>0?'right':'left'):(dy>0?'down':'up');if(arrival>0){arrival=Math.max(0,arrival-Math.max(0,Math.min(dt,.05)));return null;}const norm=Math.hypot(dx,dy)||1;const distance=180*Math.max(0,Math.min(dt,.05));
  const beforeX=player.x,beforeY=player.y;
  // Axis-separated small steps let the player slide along walls without tunnelling.
  const parts=Math.max(1,Math.ceil(distance/3));
  for(let i=0;i<parts;i++){
   const x=player.x+dx/norm*distance/parts;if(walkable(x,player.y))player.x=x;
   const y=player.y+dy/norm*distance/parts;if(walkable(player.x,y))player.y=y;
  }
  const walked=Math.hypot(player.x-beforeX,player.y-beforeY);moving=walked>0.01;if(moving)stride+=walked;
  const edge=player.x<12?'left':player.x>W-12?'right':player.y<20?'up':player.y>H-30?'down':null;
  if(edge&&room().exits[edge]){travel(room().exits[edge],edge);return edge;}
  player.x=Math.max(12,Math.min(W-12,player.x));player.y=Math.max(20,Math.min(H-30,player.y));return null;
 }
 function nearby(){
  const actor=[...room().actors].sort((a,b)=>Math.hypot(a.x-player.x,a.y-player.y)-Math.hypot(b.x-player.x,b.y-player.y)).find(a=>Math.hypot(a.x-player.x,a.y-player.y)<70);
  if(actor)return {id:actor.id,label:'Talk to '+actor.name};
  if(player.y>=260&&Math.hypot(480-player.x,290-player.y)<60)return {id:'building',label:'Enter '+room().short};
  return null;
 }
 function interact(){const target=nearby();if(!target)return false;onInteract?.(target.id,room().id);return true;}
 function paint(){const r=room(),c=canvas.getContext('2d'),p=r.palette;
  const rect=(x,y,w,h,color)=>{c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),w,h);};
  const text=(s,x,y,size=14,color='#f3eed6')=>{c.font=`${size}px monospace`;c.textAlign='center';c.fillStyle=color;c.fillText(s,x,y);};
  window.paintVillageScene(c,r);
  text(r.name,480,78,19);text(status?.(r.id)||'',480,455,13);
  for(const a of r.actors){window.paintVillagePerson(c,{x:a.x,y:a.y,coat:p.accent,accent:p.roof});text(a.name,a.x,a.y-24,12);}
  for(const [edge,id]of Object.entries(r.exits)){const name=rooms.find(x=>x.id===id).short;
   const x=edge==='left'?105:edge==='right'?855:edge==='up'?(r.northExitX||480):480,y=edge==='up'?26:edge==='down'?553:366;
   rect(x-3,y+6,6,12,'#795334');rect(x-100,y-21,200,31,'#684b35');rect(x-97,y-18,194,25,'#a4794f');rect(x-94,y-16,188,2,'#d3ad74');text(`${edge==='left'?'← ':edge==='up'?'↑ ':''}${name}${edge==='right'?' →':edge==='down'?' ↓':''}`,x,y,13);
  }
  const x=player.x,y=player.y,pace=moving&&!reducedMotion?(Math.floor(stride/9)%2?2:-2):0;
  window.paintVillagePerson(c,{x,y,coat,accent:p.accent,facing,pace});
  const hint=nearby();const hintText=hint?'E / Talk button · '+hint.label:'Walk near a guide or the front door to interact.';
  if(hint){rect(250,484,460,28,p.roof);text(hintText,480,504,13);}
  if(hintText!==lastHint){lastHint=hintText;onHint?.(hintText);}
  if(arrival>0)rect(0,0,W,H,`rgba(12,20,28,${Math.min(1,arrival/.18)})`);
 }
 function routeTo(target){
  const queue=[{id:current,steps:[]}],seen=new Set([current]);
  for(let i=0;i<queue.length;i++){const node=queue[i];if(node.id===target)return node.steps;
   for(const [direction,id]of Object.entries(rooms.find(r=>r.id===node.id).exits)){if(seen.has(id))continue;seen.add(id);queue.push({id,steps:[...node.steps,{direction,id}]});}
  }return null;
 }
 return {travel,step,interact,paint,room,player,walkable,routeTo,visited:()=>[...visited],pose:()=>({facing,moving,stride})};
};
