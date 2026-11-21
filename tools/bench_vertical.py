"""Whole-building trials. Upper floors have plans (the fire-egress signs) but no survey photos yet, so the starting position is
injected instead of coming from a photo; everything after that is the real app: destination, route to a stair both floors share,
second leg on the arrival floor, hand-off to the glasses. An independent Dijkstra in Python checks each answer.
Usage: bench_vertical.py <out dir> [n] [seed]"""
import sys, os, json, math, random, subprocess, time, heapq
from playwright.sync_api import sync_playwright
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 30; rnd = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 8)
os.makedirs(out, exist_ok=True); web = os.path.join(os.path.dirname(__file__), '..', 'web'); D = json.load(open(web + '/pack/indoor/default.json')); FL = {f['id']: f for f in D['floors']}
UP = ['f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8']
def graph(f):                                   # independent of the app: same drawn corridors, own densify + Dijkstra
    N_, E = [], {}
    def add(p): N_.append(p); E[len(N_) - 1] = []; return len(N_) - 1
    own = []
    for pi, pl in enumerate(f['paths']):
        prev = None
        for i in range(len(pl) - 1):
            A, B = pl[i], pl[i + 1]; L = math.dist(A, B); n = max(1, round(L / 6))
            for t in range(0 if i == 0 else 1, n + 1):
                k = add([A[0] + (B[0] - A[0]) * t / n, A[1] + (B[1] - A[1]) * t / n]); own.append(pi)
                if prev is not None: d = math.dist(N_[prev], N_[k]); E[prev].append((k, d)); E[k].append((prev, d))
                prev = k
    for i in range(len(N_)):
        for j in range(i + 1, len(N_)):
            if own[i] != own[j] and math.dist(N_[i], N_[j]) <= 20: d = math.dist(N_[i], N_[j]); E[i].append((j, d)); E[j].append((i, d))
    return N_, E
