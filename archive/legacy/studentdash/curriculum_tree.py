"""Curriculum presentation follows explicit captured parent references."""
from .curriculum import node_index

def tree(curriculum, evidence=None):
    nodes = node_index(curriculum or {})
    evidence = evidence or {}
    children = {}
    for key, node in nodes.items():
        children.setdefault(node.get('parent'), []).append(key)
    roots = children.get(None, []) + children.get('', [])
    if len(roots) == 1 and children.get(roots[0]):
        roots = children[roots[0]]
    def build(key):
        return dict(id=key, label=nodes[key]['label'], code=nodes[key].get('code', ''),
                    evidence=evidence.get(key), children=[build(k) for k in children.get(key, [])])
    return [build(k) for k in roots]
