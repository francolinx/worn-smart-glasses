"""Floor-1 site survey, 20 Nov 2026 (75 iPhone photos, 9 stations x 8 directions + 3 extras).
Positions are plan pixels; headings are degrees clockwise from plan-up (plan-up = east, Jay St at the bottom).
Headings are a least-squares fit of three things: the rotation measured between overlapping photos at a station (ORB +
homography, the strong term), a few views that are square-on to a wall or straight down a corridor (anchors), and the
phone compass. The compass agreed with the building in the lobby, was 35-50 degrees out in the corridor and useless
inside A 105, so it only counts in S1-S5. Expect about +-10 degrees where photos overlap, +-20 elsewhere, and +-2 m."""
ST = [
 # name, plan, (x, y), first photo index, headings
 ("S1 Atrium (Jay St glass, theater shell)", "f1", (400, 1140), 0,  [271, 314, 1, 41, 84, 125, 178, 230]),
 ("S2 Information desk / turnstiles",        "f1", (585, 1085), 8,  [270, 318, 359, 45, 92, 136, 181, 229]),
 ("S3 Behind the escalators / Elevator Bank B", "f1", (665, 735), 16, [269, 315, 360, 53, 89, 136, 176, 222]),
 ("S4 Corridor doors / Exit Stair E",        "f1", (725, 1016), 24, [272, 325, 1, 35, 89, 144, 186, 229]),
 ("S5 Corridor outside A 105",               "f1", (810, 1020), 32, [266, 313, 350, 28, 87, 139, 177, 227]),
 ("S6 A 105 north-east corner (north door)", "a105", (300, 290), 40, [270, 308, 354, 45, 92, 134, 172, 240]),
 ("S7 A 105 north-west corner (windows)",    "a105", (215, 790), 48, [273, 329, 19, 61, 95, 133, 178, 204]),
 ("S8 A 105 south-west corner (windows)",    "a105", (1185, 790), 56, [284, 326, 8, 55, 121, 168, 186, 247]),
 ("S9 A 105 south-east corner (south door)", "a105", (1100, 290), 64, [275, 328, 11, 44, 73, 137, 194, 241]),
 ("X1 A 105 front, looking at the boards (north half)", "a105", (700, 300), 72, [320]),
 ("X2 A 105 front, looking at the boards (south half)", "a105", (760, 300), 73, [35]),
 ("X3 A 105 front, looking back at the windows",        "a105", (700, 240), 74, [180]),
]
# people are visible: the published thumbnail is blurred (radius in px at 640 wide). Matching uses features only.
BLUR = {8:4, 9:5, 10:9, 15:4, 18:3, 28:6, 36:9, 37:9, 38:4, 39:9, 43:7, 44:7, 45:7, 46:7, 50:7, 51:7, 52:6, 56:6, 57:9,
        58:8, 59:6, 63:4, 64:9, 65:8, 69:7, 70:9, 71:9, 72:9, 73:10, 74:8}
def photos():
    out = []
    for si, (name, plan, (x, y), i0, hs) in enumerate(ST):
        for k, h in enumerate(hs):
            out.append(dict(i=i0 + k, id="pre:p%02d" % (i0 + k), station=si, station_name=name, floor=plan, x=x, y=y, heading=h))
    return out
