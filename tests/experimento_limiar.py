"""Foton -- experimento de limiar (item 3 do PROMPT-PROXIMA-SESSAO.md).

Objetivo: medir a similaridade cosseno (o MESMO calculo de rig.py: `g @ f` sobre
embeddings normalizados do buffalo_s) entre pares de rostos da MESMA pessoa em fotos
diferentes vs pares de PESSOAS diferentes, usando fotos reais (nao sinteticas).

Isto NAO chama a producao -- roda o mesmo modelo (buffalo_s) localmente, offline,
sobre fotos-teste/*.jpg (fotos-teste/ e ignorada pelo git; nada disto sai da maquina).

Modo 1 -- recortar (gera a folha de contato para inspecao visual):
    python tests/experimento_limiar.py recortar

Isso deteta todo rosto em fotos-teste/*.{jpg,jpeg,png} (NAO entra em selfies/, que e
outro uso), salva cada recorte numerado em fotos-teste/_recortes/, salva os embeddings
em fotos-teste/_embeddings.json, e monta folhas de contato (grade com o numero de cada
recorte) em fotos-teste/_folha-N.jpg para inspecao visual.

Modo 2 -- medir (depois de anotar quais numeros sao a mesma pessoa):
    python tests/experimento_limiar.py medir 3,7,15  9,22  1,4,4,18 -- --impostores auto
Cada grupo separado por espaco é uma pessoa (2+ recortes = pares genuinos).
Sem --impostores auto, todo par entre grupos diferentes tambem vira par impostor;
com --impostores auto, pares impostores sao amostrados entre TODOS os recortes nao
listados em nenhum grupo tambem (usa mais dado).
"""
import io, os, sys, json, itertools, random

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "fotos-teste")
RECORTES = os.path.join(PASTA, "_recortes")
EMB_JSON = os.path.join(PASTA, "_embeddings.json")
THRESH_ATUAL = 0.25  # o mesmo valor de app/test_rig/rig.py -- NAO mudar aqui sem medir


# excluido de proposito: grade de 36 fotos de perfil de contatos de terceiros
# (nao e material que o dono tirou para o teste -- ver docs/BENCHMARKS.md).
EXCLUIR = {"captura de tela 2026-09-01 104301.png"}


def imagens(pasta):
    if not os.path.isdir(pasta):
        return []
    vistos, saida = set(), []
    for nome in sorted(os.listdir(pasta)):
        if nome.lower() in EXCLUIR or nome.startswith("_"):
            continue  # "_" = artefato nosso (folha de contato, etc), nao foto-fonte
        if not nome.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        cam = os.path.join(pasta, nome)
        if os.path.isfile(cam) and cam.lower() not in vistos:
            vistos.add(cam.lower())
            saida.append(cam)
    return saida


