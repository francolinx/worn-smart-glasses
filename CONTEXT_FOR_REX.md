# Context for Rex: everything that happened before you arrived

Written Sat 21 Nov 2026, 3 AM, by the coding assistant Franco worked with overnight. You were not at the venue on Friday, so
this is the whole story in one place. **For the steps to run the demo, read [`DEMO_DAY.md`](DEMO_DAY.md). This file is the
background.** If you use a coding agent, give it this repo and tell it: "Read DEMO_DAY.md, then CONTEXT_FOR_REX.md."

---

## 1. The event

| | |
|---|---|
| Event | Worn smart glasses hackathon, 20–21 Nov 2026 |
| Venue | City Tech Academic Complex, 285 Jay St, Brooklyn. Our room: **A 105**, first floor |
| Hardware | MicroLumin M6 waveguide glasses (640×480 display, Android 9 inside, 12 MP 110° camera, touchpad + ring) |
| Saturday | Building opens 8:00 AM. **Code freeze 2:00 PM. Table demos 2:15 PM** |
| Team | Franco (lead, **not on site Saturday**), Rex (you: running the build and the demo), Maahi (survey photos), Rachel (MacBook on Friday) |

## 2. The idea in one breath

**Point & Go.** A responder inside a building takes one photo. With no GPS, no compass and no signal needed for the fix, the
phone works out the floor, the position and the way they face, and the glasses show a floor schematic with the route.

Who it is for: **fire rescue, police, paramedics.** A crew surveys a building once on a quiet day (floor plan plus eight photos
at each junction). On the call, one photo replaces "where am I?".

Why it is believable: we measured the problem on site. In the first-floor corridor of this building the phone compass was
**35 to 50 degrees wrong**, and inside A 105 it was useless. GPS error in the photo metadata was 14 to 47 m. So we fix
position and heading from the picture instead.

## 3. How we got here (Friday, in order)

1. **6 PM.** Started as an outdoor idea reused from our Code Metal Forge entry (Boston, 6–8 Nov): tap three rooftops in a
   photo, solve position by three-point resection. That still works and is the "outdoor" page (`web/index.html`).
2. **9:25 PM.** Franco picked the direction: **indoor**, for search and rescue, in the building we are sitting in.
3. **9:40 PM.** Franco photographed the fire-egress sign at Elevator Bank B on every floor, 1 to 8. Those eight photos are our
   floor plans for the upper floors.
4. **10–10:15 PM.** Maahi walked floor 1 with an iPhone: 9 stations × 8 directions clockwise + 3 extras = **75 photos**, with
   an Otter voice log. 71 are in the app (4 were blank walls).
5. **Overnight.** Survey pack, 3D views, glasses schematic, routing across floors, benchmarks, responder scenarios, the M6
   build, these documents.

Things that did not work, so you do not repeat them:
- **Vercel / v0 hosting**: the account was restricted. We host on **GitHub Pages** (`gh-pages` branch = a copy of `web/`).
- **Phone compass indoors**: wrong, see above. The ALIGN button on the glasses replaces it.
- **Guessing from weak matches**: produced fixes in the wrong place. The app now refuses and says "look another way".

## 4. What exists right now

Live site: https://francolinx.github.io/worn-smart-glasses/

| Page | Use |
|---|---|
| `indoor.html` | **Phone app.** Take the photo, pick a target, press GO |
| `glasses.html` | **Glasses display.** Schematic, route, next move. Scales itself to any screen |
| `building3d.html` | Whole building, 8 floors, on satellite imagery. "Scenarios" plays 11 responder stories |
| `floor3d.html` | Floor 1 in 3D with every survey photo where it was taken |
| `handoff.html` | Overnight report: every scenario, frame by frame as the glasses show it |
| `benchmark.html` | 50 simulated missions with the wearer's view |
| `index.html` | Outdoor mode (rooftops). Not part of Saturday's demo |

On the glasses: white arrow = you (the way you face is up). **Green** line = route. **Red** tags = exits and stairs.
**Amber** ring = target. Top line = the next move, for example "↱ RIGHT 5 m" or "TAKE STAIR E TO FLOOR 8". Buttons:
ALIGN (press while facing the way you shot, then the map turns with your head), DEST ▸, MAP/ARROW.

The phone and glasses are paired by a **room name** in the URL (`?room=NAME`, default `worn-pg-k7x2m9q4`). They talk through
a public relay (ntfy.sh). Do not put anything private in it.

### What is surveyed with real photos
Floor 1 only: the atrium, the information desk, behind the escalators, the corridor doors by Exit Stair E, the corridor
outside A 105, the four corners of A 105 and the front of the room.

### What is plans only (no photos)
Floors 2 to 8, from the fire signs. The app can route there (stairs only, never elevators) and the glasses can draw those
floors, but **it cannot locate you there from a photo**. In the demo, anything above floor 1 is "here is the route you would
get", not "here is where the photo says you are".

## 5. The numbers (and what each one does not prove)

| Test | Result | Does not cover |
|---|---|---|
| Each survey photo matched against the other 70 | 57 matched, all to the right or the next station | Another camera |
| 50 simulated missions, Chrome | 48 reached the target, 0 wrong-place fixes | Photos from glasses |
| 50 simulated missions, iPhone-profile WebKit + 640×480 glasses page | 48 reached, 0 wrong-place, worst heading 22° | A real iPhone or M6 |
| 30 upper-floor routing trials, checked by an independent solver | 30 / 30 | Positions there are injected |
| 11 responder scenarios, floors 1–8 | 11 / 11 | Same |

