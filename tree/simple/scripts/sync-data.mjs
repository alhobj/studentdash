import {readFile,writeFile} from 'node:fs/promises';
import {buildSimpleMap} from './build-map.mjs';
const source=JSON.parse(await readFile(new URL('../../src/data/map.json',import.meta.url),'utf8'));
const review=JSON.parse(await readFile(new URL('../src/data/prerequisites.json',import.meta.url),'utf8'));
const map=buildSimpleMap(source,review);
await writeFile(new URL('../src/data/map.json',import.meta.url),JSON.stringify(map,null,2)+'\n');
console.log(`Synced ${map.nodes.length} curriculum nodes and ${map.edges.filter(e=>e.type==='prerequisite').length} reviewed teaching dependencies.`);
