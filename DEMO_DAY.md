# Demo-day runbook: Point & Go on the MicroLumin M6

**For Rex (and for whatever coding agent Rex points at this repo).** Franco is not at the venue on Saturday.
Code freeze is **Sat 21 Nov, 2:00 PM**. Table demos start **2:15 PM**. Room **A 105**, 285 Jay St.

Read this file top to bottom once. Then do "Path A". Everything else is optional.

---

## 0. What this project is, in five lines

- A firefighter, police officer or medic is inside a building. GPS does not work. The compass lies.
- They take **one photo**. The phone matches it against photos surveyed earlier and gets floor, position and facing.
- The glasses show a floor schematic with a green route, red exits and the next move in big text.
- Phone page: `web/indoor.html`. Glasses page: `web/glasses.html`. Both are hosted, nothing runs on a laptop.
- Live site: https://francolinx.github.io/worn-smart-glasses/ (served from the `gh-pages` branch, which is a copy of `web/`).

## 1. Hard rules (agents: obey these)

1. **The MicroLumin SDK kit is confidential.** Never copy any file from the kit into this repo, a gist, an issue, a chat or a
   public link. This repo is public. `.gitignore` blocks the kit's folder names; do not work around it.
2. **Do not touch the matcher or the survey pack on demo day** (`web/js/vpr.js`, `web/pack/indoor/refs.json`,
   `tools/survey_floor1.py`) unless a test below fails. They were benchmarked overnight.
3. Never type passwords, tokens or API keys. Signing in to Apple, GitHub or Wi-Fi is done by the human.
4. A change to `web/` is not live until it is copied to the `gh-pages` branch (section 8).
5. If something is not working 30 minutes before the demo, fall back to "Path Z" (section 7). It needs no glasses.

## 2. What you need on the table

| Item | Why |
|---|---|
| M6 glasses + USB cable, charging | They arrive flat. Long-press power the first time |
| Mac with Xcode 26.5 | Only to run MLDemo once (Developer Mode + Wi-Fi) and, optionally, our iOS wrapper |
| iPhone (iOS 15+) + cable | Runs the phone page. Also the hotspot |
| The SDK kit, on the Mac only | `04_Demo_Apps/MLDemo` is inside it |
| `adb` | `brew install android-platform-tools` |

**Network: use the iPhone's Personal Hotspot** for the glasses. Venue Wi-Fi usually has a sign-in page, and the glasses cannot
get past one. The phone itself stays on cellular. The phone and glasses talk through a public relay (ntfy.sh), so both need
internet, but they do not need to be on the same network.

## 3. Path A: the demo with the fewest moving parts (do this first)

**Phone = Safari on the iPhone. Glasses = our small Android app showing the hosted glasses page.** No SDK code of ours, no
Xcode build of ours.

### A1. Turn on Developer Mode and Wi-Fi on the glasses (kit's MLDemo, about 15 min)

1. On the Mac, open the kit: `04_Demo_Apps/MLDemo/MLDemo.xcworkspace` (the workspace, not the project).
2. Target MLDemo > Signing & Capabilities: pick Rex's team, change the bundle ID to something unique.
3. Run on the real iPhone. Allow Bluetooth. Glasses screen > **Set Up Glasses** > tap your pair (hold them next to the phone).
4. Glasses screen > Developer > **Developer Mode: on**.
5. Turn on the iPhone hotspot. MLDemo > **Wi-Fi** > join the glasses to the hotspot.
6. Unplug the glasses' USB cable and plug it into the Mac.

Check: `adb devices -l` lists a device with `model:XNM_Glass`. Accept the debugging prompt on the glasses if one appears.

### A2. Install the glasses app (2 min)

The APK is built by GitHub Actions from `m6/glasses-app` and published on the `apk` branch.

```bash
curl -L -o PointGoGlasses.apk https://github.com/francolinx/worn-smart-glasses/raw/apk/PointGoGlasses.apk
adb uninstall com.pointgo.glasses 2>/dev/null     # each CI build has a new debug signature
adb install -r PointGoGlasses.apk
adb shell am start -n com.pointgo.glasses/.MainActivity
```

Check: the glasses show "Waiting for a fix from the phone…" on black. If they show "No connection to the page", the glasses
are not on the internet: redo A1 step 5.

Useful variants (no rebuild needed):

