"""Independent shortest-path check on the drawn corridors (own graph + Dijkstra; shares nothing with the app but the plan data)."""
import json, math, heapq, os
web = os.path.join(os.path.dirname(__file__), '..', 'web'); D = json.load(open(web + '/pack/indoor/default.json')); FL = {f['id']: f for f in D['floors']}; G = {}
def graph(f):
    N, E, own = [], {}, []
    for pi, pl in enumerate(f['paths']):
        prev = None
        for i in range(len(pl) - 1):
            A, B = pl[i], pl[i + 1]; n = max(1, round(math.dist(A, B) / 6))
            for t in range(0 if i == 0 else 1, n + 1):
                N.append([A[0] + (B[0] - A[0]) * t / n, A[1] + (B[1] - A[1]) * t / n]); k = len(N) - 1; E[k] = []; own.append(pi)
                if prev is not None: d = math.dist(N[prev], N[k]); E[prev].append((k, d)); E[k].append((prev, d))
                prev = k
    for i in range(len(N)):
        for j in range(i + 1, len(N)):
            if own[i] != own[j] and math.dist(N[i], N[j]) <= 20: d = math.dist(N[i], N[j]); E[i].append((j, d)); E[j].append((i, d))
    return N, E
def dist(fid, a, b):
    if fid not in G: G[fid] = graph(FL[fid])
    N, E = G[fid]; near = lambda p: min(range(len(N)), key=lambda i: math.dist(N[i], p)); s, t = near(a), near(b); Dd = {s: 0}; pq = [(0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == t: return (d + math.dist(N[s], a) + math.dist(N[t], b)) * FL[fid]['m_per_px']
        if d > Dd.get(u, 1e18): continue
        for v, w in E[u]:
            if d + w < Dd.get(v, 1e18): Dd[v] = d + w; heapq.heappush(pq, (d + w, v))
    return None
def off_corridor(fid, pts):
    if fid not in G: G[fid] = graph(FL[fid])
    N, _ = G[fid]; return max([min(math.dist(p, q) for q in N) for p in pts[1:-1]] or [0]) * FL[fid]['m_per_px']
def dest(fid, name): return next(d for d in FL[fid]['dests'] if d['name'] == name)['p']
