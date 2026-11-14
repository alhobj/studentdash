import {test} from 'node:test';
import assert from 'node:assert/strict';
import {existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {filesUnder, checkStudentBuild} from '../scripts/check-student-build';
import ts from 'typescript';

function localImports(file: string): string[] {
  const content = readFileSync(file, 'utf8');
  const imports: string[] = [];
  const source = ts.createSourceFile(file, content, ts.ScriptTarget.Latest, true);
  function inspect(node: ts.Node) {
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
      imports.push(node.moduleSpecifier.text);
    }
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      assert.ok(node.arguments.length === 1 && ts.isStringLiteral(node.arguments[0]), 'Student dynamic imports must have inspectable static paths');
      imports.push(node.arguments[0].text);
    }
    ts.forEachChild(node, inspect);
  }
  inspect(source);
  return imports.filter(specifier => specifier.startsWith('.')).map(specifier => {
    const base = resolve(dirname(file), specifier);
    const found = [base, `${base}.ts`, `${base}.tsx`, `${base}.json`, `${base}.css`].find(existsSync);
    assert.ok(found, `Unresolved production import ${specifier} in ${file}`);
    return found;
  });
}

test('student entry module graph cannot reach assessment models, rules or learner fixtures', () => {
  const seen = new Set<string>();
  function walk(file: string) {
    if (seen.has(file)) return;
    seen.add(file);
    assert.ok(!/[/\\](?:dev|fixtures)[/\\]/.test(file), `Development material imported by student application: ${file}`);
    assert.ok(!file.endsWith('/src/model.ts'), 'The old assessment entry must not be restored to the student graph');
    if (/\.[jt]sx?$/.test(file)) for (const imported of localImports(file)) walk(imported);
  }
  walk(resolve('src/main.tsx'));
  assert.ok(seen.has(resolve('src/curriculum.ts')));
  assert.ok(seen.has(resolve('src/generated/student-map.json')));
  assert.ok(!seen.has(resolve('src/data/map.json')), 'Reviewed source is kept outside the compact runtime graph');
  const publicFiles = filesUnder('public');
  assert.equal(publicFiles.filter(file => /student-|fixtures|examples|assessment/i.test(file)).length, 0);
  assert.ok(!existsSync('tests/support/assessment/model.ts'), 'Retired assessment prototype stays removed');
  assert.ok(!existsSync('tests/fixtures/prototype/student-1001.json'), 'Retired demo fixtures stay removed');
});

test('production artifact checker rejects fixture files and private-result import code', () => {
  const directory = mkdtempSync(join(tmpdir(), 'chemistree-release-'));
  try {
    writeFileSync(join(directory, 'index.html'), '<html><script src="./app.js"></script></html>');
    writeFileSync(join(directory, 'app.js'), 'console.log("student curriculum");');
    assert.equal(checkStudentBuild(directory).files, 2);
    writeFileSync(join(directory, 'app.js'), 'const data={teacherJudgments:[]};');
    assert.throws(() => checkStudentBuild(directory), /Assessment material/);
    writeFileSync(join(directory, 'app.js'), 'console.log("student curriculum");');
    mkdirSync(join(directory, 'fixtures'));
    writeFileSync(join(directory, 'fixtures', 'student-1001.json'), '{}');
    assert.throws(() => checkStudentBuild(directory), /must not be published/);
  } finally {rmSync(directory, {recursive: true, force: true});}
});

test('production artifact checker rejects remote runtime assets and service workers', () => {
  const directory = mkdtempSync(join(tmpdir(), 'chemistree-release-'));
  try {
    writeFileSync(join(directory, 'index.html'), '<html></html>');
    writeFileSync(join(directory, 'app.js'), 'console.log("student curriculum");');
    writeFileSync(join(directory, 'app.css'), '@import "https://fonts.example.test/font.css";');
    assert.throws(() => checkStudentBuild(directory), /External CSS/);
    rmSync(join(directory, 'app.css'));
    writeFileSync(join(directory, 'index.html'), '<script src="https://cdn.example.test/app.js"></script>');
    assert.throws(() => checkStudentBuild(directory), /External runtime/);
    writeFileSync(join(directory, 'index.html'), '<html></html>');
    writeFileSync(join(directory, 'app.js'), 'navigator.serviceWorker.register("offline.js")');
    assert.throws(() => checkStudentBuild(directory), /Service worker/);
  } finally {rmSync(directory, {recursive: true, force: true});}
});


test('production artifacts enforce entry and total JavaScript budgets', () => {
  const directory = mkdtempSync(join(tmpdir(), 'chemistree-budget-'));
  try {
    writeFileSync(join(directory, 'index.html'), '<script src="./app.js"></script>');
    writeFileSync(join(directory, 'app.js'), ' '.repeat(550_001));
    assert.throws(() => checkStudentBuild(directory), /entry JavaScript/);
    writeFileSync(join(directory, 'app.js'), ' '.repeat(400_000));
    writeFileSync(join(directory, 'optional.js'), ' '.repeat(400_001));
    assert.throws(() => checkStudentBuild(directory), /total JavaScript/);
    writeFileSync(join(directory, 'index.html'), '<html></html>');
    assert.throws(() => checkStudentBuild(directory), /entry module/);
  } finally {rmSync(directory, {recursive:true, force:true});}
});
