"""Curriculum presentation follows explicit captured parent references."""
from .curriculum import node_index

def tree(curriculum, evidence=None):
    nodes = node_index(curriculum or {})
    order_by_evidence = evidence is not None
    evidence = evidence or {}
    children = {}
    for key, node in nodes.items():
        children.setdefault(node.get('parent'), []).append(key)
    roots = children.get(None, []) + children.get('', [])
    if len(roots) == 1 and children.get(roots[0]):
        roots = children[roots[0]]
    def ordered(items):
        return sorted(items, key=lambda item: not (item['evidence'] and item['evidence'].get('count', 0))) if order_by_evidence else items
    def build(key):
        return dict(id=key, label=nodes[key]['label'], code=nodes[key].get('code', ''),
                    evidence=evidence.get(key), children=ordered([build(k) for k in children.get(key, [])]))
    return ordered([build(k) for k in roots])


def selection(curriculum):
    nodes = node_index(curriculum or {})
    groups = tree(curriculum)
    visible = set()
    def visit(group):
        visible.add(group['id'])
        for child in group['children']:
            visit(child)
    for group in groups:
        visit(group)
    return dict(groups=groups, containers=[dict(id=key, label=node['label'], code=node.get('code', ''))
                 for key, node in nodes.items() if key not in visible])
