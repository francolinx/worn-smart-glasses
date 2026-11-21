# Point & Go — Worn smart glasses hackathon (Nov 20–21, 2026)

**One photo tells a firefighter or police officer where they are inside a building, which way they face, and which way to go.**
No GPS, no compass, no signal needed for the fix.

## Who it is for: fire rescue and police

GPS stops at the door. Inside, steel and wiring bend the compass: on our own survey of this building the phone compass was
35 to 50 degrees out in the first-floor corridor and useless inside Room A 105. Crews work from memory and radio.

1. **Before the call (pre-incident survey).** A crew walks the building once: floor plan, plus eight photos at each junction.
   That is a 17-minute job for the first floor here (9 stations, 75 photos, 20 Nov 2026).
2. **On the call.** The responder takes one photo through the glasses. The phone matches it against the survey, offline:
   floor, position, facing.
3. **Go.** The glasses show an arrow and distance to the target room, or one tap for the nearest exit or stair.
   Routes that cross to another plan hand off at a named door or stair.

See the surveyed floor in 3D: https://francolinx.github.io/worn-smart-glasses/floor3d.html

50 simulated missions on the real survey photos, with the wearer's view for every leg: https://francolinx.github.io/worn-smart-glasses/benchmark.html
(48 of 50 reached the target; in 44 every first move matched the true pose; no fix landed in the wrong place once weak matches were refused. `tools/bench_missions.py`, `tools/bench_report.py`.)

Outdoors, the same idea works from the skyline: tap three rooftops in a photo and get position, heading and floor.

