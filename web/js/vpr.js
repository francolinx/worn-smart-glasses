/* Indoor place recognition for Point & Go: match one photo against surveyed reference photos, all on-device.
   ORB features + Hamming matching + RANSAC homography (OpenCV.js, self-hosted so it works with no network).
   Position = the surveyed spot of the best-matching reference. Heading = that reference's heading corrected by
   how far its centre has shifted sideways in the new photo. This is "nearest surveyed viewpoint", not metric SLAM. */
(function (root) {
  let ready = null;
  function load() {
    if (ready) return ready;
    ready = new Promise((res, rej) => {
      const s = document.createElement('script'); s.src = 'js/opencv.js'; s.async = true;
      s.onerror = () => rej(new Error('could not load the vision library (js/opencv.js)'));
      s.onload = async () => {
        try {
          let c = root.cv; if (c instanceof Promise) c = await c;
          if (c && c.Mat) { root.cv = c; return res(c); }
          c.onRuntimeInitialized = () => res(c);
        } catch (e) { rej(e); }
      };
      document.head.appendChild(s);
    });
    return ready;
  }
  const W = 640, NF = 1500;
  function toCanvas(src) {                    // downscale to W px on the long side
    const L = Math.max(src.width, src.height), k = Math.min(1, W / L), c = document.createElement('canvas');
    c.width = Math.round(src.width * k); c.height = Math.round(src.height * k); c.getContext('2d').drawImage(src, 0, 0, c.width, c.height); return c;
  }
  async function features(src) {
    const cv = await load(), c = toCanvas(src), img = cv.imread(c), gray = new cv.Mat(); cv.cvtColor(img, gray, cv.COLOR_RGBA2GRAY);
    const orb = new cv.ORB(NF), kps = new cv.KeyPointVector(), des = new cv.Mat(), none = new cv.Mat();
    orb.detectAndCompute(gray, none, kps, des);
    const n = kps.size(), kp = new Float32Array(n * 2); for (let i = 0; i < n; i++) { const p = kps.get(i).pt; kp[2 * i] = p.x; kp[2 * i + 1] = p.y; }
    const desc = n ? new Uint8Array(des.data) : new Uint8Array(0);
    img.delete(); gray.delete(); orb.delete(); kps.delete(); des.delete(); none.delete();
    return { n, kp, desc, w: c.width, h: c.height, thumb: c.toDataURL('image/jpeg', 0.7) };
  }
  /* q, r: feature sets. Returns {inliers, good, cx} where cx = x in the query image of the reference image's centre. */
  function matchPair(cv, q, r) {
    if (q.n < 12 || r.n < 12) return { inliers: 0, good: 0 };
    const dq = cv.matFromArray(q.n, 32, cv.CV_8U, q.desc), dr = cv.matFromArray(r.n, 32, cv.CV_8U, r.desc);
    const bf = new cv.BFMatcher(cv.NORM_HAMMING, false), mm = new cv.DMatchVectorVector();
    bf.knnMatch(dr, dq, mm, 2);
    const src = [], dst = [];
    for (let i = 0; i < mm.size(); i++) { const v = mm.get(i); if (v.size() < 2) continue; const a = v.get(0), b = v.get(1);
      if (a.distance < 0.75 * b.distance) { src.push(r.kp[2 * a.queryIdx], r.kp[2 * a.queryIdx + 1]); dst.push(q.kp[2 * a.trainIdx], q.kp[2 * a.trainIdx + 1]); } }
    dq.delete(); dr.delete(); bf.delete(); mm.delete();
    const good = src.length / 2; if (good < 10) return { inliers: 0, good };
    const ms = cv.matFromArray(good, 1, cv.CV_32FC2, src), md = cv.matFromArray(good, 1, cv.CV_32FC2, dst), mask = new cv.Mat();
    const H = cv.findHomography(ms, md, cv.RANSAC, 4, mask);
    let inliers = 0, cx = null; for (let i = 0; i < mask.rows; i++) inliers += mask.data[i] ? 1 : 0;
    if (!H.empty() && inliers >= 8) { const h = H.data64F, P = (x, y) => { const w = h[6] * x + h[7] * y + h[8]; return Math.abs(w) > 1e-9 ? [(h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w, w] : null; };
      /* sanity: the part of the reference that the matches cover must land in the query as a convex quad of similar size.
         A folded, mirrored or collapsed one is a chance match (plain doors, floor tiles). */
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (let i = 0; i < mask.rows; i++) if (mask.data[i]) { const x = src[2 * i], y = src[2 * i + 1]; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
      const q4 = [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)]; let ok = x1 - x0 > 20 && y1 - y0 > 20 && q4.every(c => c && c[2] > 0 === q4[0][2] > 0), area = 0, sign = 0;
      if (ok) for (let i = 0; i < 4; i++) { const a = q4[i], b = q4[(i + 1) % 4], c = q4[(i + 2) % 4], z = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]); if (z <= 0) ok = false; area += a[0] * b[1] - b[0] * a[1]; }
      area = Math.abs(area) / 2 / Math.max(1, (x1 - x0) * (y1 - y0)); if (!ok || area < 0.1 || area > 10) inliers = 0; else { const c = P(r.w / 2, r.h / 2); if (c && c[2] > 0 === q4[0][2] > 0) cx = c[0]; } }
    ms.delete(); md.delete(); mask.delete(); H.delete();
    return { inliers, good, cx };
  }
  /* refs: [{id, x, y, heading, f:{n,kp,desc,w,h}}]; fPx = query focal length in px at the 640-px scale */
  async function locate(q, refs, fPx) {
    const cv = await load(), out = [];
    for (const r of refs) { const m = matchPair(cv, q, r.f); let yaw = null;
      if (m.cx != null && isFinite(m.cx)) yaw = -Math.atan((Math.max(-q.w, Math.min(2 * q.w, m.cx)) - q.w / 2) / fPx) * 180 / Math.PI;   // ref centre left of ours => we turned right
      out.push({ ref: r, inliers: m.inliers, good: m.good, yaw }); }
    out.sort((a, b) => b.inliers - a.inliers);
    return out;
  }
  root.VPR = { load, features, locate };
})(window);