def recortar():
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    from insightface.app import FaceAnalysis

    # varre a raiz (fotos de evento, varias pessoas) E selfies/ (aqui usado para
    # fotos da MESMA pessoa em dias diferentes -- o dado que faltava antes).
    fotos = [(f, os.path.basename(f)) for f in imagens(PASTA)]
    fotos += [(f, "selfies/" + os.path.basename(f)) for f in imagens(os.path.join(PASTA, "selfies"))]
    if not fotos:
        print(f"Nenhuma foto em {PASTA}. Coloque fotos com gente.")
        sys.exit(1)

    print(f"carregando buffalo_s ...")
    fa = FaceAnalysis(name="buffalo_s", root=os.path.join(RAIZ, "app", "test_rig"),
                       allowed_modules=["detection", "recognition"],
                       providers=["CPUExecutionProvider"])
    fa.prepare(ctx_id=-1, det_size=(640, 640))

    os.makedirs(RECORTES, exist_ok=True)
    for f in os.listdir(RECORTES):
        os.remove(os.path.join(RECORTES, f))

    registros = []  # {"n": int, "arquivo": str, "embedding": [floats]}
    crops = []      # (n, PIL.Image, arquivo)
    n = 0
    for cam, nome in fotos:
        with open(cam, "rb") as fh:
            raw = fh.read()
        arr = np.frombuffer(raw, np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            print(f"  {nome}: nao abriu"); continue
        faces = fa.get(bgr)
        print(f"  {nome}: {len(faces)} rosto(s)")
        h, w = bgr.shape[:2]
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            pad = int(0.25 * max(x2 - x1, y2 - y1))
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
            crop_bgr = bgr[y1:y2, x1:x2]
            crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(crop_rgb)
            n += 1
            im.save(os.path.join(RECORTES, f"{n:03d}.jpg"), quality=90)
            registros.append({"n": n, "arquivo": nome,
                               "embedding": face.normed_embedding.astype(float).tolist()})
            crops.append((n, im, nome))

    json.dump(registros, open(EMB_JSON, "w", encoding="utf-8"))
    print(f"\n{n} rosto(s) recortado(s) em {os.path.relpath(RECORTES, RAIZ)}/")
    print(f"embeddings salvos em {os.path.relpath(EMB_JSON, RAIZ)}")

    # folha de contato: grade de ate 30 recortes por folha, com o numero escrito
    CEL = 160
    COLS = 6
    try:
        fonte = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
    except Exception:
        fonte = ImageFont.load_default()
    por_folha = 30
    for pagina, i0 in enumerate(range(0, len(crops), por_folha), 1):
        lote = crops[i0:i0 + por_folha]
        linhas = (len(lote) + COLS - 1) // COLS
        folha = Image.new("RGB", (COLS * CEL, linhas * CEL), (20, 20, 20))
        draw = ImageDraw.Draw(folha)
        for i, (num, im, nome) in enumerate(lote):
            r, c = divmod(i, COLS)
            t = im.copy()
            t.thumbnail((CEL - 8, CEL - 30))
            x, y = c * CEL + 4, r * CEL + 4
            folha.paste(t, (x, y))
            draw.text((x, r * CEL + CEL - 24), f"#{num}", font=fonte, fill=(255, 220, 80))
        caminho = os.path.join(PASTA, f"_folha-{pagina}.jpg")
        folha.save(caminho, quality=88)
        print(f"folha de contato: {os.path.relpath(caminho, RAIZ)}")


def medir(grupos_txt, impostores_auto, impostores_mesma_foto):
    import numpy as np
    registros = json.load(open(EMB_JSON, encoding="utf-8"))
    por_n = {r["n"]: np.array(r["embedding"], dtype=np.float32) for r in registros}
    arquivo_de = {r["n"]: r["arquivo"] for r in registros}

    grupos = []
    usados = set()
    for g in grupos_txt:
        ns = [int(x) for x in g.split(",")]
        for x in ns:
            if x not in por_n:
                print(f"aviso: #{x} nao existe nos embeddings, ignorando"); ns.remove(x)
        grupos.append(ns)
        usados.update(ns)

    genuinos = []
    for g in grupos:
        for a, b in itertools.combinations(g, 2):
            genuinos.append((a, b, float(por_n[a] @ por_n[b])))

    impostores = []
    for ga, gb in itertools.combinations(grupos, 2):
        for a in ga:
            for b in gb:
                impostores.append((a, b, float(por_n[a] @ por_n[b])))

    if impostores_mesma_foto:
        # duas faces na MESMA foto sao garantidamente pessoas diferentes -- fonte
        # de impostor quase sempre confiavel, sem rotulagem manual -- EXCETO reflexo
        # de espelho (a mesma pessoa aparece 2x na mesma foto). Pares ja marcados
        # como genuinos (grupos manuais) sao excluidos daqui para nao contradizer.
        genuino_pares = {frozenset(p) for g in grupos for p in itertools.combinations(g, 2)}
        por_arquivo = {}
        for n, arq in arquivo_de.items():
            por_arquivo.setdefault(arq, []).append(n)
        for arq, ns in por_arquivo.items():
            for a, b in itertools.combinations(ns, 2):
                if frozenset((a, b)) in genuino_pares:
                    continue
                impostores.append((a, b, float(por_n[a] @ por_n[b])))

    if impostores_auto:
        sobrando = [n for n in por_n if n not in usados]
        random.seed(0)
        amostra = random.sample(sobrando, min(len(sobrando), 40))
        for a in amostra:
            for g in grupos:
                for b in g:
                    impostores.append((a, b, float(por_n[a] @ por_n[b])))

    def resumo(nome, pares):
        if not pares:
            print(f"{nome}: nenhum par"); return
        vals = sorted(v for _, _, v in pares)
        print(f"{nome}: n={len(vals)}  min={vals[0]:.3f}  "
              f"p50={vals[len(vals)//2]:.3f}  max={vals[-1]:.3f}")
        return vals

    print("=" * 60)
    gv = resumo("GENUINOS  (mesma pessoa, fotos diferentes)", genuinos)
    iv = resumo("IMPOSTORES (pessoas diferentes)", impostores)
    print("=" * 60)
    if gv and iv:
        pior_genuino = min(gv)
        pior_impostor = max(iv)
        print(f"pior par genuino  (mais parecido de ser 'diferente') = {pior_genuino:.3f}")
        print(f"pior par impostor (mais parecido de ser 'igual')     = {pior_impostor:.3f}")
        if pior_genuino > pior_impostor:
            meio = (pior_genuino + pior_impostor) / 2
            print(f"SEPARAM: ha uma faixa livre entre {pior_impostor:.3f} e {pior_genuino:.3f}.")
            print(f"limiar sugerido (meio da faixa) = {meio:.3f}  "
                  f"(limiar atual de rig.py = {THRESH_ATUAL})")
        else:
            print("NAO SEPARAM LIMPO -- ha sobreposicao entre genuino e impostor nesta amostra.")
            print("Nao dá pra apertar o limiar com seguranca so com esses dados.")
    print()
    print("pares genuinos:", [(a, b, round(v, 3)) for a, b, v in genuinos])
    print("pares impostores (amostra):", [(a, b, round(v, 3)) for a, b, v in impostores[:20]])


def sugerir(top=25):
    """Em vez de eu adivinhar identidade por olho em 300 recortes, deixa o PROPRIO
    modelo propor os pares mais parecidos entre fotos de DIAS diferentes -- so entao
    eu confiro visualmente so os candidatos, em vez de rotular tudo as cegas."""
    import numpy as np
    registros = json.load(open(EMB_JSON, encoding="utf-8"))
    por_n = {r["n"]: np.array(r["embedding"], dtype=np.float32) for r in registros}
    arquivo_de = {r["n"]: r["arquivo"] for r in registros}

    def data_de(arquivo):
        # tenta achar um AAAAMMDD no nome; senao usa o nome do arquivo inteiro
        import re
        m = re.search(r"(20\d{6})", arquivo)
        return m.group(1) if m else arquivo

    ns = sorted(por_n)
    candidatos = []
    for a, b in itertools.combinations(ns, 2):
        da, db = data_de(arquivo_de[a]), data_de(arquivo_de[b])
        if da == db:
            continue  # mesmo dia -- nao e o dado que falta
        candidatos.append((a, b, float(por_n[a] @ por_n[b]), arquivo_de[a], arquivo_de[b]))
    candidatos.sort(key=lambda x: -x[2])
    print(f"top {top} pares MAIS PARECIDOS entre fotos de dias diferentes:")
    for a, b, v, fa, fb in candidatos[:top]:
        print(f"  #{a:>3} ({fa:<32}) <-> #{b:>3} ({fb:<32})  sim={v:.3f}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("recortar", "medir", "sugerir"):
        print(__doc__); sys.exit(1)
    if sys.argv[1] == "recortar":
        recortar()
    elif sys.argv[1] == "sugerir":
        sugerir()
    else:
        args = sys.argv[2:]
        auto = "--impostores" in args and "auto" in args
        mesma_foto = "--impostores-mesma-foto" in args
        grupos = [a for a in args if a not in ("--impostores", "auto", "--impostores-mesma-foto")]
        medir(grupos, auto, mesma_foto)