"Simulated mission" means: a survey photo is removed from the pack, cropped, tilted, darkened, blurred and re-compressed, then
sent through the real phone page and the real glasses page. It is the survey phone, on the survey evening.

**The honest headline: it works on our own phone photos of floor 1. Nobody has matched a photo taken by any glasses yet.**
If a judge asks, say exactly that.

## 6. What is not done / known weak spots

1. **Never run on an M6.** The glasses app is built (by CI) but has not been installed on a device. The glasses' web view
   may be old; the page was written to cope, but that is untested.
2. **The iOS wrapper has never been compiled.** Safari works without it.
3. **M6 camera photos are untested** and the lens is much wider (110°) than the survey photos (about 74°).
4. **Window corners of A 105 match badly** (green glass, cabinet fronts). Shoot doors, signs, whiteboards, bins instead.
5. **Corridor fixes can land one station (5 m) off**, which can make the first arrow wrong. Maahi's round-2 photos fix this
   if she takes them: her shot list is in the Drive folder ("Maahi — photo shot list, round 2"). Adding photos needs the
   pack rebuilt, which needs the original photos (Drive folder "Maahi 1st floor"), `tools/survey_floor1.py` edited with each
   new station's spot and headings, then `tools/build_indoor_pack.py`. Easier on the day: use the phone page's **Survey** tab,
   "＋ From camera roll (many)", and tap each photo's spot and direction on the plan. That saves on that phone only.
6. Position is "the nearest surveyed spot" (about 2 m), not a live track. Between photos the glasses do not know you moved.
7. Storey heights in the 3D view are assumed. Corridor distances exclude the stair climb.
8. The floor-1 plan is a venue map, not an architect's drawing. Distances are approximate.

## 7. If a judge asks…

- **"How does it know where I am?"** It compares your photo with photos taken earlier at known spots (ORB features, RANSAC
  homography, all on the phone). The best match gives the spot; how far the view has shifted sideways gives the heading.
- **"Why not Wi-Fi / Bluetooth beacons / UWB?"** Those need hardware installed in every building and power that stays on. A
  photo survey needs a phone and twenty minutes. Fire departments already do pre-incident plans; this adds photos to them.
- **"What about smoke or darkness?"** Untested. It is the obvious limit of any camera method, and the answer is thermal or
  depth sensors later. The routing, the schematic and the stair logic do not depend on the camera.
- **"What did you build this weekend versus before?"** The rooftop solver is a port from our Forge entry (disclosed in
  `README.md`). Everything indoor is new: survey, matcher, multi-floor routing, glasses schematic, 3D views, M6 app.
- **"Does it need the internet?"** The fix does not: matching runs on the phone. The phone-to-glasses hand-off currently
  does (public relay). On-device hand-off over Bluetooth through the M6 SDK is the next step.
- **"Who pays?"** Building owners and fire departments (pre-incident planning is already required for many buildings), then
  campus security and hospitals. Accessibility wayfinding is the same engine with a different front end.
- **"Accuracy?"** About 2 m and 10–20° on floor 1 with our photos. Zero wrong-place fixes in 100 simulated missions once weak
  matches were refused. Say "simulated".

## 8. The SDK kit (confidential)

The MicroLumin kit must stay on your laptop. No public repo, shared link or chat. This repo contains **no** kit files.

What we learned from its documents:
- The phone SDKs (iOS `MLVisionM6SDK`, Android `connect` modules) drive the glasses' **built-in** apps over Bluetooth:
  assistant, camera, recorder, translation, album. There is no call to draw your own screen on the glasses.
- So our display is a **glasses app**: a plain Android app installed with `adb`. Ours is a full-screen web view.
- Installing a glasses app needs **Developer Mode**, which is switched on from the kit's iOS sample app **MLDemo** (Xcode,
  real iPhone, Bluetooth). MLDemo also joins the glasses to Wi-Fi.
- The kit says the glasses-side SDK and the phone-side camera stream are **missing** from it. That is why the photo comes
  from the phone, or from the glasses via MLDemo's Camera + Files screens.
- The kit's README lists an SDK crash after taking a glasses photo, with a workaround inside MLDemo.

## 9. Where everything lives

- **Code:** https://github.com/francolinx/worn-smart-glasses (`main`). Live site = `gh-pages`. Glasses APK = `apk` branch.
- **Drive, folder "MicroLumin":**
  - "Overnight handoff" → the visual report, your runbook, this context
  - "Maahi — photo shot list, round 2"
  - "Maahi 1st floor" → the 75 original survey photos
  - "Artifact Context From MicroLumin/Event" → event material
- **Voice log of the survey:** Otter, "Facility Site Survey and Photo Log" (Friday 9:57 PM).

## 10. Saturday, suggested order

| Time | Do |
|---|---|
| 8:00 | Arrive. Charge the glasses. Start Path A in `DEMO_DAY.md` (MLDemo → Developer Mode → hotspot Wi-Fi) |
| 8:45 | Install the glasses APK. Smoke test in A 105 |
| 9:15 | Try one photo **from the M6 camera** through the phone page. Note whether it matches. This decides what you claim |
| 9:45 | If Maahi is in: round-2 photos, at least the corridor spots (N2, N3) |
| 11:00 | Rehearse the 3-minute demo twice, timed, with the glasses on someone else |
| 12:30 | Stop changing code unless something is broken |
| 2:00 | Code freeze |

If you change one thing only: make sure the glasses are on the **iPhone hotspot**, not the venue Wi-Fi.
