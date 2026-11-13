import data from './generated/student-map.json';

const {supportText, nodes, ...curriculum} = data;
export const map = {...curriculum, nodes: nodes.map(({support, ...node}) => ({...node,
  explanation: supportText[support[0]], practice: supportText[support[1]],
  criteria: supportText[support[2]], misconception: supportText[support[3]],
}))};
export type Skill = typeof map.nodes[number];
const ids = new Set(map.nodes.map(node => node.id));

export function ancestors(id: string, edges = map.edges): string[] {
  const found = new Set<string>();
  function visit(target: string) {
    for (const edge of edges.filter(e => e.type === 'prerequisite' && e.target === target)) {
      if (!found.has(edge.source)) { found.add(edge.source); visit(edge.source); }
    }
  }
  visit(id);
  return [...found];
}

export function validateGraph() {
  const active = new Set<string>(), done = new Set<string>();
  function visit(id: string) {
    if (active.has(id)) throw Error('Prerequisite cycle at ' + id);
    if (done.has(id)) return;
    active.add(id);
    for (const edge of map.edges.filter(e => e.type === 'prerequisite' && e.source === id)) visit(edge.target);
    active.delete(id); done.add(id);
  }
  for (const node of map.nodes) visit(node.id);
  for (const edge of map.edges) if (!ids.has(edge.source) || !ids.has(edge.target)) throw Error('Unknown endpoint');
  return true;
}

// Content and requested level are the only inputs. Learner envelopes are never accepted here.
export function prompt(node: Skill, level: 'SL' | 'HL') {
  const prerequisites = node.prerequisites.map(id => map.nodes.find(n => n.id === id)!.title);
  return `Act as an IB DP Chemistry tutor (first assessment 2025), at ${level} level. Use English by default.
Official guide statement — ${node.official.code}: ${node.official.statement}
Statement allocation: ${node.level === 'HL' ? 'additional higher level; for an SL learner, present this as optional extension content' : 'shared SL/HL'}.
The following teaching scaffold and prerequisite links are editorial, not additional official syllabus statements.
Learning goal: ${node.official.statement}
Evidence to look for: ${node.criteria}
Suggested prerequisites: ${prerequisites.join('; ') || 'No specific prior nodes'}. Do not assume I have mastered them; diagnose briefly as needed.
Study focus: ${node.explanation}
Ask ONE question at a time, wait for my response, and adapt. Offer a hint before giving a full solution. Check understanding with a transfer question. Address this misconception: ${node.misconception}
Use correct chemical notation, units and significant figures. Explain limitations of models.`;
}

validateGraph();
