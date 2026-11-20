/* Phone -> glasses hand-off. The phone publishes {fix, dest}; the glasses poll for it.
   Three transports, newest message wins:
     1. localStorage  (same device / same browser: instant, for testing)
     2. /api/state    (Vercel function next to the app, in-memory)
     3. ntfy.sh topic (public pub/sub; the room name is the only secret, so keep it unguessable)
   Room: ?room=NAME on both pages, else the default below. */
(function (root) {
  const q = new URLSearchParams(location.search);
  const ROOM = (q.get('room') || localStorage.getItem('pg_room') || 'worn-pg-k7x2m9q4').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 48);
  if (q.get('room')) try { localStorage.setItem('pg_room', ROOM); } catch (_) {}
  const NTFY = 'https://ntfy.sh/' + ROOM, API = 'api/state?room=' + ROOM, KEY = 'pg_state_' + ROOM;
  let last = 0; const status = { api: null, ntfy: null };

  async function publish(state) {
    state.t = Date.now(); state.v = 1; const body = JSON.stringify(state);
    try { localStorage.setItem(KEY, body); } catch (_) {}
    const out = await Promise.allSettled([
      fetch(API, { method: 'POST', headers: { 'content-type': 'application/json' }, body }).then(r => { if (!r.ok) throw 0; }),
      fetch(NTFY, { method: 'POST', body, headers: { Title: 'point-and-go' } }).then(r => { if (!r.ok) throw 0; })
    ]);
    status.api = out[0].status === 'fulfilled'; status.ntfy = out[1].status === 'fulfilled';
    return status;
  }
  function subscribe(cb) {
    const take = s => { if (s && s.t && s.t > last && s.fix) { last = s.t; cb(s); } };
    const local = () => { try { take(JSON.parse(localStorage.getItem(KEY) || 'null')); } catch (_) {} };
    addEventListener('storage', local); local();
    (async function a() { try { const r = await fetch(API + '&_=' + Date.now(), { cache: 'no-store' }); status.api = r.ok; if (r.ok) take(await r.json()); } catch (_) { status.api = false; } setTimeout(a, 1000); })();
    (async function n() {
      try {
        const r = await fetch(NTFY + '/json?poll=1&since=12h', { cache: 'no-store' }); status.ntfy = r.ok;
        if (r.ok) { const lines = (await r.text()).trim().split('\n').filter(Boolean); for (const ln of lines.slice(-3)) { try { take(JSON.parse(JSON.parse(ln).message)); } catch (_) {} } }
      } catch (_) { status.ntfy = false; }
      setTimeout(n, 2500);
    })();
  }
  root.PGSync = { ROOM, publish, subscribe, status };
})(window);
