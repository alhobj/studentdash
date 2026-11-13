import {map} from './curriculum';

const nodeIds = new Set(map.nodes.map(node => node.id));
const INVALID_LINK = 'This curriculum link is invalid. Use a link containing only #node= followed by a known curriculum node ID, or choose a statement from the map.';
const UNKNOWN_NODE = 'This curriculum node was not found in this version of Chemistree. Search the map for its statement code or request an updated curriculum link.';

export type NodeLink = {nodeId?: string; error?: string};

/** Reads only a curriculum fragment; it never reads or changes local progress.
 * Do not echo fragment contents: a malformed external link may include private data.
 */
export function readNodeLink(hash: string): NodeLink {
  if (hash === '' || hash === '#' || hash === '#main' || hash === '#node-details') return {};
  if (!hash.startsWith('#node=')) return {error: INVALID_LINK};
  const encodedId = hash.slice('#node='.length);
  if (!encodedId || /[&=#?]/.test(encodedId)) return {error: INVALID_LINK};
  let id: string;
  try {id = decodeURIComponent(encodedId);}
  catch {return {error: INVALID_LINK};}
  if (!nodeIds.has(id)) return {error: UNKNOWN_NODE};
  return {nodeId: id};
}

/** Produces no identity, result, status, token or tracking fields. */
export function nodeFragment(id: string): string {
  if (!nodeIds.has(id)) throw new Error(UNKNOWN_NODE);
  return `#node=${encodeURIComponent(id)}`;
}