**Venue pack:** 285 Jay St (City Tech), Downtown Brooklyn. Tillary St to the north, Jay St to the west, Bridge St to the east,
and Tech Place to the south (OpenStreetMap's name for the former Johnson St alignment).

## Run it

**Live (GitHub Pages, `gh-pages` branch = `web/`):** phone https://francolinx.github.io/worn-smart-glasses/ · glasses https://francolinx.github.io/worn-smart-glasses/glasses.html
Pages has no relay function, so the hand-off there runs over the ntfy.sh topic only.

Everything in `web/` is static and solves in the browser. Host `web/` at any HTTPS URL.

| Page | Device | What it does |
|---|---|---|
| `index.html` | phone | Shoot a photo, tap 3 rooftops, get a fix, pick a destination, press **GO** |
| `indoor.html` | phone | Indoor: survey a building once (reference photos pinned to a floor plan), then shoot one photo to get your spot and heading |
| `floor3d.html` | any | 3D view of floor 1 built from the venue plan and the survey: rooms, the theater shell, Room A 105's interior, every photo station with its view wedges and photo rings, and the entry route. Tap a wedge to see that photo and its fix |
| `glasses.html` | glasses (600×600, black = transparent) | Arrow, distance, heading-up map. Press ALIGN while facing the way you shot. `?demo=1` fakes a fix |

Meta Ray-Ban Display (Developer Mode): Meta AI app → App settings → App connections → Web Apps → Add a Web App →
`https://<host>/glasses.html`. Open `https://<host>/` on the phone. Both pages share a room; add `?room=NAME` to both to change it.

Local: `cd web && python3 -m http.server 8765` (the relay function is absent locally; same-browser hand-off still works).

## How the fix works

1. Lens: focal length in pixels from the photo's EXIF 35 mm-equivalent focal length (fallback: 69° HFOV).
2. Each tapped rooftop becomes an angle off the optical axis. The two angles between three known buildings place the
   camera by three-point resection (Snellius–Pothenot), then a Gauss–Newton polish on (east, north, heading).
3. There is no sea horizon here, so camera tilt is found by choosing the pitch at which all tapped rooftops, whose heights are
   known, agree on one camera height. That height above the street gives the floor.
4. The ring is the largest move of the fix when each angle is off by ±0.5°.
5. Green ticks on the photo mark where other known rooftops should appear. If they sit on real roofs, the fix is good.

Naming a tap is quick: the list is ranked by what should be at that spot, from the window direction you chose and then from
the first rooftop you named.

## Indoor mode

GPS does not work indoors and there is no skyline, so indoor mode recognises the place itself.

1. **Survey (once per building).** Take reference photos; for each, tap where you stood on the floor plan and which way you faced.
   The photo's ORB features are stored on the phone (IndexedDB). Export the pack as one JSON file to share it or to ship it with the app.
2. **Go.** One photo is matched on the phone against every reference (Hamming matching, ratio test, RANSAC homography; OpenCV.js,
   self-hosted). Position is the best-matching reference's spot. Heading is that reference's heading, corrected by how far its
   centre has shifted sideways in the new photo.
3. The fix goes to the glasses the same way as outdoors. A service worker caches the app, so solving works with no connection;
   the hand-off to the glasses still needs one.

Bundled plans for the City Tech Academic Complex (`pack/indoor/default.json`): the first-floor venue map (The Theater at City Tech,
`AC_layout.pdf`) and the fire-egress sign at Elevator Bank B on each of floors 1 to 8 (photographed by the team), with every labelled
stair and exit as a destination and the signs' dashed egress lines as walkable paths. One reference set spans all floors, so a photo
also identifies the floor. A destination on another floor routes to the nearest stair both floors share. Scale and north are
approximate on every plan, so distances are rough; the floor-6 sign's floor number is assumed from the order the photos were taken.
### The floor-1 survey that ships with the app (`pack/indoor/refs.json`)

71 reference photos from 9 stations (atrium, information desk, behind the escalators, corridor doors by Exit Stair E, corridor
outside A 105, and the four corners of A 105) plus three from the front of the room. `tools/survey_floor1.py` holds each
photo's spot and heading; `tools/build_indoor_pack.py` computes the features with the page's own matcher. The photos themselves
are not in the repo; thumbnails with people in them are blurred.

Headings are a least-squares fit of the rotation measured between overlapping photos, a few square-on anchor views, and the
compass where it could be trusted (lobby only). Station spots were placed on the plans by eye from what the photos show.

**Measured on the real photos (leave one out: each photo matched against the other 70):**

| Area | Photos | Matched (14+ points) | Matched to the right or the adjacent station |
|---|---|---|---|
| Lobby and corridor | 38 | 35 | 35 |
| Room A 105 | 33 | 22 | 22 |

The 14 with no match are plain walls, glass, cabinet fronts and views that are mostly people. Two chance matches (a plain door,
a crowd) were removed by a geometry check on the homography. A neighbouring photo is 45 degrees away, so this is a harder test
than re-shooting a surveyed view, but it is still the same camera, the same evening and the same lighting. **No photo from the
glasses camera has been matched yet.** Heading agreement between neighbours is about 1 degree median, which measures consistency,
not truth: absolute headings are good to about 10 to 20 degrees and positions to about 2 m.

## Data in `web/pack/` (rebuild with `python3 tools/build_pack.py`)

| File | Content | Source |
|---|---|---|
| `sat_block.jpg`, `sat_area.jpg` | Aerial mosaics, 460 m at 0.13 m/px and 1.4 km at 0.39 m/px, Web Mercator, bounds in `sat.json` | NYS ITS orthoimagery (public domain) |
| `osm.json` | Streets, named places, subway entrances, the four block corners; raw extracts in `data/osm_raw/` | © OpenStreetMap contributors (ODbL) |
| `buildings.json` | 1,161 footprints with roof height and ground elevation: all within 750 m, plus every building over 45 m within 2.2 km | NYC Open Data building footprints + PLUTO (public domain) |
| `landmarks.json` | 218 rooftops over 55 m, labelled by street address; 8 carry a common name from `tools/landmark_names.json` | derived |

## Limits

- Outdoor mode is measured only on synthetic photos so far (exact with perfect taps; within the ring with 12–25 px tap noise).
- Indoor mode is measured on the survey phone's own photos (above), not yet on the glasses camera. Position is the nearest
  surveyed station, not a continuous track. Aim at fixed things (doors, signs, boards, bins), not at people or blank walls.
- The floor-1 plan is a venue map, not a survey drawing: the 3D view and the distances are approximate.
- The glasses do not track you as you walk: position stays at the photo fix until the next photo.
- Heading on the glasses: after ALIGN, the photo's solved heading plus head turn since then. Before ALIGN, the device compass if it reports north.
- Roof heights are roof level, not spires or mechanical floors. Tap the roof line.
- The hand-off relay is an in-memory function plus a public ntfy.sh topic named after the room. Do not put anything private in it.
- Not yet ported to the MicroLumin M6 SDK. The glasses page is plain HTML built for a 600×600 web view.

## Prior work (disclosure)

The resection solver is a JavaScript port of `spark/skyfix/city/resect.py` from our Code Metal Forge entry
(Team 3, "Lost and Found", Nov 6–8, 2026, open source: github.com/CodeMetalForge-Hackathon/Team-3). The glasses arrow page
started from `glasses/index.html` in the same repo. New for Worn: the browser-only solver, pitch and floor from rooftop
heights, ranked landmark naming, the Brooklyn pack, the phone → glasses hand-off, and the heading-up map.