```bash
adb shell am start -n com.pointgo.glasses/.MainActivity --es mono 1      # green-only display
adb shell am start -n com.pointgo.glasses/.MainActivity --es room rex1   # private room name (then use ?room=rex1 on the phone)
adb shell am start -n com.pointgo.glasses/.MainActivity --es url "https://francolinx.github.io/worn-smart-glasses/glasses.html?demo=1"   # fake fix, proves the display
adb logcat | grep -i -E "chromium|pointgo|KeyEvent"                       # page errors and touchpad / ring key codes
```

### A3. Phone (1 min)

Open **https://francolinx.github.io/worn-smart-glasses/indoor.html** in Safari. The first load pulls about 18 MB (the vision
library and the survey). The red card should say "Survey on board: 12 stations, 71 photos of floor 1".

### A4. Smoke test (3 min). Do it in A 105

1. Stand inside A 105 near the north door. Tap **Point & shoot**, photograph the door with its EXIT sign.
2. Expect "Matched … Room A 105 · confidence high/medium". If it says "look another way", do that: doors, signs and
   whiteboards work; people, cabinet fronts and the green glass do not.
3. Tap **⛑ Nearest exit**, then **GO ▸ glasses**.
4. The glasses switch to the floor schematic: white arrow = you, green line = route, red tags = exits.
5. Face the way you shot and press **ALIGN** on the glasses (touchpad tap, or Enter on the ring). The map now turns with your head.

If step 4 does nothing: phone and glasses are in different rooms, or one has no internet. The phone prints
"ntfy relay ✔/✘" under the GO button.

## 4. Path B: our iOS wrapper app (optional, about 10 min)

Same phone page inside a native app, so the demo is "an iOS app" and Safari's address bar is gone.

1. Open `m6/ios/PointGo/PointGo.xcodeproj`. Target PointGo > Signing & Capabilities: team, and change `com.CHANGEME.pointgo`.
2. Run on the iPhone. Allow the camera when asked.

**This project was written without Xcode and has never been compiled.** The project file parses, the Swift is plain SwiftUI +
WKWebView (iOS 15+), but expect to fix a typo. If the project will not open: `brew install xcodegen && cd m6/ios/PointGo && xcodegen`
regenerates it from `project.yml`. If it costs more than 15 minutes, drop it and stay on Safari. Nothing else depends on it.

## 5. Path C: the fix comes from the glasses' own camera (stretch)

The kit has no phone-side camera stream and no glasses-side SDK. The route that exists: MLDemo's **Camera** screen takes a photo
on the glasses, MLDemo's **Files** screen syncs it to the phone over Wi-Fi.

- Simple: after syncing, save the photo to Photos, then in our phone page tap **🕶 Use a photo taken by the glasses**.
- One app: copy `m6/ios/MLDemo-addon/PointGoViewController.swift` into Rex's fork of MLDemo and push it from MLDemo's home
  screen (two lines, written at the top of that file). Its "Glasses photo" button finds the newest image in MLDemo's folders and
  hands it to the page through `window.PG_usePhoto(dataURL)`. Not tested on a device: where MLDemo saves synced files is not
  documented.

Known SDK bug from the kit's README: the SDK crashes after a glasses photo unless MLDemo's `BluetoothTrafficProbe` workaround
is in place. A fork of MLDemo has it. A new app built straight on the SDK does not.

**Nobody has matched a photo from the M6 camera yet.** It is 110° wide; the survey photos are about 74° wide. It may match
worse. Try it early. If it does not match, shoot with the phone and say so.

## 6. The three-minute demo

1. "GPS stops at the door. In this corridor our phone's compass was 35 to 50 degrees wrong." (true: see `README.md`)
2. Shoot the A 105 north door. Read out: floor, room, confidence.
3. **Nearest exit** → GO. Hand over the glasses: schematic, green route, red exit, "THROUGH DOOR A 105 (NORTH)".
4. Step into the corridor, shoot the "EXIT STAIR E" sign, pick **Elevator Bank B on Floor 8** from the list → GO.
   The glasses say "TAKE STAIR E TO FLOOR 8". Say: no elevators, responders take stairs.
5. On a laptop or the phone, open https://francolinx.github.io/worn-smart-glasses/building3d.html → **Scenarios**: the whole
   building, eight floors, with the wheelchair-rescue story.
6. Numbers, if asked (all from our own phone photos, see section 9): 48 of 50 simulated missions reached the target, no fix in
   the wrong place.

Good places to shoot in A 105: north door + EXIT sign, the whiteboards from the door corner, the recycling bins by either door.
In the lobby: the INFORMATION pillar, the escalators, the elevators, the turnstiles.

## 7. Path Z: nothing works

