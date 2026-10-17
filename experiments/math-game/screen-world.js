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
  rect(0,0,W,H,p.ground);
  for(let x=0;x<W;x+=32)for(let y=0;y<H;y+=32)if((x/32+y/32)%3===0)rect(x+7,y+14,4,3,p.detail);
  // The north path passes beside the building, with a clear walking corridor.
  rect(448,280,64,116,p.path);
  if(r.exits.left)rect(0,332,480,64,p.path);
  if(r.exits.right)rect(480,332,480,64,p.path);
  if(r.exits.up){const nx=r.northExitX||480;rect(nx-14,0,28,364,p.path);rect(nx,332,480-nx,64,p.path);}
  if(r.exits.down)rect(448,364,64,H-364,p.path);
  if(r.theme==='water'){rect(20,100,300,180,p.water);rect(640,100,300,180,p.water);for(let y=120;y<270;y+=32){rect(40,y,250,3,p.detail);rect(665,y,250,3,p.detail);}rect(110,245,170,30,p.roof);}
  if(r.theme==='garden'){for(const x of [70,200,720,850])for(const y of [160,450]){rect(x-4,y,8,34,p.roof);rect(x-24,y-24,48,40,p.detail);rect(x-15,y-38,30,22,p.accent);}for(let i=0;i<8;i++)rect(100+i*95,500,8,8,p.accent);}
  if(r.theme==='factory'){for(const x of [90,740]){rect(x,100,120,140,p.roof);rect(x+20,120,80,90,p.detail);rect(x+45,60,25,50,p.accent);for(let y=425;y<520;y+=30)rect(x,y,130,10,p.accent);}}
  if(r.theme==='energy'){for(const x of [65,740]){rect(x,100,150,170,p.roof);for(let i=0;i<4;i++)rect(x+15+i*32,120,20,120,p.accent);}for(let x=80;x<900;x+=80)rect(x,480,45,14,p.detail);}
  if(r.theme==='archive'){for(const x of [65,735])for(const y of [110,180,450]){rect(x,y,150,48,p.roof);for(let i=0;i<7;i++)rect(x+10+i*19,y+8,11,28,i%2?p.accent:p.detail);}}
  if(r.theme==='stars'){for(let i=0;i<32;i++){const x=(i*137+30)%W,y=(i*71+60)%H;if(x<340||x>630)rect(x,y,3,3,p.accent);}for(const x of [150,800]){rect(x-5,175,10,100,p.roof);rect(x-45,150,90,24,p.detail);rect(x+24,130,25,30,p.accent);}}
  if(r.theme==='market'){for(const x of [70,730]){rect(x,120,160,90,p.roof);for(let i=0;i<8;i++)rect(x+i*20,100,20,30,i%2?p.accent:p.detail);rect(x+10,185,140,20,p.path);}}
  // A single local destination, rather than every district on one canvas.
  rect(350,106,260,174,p.roof);rect(338,96,284,30,p.accent);rect(368,142,224,90,p.detail);
  for(let i=0;i<3;i++){rect(380+i*72,151,44,35,p.window);rect(400+i*72,151,4,35,p.roof);}
  rect(462,216,36,64,p.roof);rect(468,225,24,55,p.window);
  text(r.name,480,78,19);text(status?.(r.id)||'',480,455,13);text('E · Enter / meet your guide',480,306,13);
  for(const a of r.actors){rect(a.x-7,a.y-14,14,14,'#dcb18b');rect(a.x-9,a.y,18,20,p.accent);rect(a.x-7,a.y+20,5,9,p.roof);rect(a.x+2,a.y+20,5,9,p.roof);text(a.name,a.x,a.y-24,12);}
  for(const [edge,id]of Object.entries(r.exits)){const name=rooms.find(x=>x.id===id).short;
   const x=edge==='left'?105:edge==='right'?855:edge==='up'?(r.northExitX||480):480,y=edge==='up'?26:edge==='down'?553:366;
   rect(x-100,y-19,200,28,p.roof);text(`${edge==='left'?'← ':edge==='up'?'↑ ':''}${name}${edge==='right'?' →':edge==='down'?' ↓':''}`,x,y,13);
  }
  const x=player.x,y=player.y,pace=moving&&!reducedMotion?(Math.floor(stride/9)%2?2:-2):0;
  rect(x-12,y+20,26,7,p.roof);rect(x-7,y-12,14,15,'#e0b692');rect(x-9,y-17,18,7,'#514239');
  rect(x-10,y+3,20,18,coat);rect(x-7,y+21+pace,5,9,'#1b303c');rect(x+3,y+21-pace,5,9,'#1b303c');
  rect(x-13,y+5-pace,4,12,coat);rect(x+9,y+5+pace,4,12,coat);
  if(facing==='up'){rect(x-7,y-10,14,12,'#514239');rect(x-5,y+6,10,10,p.detail);}
  else if(facing==='left'){rect(x-9,y-6,3,3,'#1b303c');rect(x+4,y+6,5,8,p.accent);}
  else if(facing==='right'){rect(x+6,y-6,3,3,'#1b303c');rect(x-8,y+6,5,8,p.accent);}
  else{rect(x-5,y-6,3,3,'#1b303c');rect(x+3,y-6,3,3,'#1b303c');rect(x+4,y+6,5,8,p.accent);}
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
