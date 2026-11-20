#!/usr/bin/env python3
"""Build the offline Brooklyn pack for 285 Jay St (City Tech), bounded by Tillary (N), Jay (W), Johnson (S), Bridge (E).

Sources (all fetched 2026-11-20):
  - OpenStreetMap API 0.6 /map (ODbL)            -> streets, named places, entrances        data/osm_raw/*.osm.gz
  - NYC Open Data building footprints 5zhs-2jue  -> footprint rings + roof height + ground  (public domain)
  - NYC PLUTO 64uk-42ks                          -> street address per tax lot             (public domain)
  - NYS ITS orthoimagery (orthos.its.ny.gov)     -> aerial mosaics                         (public domain)
Run:  python3 tools/build_pack.py [osm] [bld] [sat]
"""
import gzip, json, math, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "web/pack"; RAW = ROOT / "data/osm_raw"
C_LAT, C_LON = 40.695496, -73.986565          # 285 Jay St (NYC GeoSearch, BIN 3414138)
UA = {"User-Agent": "worn-hack-pack/0.1 (github.com/francolinx/worn-smart-glasses)"}
FT = 0.3048
KX = math.radians(1) * 6371008.8 * math.cos(math.radians(C_LAT)); KY = math.radians(1) * 6371008.8


def get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception as ex:
            print("  retry", ex); time.sleep(3 + 3 * i)
    raise SystemExit("failed " + url)


def dist_m(lat, lon):
    return math.hypot((lon - C_LON) * KX, (lat - C_LAT) * KY)


# ---------------- OSM ----------------
def osm():
    half_lat, half_lon = 650 / KY, 650 / KX; n = 4
    nodes, ways = {}, {}
    for i in range(n):
        for j in range(n):
            w = C_LON - half_lon + 2 * half_lon * i / n; e = w + 2 * half_lon / n
            s = C_LAT - half_lat + 2 * half_lat * j / n; nn = s + 2 * half_lat / n
            f = RAW / f"map_{i}_{j}.osm.gz"
            if not f.exists():
                print("osm chunk", i, j); f.write_bytes(gzip.compress(get(f"https://api.openstreetmap.org/api/0.6/map?bbox={w:.6f},{s:.6f},{e:.6f},{nn:.6f}"))); time.sleep(1.5)
            for el in ET.fromstring(gzip.decompress(f.read_bytes())):
                if el.tag == "node":
                    nodes[el.get("id")] = (float(el.get("lat")), float(el.get("lon")), {t.get("k"): t.get("v") for t in el.findall("tag")})
                elif el.tag == "way":
                    ways[el.get("id")] = ([x.get("ref") for x in el.findall("nd")], {t.get("k"): t.get("v") for t in el.findall("tag")})
    streets, places, named_b = [], [], []
    for wid, (nds, t) in ways.items():
        pts = [[round(nodes[x][0], 6), round(nodes[x][1], 6)] for x in nds if x in nodes]
        if len(pts) < 2:
            continue
        if "highway" in t and t["highway"] not in ("proposed", "construction"):
            streets.append({"id": wid, "name": t.get("name"), "kind": t["highway"], "pts": pts, "nd": nds})
        elif "building" in t and (t.get("name") or t.get("addr:housenumber")):
            la = sum(p[0] for p in pts) / len(pts); lo = sum(p[1] for p in pts) / len(pts)
            named_b.append({"osm": "way/" + wid, "name": t.get("name"), "addr": (t.get("addr:housenumber", "") + " " + t.get("addr:street", "")).strip() or None,
                            "lat": round(la, 6), "lon": round(lo, 6), "height": t.get("height"), "levels": t.get("building:levels")})
        if t.get("name") and any(k in t for k in ("amenity", "leisure", "tourism", "shop", "railway", "public_transport", "office")) and "highway" not in t:
            la = sum(p[0] for p in pts) / len(pts); lo = sum(p[1] for p in pts) / len(pts)
            places.append({"name": t["name"], "kind": next(t[k] for k in ("amenity", "leisure", "tourism", "shop", "railway", "public_transport", "office") if k in t), "lat": round(la, 6), "lon": round(lo, 6), "osm": "way/" + wid})
    for nid, (la, lo, t) in nodes.items():
        if t.get("name") and any(k in t for k in ("amenity", "shop", "tourism", "railway", "leisure", "office")):
            places.append({"name": t["name"], "kind": next(t[k] for k in ("amenity", "shop", "tourism", "railway", "leisure", "office") if k in t), "lat": round(la, 6), "lon": round(lo, 6), "osm": "node/" + nid})
        elif t.get("railway") == "subway_entrance" or t.get("entrance") in ("main", "yes"):
            places.append({"name": t.get("name") or ("Subway entrance" if t.get("railway") else "Entrance"), "kind": t.get("railway") or "entrance", "ref": t.get("ref"), "lat": round(la, 6), "lon": round(lo, 6), "osm": "node/" + nid})
    # intersections of the four bounding streets (shared nodes)
    def nds_of(name):
        return {x for s in streets if s["name"] == name for x in s["nd"]}
    corners = []
    def pts_of(name):
        return [p for s in streets if s["name"] == name for p in s["pts"] if dist_m(p[0], p[1]) < 260]
    # OSM names the block's south side "Tech Place"; it is the former Johnson Street alignment.
    for a, b, lab, shown in (("Jay Street", "Tillary Street", "NW", "Jay & Tillary"), ("Bridge Street", "Tillary Street", "NE", "Bridge & Tillary"),
                             ("Jay Street", "Tech Place", "SW", "Jay & Tech Pl (Johnson St)"), ("Bridge Street", "Tech Place", "SE", "Bridge & Tech Pl (Johnson St)")):
        sh = {x for x in nds_of(a) & nds_of(b) if dist_m(nodes[x][0], nodes[x][1]) < 260}
        if sh:
            la = sum(nodes[x][0] for x in sh) / len(sh); lo = sum(nodes[x][1] for x in sh) / len(sh); how = "shared OSM node"
        else:
            pa, pb = pts_of(a), pts_of(b)
            if not pa or not pb:
                print("  !! no corner for", a, b); continue
            d, qa, qb = min(((math.hypot((x[1] - y[1]) * KX, (x[0] - y[0]) * KY), x, y) for x in pa for y in pb), key=lambda t: t[0])
            la, lo = (qa[0] + qb[0]) / 2, (qa[1] + qb[1]) / 2; how = "nearest approach of the two ways (%.0f m apart)" % d
        corners.append({"name": f"{shown} ({lab} corner)", "kind": "corner", "lat": round(la, 6), "lon": round(lo, 6), "how": how})
    for s in streets:
        del s["nd"]
    out = {"center": [C_LAT, C_LON], "streets": [s for s in streets if s["name"] or s["kind"] in ("footway", "pedestrian", "steps", "service")],
           "places": places, "corners": corners, "named_buildings": named_b, "attribution": "© OpenStreetMap contributors (ODbL)"}
    (PACK / "osm.json").write_text(json.dumps(out, separators=(",", ":")))
    print("osm: %d streets, %d places, %d corners, %d named buildings" % (len(out["streets"]), len(places), len(corners), len(named_b)))