Phone only. Open the phone page, shoot, show the route on the phone's own floor plan. Then open `building3d.html` and
`handoff.html`. That is still the whole idea, minus the glasses.

## 8. Changing and shipping code

```bash
git clone https://github.com/francolinx/worn-smart-glasses && cd worn-smart-glasses
cd web && python3 -m http.server 8765        # phone: http://localhost:8765/indoor.html   glasses: /glasses.html?m6=1

# ship web/ to the live site
git worktree add /tmp/ghp gh-pages 2>/dev/null || true
(cd /tmp/ghp && find . -mindepth 1 -maxdepth 1 ! -name .git ! -name .nojekyll -exec rm -rf {} + && cp -a "$OLDPWD/web/." . && git add -A && git commit -m "Deploy" && git push origin gh-pages)
```

- Glasses app: edit `m6/glasses-app/app/src/main/java/com/pointgo/glasses/MainActivity.java`, push to `main`; Actions rebuilds
  the APK onto the `apk` branch in about 2 minutes. Local build: open `m6/glasses-app` in Android Studio (JDK 17).
- Glasses page layout: everything is drawn on a 600×600 stage and scaled to the display (0.8 on the M6's 640×480). The JavaScript
  on that page is kept to ES2018 on purpose: the M6 runs Android 9 and its web view may be old.
- Tests (need Python, Playwright and Chrome; the photo tests also need the survey photos, which are **not** in the repo):
  `tools/bench_vertical.py /tmp/out 30` (routing, all floors) runs from the repo alone.

## 9. What was tested, and how

| Test | Result | What it does not cover |
|---|---|---|
| Phone page in WebKit with an iPhone profile + glasses page at 640×480, 50 missions | see `README.md`, "M6 rehearsal" | A real iPhone, a real M6, the relay over the internet |
| 50 missions in Chrome, hold-out degraded survey photos | 48 / 50 reached, 0 wrong-place fixes | Photos from any glasses camera |
| 30 upper-floor routing trials, independent solver | 30 / 30 | Upper floors have no survey photos: positions are injected |
| 11 responder scenarios, floors 1 to 8 | 11 / 11 | Same |
| Glasses APK | Built by CI; never installed on an M6 | Everything on the device |
| iOS wrapper | Project file parses; never compiled | Everything |

## 10. If it breaks

| Symptom | Likely cause | Do |
|---|---|---|
| Glasses: "No connection to the page" | Glasses not on the internet | Hotspot on, MLDemo > Wi-Fi again |
| Glasses stay on "Waiting for a fix" after GO | Different rooms, or relay blocked | Same `?room=` on both; check "ntfy relay ✔" on the phone |
| Glasses page blank or half drawn | Old web view on the glasses | `adb logcat | grep chromium`; the offline screen prints the web view version |
| Map does not turn with the head | No ALIGN, or no orientation sensor in the web view | Press ALIGN facing the way you shot. Without a sensor the map stays in the photo's direction, which is still correct at the moment of the shot |
| "Look another way" every time | Aiming at people, glass or blank wall | Doors, signs, boards, bins. Step to a survey spot (corners of A 105, the corridor door) |
| Touchpad does nothing | Focus is not in the page | Tap once; `adb logcat` shows the key codes the touchpad sends. Left/right move between ALIGN / DEST / MAP, Enter presses |
| `adb install` fails with a signature error | Older build installed | `adb uninstall com.pointgo.glasses` first |
| Phone page shows old behaviour | Cached | Reload twice, or add `?v=2` to the URL |

## 11. Where things are

```
web/indoor.html        phone: photo fix, destinations, routing, survey tools
web/glasses.html       glasses: schematic map, arrow, ALIGN
web/js/vpr.js          matcher (ORB + homography, OpenCV.js)
web/pack/indoor/       floor plans, schematic vectors, survey pack (refs.json)
web/building3d.html    whole building in 3D, scenarios    web/floor3d.html   floor 1 in 3D
web/handoff.html       overnight report with every scenario frame by frame
m6/glasses-app/        Android app for the M6 (web view shell, no SDK)
m6/ios/PointGo/        iOS wrapper (WKWebView, no SDK)
m6/ios/MLDemo-addon/   optional file to drop into a fork of the kit's MLDemo
tools/                 pack builder, benchmarks, scenario runner
README.md              how it works, data sources, every measured number
```

People: Franco (lead, remote on Saturday), Rex (running the demo), Maahi (survey photos; her round-2 shot list is in the
team's Drive folder), Rachel (has the MacBook used on Friday).
