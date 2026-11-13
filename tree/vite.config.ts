import {defineConfig} from 'vite';
import {resolve} from 'node:path';
import {generateStudentData} from './scripts/generate-student-data';
export default defineConfig({base:'./',server:{allowedHosts:['terminal.local']},plugins:[{
  name:'refresh-student-curriculum',
  configureServer(server) {
    const sources=new Set(['src/data/map.json','src/data/practice.json'].map(file=>resolve(file)));
    server.watcher.on('change',file=>{if(sources.has(file))generateStudentData();});
  },
}]});
