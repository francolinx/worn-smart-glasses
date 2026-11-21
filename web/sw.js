// Point & Go offline cache: network first (so fixes go live at once), cache as the fallback when there is no connection.
const C = 'pg-v8';
const SHELL = ['./', 'index.html', 'indoor.html', 'glasses.html', 'floor3d.html', 'building3d.html', 'pack/sat_3d.jpg', 'pack/sat_3d.json', 'pack/near_3d.json', 'bench/vertical_runs.json', 'bench/stories.json', 'handoff.html', 'js/three/three.module.min.js', 'js/three/OrbitControls.js', 'pack/indoor/refs.json', 'pack/indoor/schematic.json', 'benchmark.html', 'js/solver.js', 'js/sync.js', 'js/vpr.js', 'js/opencv.js',
  'pack/sat.json', 'pack/sat_block.jpg', 'pack/landmarks.json', 'pack/buildings.json', 'pack/osm.json', 'pack/indoor/default.json', 'pack/indoor/citytech_f1.png', 'pack/indoor/a105.png',
  ...['f1s', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8'].map(f => `pack/indoor/${f}.jpg`)];
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(C).then(c => Promise.allSettled(SHELL.map(u => c.add(u))))); });
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.includes('/api/')) return;
  e.respondWith(fetch(e.request).then(r => { if (r.ok) { const cp = r.clone(); caches.open(C).then(c => c.put(e.request, cp)); } return r; })
    .catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || Response.error())));
});
