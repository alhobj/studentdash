import {test} from 'node:test';
import assert from 'node:assert/strict';
import source from '../src/data/map.json';
import runtime from '../src/generated/student-map.json';
import practice from '../src/data/practice.json';
import index from '../src/generated/practice-index.json';
import {projectStudentMap} from '../scripts/generate-student-data';
import {map, prompt} from '../src/curriculum';

test('compact student data preserves every official statement, citation and teaching field', () => {
  assert.deepEqual(runtime, projectStudentMap(source));
  assert.equal(runtime.nodes.length, source.nodes.length);
  for (let i = 0; i < source.nodes.length; i++) {
    const original = source.nodes[i], node = map.nodes[i];
    for (const field of ['id', 'title', 'group', 'level', 'explanation', 'practice', 'criteria', 'misconception', 'prerequisites', 'syllabusRefs'] as const) assert.deepEqual(node[field], original[field]);
    const actualParts = node.official.statementParts ?? [{text: node.official.statement, script: 'normal'}];
    assert.deepEqual(actualParts, original.official.statementParts);
    assert.deepEqual({...node.official, statementParts: actualParts}, original.official);
    assert.ok(prompt(node, 'SL').includes(original.objective));
  }
  assert.deepEqual(runtime.edges, source.edges.map(({provenance, ...edge}) => edge));
  assert.deepEqual(runtime.resources, source.resources);
  assert.ok(JSON.stringify(runtime).length < JSON.stringify(source).length * .85);
});

test('guided practice discovery index matches all bundled editorial exercises', () => {
  assert.deepEqual(index, practice.map(exercise => exercise.nodeId));
  assert.equal(new Set(index).size, index.length);
});
