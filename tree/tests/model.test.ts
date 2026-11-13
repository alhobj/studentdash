import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {map, validateGraph, ancestors, prompt} from '../src/curriculum';
import {parseImport, status, STORAGE_KEY} from './support/assessment/model';

const read = (file: string) => JSON.parse(fs.readFileSync(file, 'utf8'));
const a = parseImport(read('tests/fixtures/prototype/student-1001.json'));
const b = parseImport(read('tests/fixtures/prototype/student-1002.json'));
const foundation = 'ib-2025-structure-1.1.1';
const bond = 'ib-2025-structure-2.2.1';
const polarity = 'ib-2025-structure-2.2.6';

test('official objective identities have valid endpoints and acyclic prerequisites', () => {
  assert.equal(map.version, '2.0');
  assert.ok(map.nodes.length > 100);
  assert.equal(new Set(map.nodes.map(n => n.id)).size, map.nodes.length);
  assert.ok(map.nodes.every(n => n.id.startsWith('ib-2025-')));
  assert.ok(validateGraph());
  for (const node of map.nodes) assert.ok(!ancestors(node.id).includes(node.id));
});

test('new fictional demos preserve learner IDs and keep distinct direct evidence', () => {
  assert.equal(a.student.externalId, 'prism-1001');
  assert.equal(b.student.externalId, 'prism-1002');
  assert.notEqual(a.student.id, b.student.id);
  assert.equal(status(a, foundation), 'Evidence: secure');
  assert.equal(status(b, foundation), 'Evidence: revisit');
  assert.ok(a.evidence.every(e => e.id.startsWith('v2-')));
  assert.equal(status({...a, evidence: [a.evidence[0]]}, foundation), 'Limited evidence');
});

test('absence, missing, exemption, pending and thematic tags never imply low mastery', () => {
  assert.equal(status(a, bond), 'Not assessed');
  assert.equal(status(b, bond), 'Not assessed');
  assert.equal(status(a, polarity), 'Not assessed');
  for (const state of ['missing', 'exempt', 'absent', 'pending'] as const) {
    assert.equal(status({...a, evidence: [{...a.evidence[0], status: state, score: 0}]}, foundation), 'Not assessed');
  }
  assert.equal(status({...a, evidence: [{...a.evidence[0], scope: 'thematic', score: 0}]}, foundation), 'Not assessed');
});

test('coverage, self-assessment and teacher judgment do not alter direct evidence', () => {
  const learner = {...a, evidence: [], covered: [foundation], selfAssessments: {[foundation]: 'confident' as const},
    teacherJudgments: [{nodeId: foundation, judgment: 'secure' as const, date: '2026-11-04', note: 'Fictional'}]};
  assert.equal(status(learner, foundation), 'Not assessed');
});

test('invalid imports fail without mutating existing learner data', () => {
  const before = JSON.stringify(a);
  for (const change of [
    {schemaVersion: '2.0'}, {covered: ['bad-id']}, {student: {id: 'x'}},
    {evidence: [{...a.evidence[0], score: 99}]}, {evidence: [a.evidence[0], a.evidence[0]]},
    {students: [a.student, b.student]}, {selfAssessments: {'ct-particles': 'confident'}},
    {teacherJudgments: [{...a.teacherJudgments[0], nodeId: 'ct-particles'}]},
  ]) assert.throws(() => parseImport({...a, ...change}));
  assert.equal(JSON.stringify(a), before);
});

test('legacy map exports are explicitly rejected without remapping IDs', () => {
  const old = read('tests/fixtures/legacy-student-1001.json');
  const before = JSON.stringify(old);
  assert.throws(() => parseImport(old), /teacher-reviewed migration/);
  assert.throws(() => parseImport({...old, mapVersion: '2.0'}), /Unknown Chemistree node ID/);
  assert.equal(JSON.stringify(old), before);
  assert.equal(STORAGE_KEY, 'chemistree-v2');
});

test('scores must be finite and graded records need valid bounds', () => {
  for (const score of [NaN, Infinity, -Infinity, -1]) {
    assert.throws(() => parseImport({...a, evidence: [{...a.evidence[0], score}]}));
  }
  for (const change of [{score: undefined}, {maxScore: undefined}, {maxScore: 0}, {maxScore: Infinity}]) {
    assert.throws(() => parseImport({...a, evidence: [{...a.evidence[0], ...change}]}));
  }
});

test('generated prompts cite the official objective and distinguish editorial scaffolding', () => {
  for (const node of map.nodes) {
    const text = prompt(node, 'HL');
    assert.ok(text.includes(node.official.code));
    assert.ok(text.includes(node.official.statement));
    assert.ok(text.includes('editorial'));
    assert.ok(text.includes('ONE question'));
    assert.ok(text.includes('hint'));
    for (const privateValue of [a.student.externalId, a.student.id, a.student.label, ...a.evidence.map(e => e.id)]) {
      assert.ok(!text.includes(privateValue));
    }
  }
});

test('prerequisite arrays match edge data and references resolve', () => {
  for (const node of map.nodes) {
    assert.deepEqual([...node.prerequisites].sort(), map.edges.filter(e => e.type === 'prerequisite' && e.target === node.id).map(e => e.source).sort());
    for (const ref of node.syllabusRefs) assert.ok(map.syllabus.some(s => s.id === ref));
    for (const resource of node.resources) assert.ok(map.resources.some(r => r.id === resource));
  }
});

test('broad tags cannot reuse a score as direct evidence for several objectives', () => {
  const broad = {...a.evidence[0], nodeIds: [foundation, bond]};
  assert.throws(() => parseImport({...a, evidence: [broad]}));
  assert.doesNotThrow(() => parseImport({...a, evidence: [{...broad, scope: 'thematic'}]}));
});
