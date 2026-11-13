/** Guard the actual production artifacts against leaking development assessment features. */
import {existsSync, readdirSync, readFileSync, statSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const forbiddenContent = [
  'demo-1001', 'demo-1002', 'prism-1001', 'prism-1002',
  'teacherJudgments', 'externalSyllabusIds', 'assessmentId', 'questionId',
  'maxScore', 'externalId', 'Evidence: secure', 'Evidence: revisit',
  'Direct evidence must identify', 'Map 1.0 uses retired prototype objectives',
  'Choose learner JSON', 'Import one learner', 'Demo learner',
];

export function filesUnder(directory: string): string[] {
  if (!existsSync(directory)) return [];
  return readdirSync(directory).flatMap(name => {
    const path = join(directory, name);
    return statSync(path).isDirectory() ? filesUnder(path) : [path];
  });
}

export function checkStudentBuild(directory = 'dist') {
  if (!existsSync(join(directory, 'index.html'))) throw Error('Student build has no index.html. Run Vite build first.');
  const files = filesUnder(directory);
  if (!files.some(file => file.endsWith('.js'))) throw Error('Student build has no JavaScript application assets.');
  for (const file of files) {
    if (/(?:^|[/\\])(?:dev|fixtures|examples)(?:[/\\]|$)|student-\d+\.json|service[-_]?worker|sw\.js$/i.test(file)) {
      throw Error(`Development fixture or worker must not be published: ${file}`);
    }
    if (!/\.(?:html|js|css|json|map)$/.test(file)) continue;
    const content = readFileSync(file, 'utf8');
    for (const token of forbiddenContent) {
      if (content.includes(token)) throw Error(`Assessment material found in student build ${file}: ${token}`);
    }
    if (file.endsWith('.html') && /<(?:script|iframe|img)\b[^>]+src=["'](?:https?:)?\/\//i.test(content)) {
      throw Error(`External runtime asset or embed found in ${file}`);
    }
    if (file.endsWith('.css') && /(?:url\(\s*["']?(?:https?:)?\/\/|@import\s*["'](?:https?:)?\/\/)/i.test(content)) {
      throw Error(`External CSS asset found in ${file}`);
    }
    if (/serviceWorker\s*\.\s*register/.test(content)) throw Error(`Service worker registration found in ${file}`);
  }
  const jsFiles = files.filter(file => file.endsWith('.js'));
  const totalJsBytes = jsFiles.reduce((sum, file) => sum + statSync(file).size, 0);
  const html = readFileSync(join(directory, 'index.html'), 'utf8');
  const entry = html.match(/<script\b[^>]*src=["']([^"']+\.js)["']/i)?.[1];
  const entryFile = entry && join(directory, entry.replace(/^\.\//, '').replace(/^\//, ''));
  if (!entryFile || !existsSync(entryFile)) throw Error('Student build has no resolvable JavaScript entry module.');
  const entryJsBytes = statSync(entryFile).size;
  if (entryJsBytes > 550_000) throw Error('Student entry JavaScript exceeds the 550 kB budget; keep optional features split.');
  if (totalJsBytes > 800_000) throw Error('Student total JavaScript exceeds the 800 kB budget. Review curriculum/content or library changes.');
  return {files: files.length, entryJsBytes, totalJsBytes};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = checkStudentBuild(process.argv[2] || 'dist');
  console.log(`Student production boundary passed (${result.files} files; entry ${result.entryJsBytes} bytes, total JS ${result.totalJsBytes} bytes; no assessment fixtures or result-import implementation).`);
}
