/* Fóton — service worker.
   REGRA DE OURO: nunca cachear API nem fotos do evento (dados vivos).
   Só a "casca" do app (html, ícones, manifest) fica em cache para abrir offline/rápido. */
const CACHE = 'foton-v1';
const CASCA = ['./', './index.html', './manifest.webmanifest',
               './icons/icon-192.png', './icons/icon-512.png'];

// caminhos que NUNCA podem ser cacheados (dados ao vivo)
const API = /\/(ingest|selfie|feed|photos|stats|contatos|event|health|qr|img)(\/|\?|$)/;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;                       // POSTs passam direto
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;        // externo (fontes) passa direto
  if (API.test(url.pathname)) return;                     // API/fotos: sempre da rede

  // navegação: rede primeiro (para pegar deploy novo), cache como rede de segurança
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(() => caches.match('./index.html')));
    return;
  }
  // estáticos: cache primeiro, atualiza em segundo plano
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    const copy = res.clone();
    caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
    return res;
  })));
});
