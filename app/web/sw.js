/* Fóton — service worker.

   REGRA DE OURO (aprendida na marra): NUNCA cachear resposta de API.
   A versão anterior tinha uma lista de rotas a excluir e ela tinha furos —
   /me e /events acabaram cacheados, e o app mostrava os dados de OUTRA conta
   depois de trocar de login. Agora a lógica é invertida: só entra no cache o
   que está numa lista curta e explícita de arquivos estáticos. Qualquer coisa
   fora dessa lista vai sempre para a rede. */
const CACHE = 'foton-v5';   // sobe a versao para o celular buscar a casca nova

/* Cache SEPARADO, só para as fotos que o Android entrega pelo menu "Compartilhar".
   Separado de propósito: o activate limpa versões velhas do cache da casca e não
   pode levar junto um lote de fotos que a fotógrafa acabou de mandar. */
const CACHE_SHARE = 'foton-compartilhado';
const PREFIXO_SHARE = '/__compartilhado/';
const VALIDADE_SHARE_MS = 60 * 60 * 1000;   // lote esquecido > 1h é lixo, some

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
    .then(ks => Promise.all(ks
      .filter(k => k !== CACHE && k !== CACHE_SHARE)     // nunca apagar o lote compartilhado
      .map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

/* ===================== Web Share Target =====================
   Com o app instalado, o Fóton aparece no menu "Compartilhar" do Android. Ao
   escolher o Fóton, o sistema faz um POST multipart para /compartilhar com as
   fotos no campo "fotos" (declarado no manifest). Esse POST NUNCA chega ao
   servidor: é atendido aqui, as fotos ficam no CacheStorage e a página é aberta
   em /?compartilhado=<id> para enviá-las com a sessão da fotógrafa.

   Por que passar pelo cache e não mandar direto daqui: o upload precisa do token
   da conta, que mora no localStorage — o service worker não enxerga localStorage. */
async function limparShareVelho(c) {
  const agora = Date.now();
  for (const req of await c.keys()) {
    const id = new URL(req.url).pathname.slice(PREFIXO_SHARE.length).split('/')[0];
    const t = parseInt(id.slice(1), 36);
    if (!t || agora - t > VALIDADE_SHARE_MS) await c.delete(req);
  }
}

async function receberCompartilhadas(req) {
  const base = self.registration.scope;
  let destino = new URL('./', base).href;
  try {
    const fd = await req.formData();
    const fotos = fd.getAll('fotos').filter(f => f && typeof f === 'object' && f.size > 0);
    if (fotos.length) {
      const id = 'c' + Date.now().toString(36);
      const c = await caches.open(CACHE_SHARE);
      await limparShareVelho(c);
      const nomes = [], tipos = [];
      for (let i = 0; i < fotos.length; i++) {
        nomes.push(fotos[i].name || ('foto-' + (i + 1) + '.jpg'));
        tipos.push(fotos[i].type || 'image/jpeg');
        await c.put(PREFIXO_SHARE + id + '/' + i,
                    new Response(fotos[i], { headers: { 'Content-Type': tipos[i] } }));
      }
      await c.put(PREFIXO_SHARE + id + '/lote',
                  new Response(JSON.stringify({ n: fotos.length, nomes, tipos }),
                               { headers: { 'Content-Type': 'application/json' } }));
      destino = new URL('./?compartilhado=' + id, base).href;
    } else {
      destino = new URL('./?compartilhado=vazio', base).href;
    }
  } catch (err) {
    destino = new URL('./?compartilhado=erro', base).href;
  }
  // 303: o navegador troca o POST por um GET na página do app
  return Response.redirect(destino, 303);
}

self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);

  // o alvo de compartilhamento vem antes de tudo — é o único POST que atendemos
  if (req.method === 'POST' && url.origin === self.location.origin &&
      url.pathname.replace(/\/+$/, '').endsWith('/compartilhar')) {
    e.respondWith(receberCompartilhadas(req));
    return;
  }

  if (req.method !== 'GET') return;                        // POST sempre na rede
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
