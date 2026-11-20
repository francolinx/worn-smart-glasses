// Tiny hand-off store for Point & Go: the phone POSTs {fix, dest}, the glasses GET it.
// In-memory only (one warm instance); js/sync.js also mirrors every message to ntfy.sh as a fallback.
const store = globalThis.__pg || (globalThis.__pg = new Map());
module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'content-type');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(204).end();
  const room = String((req.query && req.query.room) || 'default').slice(0, 48);
  if (req.method === 'POST') {
    let b = req.body; if (typeof b === 'string') { try { b = JSON.parse(b); } catch (_) { b = null; } }
    if (!b || typeof b !== 'object' || JSON.stringify(b).length > 8000) return res.status(400).json({ error: 'bad body' });
    store.set(room, b); if (store.size > 200) store.delete(store.keys().next().value);
  }
  res.status(200).json(store.get(room) || {});
};
