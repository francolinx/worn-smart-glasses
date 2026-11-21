"""Turn bench_missions.py output into web/benchmark.html. Usage: bench_report.py <bench dir>"""
import json, sys, os, shutil, glob, statistics as st, html
src = sys.argv[1]; R = json.load(open(src + '/runs.json')); web = os.path.join(os.path.dirname(__file__), '..', 'web'); e = html.escape
for f in glob.glob(web + '/bench/m*_pov.jpg'): os.remove(f)
for f in glob.glob(src + '/m*_pov.jpg'): shutil.copy(f, web + '/bench/')
shutil.copy(src + '/runs.json', web + '/bench/runs.json')
alllegs = [l for r in R for l in r['legs']]; legs = [l for l in alllegs if l.get('fix')]; shots = [s for l in alllegs for s in l['shots']]; fx = [l['fix'] for l in legs]
h = sorted(abs(s['hdg_err']) for s in fx); ms = sorted(s['ms'] for s in fx); strict = [r for r in R if r['ok'] and all(l['instr_ok'] for l in r['legs'])]
rows = [('Missions that reached the destination', f"{sum(r['ok'] for r in R)} / {len(R)}"), ('…with every first move the same as from the true pose', f"{len(strict)} / {len(R)}"),
 ('Photo fixes (legs)', str(len(legs))), ('First photo matched', f"{sum(l['shots'][0]['matched'] for l in alllegs)} / {len(alllegs)}"), ('Matched within 3 photos', f"{len(legs)} / {len(alllegs)}"),
 ('Wrong-place fixes (more than 6 m off)', str(sum(s['pos_err'] > 6 for s in fx))), ('Fix on the exact station / one station over (5 m)', f"{sum(s['pos_err'] == 0 for s in fx)} / {sum(0 < s['pos_err'] <= 6 for s in fx)}"),
 ('Heading error: median / 90th pct / worst', f"{st.median(h):.0f}° / {h[int(len(h) * .9)]:.0f}° / {h[-1]:.0f}°"), ('Match time (desktop Chrome): median / worst', f"{st.median(ms) / 1000:.1f} s / {ms[-1] / 1000:.1f} s"),
 ('Confidence shown: high / medium / low', ' / '.join(str(sum(s['conf'] == c for s in fx)) for c in ('high', 'medium', 'low')))]
for a, b in rows: print(a, '|', b)
for r in R:
    if not (r['ok'] and all(l['instr_ok'] for l in r['legs'])): print(' ', r['n'], r['start'][:3], '->', r['dest'][:24], '|', r['why'] or '; '.join('%s got %s, true %s (pos %.0f m, hdg %+.0f)' % (l['station'][:2], l['first'], l['true_first'], l['fix']['pos_err'], l['fix']['hdg_err']) for l in r['legs'] if l.get('fix') and not l['instr_ok']))
body = ''.join(f"<tr><td>{e(a)}</td><td><b>{e(b)}</b></td></tr>" for a, b in rows); runs = ''
for r in R:
    so = r['ok'] and all(l['instr_ok'] for l in r['legs'])
    runs += f"<div class='run {'ok' if so else 'warn' if r['ok'] else 'bad'}'><h3>#{r['n']} · {e(r['start'].split(' ', 1)[1])} → {e(r['dest'])} <span>{'PASS' if so else 'REACHED, a first move was off' if r['ok'] else 'FAIL'}</span></h3>"
    if r['why']: runs += f"<div class='why'>{e(r['why'])}</div>"
    for i, l in enumerate(r['legs']):
        miss = sum(not s['matched'] for s in l['shots'])
        if not l.get('fix'): runs += f"<div class='leg'>Leg {i + 1} at {e(l['station'])}: no match in {len(l['shots'])} photos.</div>"; continue
        f = l['fix']; runs += f"<div class='leg'><img loading='lazy' src='bench/{l['img']}_pov.jpg'><div>Leg {i + 1} · at <b>{e(l['station'])}</b>{' · ' + str(miss) + ' photo(s) with no match first' if miss else ''}<br>Fix: {f['pos_err']:.0f} m off, heading {f['hdg_err']:+.0f}°, {f['inl']} points, confidence {f['conf']}, {f['ms']} ms<br>Route ({l['total']} m): {e(l['route'])}<br>{'First move matches the true pose.' if l['instr_ok'] else '<span class=x>First move: ' + e(l['first']) + '. From the true pose it would be: ' + e(l['true_first']) + '.</span>'}</div></div>"
    runs += '</div>'
open(web + '/benchmark.html', 'w').write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Point & Go · {len(R)} simulated missions</title>
<style>body{{margin:0;background:#0e1116;color:#e6e8eb;font:15px system-ui,-apple-system,sans-serif;padding:12px;max-width:860px;margin:auto}}a{{color:#ffb020}}h1{{font-size:20px}}h3{{font-size:15px;margin:0 0 6px}}h3 span{{float:right;font-size:12px}}
table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid #2a313b;padding:6px 4px}}.run{{background:#161b22;border:1px solid #2a313b;border-left:5px solid #3fb950;border-radius:10px;padding:10px;margin:10px 0}}.run.warn{{border-left-color:#ffb020}}.run.bad{{border-left-color:#f85149}}
.leg{{display:flex;gap:10px;align-items:flex-start;margin-top:8px;font-size:13px;color:#c5ccd3}}.leg img{{width:46%;max-width:330px;border-radius:8px}}.why,.x{{color:#ffb020}}.mut{{color:#9aa3ad;font-size:13px}}</style></head><body>
<h1>{len(R)} simulated missions · floor 1, 285 Jay St</h1>
<p class="mut">Fire rescue / police persona: the wearer is somewhere on floor 1, takes one photo, and is routed to a random target. <a href="indoor.html">App</a> · <a href="floor3d.html">3D floor</a></p>
<table>{body}</table>
<p class="mut"><b>How a run works.</b> A random start station and target. The wearer looks in a random direction: that survey photo is taken out of the pack, then cropped, shifted, tilted, re-exposed, blurred, noised and re-compressed to stand in for another camera, and sent through the real phone page and the real glasses page in headless Chrome. No match means look another way (up to 3 photos). If the route leaves the plan through a door, the next photo is taken on the other side. Each picture is the scene with the glasses' floor schematic on top.</p>
<p class="mut"><b>What this does not prove.</b> The test photos come from the survey phone, on the survey evening, from the survey spots. A photo from the glasses camera, from a spot between stations, in smoke or in the dark, has not been tried. <code>tools/bench_missions.py</code>, seed 2027.</p>
{runs}</body></html>""")
