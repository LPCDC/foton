/* Fóton — service worker.

   REGRA DE OURO (aprendida na marra): NUNCA cachear resposta de API.
   A versão anterior tinha uma lista de rotas a excluir e ela tinha furos —
   /me e /events acabaram cacheados, e o app mostrava os dados de OUTRA conta
   depois de trocar de login. Agora a lógica é invertida: só entra no cache o
   que está numa lista curta e explícita de arquivos estáticos. Qualquer coisa
   fora dessa lista vai sempre para a rede. */
const CACHE = 'foton-v3';

// única coisa que pode ser cacheada — a "casca" do app
const CASCA = ['/', '/index.html', '/manifest.webmanifest',
               '/icons/icon-192.png', '/icons/icon-512.png'];

// arquivos estáticos por extensão (fotos de exemplo, ícones, fontes locais)
const ESTATICO = /\.(png|jpg|jpeg|webp|svg|ico|woff2?|css)$/i;

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
  if (req.method !== 'GET') return;                        // POST sempre na rede
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;         // externo passa direto
  if (req.headers.has('Authorization')) return;            // qualquer coisa com sessão: rede

  // navegação: rede primeiro (pega deploy novo), cache como rede de segurança
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(() => caches.match('/index.html')));
    return;
  }

  const cacheavel = CASCA.includes(url.pathname) || ESTATICO.test(url.pathname);
  if (!cacheavel) return;                                  // API e tudo mais: sempre rede

  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {}); }
    return res;
  })));
});
