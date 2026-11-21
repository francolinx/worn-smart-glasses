"""Simulated missions on the real survey photos. Each mission: a random start station and a random destination. At each leg the
"wearer" looks in a random direction; that survey photo is REMOVED from the pack (hold-out), degraded to stand in for a different
camera (crop, shift, tilt, exposure, noise, JPEG) and pushed through the real phone page and the real glasses page in headless
Chrome. Usage: bench_missions.py <dir with p00.jpg...> <out dir> [n] [seed]"""
import sys, os, json, math, random, subprocess, time, io
from PIL import Image, ImageEnhance, ImageFilter, ImageChops
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import survey_floor1 as S
from playwright.sync_api import sync_playwright
src, out = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 20; rnd = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 2026)
os.makedirs(out, exist_ok=True); web = os.path.join(os.path.dirname(__file__), '..', 'web')
PH = {p['i']: p for p in S.photos()}; BY = {}
for p in PH.values(): BY.setdefault(p['station'], []).append(p)
DESTS = [('f1', 'Exit: Main Entrance (Jay St)'), ('f1', 'Elevator Bank B'), ('f1', 'Escalator to 2nd floor'), ('f1', 'Information desk'), ('f1', 'Exit Stair E (by corridor doors)'),
         ('f1', "Women's restroom (corridor)"), ('f1', 'A 103'), ('f1', 'A 106'), ('f1', 'Courtyard doors'), ('f1', 'Theater (orchestra)'),
         ('a105', 'Whiteboards (front)'), ('a105', 'Windows (Jay St side)'), ('a105', 'South cabinets'), (None, 'NEAREST EXIT')]
DOOR = {('Door A 105 (north)', 'a105'): 5, ('Door A 105 (north)', 'f1'): 4, ('Door A 105 (south)', 'a105'): 8}     # station you are at after stepping through
w180 = lambda a: (a + 180) % 360 - 180
def degrade(i):
    im = Image.open('%s/p%02d.jpg' % (src, i)).convert('RGB'); w, h = im.size; k = rnd.uniform(0.78, 0.92); cw, ch = int(w * k), int(h * k)
    im = im.rotate(rnd.uniform(-4, 4), resample=Image.BICUBIC, center=(w / 2, h / 2))
    x = int((w - cw) * rnd.uniform(0.1, 0.9)); y = int((h - ch) * rnd.uniform(0.2, 0.8)); im = im.crop((x, y, x + cw, y + ch))
    yaw = math.degrees(math.atan(((x + cw / 2) - w / 2) / (0.667 * w)))
    im = ImageEnhance.Brightness(im).enhance(rnd.uniform(0.7, 1.2)); im = ImageEnhance.Contrast(im).enhance(rnd.uniform(0.85, 1.1)); im = im.resize((960, 720)).filter(ImageFilter.GaussianBlur(rnd.uniform(0, 1.0)))
    a = np.asarray(im).astype(np.int16) + np.random.RandomState(rnd.randrange(1 << 30)).normal(0, 5, (720, 960, 3)); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    f = '%s/q.jpg' % out; im.save(f, quality=rnd.randint(55, 75)); return f, im, yaw
