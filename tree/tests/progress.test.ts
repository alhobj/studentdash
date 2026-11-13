import {test} from 'node:test';
import assert from 'node:assert/strict';
import {
  STORAGE_KEY, MAX_IMPORT_BYTES, EXPORT_FILENAME, parseProgressFile, exportProgress,
  setSelfAssessment, importConflicts, applyImport, loadProgress, saveProgress, clearProgress,
  type Progress,
} from '../src/progress';

const a = 'ib-2025-structure-1.1.1';
const b = 'ib-2025-structure-2.2.6';
const c = 'ib-2025-reactivity-1.1.1';
const file = (selfAssessments: unknown, fields = {}) => JSON.stringify({schemaVersion: '1.0', mapVersion: '2.0', selfAssessments, ...fields});
function memoryStorage(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial));
  const calls: string[] = [];
  return {
    values, calls,
    getItem(key: string) {calls.push('read:' + key); return values.get(key) ?? null;},
    setItem(key: string, value: string) {calls.push('write:' + key); values.set(key, value);},
    removeItem(key: string) {calls.push('remove:' + key); values.delete(key);},
  };
}

test('clean first launch has no identity or records and reads only the self-assessment key', () => {
  const storage = memoryStorage({'chemistree-v1': '{"student":{"id":"legacy"}}', 'chemistree-v2': '{"evidence":[]}'});
  assert.deepEqual(loadProgress(storage), {progress: {}});
  assert.deepEqual(storage.calls, ['read:' + STORAGE_KEY]);
  assert.equal(storage.values.size, 2);
});

test('self-assessment export/import round trip contains only versions and entries', () => {
  const progress: Progress = {[a]: 'needs-practice', [b]: 'developing', [c]: 'confident'};
  const text = exportProgress(progress);
  assert.deepEqual(parseProgressFile(text), progress);
  const raw = JSON.parse(text);
  assert.deepEqual(Object.keys(raw).sort(), ['mapVersion', 'schemaVersion', 'selfAssessments']);
  assert.equal(EXPORT_FILENAME, 'chemistree-self-assessment.json');
  assert.ok(!/timestamp|student|score|evidence|teacher|identity/i.test(text));
  assert.deepEqual(parseProgressFile(exportProgress({})), {});
});

test('not reviewed and individual reset are the absence of an entry, with no timestamps', () => {
  const original: Progress = {[a]: 'confident', [b]: 'developing'};
  const changed = setSelfAssessment(original, a, 'needs-practice');
  assert.deepEqual(changed, {[a]: 'needs-practice', [b]: 'developing'});
  assert.deepEqual(setSelfAssessment(changed, a, 'not-reviewed'), {[b]: 'developing'});
  assert.deepEqual(original, {[a]: 'confident', [b]: 'developing'});
  assert.throws(() => setSelfAssessment(original, 'unknown', 'confident'), /unknown curriculum node/);
});

test('manual merge preserves conflicts unless each overwritten node is accepted', () => {
  const current: Progress = {[a]: 'confident', [b]: 'developing'};
  const incoming: Progress = {[a]: 'needs-practice', [b]: 'developing', [c]: 'confident'};
  const beforeCurrent = JSON.stringify(current), beforeIncoming = JSON.stringify(incoming);
  assert.deepEqual(importConflicts(current, incoming), [a]);
  assert.deepEqual(applyImport(current, incoming, 'merge'), {...current, [c]: 'confident'});
  assert.deepEqual(applyImport(current, incoming, 'merge', [a]), incoming);
  assert.deepEqual(applyImport(current, incoming, 'merge', [b]), {...current, [c]: 'confident'});
  assert.equal(JSON.stringify(current), beforeCurrent);
  assert.equal(JSON.stringify(incoming), beforeIncoming);
});

test('replacement is explicit, cancellation preserves current reference and no input is mutated', () => {
  const current: Progress = {[a]: 'confident'}, incoming: Progress = {[b]: 'needs-practice'};
  assert.deepEqual(applyImport(current, incoming, 'replace'), incoming);
  assert.notEqual(applyImport(current, incoming, 'replace'), incoming);
  assert.deepEqual(applyImport(current, {}, 'replace'), {});
  assert.equal(applyImport(current, incoming, 'cancel'), current);
  assert.deepEqual(current, {[a]: 'confident'});
});

test('entire transfer rejects unknown nodes, invalid values, versions, identity and result fields', () => {
  const valid: Progress = {[a]: 'developing'};
  const invalid = [
    'not json', 'null', '[]', '{}',
    file(valid, {schemaVersion: '2.0'}), file(valid, {mapVersion: '1.0'}),
    file({[a]: 'developing', unknown: 'confident'}), file({[a]: 'secure'}),
    file({[a]: 'not-reviewed'}), file({[a]: {value: 'confident', score: 4}}),
    file(null), file([]), file(valid, {student: {id: 'private'}}),
    file(valid, {identity: 'private'}), file(valid, {scores: [4]}),
    file(valid, {teacherComments: ['private']}), file(valid, {timestamp: '2026-11-05'}),
    file(valid, {unexpected: true}),
    '{"schemaVersion":"1.0","mapVersion":"2.0","selfAssessments":{"__proto__":"confident"}}',
  ];
  const current: Progress = {[b]: 'confident'};
  const before = JSON.stringify(current);
  for (const text of invalid) {
    assert.throws(() => {const preview = parseProgressFile(text); applyImport(current, preview, 'replace');});
    assert.equal(JSON.stringify(current), before);
  }
  assert.equal(({} as Record<string, unknown>).confident, undefined);
});

test('import size limit counts UTF-8 bytes and rejects oversize before parsing', () => {
  assert.throws(() => parseProgressFile(' '.repeat(MAX_IMPORT_BYTES + 1)), /too large/);
  assert.throws(() => parseProgressFile('é'.repeat(MAX_IMPORT_BYTES / 2 + 1)), /too large/);
});

test('local persistence saves only validated student progress and clear removes only its key', () => {
  const storage = memoryStorage({'chemistree-v2': 'untouched old data'});
  const progress: Progress = {[a]: 'needs-practice'};
  assert.deepEqual(saveProgress(storage, progress), {ok: true});
  assert.deepEqual(loadProgress(storage), {progress});
  assert.deepEqual(JSON.parse(storage.values.get(STORAGE_KEY)!), JSON.parse(exportProgress(progress)));
  assert.deepEqual(clearProgress(storage), {ok: true});
  assert.equal(storage.values.has(STORAGE_KEY), false);
  assert.equal(storage.values.get('chemistree-v2'), 'untouched old data');
});

test('unavailable, quota-full and malformed storage report failures without losing session state', () => {
  const progress: Progress = {[a]: 'developing'};
  const broken = {
    getItem() {throw new Error('SecurityError');},
    setItem() {throw new Error('QuotaExceededError');},
    removeItem() {throw new Error('SecurityError');},
  };
  for (const storage of [null, broken]) {
    const loaded = loadProgress(storage);
    assert.deepEqual(loaded.progress, {});
    assert.match(loaded.message!, /could not be read/);
    const saved = saveProgress(storage, progress);
    assert.equal(saved.ok, false); assert.match(saved.message!, /unavailable or full/);
    const cleared = clearProgress(storage);
    assert.equal(cleared.ok, false); assert.match(cleared.message!, /could not be removed/);
  }
  const corrupt = memoryStorage({[STORAGE_KEY]: '{bad'});
  assert.match(loadProgress(corrupt).message!, /has not been changed/);
  assert.equal(corrupt.values.get(STORAGE_KEY), '{bad');
  assert.deepEqual(progress, {[a]: 'developing'});
});
