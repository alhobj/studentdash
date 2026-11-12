/* Shared Chemistree prerequisite layout/router, transpiled from TypeScript. */
(()=>{const exports={};
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ROUTE_CLEARANCE = exports.CARD_HEIGHT = exports.CARD_WIDTH = void 0;
exports.buildLayout = buildLayout;
exports.segmentHitsRect = segmentHitsRect;
exports.roundedPath = roundedPath;
exports.routeEdges = routeEdges;
/** Prerequisite-ranked nodes and obstacle-aware orthogonal routes, in flow coordinates.
 * Geometry uses the full map, so filtering does not move cards or invalidate routes.
 * Placement is a reading aid, never a declaration of prerequisite relationships.
 */
exports.CARD_WIDTH = 264;
exports.CARD_HEIGHT = 172;
exports.ROUTE_CLEARANCE = 18;
function buildLayout(nodes, edges, sort = 'top') {
    const positions = {}, ids = new Set(nodes.map(n => n.id));
    const parents = new Map(nodes.map(n => [n.id, []]));
    const children = new Map(nodes.map(n => [n.id, []]));
    for (const e of edges.filter(e => e.type === 'prerequisite')) {
        if (!ids.has(e.source) || !ids.has(e.target))
            throw Error('Unknown prerequisite endpoint: ' + e.id);
        if (!parents.get(e.target).includes(e.source)) {
            parents.get(e.target).push(e.source);
            children.get(e.source).push(e.target);
        }
    }
    const depth = new Map(), active = new Set();
    function rank(id) {
        if (active.has(id))
            throw Error('Prerequisite cycle at ' + id);
        if (depth.has(id))
            return depth.get(id);
        active.add(id);
        const d = Math.max(-1, ...(sort === 'bottom' ? children : parents).get(id).map(rank)) + 1;
        active.delete(id);
        depth.set(id, d);
        return d;
    }
    for (const n of nodes)
        rank(n.id);
    // Distance from a sink counts remaining edges, not the number of descendants.
    // Reverse the ranks so dependencies still point downwards in both modes.
    if (sort === 'bottom') {
        const height = Math.max(0, ...depth.values());
        for (const [id, d] of depth)
            depth.set(id, height - d);
    }
    const rows = new Map();
    for (const n of nodes) {
        const d = depth.get(n.id);
        if (!rows.has(d))
            rows.set(d, []);
        rows.get(d).push(n.id);
    }
    const deepest = Math.max(0, ...depth.values());
    const gapX = exports.CARD_WIDTH + 56, gapY = exports.CARD_HEIGHT + 104;
    // Barycentric sweeps reduce crossings across the whole dependency network.
    // All rows share a centre, preventing cumulative rightward drift on long chains.
    for (const row of rows.values())
        row.sort((a, b) => a.localeCompare(b));
    const fractions = () => new Map([...rows.values()].flatMap(row => row.map((id, i) => [id, (i + .5) / row.length])));
    for (let pass = 0; pass < 8; pass++) {
        for (const forward of [true, false]) {
            const levels = Array.from({ length: deepest + 1 }, (_, i) => forward ? i : deepest - i);
            for (const d of levels) {
                const row = rows.get(d) || [], order = fractions();
                const neighbours = forward ? parents : children;
                const weight = (id) => { const links = neighbours.get(id); return links.length ? links.reduce((sum, p) => sum + order.get(p), 0) / links.length : order.get(id); };
                row.sort((a, b) => weight(a) - weight(b) || a.localeCompare(b));
            }
        }
    }
    const widest = Math.max(1, ...[...rows.values()].map(r => r.length));
    const offsets = new Map([...rows].map(([d, row]) => [d, (widest - row.length) / 2]));
    const x = new Map();
    const update = (d) => rows.get(d).forEach((id, i) => x.set(id, offsets.get(d) + i));
    for (const d of rows.keys())
        update(d);
    const links = [...children].flatMap(([source, targets]) => targets.map(target => [source, target]));
    const siblings = [...children.values()].filter(c => c.length > 1);
    // Minimise horizontal edge travel and sibling spread. Vertical ranks are fixed.
    // This is deterministic local optimisation, not a claim of a global minimum.
    const cost = () => links.reduce((sum, [a, b]) => sum + Math.abs(x.get(a) - x.get(b)), 0)
        + siblings.reduce((sum, c) => sum + .65 * (Math.max(...c.map(id => x.get(id))) - Math.min(...c.map(id => x.get(id)))), 0);
    const isLeaf = (id) => children.get(id).length === 0;
    // Terminal nodes flank the continuing branches; pick their cheaper left/right split.
    for (const [d, row] of rows) {
        const leaves = row.filter(isLeaf), through = row.filter(id => !isLeaf(id));
        if (!leaves.length || !through.length)
            continue;
        let best = [...row], score = Infinity;
        const start = leaves.length > 1 ? 1 : 0, end = leaves.length > 1 ? leaves.length - 1 : leaves.length;
        for (let split = start; split <= end; split++) {
            row.splice(0, row.length, ...leaves.slice(0, split), ...through, ...leaves.slice(split));
            update(d);
            const value = cost();
            if (value < score) {
                score = value;
                best = [...row];
            }
        }
        row.splice(0, row.length, ...best);
        update(d);
    }
    const valid = (row) => { const inner = row.map((id, i) => !isLeaf(id) ? i : -1).filter(i => i >= 0); return !inner.length || row.slice(inner[0], inner.at(-1) + 1).every(id => !isLeaf(id)); };
    for (let pass = 0; pass < 12; pass++) {
        let improved = false;
        for (const d of [...rows.keys()].sort((a, b) => pass % 2 ? b - a : a - b)) {
            const row = rows.get(d);
            let score = cost();
            for (let i = 0; i < row.length; i++)
                for (let j = i + 1; j < row.length; j++) {
                    [row[i], row[j]] = [row[j], row[i]];
                    if (valid(row)) {
                        update(d);
                        const candidate = cost();
                        if (candidate < score - 1e-8) {
                            score = candidate;
                            improved = true;
                            continue;
                        }
                    }
                    [row[i], row[j]] = [row[j], row[i]];
                    update(d);
                }
            // Shift whole rows towards their neighbours without collisions or widening the map.
            let best = offsets.get(d);
            for (let offset = 0; offset <= widest - row.length; offset += .5) {
                offsets.set(d, offset);
                update(d);
                const candidate = cost();
                if (candidate < score - 1e-8) {
                    score = candidate;
                    best = offset;
                    improved = true;
                }
            }
            offsets.set(d, best);
            update(d);
        }
        if (!improved)
            break;
    }
    for (const [id, value] of x)
        positions[id] = { x: 40 + value * gapX, y: 40 + depth.get(id) * gapY };
    const obstacles = nodes.map(n => ({ id: n.id, ...positions[n.id], width: exports.CARD_WIDTH, height: exports.CARD_HEIGHT }));
    return { positions, labels: [], obstacles, bounds: { x: 0, y: 0, width: Math.max(1, ...obstacles.map(r => r.x + r.width)) + 40, height: Math.max(1, ...obstacles.map(r => r.y + r.height)) + 40 } };
}
/** True only when a straight segment enters the rectangle's interior.
 * Boundary contact is allowed; routes are calculated with expanded obstacles.
 */
function segmentHitsRect(a, b, r) {
    if (a.y === b.y)
        return a.y > r.y && a.y < r.y + r.height && Math.max(a.x, b.x) > r.x && Math.min(a.x, b.x) < r.x + r.width;
    if (a.x === b.x)
        return a.x > r.x && a.x < r.x + r.width && Math.max(a.y, b.y) > r.y && Math.min(a.y, b.y) < r.y + r.height;
    throw Error('Routing segments must be horizontal or vertical');
}
function expanded(r) {
    return { ...r, x: r.x - exports.ROUTE_CLEARANCE, y: r.y - exports.ROUTE_CLEARANCE, width: r.width + 2 * exports.ROUTE_CLEARANCE, height: r.height + 2 * exports.ROUTE_CLEARANCE };
}
function simplify(points) {
    const out = [];
    for (const p of points) {
        if (out.length && out.at(-1).x === p.x && out.at(-1).y === p.y)
            continue;
        while (out.length > 1) {
            const a = out[out.length - 2], b = out[out.length - 1];
            if ((a.x === b.x && b.x === p.x) || (a.y === b.y && b.y === p.y))
                out.pop();
            else
                break;
        }
        out.push(p);
    }
    return out;
}
/** Corner radius is smaller than obstacle clearance: each curve remains inside
 * the safe corridor even where it cuts a corner of an expanded rectangle.
 */
function roundedPath(points, radius = 8) {
    if (!points.length)
        return '';
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length - 1; i++) {
        const a = points[i - 1], b = points[i], c = points[i + 1];
        const ab = Math.hypot(b.x - a.x, b.y - a.y), bc = Math.hypot(c.x - b.x, c.y - b.y);
        const r = Math.min(radius, ab / 2, bc / 2);
        const before = { x: b.x + (a.x - b.x) * r / ab, y: b.y + (a.y - b.y) * r / ab };
        const after = { x: b.x + (c.x - b.x) * r / bc, y: b.y + (c.y - b.y) * r / bc };
        path += ` L ${before.x} ${before.y} Q ${b.x} ${b.y} ${after.x} ${after.y}`;
    }
    if (points.length > 1)
        path += ` L ${points.at(-1).x} ${points.at(-1).y}`;
    return path;
}
// Small binary min-heap used by A*; avoids sorting the whole frontier per step.
class Queue {
    heap = [];
    push(id, cost) {
        const item = { id, cost };
        let i = this.heap.length;
        this.heap.push(item);
        while (i) {
            const p = (i - 1) >> 1;
            if (this.heap[p].cost <= cost)
                break;
            this.heap[i] = this.heap[p];
            i = p;
        }
        this.heap[i] = item;
    }
    pop() {
        const first = this.heap[0], last = this.heap.pop();
        if (this.heap.length && last) {
            let i = 0;
            while (i * 2 + 1 < this.heap.length) {
                let c = i * 2 + 1;
                if (c + 1 < this.heap.length && this.heap[c + 1].cost < this.heap[c].cost)
                    c++;
                if (this.heap[c].cost >= last.cost)
                    break;
                this.heap[i] = this.heap[c];
                i = c;
            }
            this.heap[i] = last;
        }
        return first;
    }
    get size() { return this.heap.length; }
}
function makeGrid(layout) {
    const obstacles = layout.obstacles.map(expanded);
    const xSet = new Set([-80, layout.bounds.width + 80]);
    const ySet = new Set([-80, layout.bounds.height + 80]);
    for (const r of obstacles) {
        xSet.add(r.x);
        xSet.add(r.x + r.width);
        ySet.add(r.y);
        ySet.add(r.y + r.height);
    }
    for (const p of Object.values(layout.positions))
        xSet.add(p.x + exports.CARD_WIDTH / 2);
    const xs = [...xSet].sort((a, b) => a - b), ys = [...ySet].sort((a, b) => a - b);
    const xIndex = new Map(xs.map((x, i) => [x, i])), yIndex = new Map(ys.map((y, i) => [y, i]));
    const width = xs.length, height = ys.length;
    const blocked = new Uint8Array(width * height);
    // Mark interiors in one pass per rectangle, then connect neighbouring free
    // points only when the entire segment is clear (thin headings also count).
    for (const r of obstacles)
        for (let yi = yIndex.get(r.y) + 1; yi < yIndex.get(r.y + r.height); yi++) {
            for (let xi = xIndex.get(r.x) + 1; xi < xIndex.get(r.x + r.width); xi++)
                blocked[yi * width + xi] = 1;
        }
    const links = new Map();
    function connect(a, b, p, q) {
        if (blocked[a] || blocked[b] || obstacles.some(r => segmentHitsRect(p, q, r)))
            return;
        const distance = Math.abs(p.x - q.x) + Math.abs(p.y - q.y);
        if (!links.has(a))
            links.set(a, []);
        if (!links.has(b))
            links.set(b, []);
        links.get(a).push({ id: b, distance });
        links.get(b).push({ id: a, distance });
    }
    for (let yi = 0; yi < height; yi++)
        for (let xi = 0; xi < width; xi++) {
            const id = yi * width + xi, p = { x: xs[xi], y: ys[yi] };
            if (xi + 1 < width)
                connect(id, id + 1, p, { x: xs[xi + 1], y: p.y });
            if (yi + 1 < height)
                connect(id, id + width, p, { x: p.x, y: ys[yi + 1] });
        }
    return { xs, ys, links, xIndex, yIndex };
}
const gridCache = new WeakMap();
const routeCache = new WeakMap();
function routeEdges(layout, edges) {
    let grid = gridCache.get(layout);
    if (!grid) {
        grid = makeGrid(layout);
        gridCache.set(layout, grid);
    }
    let cache = routeCache.get(layout);
    if (!cache) {
        cache = new Map();
        routeCache.set(layout, cache);
    }
    const { xs, ys, links, xIndex, yIndex } = grid, width = xs.length;
    const at = (id) => ({ x: xs[id % width], y: ys[Math.floor(id / width)] });
    const result = {};
    for (const edge of edges) {
        const key = edge.source + '\0' + edge.target;
        if (cache.has(key)) {
            result[edge.id] = cache.get(key);
            continue;
        }
        const source = layout.positions[edge.source], target = layout.positions[edge.target];
        if (!source || !target)
            throw Error('Unknown routing endpoint: ' + edge.id);
        const a = { x: source.x + exports.CARD_WIDTH / 2, y: source.y + exports.CARD_HEIGHT };
        const b = { x: target.x + exports.CARD_WIDTH / 2, y: target.y };
        const start = yIndex.get(a.y + exports.ROUTE_CLEARANCE) * width + xIndex.get(a.x);
        const goal = yIndex.get(b.y - exports.ROUTE_CLEARANCE) * width + xIndex.get(b.x);
        const costs = new Map([[start, 0]]), previous = new Map();
        const queue = new Queue();
        queue.push(start, 0);
        const closed = new Set();
        while (queue.size) {
            const { id } = queue.pop();
            if (closed.has(id))
                continue;
            if (id === goal)
                break;
            closed.add(id);
            for (const next of links.get(id) || []) {
                const cost = costs.get(id) + next.distance;
                if (cost >= (costs.get(next.id) ?? Infinity))
                    continue;
                costs.set(next.id, cost);
                previous.set(next.id, id);
                const p = at(next.id);
                queue.push(next.id, cost + Math.abs(p.x - b.x) + Math.abs(p.y - (b.y - exports.ROUTE_CLEARANCE)));
            }
        }
        if (start !== goal && !previous.has(goal))
            throw Error('No obstacle-free route: ' + edge.id);
        const points = [];
        let cursor = goal;
        while (cursor !== start) {
            points.push(at(cursor));
            cursor = previous.get(cursor);
        }
        points.push(at(start));
        points.reverse();
        const simplified = simplify([a, ...points, b]);
        const route = { points: simplified, path: roundedPath(simplified) };
        cache.set(key, route);
        result[edge.id] = route;
    }
    return result;
}

window.MathtreeLayout=exports;})();
