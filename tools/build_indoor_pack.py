"""Build web/pack/indoor/refs.json from the survey photos, using the page's own matcher (js/vpr.js in headless Chrome)
so the stored features are exactly what the phone computes. Usage: build_indoor_pack.py <dir with p00.jpg ...> <meta.json>
The photos themselves are not committed (people are in many of them); only features and small thumbnails are."""
import sys, json, base64, io, os, subprocess, time
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from survey_floor1 import photos, BLUR, ST
from playwright.sync_api import sync_playwright
src, meta = sys.argv[1], json.load(open(sys.argv[2]))
web = os.path.join(os.path.dirname(__file__), '..', 'web')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '-d', web], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
refs = []; weak = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = b.new_context(service_workers='block').new_page(); pg.goto('http://localhost:8765/indoor.html'); pg.wait_for_function('window.VPR'); pg.evaluate('VPR.load()')
        for ph in photos():
            raw = open('%s/p%02d.jpg' % (src, ph['i']), 'rb').read()
            f = pg.evaluate('''async b64 => { const im = new Image(); im.src = 'data:image/jpeg;base64,' + b64; await im.decode(); const f = await VPR.features(im);
              const enc = u8 => { let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); };
              return { n: f.n, w: f.w, h: f.h, kp: enc(new Uint8Array(f.kp.buffer)), desc: enc(f.desc) }; }''', base64.b64encode(raw).decode())
            im = Image.open(io.BytesIO(raw)).convert('RGB'); im.thumbnail((640, 640))
            if ph['i'] in BLUR: im = im.filter(ImageFilter.GaussianBlur(BLUR[ph['i']]))
            im.save(os.path.join(web, 'pack/indoor/photos/p%02d.jpg' % ph['i']), quality=72)
            t = im.copy(); t.thumbnail((200, 200)); buf = io.BytesIO(); t.save(buf, 'JPEG', quality=60)
            f['thumb'] = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
            m = meta[ph['i']]
            r = dict(id=ph['id'], floor=ph['floor'], x=ph['x'], y=ph['y'], heading=ph['heading'], f35=m['f35'], f=f, station=ph['station'], photo='pack/indoor/photos/p%02d.jpg' % ph['i'], t=m['t'], compass=round(m['hdg'], 1))
            if f['n'] < 80: weak.append(ph['i']); continue          # blank wall or plain glass: nothing to recognise
            refs.append(r); print(ph['id'], ph['floor'], f['n'])
        b.close()
finally:
    srv.terminate()
out = dict(v=2, rev='floor1-'+time.strftime('%Y%m%d-%H%M%S'), surveyed='20 Nov 2026', dests={}, paths={}, custom=[], resetFloors=['f1', 'a105'], stations=[dict(name=s[0], floor=s[1], x=s[2][0], y=s[2][1]) for s in ST], refs=refs)
json.dump(out, open(os.path.join(web, 'pack/indoor/refs.json'), 'w'), separators=(',', ':'))
print(len(refs), 'refs; too plain, left out:', weak, '; bytes', os.path.getsize(os.path.join(web, 'pack/indoor/refs.json')))
