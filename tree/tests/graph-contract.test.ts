/** Current graph and prompt contracts, independent of the retired assessment prototype. */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {map, validateGraph, ancestors, prompt} from '../src/curriculum';

test('official objective identities have valid endpoints and acyclic prerequisites', () => {
  assert.equal(map.version, '2.0');
  assert.ok(map.nodes.length > 100);
  assert.equal(new Set(map.nodes.map(n => n.id)).size, map.nodes.length);
  assert.ok(map.nodes.every(n => n.id.startsWith('ib-2025-')));
  assert.ok(validateGraph());
  for (const node of map.nodes) assert.ok(!ancestors(node.id).includes(node.id));
});

test('generated prompts cite official objectives and distinguish editorial scaffolding', () => {
  for (const node of map.nodes) {
    const text = prompt(node, 'HL');
    for (const expected of [node.official.code, node.official.statement, 'editorial', 'ONE question', 'hint']) {
      assert.ok(text.includes(expected));
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
