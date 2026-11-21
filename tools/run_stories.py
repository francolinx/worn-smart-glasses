"""Scenario runs through the real phone and glasses pages, with a glasses frame at every fix and every turn.
Floor 1 (venue plan and Room A 105) uses real survey photos, held out and degraded, for each fix. Floors 2-8 have plans but no
photos yet, so positions there are injected. Frames between fixes are simulated positions at each turn of the route.
Usage: run_stories.py <photo dir> <out dir>"""
import sys, os, json, math, random, subprocess, time
from PIL import Image, ImageEnhance, ImageFilter, ImageChops, ImageDraw, ImageFont
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import survey_floor1 as S, pathcheck as PC
from playwright.sync_api import sync_playwright
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); web = PC.web; rnd = random.Random(11); FL = PC.FL
BY = {}
for p in S.photos(): BY.setdefault(p['station'], []).append(p)
ARRIVE = {('Door A 105 (north)', 'a105'): 5, ('Door A 105 (south)', 'a105'): 8, ('Door A 105 (north)', 'f1'): 4}
STORIES = [
 dict(id='s00', unit='FDNY Engine 207 + Ladder 110', persona='Fire rescue', title='Wheelchair user down at the 8th-floor elevators',
      story='Smoke on 8. The elevators are out. A wheelchair user called from Room A 105 an hour ago, then again from the 8th-floor elevator lobby before the line went quiet. The crew checks A 105 first, finds it empty, then climbs Stair E to the 8th-floor elevators and carries the person down the same stair.',
      start=('f1', 1), goals=[('a105', 'Whiteboards (front)', 'Check Room A 105: not there'), ('f8', 'Elevator Bank B', 'Climb to the 8th-floor elevator lobby: person found'), (None, 'NEAREST EXIT', 'Carry down and out')]),
 dict(id='s01', unit='FDNY Ladder 110', persona='Fire rescue', title='Primary search, 5th floor, far end', story='Fire reported on 5. The search team enters from Jay St, climbs to 5, searches to Stair A at the south end, and leaves by the nearest stair to the street.',
      start=('f1s', 'Exit: Jay St (main lobby)'), goals=[('f5', 'Stair A', 'Search to the far end of 5'), (None, 'NEAREST EXIT', 'Withdraw')]),
 dict(id='s02', unit='Building fire warden', persona='Fire rescue', title='Evacuate the 7th-floor elevator lobby', story='Alarm on 7. People are waiting at dead elevators. The warden\'s glasses show the nearest stair and the street exit below it.',
      start=('f7', 'Elevator Bank B'), goals=[(None, 'NEAREST EXIT', 'Lead the group out')]),
 dict(id='s03', unit='NYPD ESU entry team', persona='Police', title='Shots reported, upper auditorium, floor 3', story='Callers report shots near the upper auditorium on 3. The entry team comes in by the loading dock, away from the lobby, climbs to 3, reaches the auditorium, then holds Stair H.',
      start=('f1s', 'Exit: loading dock (south)'), goals=[('f3', 'Auditorium (upper)', 'Move to the auditorium'), ('f3', 'Stair H', 'Hold the north stair')]),
 dict(id='s04', unit='NYPD patrol, first on scene', persona='Police', title='Lockdown sweep of the first-floor classrooms', story='Lockdown. Two officers enter by the main doors and clear the classroom corridor room by room: A 105, A 103, A 106, then the elevator lobby.',
      start=('f1', 1), goals=[('f1', 'Door A 105 (north)', 'A 105 door'), ('f1', 'A 103', 'A 103'), ('f1', 'A 106', 'A 106'), ('f1', 'Elevator Bank B', 'Elevator lobby')]),
 dict(id='s05', unit='FDNY EMS 31 Adam', persona='Paramedics', title='Cardiac arrest in Room A 105', story='A student has collapsed at the south end of A 105. The medics come in the main entrance with the stretcher, reach the patient, and take the shortest way back out.',
      start=('f1', 1), goals=[('a105', 'South cabinets', 'Reach the patient'), ('f1', 'Exit: Main Entrance (Jay St)', 'Stretcher out to the ambulance')]),
 dict(id='s06', unit='FDNY EMS 31 Adam', persona='Paramedics', title='Fall at the 4th-floor escalator landing', story='Elevators are held for the fire department, so the medics take the stairs to 4, reach the escalator landing, and bring the patient down to Jay St.',
      start=('f1s', 'Exit: Jay St (main lobby)'), goals=[('f4', 'Escalator', 'Reach the patient'), (None, 'NEAREST EXIT', 'Carry down and out')]),
 dict(id='s07', unit='FDNY Rescue 2', persona='Fire rescue', title='Occupants trapped at the far end of 8', story='Three people are sheltering by Stair F at the far end of 8. Rescue 2 goes up Stair D from the east side, crosses the floor to them, and takes them down.',
      start=('f1s', 'Exit: east (by Stair D)'), goals=[('f8', 'Stair F', 'Reach the group'), (None, 'NEAREST EXIT', 'Bring them down')]),
 dict(id='s08', unit='FDNY Engine 207', persona='Fire rescue', title='Stretch a line to the 6th floor', story='The engine company enters at the loading dock, takes the hose up to 6 by Stair D and advances across the floor to Stair F.',
      start=('f1s', 'Exit: loading dock (south)'), goals=[('f6', 'Stair D', 'Standpipe on 6'), ('f6', 'Stair F', 'Advance across the floor')]),
 dict(id='s09', unit='NYPD patrol', persona='Police', title='Escort a class out from the 2nd-floor escalator', story='A class is held at the top of the escalator on 2. Officers bring them down a stair and out to Jay St, away from the lobby.',
      start=('f2', 'Escalator'), goals=[('f1s', 'Exit: Jay St (by Stair E)', 'Out to Jay St')]),
 dict(id='s10', unit='FDNY EMS + Ladder 110', persona='Paramedics', title='From A 105 to a patient in the upper auditorium', story='While treating in A 105, the crew is sent to a second patient in the upper auditorium on 2. Three plans in one trip: the room, the first floor, the second floor.',
      start=('a105', 8), goals=[('f2', 'Auditorium (upper)', 'Second patient')]),
]
def degrade(i):
    im = Image.open('%s/p%02d.jpg' % (src, i)).convert('RGB'); w, h = im.size; k = rnd.uniform(0.8, 0.92); cw, ch = int(w * k), int(h * k); im = im.rotate(rnd.uniform(-3, 3), resample=Image.BICUBIC)
    x = int((w - cw) * rnd.uniform(0.2, 0.8)); y = int((h - ch) * rnd.uniform(0.3, 0.7)); im = im.crop((x, y, x + cw, y + ch)); yaw = math.degrees(math.atan(((x + cw / 2) - w / 2) / (0.667 * w)))
    im = ImageEnhance.Brightness(im).enhance(rnd.uniform(0.75, 1.1)).resize((960, 720)); a = np.asarray(im).astype(np.int16) + np.random.RandomState(rnd.randrange(1 << 30)).normal(0, 4, (720, 960, 3))
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); f = out + '/q.jpg'; im.save(f, quality=65); return f, im, yaw
def pov(im, i, hud, path):
    if i in S.BLUR: im = im.filter(ImageFilter.GaussianBlur(S.BLUR[i] * 1.5))
    base = im.resize((800, 600)); h = Image.open(hud).convert('RGB').resize((460, 460)); layer = Image.new('RGB', base.size, 'black'); layer.paste(h, (170, 70)); ImageChops.screen(ImageEnhance.Brightness(base).enhance(0.6), layer).save(path, quality=82)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8771', '-d', web], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); OUT = []
