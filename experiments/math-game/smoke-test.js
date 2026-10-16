/* No dependencies. Serve locally and open smoke-test.html in a browser. */
(() => {
  const lines = [], P = window.MATH_GAME_PROFILE, output = document.getElementById('result');
  const assert = (condition, label) => {if (!condition) throw Error(label);};
  const throws = (fn, label) => {let rejected=false;try{fn();}catch{rejected=true;}assert(rejected,label);};
  const pass = label => {lines.push('PASS · '+label);output.textContent=lines.join('\n');};
  // Independently worked values; avoids simply submitting the profile's answer keys.
  const answers = {
    market:[[12,68],[27],[540.8]], scale:[[4.2,6],[5],[4.1666666667]],
    clock:[[2,3],[15],[3,9]], arch:[[3,9],[0,6],[5]],
    survey:[[10],[4,6],[21.5]], shelter:[[12],[37.699111843],[5]],
    garden:[[7,4],[6],[9]], chance:[[0.36],[0.375],[0.5]],
    motion:[[4],[3,6],[3]], park:[[10,20],[9],[36]]
  };
  const memory = new Map(), storage = {getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)};
  const engine = window.createQuestEngine(P,storage);
  function finish(id, supported=false) {
    engine.start(id); if(supported)engine.hint(id);
    for(const values of answers[id]){engine.record(id,values.map(String));assert(engine.check(id),id+' correct answer');engine.advance(id);}
  }
  try {
    assert(new Set(P.quests.map(q=>q.id)).size===P.quests.length,'unique quest IDs');
    P.quests.forEach(q=>assert(P.districts.some(d=>d.id===q.district)&&q.requires.every(id=>P.quests.some(other=>other.id===id)),'known district and prerequisite'));
    throws(()=>engine.start('park'),'locked route');throws(()=>engine.start('unknown'),'unknown route');pass('Content references and locked routes');
    engine.start('market');engine.record('market',['','']);assert(!engine.check('market'),'blank is not zero');
    engine.record('market',['12','68']);assert(engine.check('market'),'accept first step');engine.advance('market');
    const restored=window.createQuestEngine(P,storage);assert(restored.read().drafts.market.stage===1,'draft stage survives reload');assert(restored.read().drafts.market.assisted,'retry support flag survives reload');
    engine.reset();finish('market',true);assert(!engine.read().independent.includes('market'),'hint does not become independent');
    const credit=engine.read().credits;finish('market');assert(engine.read().credits===credit,'no repeat reward');assert(engine.read().independent.includes('market'),'fresh replay can be independent');pass('Draft recovery, blank answers, support flags and one-time rewards');
    for(const q of P.quests)if(q.id!=='market')finish(q.id);
    assert(engine.read().completed.length===10,'all investigations reachable');assert(engine.read().independent.length===10,'all independent runs');
    assert(engine.read().credits===186,'sum of one-time rewards');pass('All 30 steps match independently worked numerical answers');
    ['ledger','graph','compass'].forEach(id=>engine.place(id));throws(()=>engine.place('data'),'three slots enforced');engine.place('graph');engine.place('data');
    engine.buy('lamp');throws(()=>engine.buy('lamp'),'no duplicate purchase');engine.note('market','Discount = original × rate.');
    const exported=engine.exportSave();engine.reset();engine.importSave(exported);assert(engine.read().notes.market.includes('Discount'),'note restored');assert(engine.read().placed.includes('data'),'equipment restored');
    const before=engine.exportSave();for(const mutation of [s=>s.profile='chemistry',s=>s.credits++,s=>s.completed.push('unknown'),s=>s.placed.push('tangent'),s=>s.notes.unknown='bad',s=>s.independent.push('unknown')]){
      const bad=JSON.parse(before);mutation(bad);throws(()=>engine.importSave(JSON.stringify(bad)),'bad import rejected');assert(engine.exportSave()===before,'bad import leaves save unchanged');
    }
    const broken=window.createQuestEngine(P,{getItem(){throw Error('unavailable');},setItem(){throw Error('quota');}});broken.start('market');assert(broken.error(),'storage error visible');assert(broken.exportSave().includes('market'),'export still works');
    pass('Equipment, purchases, notebook export/import, invalid imports and storage failures');
  } catch(error) {output.textContent=lines.join('\n')+'\nFAIL · '+error.stack;document.title='FAIL · Pattern Quest';return;}
  const frame=document.getElementById('game');
  async function ui(){
    const key=P.storageKey,backup=localStorage.getItem(key);
    try{
      const doc=frame.contentDocument,win=frame.contentWindow;
      const click=label=>{const b=[...doc.querySelectorAll('button')].find(b=>b.textContent===label&&!b.disabled);assert(b,'button: '+label);b.click();};
      const panel=()=>doc.getElementById('panel');
      click('Start a new expedition');click('Reset this game save');
      click('Open quest journal');click('All quests');assert(panel().textContent.includes('Requires:'),'locked requirements displayed');
      doc.getElementById('close').click();
      for(const q of P.quests){
        doc.getElementById('journal').click();click('All quests');
        const b=[...panel().querySelectorAll('button')].find(b=>b.textContent.includes(q.title));assert(b,'quest button');b.click();click('Accept quest and begin');
        answers[q.id].forEach((values,index)=>{
          const inputs=[...panel().querySelectorAll('input[type=number]')];assert(inputs.length===values.length,'input count');
          inputs.forEach((input,i)=>{input.value=values[i];input.dispatchEvent(new win.Event('input'));});
          click('Check model');assert(panel().textContent.includes('Correct.'),'visible correct feedback');
          click(index===answers[q.id].length-1?'Finish quest':'Next step →');
        });
        assert(panel().textContent.includes('restored'),'completion panel');
      }
      assert(doc.getElementById('wallet').textContent.includes('10/10'),'complete UI progress');
      doc.getElementById('studio').click();click('Place Pattern ledger');click('Place Graph board');assert(panel().textContent.includes('Slot 1: Pattern ledger'),'placed tools');
      doc.getElementById('builder').click();assert(panel().querySelector('canvas'),'graph rendered');
      const slider=panel().querySelector('input');slider.value='2';slider.dispatchEvent(new win.Event('input'));assert(panel().textContent.includes('y = 2x + 0'),'live graph readout');
      doc.getElementById('notebook').click();click('Reopen the night market');const note=panel().querySelector('textarea');note.value='<b>Personal note</b>';note.dispatchEvent(new win.Event('input'));assert(!panel().querySelector('b'),'notes are not HTML');
      doc.getElementById('close').click();
      await new Promise(resolve=>{frame.onload=resolve;frame.contentWindow.location.reload();});
      assert(frame.contentDocument.getElementById('wallet').textContent.includes('10/10'),'page reload restores all progress');
      frame.style.width='390px';
      assert(frame.contentDocument.documentElement.scrollWidth<=frame.contentWindow.innerWidth,'no horizontal overflow at 390px');
      frame.contentDocument.getElementById('builder').click();
      assert(frame.contentDocument.getElementById('dialog').scrollWidth<=frame.contentDocument.getElementById('dialog').clientWidth,'graph dialog fits narrow viewport');
      pass('Real DOM: every quest, graph canvases, studio, notebook and page reload');
      pass('390px layout and graph dialog fit without horizontal overflow');
      document.title='PASS · Pattern Quest';output.textContent=lines.join('\n')+'\nALL CHECKS PASSED';
    }catch(error){document.title='FAIL · Pattern Quest';output.textContent=lines.join('\n')+'\nFAIL · '+error.stack;}
    finally{if(backup===null)localStorage.removeItem(key);else localStorage.setItem(key,backup);}
  }
  if(frame.contentDocument?.readyState==='complete' && frame.contentDocument.getElementById('reset'))ui();else frame.addEventListener('load',ui,{once:true});
})();
