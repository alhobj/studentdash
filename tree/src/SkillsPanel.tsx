import React,{useState} from 'react';
import {ControlSection} from '../shared/ControlPanel';
import data from './data/skills.json';
export function SkillsPanel(){
 const [query,setQuery]=useState('');
 const skills=data.skills.filter(s=>`${s.label} ${s.group} ${s.sections.join(' ')}`.toLowerCase().includes(query.toLowerCase()));
 return <ControlSection title={`Skills · ${data.skills.length}`}><p>Practical, mathematical and inquiry skills. These are paraphrased teaching labels; topic links are not prerequisites.</p><label>Find a skill<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Skill, group or syllabus section"/></label><p role="status">{skills.length} skills</p>{[...new Set(skills.map(s=>s.group))].map(group=><details key={group}><summary>{group}</summary><ul>{skills.filter(s=>s.group===group).map(s=><li key={s.id}><a href={`/practice/ib-chemistry/skills-practice.html#${s.id}`} target="_blank" rel="noopener">{s.label}</a><small style={{display:'block'}}>{s.across_course?'Across the course':s.sections.join(' · ')}</small></li>)}</ul></details>)}</ControlSection>;
}