J = "ROUTE&&({pts:ROUTE.pts,steps:ROUTE.steps,total:ROUTE.total,via:ROUTE.via||null,toPlan:ROUTE.toPlan||null,then:ROUTE.then||null,mapped:ROUTE.mapped,noLink:!!ROUTE.noLink,dest:DEST&&DEST.name,dfloor:DEST&&DEST.floor})"
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); cx = b.new_context(service_workers='block', viewport={'width': 430, 'height': 900})
    cx.route('**/ntfy.sh/**', lambda r: r.abort()); cx.route('**/api/state**', lambda r: r.abort())
    ph = cx.new_page(); ph.goto('http://localhost:8771/indoor.html?room=story'); ph.wait_for_function("document.getElementById('packline').textContent.length>10", timeout=30000); ph.evaluate('window.ALL=REFS.slice()')
    gl = cx.new_page(); gl.set_viewport_size({'width': 600, 'height': 600}); gl.goto('http://localhost:8771/glasses.html?room=story'); time.sleep(1)
    def send(tag):
        ph.evaluate("document.getElementById('syncinfo').textContent=''"); ph.click('#go'); ph.wait_for_function("/sent to room/.test(document.getElementById('syncinfo').textContent)", timeout=20000); time.sleep(0.8); gl.screenshot(path=tag + '.png')
    def setdest(g):
        if g[1] == 'NEAREST EXIT': ph.click('#exitBtn')
        else: ph.evaluate("([f,n])=>{const L=destsOf(f),i=L.findIndex(d=>d.name===n); if(i<0) throw new Error('no destination '+n+' on '+f); DEST={...L[i],floor:f}; document.getElementById('dsel').value=f+'|'+i; updateGo(); drawPlan();}", [g[0], g[1]])
        return ph.evaluate(J)
    for st in STORIES:
        rec = dict(id=st['id'], unit=st['unit'], persona=st['persona'], title=st['title'], story=st['story'], frames=[], legs=[], errors=[], photo_fixes=0, shots=0, metres=0); print('==', st['id'], st['title'], flush=True)
        plan, start = st['start']; station = start if isinstance(start, int) else None; pos = None if station is not None else PC.dest(plan, start); head = rnd.randrange(360); n = 0
        try:
          for gi, g in enumerate(st['goals']):
            for hop in range(4):
                tag = '%s/%s_%02d' % (out, st['id'], n); n += 1; fr = dict(img=os.path.basename(tag), goal=g[2], plan=plan, floor=FL[plan]['label'])
                if plan in ('f1', 'a105') and station is not None:                      # a real photo fix
                    fx = None; tried = []
                    for shot in range(3):
                        q = rnd.choice([x for x in BY[station] if x['i'] not in tried]); tried.append(q['i']); f, im, yaw = degrade(q['i']); rec['shots'] += 1
                        ph.evaluate("id=>{REFS=ALL.filter(r=>r.id!==id); FIX=null; document.getElementById('goStatus').textContent='';}", q['id']); ph.set_input_files('#capGo', f)
                        ph.wait_for_function("/Matched|No surveyed/.test(document.getElementById('goStatus').textContent)", timeout=90000); fx = ph.evaluate('FIX&&({floor:FIX.floor,x:FIX.x,y:FIX.y,h:FIX.heading,inl:FIX.inliers,conf:FIX.conf})')
                        if fx: break
                    if not fx: rec['errors'].append('no photo match in 3 tries at ' + S.ST[station][0]); raise StopIteration
                    mpp = FL[q['floor']]['m_per_px']; pe = math.hypot(fx['x'] - q['x'], fx['y'] - q['y']) * mpp if fx['floor'] == q['floor'] else 99; he = ((fx['h'] - (q['heading'] + yaw) + 180) % 360) - 180
                    if pe > 6: rec['errors'].append('wrong-place fix at %s (%.0f m)' % (S.ST[station][0], pe))
                    fr.update(kind='photo', station=S.ST[station][0], tries=len(tried), pos_err=round(pe, 1), hdg_err=round(he), conf=fx['conf'], photo=q['i']); rec['photo_fixes'] += 1; pos = [fx['x'], fx['y']]; plan = fx['floor']
                else:
                    ph.evaluate("t=>{FIX={floor:t.f,x:t.x,y:t.y,heading:t.h,inliers:0,conf:'position injected'}; return setFloor(t.f);}", dict(f=plan, x=pos[0], y=pos[1], h=head)); fr.update(kind='injected')
                R = setdest(g)
                if not R or R['noLink']: rec['errors'].append('no route from %s to %s' % (FL[plan]['name'], g[1])); raise StopIteration
                end = R['pts'][-1]; ind = PC.dist(plan, pos, end); offc = PC.off_corridor(plan, R['pts'])
                if not R['mapped']: rec['errors'].append('leg off the drawn corridors on ' + FL[plan]['name'])
                if ind is not None and R['total'] > ind * 1.05 + 3: rec['errors'].append('leg longer than the independent shortest path on %s: %.0f vs %.0f m' % (FL[plan]['name'], R['total'], ind))
                if offc > 2: rec['errors'].append('route leaves the corridors by %.1f m on %s' % (offc, FL[plan]['name']))
                if R['via'] and not R['via'].startswith(('Door', 'Stair')): rec['errors'].append('used ' + R['via'])
                fr.update(steps=[s['turn'] + ('' if s.get('vertical') else ' %d m' % s['m']) for s in R['steps']], total=round(R['total']), dest=R['dest'], via=R['via'], check_m=round(ind) if ind else None)
                send(tag)
                if fr['kind'] == 'photo': pov(im, fr['photo'], tag + '.png', tag + '_pov.jpg'); fr['pov'] = os.path.basename(tag) + '_pov.jpg'
                rec['frames'].append(fr); rec['legs'].append(dict(plan=plan, label=FL[plan]['label'], pts=R['pts'])); rec['metres'] += R['total']
                for k in range(1, len(R['pts']) - 1):                                  # what the display shows at each turn on the way
                    a, c = R['pts'][k - 1], R['pts'][k]; hd = (math.degrees(math.atan2(c[0] - a[0], -(c[1] - a[1]))) + 360) % 360
                    ph.evaluate("t=>{FIX={...FIX,floor:t.f,x:t.x,y:t.y,heading:t.h}; updateGo(); drawPlan();}", dict(f=plan, x=c[0], y=c[1], h=hd)); R2 = ph.evaluate(J); tag2 = '%s/%s_%02d' % (out, st['id'], n); n += 1; send(tag2)
                    rec['frames'].append(dict(img=os.path.basename(tag2), kind='turn', plan=plan, floor=FL[plan]['label'], goal=g[2], steps=[s['turn'] + ('' if s.get('vertical') else ' %d m' % s['m']) for s in R2['steps']], total=round(R2['total']), dest=R2['dest'], via=R2['via']))
                a_, c_ = R['pts'][-2], R['pts'][-1]; hd = (math.degrees(math.atan2(c_[0] - a_[0], -(c_[1] - a_[1]))) + 360) % 360       # at the end of this leg: the door, the stair, or the target itself
                ph.evaluate("t=>{FIX={...FIX,floor:t.f,x:t.x,y:t.y,heading:t.h}; updateGo(); drawPlan();}", dict(f=plan, x=c_[0], y=c_[1], h=hd)); tag3 = '%s/%s_%02d' % (out, st['id'], n); n += 1; send(tag3); endimg = os.path.basename(tag3)
                if R['dfloor'] == plan or not R['via']:                               # arrived
                    a, c = R['pts'][-2], R['pts'][-1]; head = (math.degrees(math.atan2(c[0] - a[0], -(c[1] - a[1]))) + 360) % 360; pos = c; station = None
                    if math.dist(c, PC.dest(R['dfloor'], R['dest'])) > 1: rec['errors'].append('did not end at ' + R['dest'])
                    rec['frames'].append(dict(kind='arrive', img=endimg, plan=plan, floor=FL[plan]['label'], goal=g[2], dest=R['dest'])); break
                nxt = R['toPlan']; rec['frames'].append(dict(kind='transit', img=endimg, plan=plan, floor=FL[plan]['label'], via=R['via'], frm=FL[plan]['label'], to=FL[nxt]['label'], to_name=FL[nxt]['name'], goal=g[2]))
                station = ARRIVE.get((R['via'], nxt)); plan = nxt; pos = PC.dest(nxt, R['via']); head = rnd.randrange(360)
                if nxt in ('f1', 'a105') and station is None: rec['errors'].append('no surveyed station beyond ' + R['via'] + ': position there is injected')
            else: rec['errors'].append('goal not reached in 4 hops: ' + g[1])
            if plan in ('f1', 'a105') and station is None:                             # next goal starts where we stand; on surveyed plans re-fix at the nearest station
                cand = [(math.dist(pos, s[2]), i) for i, s in enumerate(S.ST[:9]) if s[1] == plan]; d0, i0 = min(cand); station = i0 if d0 * FL[plan]['m_per_px'] < 9 else None
        except StopIteration: pass
        rec['ok'] = not [e for e in rec['errors'] if 'injected' not in e]; rec['metres'] = round(rec['metres']); OUT.append(rec); print('  ', 'OK' if rec['ok'] else 'FAIL', rec['errors'], '| frames', len(rec['frames']), '| photo fixes', rec['photo_fixes'], '|', rec['metres'], 'm', flush=True)
    b.close()
finally: srv.terminate()
json.dump(OUT, open(out + '/stories.json', 'w')); print(sum(r['ok'] for r in OUT), '/', len(OUT))
