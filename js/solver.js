/* Point & Go solver: three-point resection (Snellius-Pothenot) from tapped landmarks in one photo.
   JS port of spark/skyfix/city/resect.py from our Code Metal Forge build (Team 3, Nov 2026), so it runs
   in the browser with no server. Added here: pitch is recovered from the landmarks' known top heights
   (there is no sea horizon in Downtown Brooklyn), which also gives camera height -> floor.
   Angles: radians inside, degrees at the API. Local frame: east/north metres. */
(function (root) {
  const R_EARTH = 6371008.8, K_REFR = 0.13, D2R = Math.PI / 180, R2D = 180 / Math.PI;
  const wrap = a => { a = (a + Math.PI) % (2 * Math.PI); if (a < 0) a += 2 * Math.PI; return a - Math.PI; };
  const wrap180 = d => ((d % 360) + 540) % 360 - 180;

  function Local(lat0, lon0) {
    const kx = D2R * R_EARTH * Math.cos(lat0 * D2R), ky = D2R * R_EARTH;
    return { en: (lat, lon) => [(lon - lon0) * kx, (lat - lat0) * ky], ll: (e, n) => [lat0 + n / ky, lon0 + e / kx] };
  }
  const bearing = (p, q) => Math.atan2(q[0] - p[0], q[1] - p[1]);
  const dist = (p, q) => Math.hypot(q[0] - p[0], q[1] - p[1]);
  function haversine(lat1, lon1, lat2, lon2) {
    const p1 = lat1 * D2R, p2 = lat2 * D2R, dl = (lon2 - lon1) * D2R;
    const a = Math.sin((p2 - p1) / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 2 * R_EARTH * Math.asin(Math.sqrt(a));
  }
  function bearingLL(lat1, lon1, lat2, lon2) {
    const y = Math.sin((lon2 - lon1) * D2R) * Math.cos(lat2 * D2R);
    const x = Math.cos(lat1 * D2R) * Math.sin(lat2 * D2R) - Math.sin(lat1 * D2R) * Math.cos(lat2 * D2R) * Math.cos((lon2 - lon1) * D2R);
    return (Math.atan2(y, x) * R2D + 360) % 360;
  }

  /* lens: focal length in px for the long side */
  function focalPx(W, H, f35, hfovFallback) {
    const L = Math.max(W, H);
    if (f35) return { f: f35 / 36 * L, how: `EXIF 35 mm-equivalent ${f35} mm` };
    const hf = hfovFallback || 69; return { f: (L / 2) / Math.tan(hf * D2R / 2), how: `fallback HFOV ${hf}° (phone main lens)` };
  }

  /* pinhole, x right / y down pixels; pitch > 0 = camera tilted up */
  function azEl(x, y, W, H, f, pitch) {
    const u = x - W / 2, v = -(y - H / 2);
    const X = u, Y = v * Math.cos(pitch) + f * Math.sin(pitch), Z = f * Math.cos(pitch) - v * Math.sin(pitch);
    return [Math.atan2(X, Z), Math.atan2(Y, Math.hypot(X, Z))];
  }
  function project(az, el, W, H, f, pitch) {
    const X = Math.sin(az) * Math.cos(el), Y = Math.sin(el), Z = Math.cos(az) * Math.cos(el);
    const v1 = Y * Math.cos(pitch) - Z * Math.sin(pitch), w = Y * Math.sin(pitch) + Z * Math.cos(pitch);
    if (w <= 1e-6) return null;
    return [W / 2 + f * X / w, H / 2 - f * v1 / w];
  }

  function circleCenters(A, B, ang) {
    const d = [B[0] - A[0], B[1] - A[1]], L = Math.hypot(d[0], d[1]), M = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
    const n = [-d[1] / L, d[0] / L], t = L / (2 * Math.tan(Math.abs(ang)));
    return [[M[0] + n[0] * t, M[1] + n[1] * t], [M[0] - n[0] * t, M[1] - n[1] * t]];
  }
  function reflect(B, O1, O2) {
    const d = [O2[0] - O1[0], O2[1] - O1[1]], dd = d[0] * d[0] + d[1] * d[1];
    if (dd < 1e-9) return null;
    const t = ((B[0] - O1[0]) * d[0] + (B[1] - O1[1]) * d[1]) / dd, F = [O1[0] + t * d[0], O1[1] + t * d[1]];
    return [2 * F[0] - B[0], 2 * F[1] - B[1]];
  }
  function resect3(pts, phi) {
    const [A, B, C] = pts, alpha = wrap(phi[1] - phi[0]), beta = wrap(phi[2] - phi[1]);
    if (Math.abs(Math.tan(alpha)) < 1e-9 || Math.abs(Math.tan(beta)) < 1e-9) return null;
    let best = null, bres = 1e9;
    for (const O1 of circleCenters(A, B, alpha)) for (const O2 of circleCenters(B, C, beta)) {
      const P = reflect(B, O1, O2);
      if (!P || dist(P, B) < 1) continue;
      const b = pts.map(q => bearing(P, q));
      const res = Math.abs(wrap(b[1] - b[0] - alpha)) + Math.abs(wrap(b[2] - b[1] - beta));
      if (res < bres) { best = P; bres = res; }
    }
    return best && bres < 0.5 * D2R ? best : null;
  }
  function solve3x3(A, b) {           // Gaussian elimination with pivoting
    const M = A.map((r, i) => [...r, b[i]]);
    for (let c = 0; c < 3; c++) {
      let p = c; for (let r = c + 1; r < 3; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      if (Math.abs(M[p][c]) < 1e-18) return null;
      [M[c], M[p]] = [M[p], M[c]];
      for (let r = 0; r < 3; r++) if (r !== c) { const k = M[r][c] / M[c][c]; for (let j = c; j < 4; j++) M[r][j] -= k * M[c][j]; }
    }
    return [M[0][3] / M[0][0], M[1][3] / M[1][1], M[2][3] / M[2][2]];
  }
  function polish(P, pts, phi) {      // Gauss-Newton on (E, N, heading); accepts >= 3 landmarks
    let s = 0, c = 0; pts.forEach((q, i) => { const a = bearing(P, q) - phi[i]; s += Math.sin(a); c += Math.cos(a); });
    const x = [P[0], P[1], Math.atan2(s, c)];
    for (let it = 0; it < 30; it++) {
      const JtJ = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], Jtr = [0, 0, 0];
      pts.forEach((q, i) => {
        const d = [q[0] - x[0], q[1] - x[1]], r2 = d[0] * d[0] + d[1] * d[1];
        const r = wrap(Math.atan2(d[0], d[1]) - (x[2] + phi[i])), J = [-d[1] / r2, d[0] / r2, -1];
        for (let a = 0; a < 3; a++) { Jtr[a] += J[a] * r; for (let b = 0; b < 3; b++) JtJ[a][b] += J[a] * J[b]; }
      });
      const dx = solve3x3(JtJ, Jtr.map(v => -v)); if (!dx) break;
      x[0] += dx[0]; x[1] += dx[1]; x[2] += dx[2];
      if (Math.max(Math.abs(dx[0]), Math.abs(dx[1])) < 1e-4) break;
    }
    const res = pts.map((q, i) => wrap(bearing([x[0], x[1]], q) - (x[2] + phi[i])));
    return { P: [x[0], x[1]], th: wrap(x[2]), res };
  }
  function solvePosition(pts, phi) { const P = resect3(pts.slice(0, 3), phi.slice(0, 3)); return P ? polish(P, pts, phi) : null; }

  function danger(pts, P) {           // distance from the circle through the 3 landmarks, as a fraction of its radius
    const [A, B, C] = pts, a11 = 2 * (B[0] - A[0]), a12 = 2 * (B[1] - A[1]), a21 = 2 * (C[0] - A[0]), a22 = 2 * (C[1] - A[1]);
    const det = a11 * a22 - a12 * a21; if (Math.abs(det) < 1e-9) return null;
    const b1 = B[0] ** 2 + B[1] ** 2 - A[0] ** 2 - A[1] ** 2, b2 = C[0] ** 2 + C[1] ** 2 - A[0] ** 2 - A[1] ** 2;
    const O = [(b1 * a22 - b2 * a12) / det, (a11 * b2 - a21 * b1) / det], R = dist(A, O);
    return Math.abs(dist(P, O) - R) / R;
  }

  /* one solve at a fixed pitch -> position, heading, per-landmark camera heights */
  function solveAt(taps, LM, W, H, f, pitch, loc, pts) {
    const ae = taps.map(t => azEl(t.x, t.y, W, H, f, pitch)), phi = ae.map(a => a[0]);
    const sol = solvePosition(pts, phi); if (!sol) return null;
    const hs = [];
    taps.forEach((t, i) => {
      const L = LM[t.id]; if (t.top === false || L.top_asl_m == null) return;
      const d = dist(pts[i], sol.P);
      hs.push({ id: t.id, d, el: ae[i][1], h: L.top_asl_m - d * Math.tan(ae[i][1]) - d * d / (2 * R_EARTH) * (1 - K_REFR) });
    });
    let spread = null, hmean = null;
    if (hs.length) { hmean = hs.reduce((a, b) => a + b.h, 0) / hs.length; spread = Math.sqrt(hs.reduce((a, b) => a + (b.h - hmean) ** 2, 0) / hs.length); }
    const rms = Math.sqrt(sol.res.reduce((a, r) => a + r * r, 0) / sol.res.length);
    return { ...sol, phi, ae, hs, spread, hmean, rms, pitch };
  }

  /* taps: [{id, x, y, top}] (>= 3 distinct); LM: {id: {lat, lon, top_asl_m, name}}; opts: {f35, hfov, angleErrDeg, groundFn} */
  function solve(taps, LM, W, H, opts) {
    opts = opts || {};
    const ids = taps.map(t => t.id);
    if (taps.length < 3 || new Set(ids).size < 3) throw new Error('tap at least 3 different landmarks');
    const lens = opts.hfov ? { f: (Math.max(W, H) / 2) / Math.tan(opts.hfov * D2R / 2), how: `HFOV override ${opts.hfov}°` } : focalPx(W, H, opts.f35);
    const f = lens.f, lat0 = ids.reduce((a, i) => a + LM[i].lat, 0) / ids.length, lon0 = ids.reduce((a, i) => a + LM[i].lon, 0) / ids.length;
    const loc = Local(lat0, lon0), pts = ids.map(i => loc.en(LM[i].lat, LM[i].lon));
    const warnings = [];
    const level = solveAt(taps, LM, W, H, f, 0, loc, pts);
    let best = level, pitchHow = 'camera assumed level';
    const nTop = taps.filter(t => t.top !== false && LM[t.id].top_asl_m != null).length;
    if (nTop >= 2) {
      // no horizon here: choose the pitch that makes every tapped rooftop agree on one camera height
      const cost = s => s && s.spread != null && s.hmean > -20 && s.hmean < 450 ? s.spread + 200 * s.rms : 1e9;
      let bp = null, bc = 1e9;
      for (let p = -35; p <= 35; p += 0.5) { const s = solveAt(taps, LM, W, H, f, p * D2R, loc, pts), c = cost(s); if (c < bc) { bc = c; bp = p; } }
      if (bp !== null) {
        for (let p = bp - 0.5; p <= bp + 0.5; p += 0.02) { const s = solveAt(taps, LM, W, H, f, p * D2R, loc, pts), c = cost(s); if (c <= bc) { bc = c; best = s; } }
        if (best && best !== level) pitchHow = `pitch ${(best.pitch * R2D).toFixed(1)}° from ${nTop} rooftop heights (spread ${best.spread.toFixed(1)} m)`;
      }
    } else warnings.push('fewer than 2 rooftops with known height: camera assumed level, no floor estimate');
    if (!best) throw new Error('no resection solution: landmarks nearly in line with you, or a name is wrong');
    if (best.spread != null && best.spread > 12) warnings.push(`rooftop heights disagree by ${best.spread.toFixed(0)} m: a landmark name is probably wrong, or a tap is not on the roof line`);
    const P = best.P, phi = best.phi, [lat, lon] = loc.ll(P[0], P[1]);
    // confidence ring: perturb the two angles by +-e and re-solve
    const e = (opts.angleErrDeg || 0.5) * D2R; let ring = 0;
    for (const da of [-e, 0, e]) for (const db of [-e, 0, e]) {
      const ph = phi.slice(); ph[1] += da; ph[2] += da + db;
      const s = solvePosition(pts, ph); ring = Math.max(ring, s ? dist(s.P, P) : Infinity);
    }
    const dg = danger(pts, P);
    if (dg !== null && dg < 0.15) warnings.push(`you are close to the circle through the three landmarks (${Math.round(dg * 100)}% of its radius): the fix is weak, pick a landmark off that circle`);
    const heading = ((best.th * R2D) % 360 + 360) % 360;
    const out = {
      lat, lon, ring_m: Math.round(ring * 10) / 10, heading_deg: Math.round(heading * 10) / 10, pitch_deg: Math.round(best.pitch * R2D * 10) / 10,
      pitch_how: pitchHow, lens: { f_px: Math.round(f), how: lens.how, hfov_long_deg: Math.round(2 * Math.atan(Math.max(W, H) / 2 / f) * R2D * 10) / 10 },
      residuals_deg: best.res.map(r => Math.round(r * R2D * 1000) / 1000), danger_circle_frac: dg, warnings,
      landmarks: taps.map((t, i) => ({ id: t.id, name: LM[t.id].name, dist_m: Math.round(dist(pts[i], P)), bearing_deg: Math.round(((bearing(P, pts[i]) * R2D) % 360 + 360) % 360 * 10) / 10, elev_deg: Math.round(best.ae[i][1] * R2D * 100) / 100 })),
      _cam: { W, H, f, pitch: best.pitch, heading: best.th }
    };
    if (best.hs.length >= 2 && best.spread <= 12) {
      const g = opts.groundFn ? opts.groundFn(lat, lon) : 11, mpf = opts.mPerFloor || 4.0;
      out.height = { h_asl_m: Math.round(best.hmean * 10) / 10, ground_m: g, above_street_m: Math.round((best.hmean - g) * 10) / 10,
        floor_est: Math.max(1, Math.round((best.hmean - g) / mpf) + 1), m_per_floor: mpf, spread_m: Math.round(best.spread * 10) / 10 };
    }
    return out;
  }

  /* where a landmark should appear in the photo for a solved camera (labels overlay / sanity check) */
  function expectedPixel(sol, L) {
    const c = sol._cam, loc = Local(sol.lat, sol.lon), q = loc.en(L.lat, L.lon), d = Math.hypot(q[0], q[1]);
    const h = sol.height ? sol.height.h_asl_m : 30;
    const az = wrap(Math.atan2(q[0], q[1]) - c.heading), el = Math.atan2((L.top_asl_m || h) - h - d * d / (2 * R_EARTH) * (1 - K_REFR), d);
    if (Math.abs(az) > 80 * D2R) return null;
    const p = project(az, el, c.W, c.H, c.f, c.pitch); return p && { x: p[0], y: p[1], d, el: el * R2D };
  }

  const api = { Local, bearing, wrap, wrap180, haversine, bearingLL, focalPx, azEl, project, solve, solvePosition, expectedPixel, D2R, R2D, R_EARTH };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PG = api;
})(typeof window !== 'undefined' ? window : globalThis);
