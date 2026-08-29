"""Ensaio com as SUAS fotos — o teste que diz se você vai passar vergonha.

Os outros testes provam que o codigo esta certo. Este prova a unica coisa que importa
no dia: **as fotos certas chegam nas pessoas certas, rapido**. Isso nenhum teste de
contrato mede, porque depende das suas fotos, da sua luz e dos rostos de verdade.

Coloque as fotos em `fotos-teste/` (a pasta e ignorada pelo git — o repo e publico):

    fotos-teste/*.jpg          as fotos do "evento", direto da camera/celular
    fotos-teste/selfies/*.jpg  um rosto por arquivo; cada uma vira um "convidado"

    python tests/ensaio.py

Cria um evento de teste em producao, mede tudo e **apaga o evento no fim**. Nao encosta
nos seus eventos de verdade.
"""
import io, os, sys, time, glob, json

try:
    import requests
except ImportError:
    print("Falta o requests:  pip install requests"); sys.exit(1)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "fotos-teste")
API = os.environ.get("FOTON_API", "https://app.foton.app.br")
LOGIN = os.environ.get("FOTON_LOGIN", "carol")
SENHA = os.environ.get("FOTON_SENHA", "fada123")
CODIGO = "ENSA"

def pct(v, p):
    if not v: return 0
    v = sorted(v); k = (len(v) - 1) * p / 100
    f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)

def mb(n): return n / 1048576.0

def imagens(pasta):
    """No Windows o glob nao diferencia maiuscula: *.jpg e *.JPG achavam o MESMO
    arquivo e ele entrava duas vezes no ensaio, inflando os numeros."""
    vistos, saida = set(), []
    for nome in sorted(os.listdir(pasta) if os.path.isdir(pasta) else []):
        if not nome.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
            continue
        cam = os.path.join(pasta, nome)
        if os.path.isfile(cam) and cam.lower() not in vistos:
            vistos.add(cam.lower()); saida.append(cam)
    return saida

fotos = imagens(PASTA)
selfies = imagens(os.path.join(PASTA, "selfies"))

if not fotos:
    print(f"Nenhuma foto em {PASTA}")
    print("Leia fotos-teste/LEIA-ME.md — e lembre: quanto mais parecido com o dia real, melhor.")
    sys.exit(1)

print("=" * 66)
print("ENSAIO DO FOTON")
print("=" * 66)
print(f"  servidor : {API}")
print(f"  conta    : {LOGIN}")
print(f"  fotos    : {len(fotos)}  ({mb(sum(os.path.getsize(f) for f in fotos)):.1f} MB, "
      f"maior {mb(max(os.path.getsize(f) for f in fotos)):.1f} MB)")
print(f"  selfies  : {len(selfies)}")
if not selfies:
    print("  AVISO: sem selfie nenhuma, o ensaio so mede envio e deteccao —")
    print("         NAO mede se a foto chega na pessoa certa, que e o que importa.")
print()

S = requests.Session()
r = S.post(f"{API}/login", data={"email": LOGIN, "senha": SENHA}, timeout=30)
if r.status_code != 200:
    print(f"Nao consegui entrar como {LOGIN} (HTTP {r.status_code}).")
    sys.exit(1)
H = {"Authorization": "Bearer " + r.json()["token"]}

S.post(f"{API}/event/delete", data={"code": CODIGO}, headers=H, timeout=30)   # sobra de ensaio anterior
r = S.post(f"{API}/event", data={"code": CODIGO, "name": "ENSAIO (apagar)"}, headers=H, timeout=60)
if r.status_code != 200:
    print(f"Nao consegui criar o evento de ensaio (HTTP {r.status_code}): {r.text[:200]}")
    sys.exit(1)
print(f"evento {CODIGO} criado\n")

# ---------------- 1. as fotos ----------------
print("1. ENVIANDO AS FOTOS (como o app envia: uma de cada vez)")
lat, sem_rosto, erros, por_foto = [], [], [], []
t0 = time.perf_counter()
for i, cam in enumerate(fotos, 1):
    nome = os.path.basename(cam)
    with open(cam, "rb") as fh:
        dados = fh.read()
    t = time.perf_counter()
    try:
        resp = S.post(f"{API}/ingest", data={"event": CODIGO},
                      files={"file": (nome, dados, "image/jpeg")}, headers=H, timeout=300)
        dt = (time.perf_counter() - t) * 1000
        if resp.status_code == 200:
            j = resp.json()
            lat.append(dt)
            por_foto.append({"arquivo": nome, "rostos": j.get("n_faces", 0),
                             "ms": round(dt), "mb": round(mb(len(dados)), 2),
                             "id": j.get("photo_id")})
            if not j.get("n_faces"): sem_rosto.append(nome)
        else:
            erros.append(f"{nome}: HTTP {resp.status_code}")
    except Exception as e:
        erros.append(f"{nome}: {str(e)[:60]}")
    print(f"   {i}/{len(fotos)}  {nome[:34]:<34} "
          f"{por_foto[-1]['rostos'] if por_foto and por_foto[-1]['arquivo'] == nome else '-'} rosto(s)  "
          f"{round(dt)} ms")
