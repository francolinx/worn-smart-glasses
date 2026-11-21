"""Vector schematic of floor 1 and Room A 105 for the glasses map (plan pixels, same frames as default.json).
Traced from the venue plan and the survey photos; approximate."""
import json
def rect(x0, y0, x1, y1, gaps=()):            # walls of a room as line segments, with door gaps: ('top'|'bottom'|'left'|'right', from, to)
    out = []
    def side(name, a, b, fixed, horiz):
        s = a
        for g in sorted([g for g in gaps if g[0] == name], key=lambda g: g[1]):
            if g[1] > s: out.append([s, fixed, g[1], fixed] if horiz else [fixed, s, fixed, g[1]])
            s = g[2]
        if s < b: out.append([s, fixed, b, fixed] if horiz else [fixed, s, fixed, b])
    side('top', x0, x1, y0, True); side('bottom', x0, x1, y1, True); side('left', y0, y1, x0, False); side('right', y0, y1, x1, False); return out
f1 = dict(mpp=0.0617, up=92, walls=[], solid=[], furn=[], exits=[], labels=[], doors=[])
W = f1['walls']
W += rect(823, 683, 983, 873, [('left', 820, 850)]) + rect(1032, 683, 1192, 873, [('left', 820, 850)])                 # A 106, A 104
W += rect(823, 882, 983, 993, [('bottom', 865, 900)]) + rect(1032, 882, 1192, 993)                                      # restrooms, service room
W += rect(823, 1050, 1192, 1275, [('top', 846, 874), ('top', 1140, 1168)])                                              # A 105
W += rect(1250, 1050, 1417, 1275, [('top', 1270, 1300)]) + rect(750, 1050, 823, 1180, [('top', 752, 782)])              # A 103, Exit Stair E
W += rect(778, 735, 810, 920)                                                                                            # elevator bank
W += [[35, 1275, 600, 1275], [820, 1275, 1558, 1275], [35, 700, 35, 1275], [1558, 667, 1558, 1275], [545, 667, 590, 667], [720, 667, 1558, 667], [750, 1000, 750, 1004], [750, 1030, 750, 1050],
      [600, 1275, 600, 1250], [820, 1275, 820, 1250]]
f1['solid'] = [[[410, 760], [545, 760], [545, 1048], [462, 1048], [462, 972], [410, 972]], [[160, 800], [365, 800], [365, 965], [160, 965]], [[35, 35], [545, 35], [545, 700], [35, 700]]]   # theater shell
f1['furn'] = [[628, 792, 652, 792], [652, 792, 652, 900], [652, 900, 628, 900], [628, 900, 628, 792], [500, 1078, 590, 1078], [590, 1078, 590, 1098], [590, 1098, 500, 1098], [500, 1098, 500, 1078]] \
           + [[x, 1062, x, 1082] for x in range(566, 731, 27)] + [[470, y, 492, y] for y in range(1080, 1251, 28)]
f1['exits'] = [dict(p=[716, 1262], t='EXIT'), dict(p=[766, 1056], t='STAIR E')]
f1['doors'] = [[860, 1050], [1154, 1050], [750, 1016]]
f1['labels'] = [dict(t='A 105', p=[1007, 1162], pri=1), dict(t='THEATER', p=[290, 520], pri=3), dict(t='A 106', p=[903, 778], pri=3), dict(t='A 104', p=[1112, 778], pri=4), dict(t='A 103', p=[1333, 1162], pri=3),
                dict(t='WC', p=[903, 938], pri=2), dict(t='ELEV', p=[794, 828], pri=2), dict(t='ESCALATOR', p=[640, 846], pri=2), dict(t='INFO', p=[545, 1088], pri=2), dict(t='JAY ST', p=[420, 1305], pri=4), dict(t='COURTYARD', p=[650, 600], pri=4)]
a = dict(mpp=0.02, up=92, walls=rect(130, 160, 1270, 855, [('top', 202, 258), ('top', 1142, 1198)]), solid=[], exits=[dict(p=[230, 150], t='EXIT'), dict(p=[1170, 150], t='EXIT')], doors=[[230, 160], [1170, 160]], labels=[], furn=[])
a['furn'] = [seg for x in (134, 1226) for seg in rect(x, 285, x + 40, 790)] + [[330, 172, 1070, 172]] + [seg for y in (345, 425, 505, 585, 665, 745) for seg in rect(265, y, 1135, y + 22)] + rect(730, 235, 800, 270)
a['labels'] = [dict(t='BOARDS', p=[700, 200], pri=2), dict(t='CABINETS', p=[205, 540], pri=3), dict(t='CABINETS', p=[1195, 540], pri=3), dict(t='WINDOWS', p=[700, 880], pri=2), dict(t='CORRIDOR', p=[700, 95], pri=2), dict(t='A 105', p=[700, 545], pri=4)]
json.dump(dict(v=1, plans=dict(f1=f1, a105=a)), open('web/pack/indoor/schematic.json', 'w'), separators=(',', ':')); print('ok')
