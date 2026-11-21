"""Storyboards, vertical views and the handoff report from run_stories.py output. Usage: build_handoff.py <stories dir>"""
import sys, os, json, html, subprocess, time
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
src = sys.argv[1]; web = os.path.join(os.path.dirname(__file__), '..', 'web'); H = web + '/handoff'; os.makedirs(H, exist_ok=True); R = json.load(open(src + '/stories.json')); e = html.escape
B = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s); N = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', s)
KIND = dict(photo=('PHOTO FIX', '#3dff7a'), injected=('POSITION SET (no photos on this floor yet)', '#ffb020'), turn=('AT THE TURN (simulated position)', '#8fdcff'), transit=('AT THE DOOR / STAIR', '#ffc400'), arrive=('ARRIVED', '#3dff7a'))
def board(r):
    fs = [f for f in r['frames'] if f.get('img')]; cols = 4; W = 380; rows = (len(fs) + cols - 1) // cols; im = Image.new('RGB', (cols * W + 20, 120 + rows * 470), '#0e1116'); d = ImageDraw.Draw(im)
    d.text((16, 12), f"{r['persona'].upper()} · {r['unit']}", fill='#ff8a80', font=B(20)); d.text((16, 42), r['title'], fill='#ffd27a', font=B(28)); d.text((16, 84), f"{len(fs)} frames · {r['metres']} m of corridor · {r['photo_fixes']} photo fixes · {'PASS' if r['ok'] else 'FAIL'}", fill='#9aa3ad', font=N(18))
    for k, f in enumerate(fs):
        x, y = 10 + (k % cols) * W, 120 + (k // cols) * 470; src_img = src + '/' + (f['pov'] if f.get('pov') else f['img'] + '.png'); t = Image.open(src_img).convert('RGB')
        if f.get('pov'): t = t.resize((360, 270)); im.paste(t, (x, y + 45))
        else: im.paste(t.resize((360, 360)), (x, y))
        lab, col = KIND[f['kind']]; d.text((x, y + 364), f"{k + 1}. {lab}", fill=col, font=B(14)); d.text((x, y + 384), f"Floor {f['floor']} · {f['goal']}"[:46], fill='#e6e8eb', font=N(14))
        if f['kind'] == 'photo': cap = f"{f['station'].split(' ', 1)[1]}: {f['pos_err']:.0f} m off, {f['hdg_err']:+d} deg" + (f", {f['tries']} tries" if f['tries'] > 1 else '')
        elif f['kind'] == 'transit': cap = f"{f['via']}: floor {f['frm']} to {f['to_name'].replace(' · fire plan', '').replace(' · venue map', '')}"
        elif f['kind'] == 'arrive': cap = 'At ' + f['dest']
        else: cap = 'Next: ' + (f['steps'][0] if f.get('steps') else '')
        d.text((x, y + 404), cap[:48], fill='#9aa3ad', font=N(14))
    im.save(f"{H}/{r['id']}_board.jpg", quality=84)
for r in R: board(r)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8772', '-d', web], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_context(service_workers='block', viewport={'width': 1100, 'height': 760}).new_page(); pg.goto('http://localhost:8772/building3d.html'); pg.wait_for_function('window.__b&&window.__b.ready', timeout=30000); time.sleep(4)
    pg.click('#bExp'); pg.click('#bShell'); pg.click('#bCity'); pg.add_style_tag(content='#bar,#top{display:none!important}#info{bottom:10px!important}')
    for i, r in enumerate(R):
        pg.evaluate('i=>__b.story(i)', i); pg.click('#bStack', force=True) if False else pg.evaluate("document.getElementById('bStack').click()"); time.sleep(2.2); pg.screenshot(path='/tmp/_v.png'); Image.open('/tmp/_v.png').convert('RGB').save(f"{H}/{r['id']}_stack.jpg", quality=82)
        pg.evaluate("document.getElementById('bSide').click()"); time.sleep(2.2); pg.screenshot(path='/tmp/_v.png'); Image.open('/tmp/_v.png').convert('RGB').save(f"{H}/{r['id']}_side.jpg", quality=82)
        if i == 0:
            n = 0
            for k in range(1, len(r['legs']) + 1):
                pg.evaluate('k=>__b.story(0,k)', k); time.sleep(1.2); pg.screenshot(path='/tmp/_v.png'); Image.open('/tmp/_v.png').convert('RGB').save(f"{H}/s00_phase{k}.jpg", quality=80)
    b.close()
finally: srv.terminate()
print('boards and vertical views written:', len(os.listdir(H)))
