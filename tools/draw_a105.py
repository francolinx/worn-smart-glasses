"""Room A 105 plan, redrawn from the 20 Nov survey photos. 1400x960 px, about 0.02 m/px, plan-up = east (corridor),
bottom = Jay St windows. Fixtures are placed from the photos, not measured."""
from PIL import Image, ImageDraw, ImageFont
W, H = 1400, 960; im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
def font(s):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',):
        try: return ImageFont.truetype(p, s)
        except Exception: pass
    return ImageFont.load_default()
F, f = font(22), font(15)
x0, x1, y0, y1 = 130, 1270, 160, 855
d.rectangle([x0, y0, x1, y1], outline='#1f6f96', width=6)
d.rectangle([40, 60, 1360, 110], fill='#eef4f7'); d.text((60, 72), 'CORRIDOR  (to lobby  <<   |   >> to A 103, exit)', fill='#35627a', font=F)
for dx in (230, 1170):                                   # doors on the corridor wall
    d.rectangle([dx - 28, y0 - 6, dx + 28, y0 + 6], fill='white'); d.line([dx - 28, y0, dx - 28, y0 - 40], fill='#c2185b', width=4)
    d.text((dx - 40, y0 - 44 - 18), 'DOOR', fill='#c2185b', font=f)
d.rectangle([x0 + 3, y1 - 5, x1 - 3, y1 + 5], fill='#9fd6c9')        # Jay St channel glass
d.text((560, y1 + 18), 'WINDOWS (green glass, blinds)  ·  JAY ST', fill='#2c7a69', font=F)
for cx in (x0 + 4, x1 - 44):                              # storage cabinets on both end walls
    d.rectangle([cx, 285, cx + 40, 790], fill='#d9b77c', outline='#8a6a34', width=2)
d.text((x0 + 52, 520), 'CABINETS', fill='#8a6a34', font=f); d.text((x1 - 140, 520), 'CABINETS', fill='#8a6a34', font=f)
for cx in (x0 + 6, x1 - 40):                              # recycling bins beside each door
    d.rectangle([cx, 190, cx + 34, 262], fill='#b9bec4', outline='#555', width=2)
d.text((x0 + 46, 215), 'bins', fill='#555', font=f); d.text((x1 - 82, 215), 'bins', fill='#555', font=f)
d.rectangle([330, y0 + 4, 1070, y0 + 14], fill='#333')    # whiteboards and screens (front of the room)
d.text((560, y0 + 22), 'WHITEBOARDS + 2 SCREENS  (front)', fill='#333', font=f)
d.rectangle([730, 235, 800, 270], outline='#8a6a34', width=3); d.text((736, 243), 'lectern', fill='#8a6a34', font=font(12))
for ry in (345, 425, 505, 585, 665, 745):                # desk rows, seats face the boards
    d.rounded_rectangle([265, ry, 1135, ry + 22], radius=8, fill='#e9d3a6', outline='#8a6a34', width=2)
d.text((600, 470), 'A 105', fill='#1f6f96', font=font(44))
d.text((60, 900), 'N  <<', fill='#666', font=F); d.text((1250, 900), '>>  S', fill='#666', font=F)
im.save('web/pack/indoor/a105.png')
