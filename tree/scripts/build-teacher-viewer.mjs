import {build} from 'vite';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'..');
await build({configFile:false,root:resolve(root,'teacher-viewer'),base:'./',resolve:{dedupe:['react','react-dom','@xyflow/react']},build:{outDir:resolve(root,'teacher-viewer/dist'),emptyOutDir:true}});
