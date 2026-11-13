import {test} from 'node:test';
import assert from 'node:assert/strict';
import map from '../src/data/map.json';
import {nodeFragment, readNodeLink} from '../src/links';

test('all stable curriculum IDs round-trip as curriculum-only fragments', () => {
  for (const node of map.nodes) {
    const fragment = nodeFragment(node.id);
    assert.equal(fragment, `#node=${node.id}`);
    assert.deepEqual(readNodeLink(fragment), {nodeId: node.id});
    assert.deepEqual(readNodeLink(`#node=${node.id.replace('ib-', '%69b-')}`), {nodeId: node.id});
  }
});

test('empty fragments and internal navigation anchors do not select a new node', () => {
  for (const hash of ['', '#', '#main', '#node-details']) assert.deepEqual(readNodeLink(hash), {});
});

test('unknown IDs and malformed fragment values fail helpfully without throwing', () => {
  for (const hash of ['#node=old-ct-particles', '#node=', '#node=%', '#node=%E0%A4%A', '#node=%00', '#unknown', 'node=ib-2025-structure-1.1.1']) {
    const result = readNodeLink(hash);
    assert.equal(result.nodeId, undefined);
    assert.ok(result.error?.includes('curriculum'));
  }
  assert.throws(() => nodeFragment('ct-particles'), /curriculum node/);
});

test('extra parameters and private values cannot enter accepted fragments or error messages', () => {
  const id = map.nodes[0].id;
  for (const hash of [
    `#node=${id}&score=private-87`, `#node=${id}&node=${id}`, `#node=${id}?token=private-87`,
    `#node=${id}#private-87`, `#node=${id}=private-87`, '#node=private-87',
    `#node=${id}%26status%3Dprivate-87`, `#node=${id}+private-87`,
  ]) {
    const result = readNodeLink(hash);
    assert.equal(result.nodeId, undefined);
    assert.ok(result.error);
    assert.ok(!result.error.includes('private-87'));
  }
  assert.throws(() => nodeFragment(`${id}&score=private-87`), /curriculum node/);
});
