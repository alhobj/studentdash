/* Optional pointer and keyboard-accessible controls. Native button clicks nudge;
   holding a pointer moves continuously through the ordinary game loop. */
window.attachWalkingControls=function({container,keys,world,interact,blocked}){
 const held=new Map();
 const stop=()=>{for(const key of held.values())keys.delete(key);held.clear();};
 const add=(text,label,key,dx,dy)=>{
  const b=document.createElement('button');b.textContent=text;b.setAttribute('aria-label',label);b.className='walk-'+key;container.append(b);
  b.onpointerdown=e=>{if(blocked()||e.button>0)return;e.preventDefault();b.setPointerCapture?.(e.pointerId);held.set(e.pointerId,key);keys.add(key);};
  const release=e=>{const k=held.get(e.pointerId);held.delete(e.pointerId);if(k&&![...held.values()].includes(k))keys.delete(k);};
  b.onpointerup=release;b.onpointercancel=release;b.onlostpointercapture=release;
  b.onclick=e=>{if(e.detail===0&&!blocked()){world.step(dx,dy,.05);world.step(dx,dy,.05);world.paint();}};
 };
 add('↑','Walk north','arrowup',0,-1);add('←','Walk west','arrowleft',-1,0);add('↓','Walk south','arrowdown',0,1);add('→','Walk east','arrowright',1,0);
 const talk=document.createElement('button');talk.textContent='Talk / enter';talk.className='walk-talk';talk.onclick=()=>{stop();if(!blocked())interact();};container.append(talk);
 window.addEventListener('blur',stop);document.addEventListener?.('visibilitychange',()=>{if(document.hidden)stop();});
 return {stop};
};