G = {k: graph(f) for k, f in FL.items() if f.get('paths')}
def dist(fid, a, b):
    N_, E = G[fid]; near = lambda p: min(range(len(N_)), key=lambda i: math.dist(N_[i], p)); s, t = near(a), near(b); Dd = {s: 0}; pq = [(0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == t: return (d + math.dist(N_[s], a) + math.dist(N_[t], b)) * FL[fid]['m_per_px']
        if d > Dd.get(u, 1e18): continue
        for v, w in E[u]:
            if d + w < Dd.get(v, 1e18): Dd[v] = d + w; heapq.heappush(pq, (d + w, v))
    return None
def best_independent(sf, sp, df, dp_name):
    dest = next(d for d in FL[df]['dests'] if d['name'] == dp_name)['p']
    if sf == df: return dict(total=dist(sf, sp, dest), via=None)
    b = None
    for a in FL[sf]['dests']:
        if not a['name'].startswith('Stair'): continue
        t = next((d for d in FL[df]['dests'] if d['name'] == a['name']), None)
        if not t: continue
        d1, d2 = dist(sf, sp, a['p']), dist(df, t['p'], dest)
        if d1 is None or d2 is None: continue
        if not b or d1 + d2 < b['total']: b = dict(total=d1 + d2, via=a['name'])
    return b
def onpath(fid, pts):                           # worst distance (m) of the interior route points from the drawn corridors
    N_, _ = G[fid]; return max([min(math.dist(p, q) for q in N_) for p in pts[1:-1]] or [0]) * FL[fid]['m_per_px']
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8769', '-d', web], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); runs = []
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); cx = b.new_context(service_workers='block', viewport={'width': 430, 'height': 900})
    cx.route('**/ntfy.sh/**', lambda r: r.abort()); cx.route('**/api/state**', lambda r: r.abort())
    ph = cx.new_page(); ph.goto('http://localhost:8769/indoor.html?room=vbench'); ph.wait_for_function("document.getElementById('packline').textContent.length>10", timeout=30000)
    gl = cx.new_page(); gl.set_viewport_size({'width': 600, 'height': 600}); gl.goto('http://localhost:8769/glasses.html?room=vbench'); time.sleep(1)
    for m in range(N):
        sf = 'f8' if m < 6 else rnd.choice(UP); f = FL[sf]; N_, _ = G[sf]
        if m == 0: eb = next(d for d in f['dests'] if d['name'] == 'Elevator Bank B')['p']; sp = max(N_, key=lambda q: math.dist(q, eb))        # the far corner of the 8th floor
        else: sp = rnd.choice(N_)
        sp = [round(sp[0]), round(sp[1])]; h = rnd.randrange(360); mode = 'exit' if (m < 3 or rnd.random() < 0.5) else 'dest'
        if mode == 'dest':
            df = rnd.choice([k for k in ['f1s'] + UP]); cand = [d['name'] for d in FL[df]['dests'] if not (df == sf and math.dist(d['p'], sp) < 30)]; dn = rnd.choice(cand)
        ph.evaluate("t=>{FIX={floor:t.f,x:t.x,y:t.y,heading:t.h,inliers:0,conf:'injected (no photos on this floor yet)'}; DEST=null;}", dict(f=sf, x=sp[0], y=sp[1], h=h))
        if mode == 'exit': ph.click('#exitBtn')
        else: ph.evaluate("([f,n])=>{const L=destsOf(f),i=L.findIndex(d=>d.name===n); DEST={...L[i],floor:f}; document.getElementById('dsel').value=f+'|'+i; updateGo(); drawPlan();}", [df, dn])
        J = "ROUTE&&({pts:ROUTE.pts,steps:ROUTE.steps,total:ROUTE.total,via:ROUTE.via||null,mapped:ROUTE.mapped,noLink:!!ROUTE.noLink,after:ROUTE.after||0,dest:DEST&&DEST.name,dfloor:DEST&&DEST.floor})"
        R1 = ph.evaluate(J); run = dict(n=m + 1, start_floor=FL[sf]['label'], sf=sf, sp=sp, mode=mode, checks={}, ok=False)
        if not R1 or R1['noLink']: run['why'] = 'no route'; runs.append(run); print(m + 1, 'FAIL no route'); continue
        df, dn = R1['dfloor'], R1['dest']; run.update(dest=dn, dest_floor=FL[df]['label'], df=df, via=R1['via'], leg1=dict(pts=R1['pts'], m=round(R1['total']), steps=[s['turn'] for s in R1['steps']]))
        shot = m < 4 or m % 7 == 0
        if shot: ph.click('#go'); ph.wait_for_function("/sent to room/.test(document.getElementById('syncinfo').textContent)", timeout=20000); time.sleep(1); gl.screenshot(path='%s/v%02d_l1_glasses.png' % (out, m + 1)); ph.locator('#planbox').screenshot(path='%s/v%02d_l1_plan.png' % (out, m + 1)); ph.evaluate("document.getElementById('syncinfo').textContent=''")
        R2 = None
        if df != sf:
            ph.evaluate("([f,via])=>{const T=destsOf(f).find(d=>d.name===via); FIX={floor:f,x:T.p[0],y:T.p[1],heading:0,inliers:0,conf:'injected'}; reroute(); updateGo(); return setFloor(f);}", [df, R1['via']]); R2 = ph.evaluate(J)
            run['leg2'] = dict(pts=R2['pts'], m=round(R2['total']), steps=[s['turn'] for s in R2['steps']])
            if shot: ph.click('#go'); ph.wait_for_function("/sent to room/.test(document.getElementById('syncinfo').textContent)", timeout=20000); time.sleep(1); gl.screenshot(path='%s/v%02d_l2_glasses.png' % (out, m + 1)); ph.locator('#planbox').screenshot(path='%s/v%02d_l2_plan.png' % (out, m + 1)); ph.evaluate("document.getElementById('syncinfo').textContent=''")
        total = R1['total'] + (R2['total'] if R2 else 0); ind = best_independent(sf, sp, df, dn); dest_p = next(d for d in FL[df]['dests'] if d['name'] == dn)['p']; last = (R2 or R1)['pts'][-1]
        C = run['checks']; C['route_on_corridors'] = R1['mapped'] and (not R2 or R2['mapped']); C['stays_on_corridors_m'] = round(max(onpath(sf, R1['pts']), onpath(df, R2['pts']) if R2 else 0), 1)
        C['uses_stair'] = df == sf or (R1['via'] or '').startswith('Stair'); C['ends_at_target'] = math.dist(last, dest_p) < 1
        C['app_m'] = round(total); C['independent_m'] = round(ind['total']) if ind else None; C['independent_via'] = ind['via'] if ind else None
        C['shortest'] = bool(ind) and total <= ind['total'] * 1.05 + 3
        if mode == 'exit':                      # is it really the nearest exit? try every street exit independently
            alt = min((best_independent(sf, sp, 'f1s', d['name']) or dict(total=1e9))['total'] for d in FL['f1s']['dests'] if d['name'].startswith('Exit')); C['nearest_exit_m'] = round(alt); C['nearest'] = total <= alt * 1.05 + 3
        run['ok'] = C['route_on_corridors'] and C['stays_on_corridors_m'] <= 2 and C['uses_stair'] and C['ends_at_target'] and C['shortest'] and C.get('nearest', True); run['total'] = round(total)
        runs.append(run); print(m + 1, 'F' + run['start_floor'], '->', dn[:26], 'F' + run['dest_floor'], 'via', run['via'], round(total), 'm | indep', C['independent_m'], C['independent_via'], '|', 'OK' if run['ok'] else 'FAIL ' + json.dumps(C), flush=True)
    b.close()
finally: srv.terminate()
json.dump(runs, open(out + '/runs.json', 'w')); print(sum(r['ok'] for r in runs), '/', len(runs))