# ---------------- buildings + landmarks ----------------
def bld():
    R = 2200
    q = urllib.parse.urlencode({"$limit": 50000, "$select": "the_geom,bin,base_bbl,mappluto_bbl,height_roof,ground_elevation,construction_year",
                                "$where": f"within_circle(the_geom,{C_LAT},{C_LON},{R})"})
    rows = json.loads(get("https://data.cityofnewyork.us/resource/5zhs-2jue.json?" + q)); print("footprints", len(rows))
    B = []
    for r in rows:
        try:
            h = float(r["height_roof"]) * FT
        except Exception:
            continue
        g = float(r.get("ground_elevation") or 30) * FT
        ring = max((poly[0] for poly in r["the_geom"]["coordinates"]), key=len)
        la = sum(p[1] for p in ring) / len(ring); lo = sum(p[0] for p in ring) / len(ring); d = dist_m(la, lo)
        if d > 750 and h < 45:
            continue
        B.append({"bin": r.get("bin"), "bbl": r.get("mappluto_bbl") or r.get("base_bbl"), "h": round(h, 1), "g": round(g, 1), "yr": r.get("construction_year"),
                  "c": [round(la, 6), round(lo, 6)], "d": round(d), "ring": [[round(p[1], 6), round(p[0], 6)] for p in ring]})
    B.sort(key=lambda b: b["d"])
    # addresses from PLUTO for the tall ones + everything on the block
    need = sorted({b["bbl"] for b in B if b["bbl"] and (b["h"] >= 45 or b["d"] < 260)})
    addr = {}
    for i in range(0, len(need), 80):
        q = urllib.parse.urlencode({"$limit": 5000, "$select": "bbl,address,numfloors,ownername,bldgclass,yearbuilt",
                                    "$where": "bbl in (" + ",".join("'%s'" % x for x in need[i:i + 80]) + ")"})
        for r in json.loads(get("https://data.cityofnewyork.us/resource/64uk-42ks.json?" + q)):
            addr[str(int(float(r["bbl"])))] = r
    print("pluto rows", len(addr), "of", len(need))
    for b in B:
        a = addr.get(b["bbl"] or "")
        if a:
            b["addr"] = a.get("address"); b["floors"] = a.get("numfloors"); b["owner"] = a.get("ownername")
    (PACK / "buildings.json").write_text(json.dumps({"center": [C_LAT, C_LON], "n": len(B), "buildings": B,
        "note": "h = roof height above ground (m), g = ground elevation (m, NAVD88). Source: NYC Open Data building footprints + PLUTO (public domain)."}, separators=(",", ":")))
    # reverse-geocode tall buildings PLUTO did not match (NYC GeoSearch, Pelias)
    for b in B:
        if b["h"] >= 55 and not b.get("addr"):
            try:
                j = json.loads(get("https://geosearch.planninglabs.nyc/v2/reverse?point.lat=%f&point.lon=%f&size=1" % (b["c"][0], b["c"][1])))
                pr = j["features"][0]["properties"]; b["addr"] = pr.get("name"); b["addr_src"] = "geosearch reverse (nearest address point)"
            except Exception as ex:
                print("  reverse failed", b["bin"], ex)
    (PACK / "buildings.json").write_text(json.dumps({"center": [C_LAT, C_LON], "n": len(B), "buildings": B,
        "note": "h = roof height above ground (m), g = ground elevation (m, NAVD88). Source: NYC Open Data building footprints + PLUTO (public domain)."}, separators=(",", ":")))
    curated = json.loads((ROOT / "tools/landmark_names.json").read_text()) if (ROOT / "tools/landmark_names.json").exists() else {}
    L = []
    for b in B:
        if b["h"] < 55 or b["d"] < 25:
            continue
        nm = curated.get((b.get("addr") or "").upper()) or curated.get(b["bin"] or "")
        L.append({"id": "bin" + str(b["bin"]), "name": nm or (b.get("addr") or "BIN " + str(b["bin"])).title(), "named": bool(nm), "addr": b.get("addr"),
                  "lat": b["c"][0], "lon": b["c"][1], "top_height_m": b["h"], "ground_m": b["g"], "top_asl_m": round(b["h"] + b["g"], 1),
                  "floors": b.get("floors"), "dist_m": b["d"],
                  "bearing_deg": round(math.degrees(math.atan2((b["c"][1] - C_LON) * KX, (b["c"][0] - C_LAT) * KY)) % 360)})
    L.sort(key=lambda l: -l["top_height_m"])
    (PACK / "landmarks.json").write_text(json.dumps({"center": [C_LAT, C_LON], "n": len(L), "landmarks": L}, separators=(",", ":")))
    print("buildings", len(B), "landmarks", len(L))
    for l in L[:25]:
        print("  %5.0f m  %4d m @ %3d°  %s" % (l["top_height_m"], l["dist_m"], l["bearing_deg"], l["name"]))