total = time.perf_counter() - t0

no_servidor = len(S.get(f"{API}/photos?event={CODIGO}", timeout=60).json().get("photos", []))
print()
print(f"   enviadas={len(fotos)}  no servidor={no_servidor}  PERDIDAS={len(fotos)-no_servidor}")
if lat:
    print(f"   por foto: P50={pct(lat,50):.0f} ms  P95={pct(lat,95):.0f} ms  max={max(lat):.0f} ms")
    print(f"   rajada inteira: {total:.1f} s")
com_rosto = len(fotos) - len(sem_rosto) - len(erros)
print(f"   com rosto detectado: {com_rosto}/{len(fotos)}")
if sem_rosto:
    print(f"   SEM rosto: {', '.join(os.path.basename(x) for x in sem_rosto[:8])}"
          + (" ..." if len(sem_rosto) > 8 else ""))
if erros:
    print(f"   ERROS: {erros[:5]}")

# ---------------- 2. os convidados ----------------
resultado_convidados = []
if selfies:
    print()
    print("2. REGISTRANDO OS CONVIDADOS (a selfie de cada um)")
    for cam in selfies:
        nome = os.path.basename(cam)
        with open(cam, "rb") as fh:
            dados = fh.read()
        t = time.perf_counter()
        try:
            resp = S.post(f"{API}/selfie", data={"event": CODIGO, "consent": "true"},
                          files={"file": (nome, dados, "image/jpeg")}, timeout=180)
            dt = (time.perf_counter() - t) * 1000
            if resp.status_code == 200:
                j = resp.json()
                resultado_convidados.append({"selfie": nome, "fotos": len(j.get("matches", [])),
                                             "ms": round(dt), "ids": j.get("matches", [])})
                print(f"   {nome[:34]:<34} reconhecido em {len(j.get('matches', []))} foto(s)  {round(dt)} ms")
            elif resp.status_code == 422:
                resultado_convidados.append({"selfie": nome, "fotos": None, "ms": round(dt)})
                print(f"   {nome[:34]:<34} NENHUM ROSTO NA SELFIE (o convidado nao entraria)")
            else:
                print(f"   {nome[:34]:<34} HTTP {resp.status_code}")
        except Exception as e:
            print(f"   {nome[:34]:<34} erro: {str(e)[:50]}")

# ---------------- 3. o veredito ----------------
print()
print("=" * 66)
print("VEREDITO")
print("=" * 66)
perdidas = len(fotos) - no_servidor
print(f"  Nenhuma foto perdida .............. {'SIM' if perdidas == 0 else 'NAO — ' + str(perdidas) + ' sumiram'}")
if lat:
    p95_total = pct(lat, 95) + 2500     # + o poll do convidado (2,5 s)
    print(f"  Do envio ate aparecer (P95) ....... {p95_total/1000:.1f} s  "
          f"{'(cabe nos 30 s do piloto)' if p95_total <= 30000 else '(ACIMA dos 30 s do piloto)'}")
print(f"  Fotos com rosto lido .............. {com_rosto}/{len(fotos)}")
if resultado_convidados:
    sem_nada = [c for c in resultado_convidados if c["fotos"] == 0]
    sem_selfie = [c for c in resultado_convidados if c["fotos"] is None]
    achados = [c for c in resultado_convidados if c["fotos"]]
    print(f"  Convidados que receberam foto ..... {len(achados)}/{len(resultado_convidados)}")
    if sem_selfie:
        print(f"  Selfies sem rosto (nao entrariam) . {len(sem_selfie)}: "
              f"{', '.join(c['selfie'] for c in sem_selfie[:5])}")
    if sem_nada:
        print(f"  Registraram mas NAO acharam foto .. {len(sem_nada)}: "
              f"{', '.join(c['selfie'] for c in sem_nada[:5])}")
    print()
    print("  ATENCAO: confira NA MAO se as fotos entregues sao mesmo daquela pessoa.")
    print("  Entregar foto para a pessoa ERRADA e a pior falha do piloto, e nenhum")
    print("  numero aqui prova isso — so o seu olho.")
    for c in achados[:10]:
        print(f"    {c['selfie']}: {API}/img/{CODIGO}/{c['ids'][0]}.jpg" if c["ids"] else "")

saida = os.path.join(PASTA, "ultimo-ensaio.json")
json.dump({"quando": time.strftime("%Y-%m-%d %H:%M"), "api": API, "fotos": por_foto,
           "convidados": resultado_convidados, "perdidas": perdidas,
           "p50_ms": round(pct(lat, 50)) if lat else None,
           "p95_ms": round(pct(lat, 95)) if lat else None,
           "rajada_s": round(total, 1), "erros": erros},
          open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print()
print(f"  bruto salvo em {os.path.relpath(saida, RAIZ)}")

print()
if input("  Apagar o evento de ensaio agora? [S/n] ").strip().lower() in ("", "s", "sim", "y"):
    S.post(f"{API}/event/delete", data={"code": CODIGO}, headers=H, timeout=60)
    print("  evento de ensaio apagado.")
else:
    print(f"  evento {CODIGO} MANTIDO — apague pelo painel quando terminar de conferir.")
