/* Atomic-number practice from the album; no isotope mass or stability assumptions. */
window.GAME_PROFILE.makeChallengeSet=function(collected=[],random=Math.random){
 const all=this.periodic.elements,pool=collected.length?all.filter(e=>collected.includes(e.z)):all.slice(0,20),shuffled=[...pool];
 for(let i=shuffled.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]];}
 return Array.from({length:5},(_,i)=>{const e=shuffled[i%shuffled.length];const base={topic:collected.length?'Your collected elements':'Starter elements · collection not required',label:'Your answer',tolerance:0};
  if(i%3===0)return {...base,title:`Count protons in ${e.name}`,prompt:`${e.symbol} has atomic number ${e.z}. How many protons are in each atom of this element?`,answer:e.z,hint:'Atomic number counts protons.',explanation:`Every ${e.name.toLowerCase()} atom has ${e.z} protons. Changing proton count changes the element.`};
  if(i%3===1)return {...base,title:`Build neutral ${e.symbol}`,prompt:`A neutral ${e.name.toLowerCase()} atom has ${e.z} protons. How many electrons does it have?`,answer:e.z,hint:'A neutral atom has equal numbers of protons and electrons.',explanation:`Neutral ${e.symbol} has ${e.z} electrons. This says nothing about which isotope is present.`};
  return {...base,title:`Locate ${e.symbol}`,prompt:`Find ${e.name} in the periodic table. What is its period number? You may close this circuit, consult the album, and return.`,answer:e.period,hint:`It belongs to period ${e.period}. Detached lanthanoid and actinoid rows belong to periods 6 and 7.`,explanation:`${e.symbol} belongs to period ${e.period}${e.series?', in the '+e.series.toLowerCase()+' series':', group '+e.group}.`};
 });
};
