"""Trace the fire-egress signs into vectors for the glasses: the cream floor area becomes outline polygons, the orange
partition lines (rooms, stair cores, elevator cars) become wall segments. Adds them to web/pack/indoor/schematic.json."""
import json, cv2, numpy as np, os
web = os.path.join(os.path.dirname(__file__), '..', 'web'); sch = json.load(open(web + '/pack/indoor/schematic.json'))
for fid in ['f1s', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8']:
    im = cv2.imread('%s/pack/indoor/%s.jpg' % (web, fid)); b, g, r = [im[:, :, i].astype(int) for i in range(3)]
    floor = ((r + g > 330) & (b > 120) | ((r > 150) & (g > 90) & (b < 140))).astype(np.uint8) * 255      # cream floor, plus the orange lines drawn on it
    floor = cv2.morphologyEx(floor, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)); floor = cv2.morphologyEx(floor, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cs, _ = cv2.findContours(floor, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); polys = []
    for c in cs:
        if cv2.contourArea(c) < 1500: continue
        a = cv2.approxPolyDP(c, 2.5, True).reshape(-1, 2); polys.append([[int(x), int(y)] for x, y in a])
    orange = ((r > 170) & (g > 110) & (g < 200) & (b < 120) & (r - b > 90)).astype(np.uint8) * 255
    orange = cv2.dilate(orange, np.ones((2, 2), np.uint8)); L = cv2.HoughLinesP(orange, 1, np.pi / 180, threshold=22, minLineLength=18, maxLineGap=4); segs = []
    for x0, y0, x1, y1 in (L.reshape(-1, 4) if L is not None else []):
        if abs(x1 - x0) > 3 and abs(y1 - y0) > 3 and np.hypot(x1 - x0, y1 - y0) < 40: continue          # keep long diagonals, drop text speckle
        s = [int(x0), int(y0), int(x1), int(y1)]
        if any(abs(s[0] - t[0]) + abs(s[1] - t[1]) + abs(s[2] - t[2]) + abs(s[3] - t[3]) < 10 for t in segs): continue
        segs.append(s)
    sch['plans'][fid] = dict(floor=polys, walls=segs[:700], solid=[], furn=[]); print(fid, len(polys), 'outline polygons,', len(segs), 'wall segments')
json.dump(sch, open(web + '/pack/indoor/schematic.json', 'w'), separators=(',', ':')); print(os.path.getsize(web + '/pack/indoor/schematic.json'))
