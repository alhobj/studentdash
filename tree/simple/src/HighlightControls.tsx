import React,{useState} from 'react';
import {ControlSection} from '../../shared/ControlPanel';
import {SECTION_NAMES,sectionStyle} from './highlighting';
export function useHighlightSettings(){
 const [before,setBefore]=useState(0),[after,setAfter]=useState(1);
 const [showUnlocked,setShowUnlocked]=useState(false);
 const [sections,setSections]=useState<Set<number>>(()=>new Set());
 const toggleSection=(group:number)=>setSections(previous=>{const next=new Set(previous);if(next.has(group))next.delete(group);else next.add(group);return next;});
 return {before,after,setBefore,setAfter,sections,toggleSection,showUnlocked,setShowUnlocked};
}
export type HighlightSettings=ReturnType<typeof useHighlightSettings>;
export function HighlightControls({settings,max,sectionOptions,connectionOptions}:{settings:HighlightSettings;max:number;sectionOptions?:React.ReactNode;connectionOptions?:React.ReactNode}){
 return <>
  <ControlSection title="Structure & Reactivity">
   {sectionOptions}
   <div className="section-buttons" role="group" aria-label="Highlight syllabus sections">
    {SECTION_NAMES.map((name,i)=><button key={name} style={sectionStyle(i) as React.CSSProperties} type="button" aria-pressed={settings.sections.has(i)} onClick={()=>settings.toggleSection(i)}>{settings.sections.has(i)?'✓ ':''}{name}</button>)}
   </div><p>Colour highlights the selected chapters.</p>
  </ControlSection>
  <ControlSection title="Arrows & connections">
   {connectionOptions}
   {(['before','after'] as const).map(direction=><label className="depth-control" key={direction}>
    <span>See {settings[direction]} levels {direction}</span>
    <input type="range" aria-label={`Levels ${direction}`} min={0} max={max} step={1} value={settings[direction]} aria-valuetext={`${settings[direction]} levels ${direction}${settings[direction]===max?' (all)':''}`} onChange={e=>(direction==='before'?settings.setBefore:settings.setAfter)(Number(e.target.value))}/>
    <span className="depth-scale"><span>0</span><span>All ({max})</span></span>
   </label>)}
  </ControlSection>
  <ControlSection title="Node availability">
   <button className="unlock-toggle" type="button" aria-pressed={settings.showUnlocked} onClick={()=>settings.setShowUnlocked(value=>!value)}>Unlocked nodes</button>
   {settings.showUnlocked&&<p className="unlock-key">Green glow: ready to cover. Faded: prerequisites still unmarked. Based on temporary marks.</p>}
   <p>Double-click a node or press M to mark it temporarily.</p>
  </ControlSection>
 </>;
}
