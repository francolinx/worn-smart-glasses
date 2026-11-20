# Point & Go — Worn smart glasses hackathon (Nov 20–21, 2026)

Point your phone at the skyline, tap three rooftops, and the glasses show an arrow and distance to where you want to go.
No GPS and no compass: the position, the heading and the floor come from one photo.

**Venue pack:** 285 Jay St (City Tech), Downtown Brooklyn. Tillary St to the north, Jay St to the west, Bridge St to the east,
and Tech Place to the south (OpenStreetMap's name for the former Johnson St alignment).

## Run it

**Live (GitHub Pages, `gh-pages` branch = `web/`):** phone https://francolinx.github.io/worn-smart-glasses/ · glasses https://francolinx.github.io/worn-smart-glasses/glasses.html
Pages has no relay function, so the hand-off there runs over the ntfy.sh topic only.

Everything in `web/` is static and solves in the browser. Host `web/` at any HTTPS URL.

| Page | Device | What it does |
|---|---|---|
| `index.html` | phone | Shoot a photo, tap 3 rooftops, get a fix, pick a destination, press **GO** |
| `glasses.html` | glasses (600×600, black = transparent) | Arrow, distance, heading-up block map. `?demo=1` fakes a fix |

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

## Data in `web/pack/` (rebuild with `python3 tools/build_pack.py`)

| File | Content | Source |
|---|---|---|
| `sat_block.jpg`, `sat_area.jpg` | Aerial mosaics, 460 m at 0.13 m/px and 1.4 km at 0.39 m/px, Web Mercator, bounds in `sat.json` | NYS ITS orthoimagery (public domain) |
| `osm.json` | Streets, named places, subway entrances, the four block corners; raw extracts in `data/osm_raw/` | © OpenStreetMap contributors (ODbL) |
| `buildings.json` | 1,161 footprints with roof height and ground elevation: all within 750 m, plus every building over 45 m within 2.2 km | NYC Open Data building footprints + PLUTO (public domain) |
| `landmarks.json` | 218 rooftops over 55 m, labelled by street address; 8 carry a common name from `tools/landmark_names.json` | derived |

## Limits

- Measured only on synthetic photos so far (exact with perfect taps; within the ring with 12–25 px tap noise). No real photo
  from the venue has been scored yet.
- The glasses do not track you as you walk: position stays at the photo fix until the next photo.
- Heading on the glasses is the device compass if it reports one; otherwise head-turn heading zeroed to the photo's direction.
- Roof heights are roof level, not spires or mechanical floors. Tap the roof line.
- The hand-off relay is an in-memory function plus a public ntfy.sh topic named after the room. Do not put anything private in it.
- Not yet ported to the MicroLumin M6 SDK. The glasses page is plain HTML built for a 600×600 web view.

## Prior work (disclosure)

The resection solver is a JavaScript port of `spark/skyfix/city/resect.py` from our Code Metal Forge entry
(Team 3, "Lost and Found", Nov 6–8, 2026, open source: github.com/CodeMetalForge-Hackathon/Team-3). The glasses arrow page
started from `glasses/index.html` in the same repo. New for Worn: the browser-only solver, pitch and floor from rooftop
heights, ranked landmark naming, the Brooklyn pack, the phone → glasses hand-off, and the heading-up map.