# ---------------- aerial ----------------
def sat():
    def merc(lat, lon):
        return lon * 20037508.342789244 / 180, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 20037508.342789244 / math.pi
    cx, cy = merc(C_LAT, C_LON); k = 1 / math.cos(math.radians(C_LAT))     # mercator metres per ground metre
    meta = {}
    for name, half_m, px in (("sat_block", 230, 3600), ("sat_area", 700, 3600)):
        hm = half_m * k; bb = (cx - hm, cy - hm, cx + hm, cy + hm)
        tiles = 2 if px > 2048 else 1; step = px // tiles
        from PIL import Image; import io
        im = Image.new("RGB", (px, px))
        for i in range(tiles):
            for j in range(tiles):
                x0 = bb[0] + (bb[2] - bb[0]) * i / tiles; x1 = bb[0] + (bb[2] - bb[0]) * (i + 1) / tiles
                y1 = bb[3] - (bb[3] - bb[1]) * j / tiles; y0 = bb[3] - (bb[3] - bb[1]) * (j + 1) / tiles
                u = ("https://orthos.its.ny.gov/arcgis/rest/services/wms/Latest/MapServer/export?bbox=%f,%f,%f,%f&bboxSR=3857&imageSR=3857&size=%d,%d&format=jpg&f=image" % (x0, y0, x1, y1, step, step))
                im.paste(Image.open(io.BytesIO(get(u))).convert("RGB"), (i * step, j * step)); print(" ", name, i, j)
        im.save(PACK / (name + ".jpg"), quality=82, optimize=True)
        inv = lambda x, y: (math.degrees(2 * math.atan(math.exp(y * math.pi / 20037508.342789244)) - math.pi / 2), x * 180 / 20037508.342789244)
        s, w = inv(bb[0], bb[1]); n, e = inv(bb[2], bb[3])
        meta[name] = {"file": name + ".jpg", "px": px, "merc_bbox": [round(v, 3) for v in bb], "south": s, "west": w, "north": n, "east": e,
                      "ground_m_per_px": round(2 * half_m / px, 4)}
    meta["source"] = "NYS ITS orthoimagery, wms/Latest (public domain), fetched 2026-11-20"
    (PACK / "sat.json").write_text(json.dumps(meta, indent=1)); print(meta)


if __name__ == "__main__":
    PACK.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    what = sys.argv[1:] or ["osm", "bld", "sat"]
    for w in what:
        {"osm": osm, "bld": bld, "sat": sat}[w]()
