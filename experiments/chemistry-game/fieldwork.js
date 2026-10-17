/* Shared optional exploration rewards; never changes credits or assessment results. */
window.validateFieldwork=function(profile,data,completedCount){
 const discoveries=data.discoveries??[],outfit=data.outfit??'classic';
 if(!Array.isArray(discoveries)||new Set(discoveries).size!==discoveries.length||discoveries.some(id=>!profile.discoveryCards.some(c=>c.id===id)))throw Error('Invalid discovery collection.');
 const style=profile.explorerStyles.find(s=>s.id===outfit);
 if(!style||discoveries.length<style.cards||completedCount<style.quests)throw Error('Invalid explorer outfit.');
 return {discoveries:[...discoveries],outfit};
};
window.createFieldwork=function({profile,read,write,completed,room,open,parent}){
 const add=(tag,text,into=parent)=>{const e=document.createElement(tag);e.textContent=text;into.append(e);return e;};
 const button=(text,fn)=>{const b=add('button',text);b.onclick=fn;return b;};
 function inspect(){const card=profile.discoveryCards.find(c=>c.room===room());if(!card)return;
  open();add('h2',card.title);add('p',card.note);add('p','A discovery is a field note, not a test or proof of mastery.');
  if(read().discoveries.includes(card.id))add('p','Already in your collection.');
  else button('Keep discovery card',()=>{if(!read().discoveries.includes(card.id))write({...read(),discoveries:[...read().discoveries,card.id]});inspect();});
  button('Open field satchel',menu);
 }
 function menu(){open();add('h2','Your field satchel');const state=read(),done=completed();
  add('p',`${state.discoveries.length} / ${profile.discoveryCards.length} discovery cards. Stamps combine exploration with completing an investigation; supported work counts too.`);
  button('Inspect this location’s discovery',inspect);
  for(const card of profile.discoveryCards){const found=state.discoveries.includes(card.id),studied=done.some(q=>q.district===card.room);const section=add('section','');section.className='notebook-entry';
   add('h3',`${card.room} · ${found&&studied?'Fieldwork stamp earned':'Stamp in progress'}`,section);
   add('p',`${found?'✓':'○'} Discover the field note · ${studied?'✓':'○'} Complete an investigation here`,section);
   if(found){add('strong',card.title,section);add('p',card.note,section);}
  }
  add('h3','Explorer wardrobe');add('p','Outfits are cosmetic and never affect questions or scores.');
  for(const style of profile.explorerStyles){const unlocked=state.discoveries.length>=style.cards&&done.length>=style.quests;
   const b=button(`${state.outfit===style.id?'Wearing':unlocked?'Wear':'Locked'} · ${style.name}`,()=>{write({...read(),outfit:style.id});menu();});b.disabled=!unlocked||state.outfit===style.id;
   if(!unlocked)add('p',`Needs ${style.cards} cards and ${style.quests} completed investigations.`);
  }
 }
 return {inspect,menu};
};
