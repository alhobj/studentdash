/** Derive student runtime assets from reviewed source files; never edit the sources. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import source from '../src/data/map.json';
import practice from '../src/data/practice.json';

export function projectStudentMap(map: typeof source) {
  const supportText: string[] = [];
  const byText = new Map<string, number>();
  function intern(text: string) {
    if (!byText.has(text)) {byText.set(text, supportText.length); supportText.push(text);}
    return byText.get(text)!;
  }
  return {
    supportText,
    version: map.version, groups: map.groups, syllabus: map.syllabus, resources: map.resources,
    nodes: map.nodes.map(node => {
      const {objective, editorial, mappingStatus, explanation, practice, criteria, misconception, ...content} = node;
      if (objective !== node.official.statement) throw Error(`Learning goal differs from official statement: ${node.id}`);
      const parts = node.official.statementParts;
      const plain = parts.length === 1 && parts.every(part => part.script === 'normal') && parts.map(part => part.text).join('') === node.official.statement;
      return {...content, support: [explanation, practice, criteria, misconception].map(intern), official: {...node.official, statementParts: plain ? null : parts}};
    }),
    edges: map.edges.map(({provenance, ...edge}) => edge),
  };
}

export function generateStudentData() {
  const directory = path.resolve('src/generated');
  fs.mkdirSync(directory, {recursive: true});
  const files = {
    'student-map.json': projectStudentMap(JSON.parse(fs.readFileSync('src/data/map.json', 'utf8')) as typeof source),
    'practice-index.json': (JSON.parse(fs.readFileSync('src/data/practice.json', 'utf8')) as typeof practice).map(exercise => exercise.nodeId),
  };
  for (const [name, data] of Object.entries(files)) {
    const content = JSON.stringify(data) + '\n';
    const target = path.join(directory, name);
    if (!fs.existsSync(target) || fs.readFileSync(target, 'utf8') !== content) fs.writeFileSync(target, content);
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) generateStudentData();