def pov(im, i, hud_png, path):                   # what the wearer sees: the scene with the display on top (black = transparent)
    if i in S.BLUR: im = im.filter(ImageFilter.GaussianBlur(S.BLUR[i] * 1.5))
    base = im.resize((800, 600)); hud = Image.open(hud_png).convert('RGB').resize((460, 460)); layer = Image.new('RGB', base.size, 'black'); layer.paste(hud, (170, 70))
    ImageChops.screen(ImageEnhance.Brightness(base).enhance(0.6), layer).save(path, quality=82)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8767', '-d', web], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); runs = []
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); IOS = os.environ.get('ENGINE') == 'webkit'      # ENGINE=webkit: phone page in WebKit with an iPhone profile, glasses page at the M6's 640x480
    if IOS: wb = p.webkit.launch(); cx = wb.new_context(**p.devices['iPhone 15 Pro']); gcx = b.new_context(service_workers='block', viewport={'width': 640, 'height': 480})
    else: cx = b.new_context(service_workers='block', viewport={'width': 430, 'height': 900}); gcx = cx
    for c in {cx, gcx}: c.route('**/ntfy.sh/**', lambda r: r.abort()); c.route('**/api/state**', lambda r: r.abort())
    ph = cx.new_page(); perr = []; ph.on('pageerror', lambda e: perr.append(str(e))); ph.goto('http://localhost:8767/indoor.html?room=bench'); ph.wait_for_function("document.getElementById('packline').textContent.length>10", timeout=30000); ph.evaluate('window.ALL=REFS.slice()')
    gl = gcx.new_page(); gerr = []; gl.on('pageerror', lambda e: gerr.append(str(e)))
    if not IOS: gl.set_viewport_size({'width': 600, 'height': 600})
    gl.goto('http://localhost:8767/glasses.html?room=bench' + ('&m6=1' if IOS else ''))
    for m in range(N):
        st = rnd.randrange(9)
        while True:
            df, dn = rnd.choice(DESTS)
            if not (df == 'a105' and S.ST[st][1] == 'a105' and dn == 'South cabinets' and st in (7, 8)): break
        run = dict(n=m + 1, start=S.ST[st][0], dest=dn, legs=[], ok=False, why=''); cur = st
        for leg in range(3):
            L = dict(station=S.ST[cur][0], shots=[], fix=None); tried = []
            for shot in range(3):                                    # no match -> look another way, up to 3 photos
                q = rnd.choice([x for x in BY[cur] if x['i'] not in tried]); tried.append(q['i']); f, im, yaw = degrade(q['i']); trueH = (q['heading'] + yaw) % 360
                ph.evaluate("id=>{REFS=ALL.filter(r=>r.id!==id); FIX=null; document.getElementById('goStatus').textContent='';}", q['id'])
                if IOS and (m + shot) % 2:                 # every other photo arrives the way a native shell hands over a glasses photo
                    import base64; ph.evaluate("u=>{window.PG_usePhoto(u)}", 'data:image/jpeg;base64,' + base64.b64encode(open(f, 'rb').read()).decode())
                else: ph.set_input_files('#capGo', f)
                ph.wait_for_function("/Matched|No surveyed/.test(document.getElementById('goStatus').textContent)", timeout=90000)
                txt = ph.inner_text('#goStatus'); fx = ph.evaluate('FIX&&({floor:FIX.floor,x:FIX.x,y:FIX.y,h:FIX.heading,inl:FIX.inliers,conf:FIX.conf})'); ms = int(txt.split('Matched in ')[1].split(' ms')[0]) if 'Matched in' in txt else None
                s = dict(photo=q['i'], matched=bool(fx), ms=ms)
                if fx:
                    mpp = 0.02 if q['floor'] == 'a105' else 0.0617
                    s.update(conf=fx['conf'], inl=fx['inl'], pos_err=round(math.hypot(fx['x'] - q['x'], fx['y'] - q['y']) * mpp, 1) if fx['floor'] == q['floor'] else 99, hdg_err=round(w180(fx['h'] - trueH), 1))
                L['shots'].append(s)
                if fx: break
            if not fx: run['why'] = 'no match in 3 photos at ' + S.ST[cur][0]; run['legs'].append(L); break
            good = s['pos_err'] <= 6 and abs(s['hdg_err']) <= 30
            # destination, route, and the same route from the true pose for comparison
            if dn == 'NEAREST EXIT': ph.click('#exitBtn')
            else: ph.evaluate("([f,n])=>{const L=destsOf(f),i=L.findIndex(d=>d.name===n); DEST={...L[i],floor:f}; document.getElementById('dsel').value=f+'|'+i; updateGo(); drawPlan();}", [df, dn])
            R = ph.evaluate("ROUTE&&({steps:ROUTE.steps,total:ROUTE.total,via:ROUTE.via||null,mapped:ROUTE.mapped,noLink:!!ROUTE.noLink,dest:DEST&&DEST.name,dfloor:DEST&&DEST.floor})")
            T = ph.evaluate("([t,keep])=>{FIX={...FIX,floor:t.floor,x:t.x,y:t.y,heading:t.h}; reroute(); const o=ROUTE&&({turn:ROUTE.steps[0]&&ROUTE.steps[0].turn,total:ROUTE.total}); FIX=keep; reroute(); return o;}", [dict(floor=q['floor'], x=q['x'], y=q['y'], h=trueH), fx | dict(heading=fx['h'], inliers=fx['inl'])])
            L.update(fix=s, route=' → '.join('%s%s' % (x['turn'], '' if x.get('vertical') else ' %d m' % x['m']) for x in R['steps']), total=round(R['total']), via=R['via'], first=R['steps'][0]['turn'] if R['steps'] else '', true_first=T['turn'], instr_ok=bool(R['steps']) and R['steps'][0]['turn'] == T['turn'], good=good, dest=R['dest'])
            ph.click('#go'); ph.wait_for_function("/sent to room/.test(document.getElementById('syncinfo').textContent)", timeout=20000)
            if IOS:                              # two different browsers: carry the relay message across by hand (stands in for the ntfy hop)
                msg = ph.evaluate("localStorage.getItem('pg_state_bench')"); gl.evaluate("m=>{localStorage.setItem('pg_state_bench',m); window.dispatchEvent(new Event('storage'));}", msg); L['msg_bytes'] = len(msg)
                time.sleep(0.9); L['glasses_ok'] = gl.evaluate("!!(state&&state.fix&&state.fix.plan&&mapOn&&SCH&&SCH[state.fix.plan])")
            else: time.sleep(0.9)
            tag = '%s/m%02d_l%d' % (out, m + 1, leg + 1); gl.screenshot(path=tag + '_map.png'); pov(im, q['i'], tag + '_map.png', tag + '_pov.jpg')      # indoors the glasses open on the floor schematic
            ph.locator('#planbox').screenshot(path=tag + '_plan.png'); L['img'] = os.path.basename(tag); run['legs'].append(L)
            if not good: run['why'] = 'wrong fix at %s (%.0f m, %.0f deg)' % (S.ST[cur][0], s['pos_err'], s['hdg_err']); break
            if R['noLink'] or not R['mapped']: run['why'] = 'no route'; break
            if R['dfloor'] == fx['floor']: run['ok'] = True; break                      # this leg ends at the destination
            nxt = DOOR.get((R['via'], R['dfloor']))
            if nxt is None: run['why'] = 'no surveyed station on the far side of ' + str(R['via']); break
            cur = nxt
        runs.append(run); print(run['n'], run['start'][:3], '->', run['dest'][:26], 'OK' if run['ok'] else 'FAIL: ' + run['why'], '| legs', len(run['legs']), '| shots', sum(len(l['shots']) for l in run['legs']), flush=True)
    b.close()
finally: srv.terminate()
json.dump(runs, open(out + '/runs.json', 'w'), indent=1)
if os.environ.get('ENGINE') == 'webkit': print('page errors: phone', perr[:5], 'glasses', gerr[:5])
