"""Foton -- experimento de MODERACAO para a Foto'n Fiesta (convidado envia foto).

Pergunta do dono (PRODUTO §2): o corte e genitalia e mamilo, NAO "nudez" generica --
"um filtro treinado em nudez generica reprovaria metade de um casamento". Este script
mede exatamente esse medo, e o custo em tempo, antes de qualquer linha de produto:

  1. FALSO POSITIVO em foto de festa real: as fotos de fotos-teste/ nao tem nudez
     nenhuma, entao TODO alerta de classe bloqueada e um falso positivo.
  2. CUSTO: tempo do NudeNet (320n) vs o do buffalo_s que ja roda no /ingest, nas MESMAS
     fotos, reduzidas a 2048 px como a producao, com o processo preso a UM nucleo. O
     absoluto e desta maquina; a RAZAO entre os dois e o que se transfere para a VM.

    python tests/experimento_moderacao.py

Dependencias SO do experimento (nao do produto -- entrar no produto exige ADR):
nudenet==3.4.2 (MIT, ONNX), psutil. Roda offline; nada sai da maquina.
"""
import os, sys, time, glob, json

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "fotos-teste")
LONG_EDGE = 2048                                     # o mesmo de app/test_rig/rig.py

# A regra do dono (PRODUTO §2, fechada em 2026-09-12): genitalia, mamilo e anus nao;
# bunda pode; decote passa; PEITO MASCULINO PASSA (festa de piscina, praia).
BLOQUEIA = {"FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED",
            "MALE_GENITALIA_EXPOSED", "ANUS_EXPOSED"}
EM_ABERTO = set()          # nada em aberto: as tres duvidas foram decididas pelo dono
EXCLUIR = {"captura de tela 2026-09-01 104301.png"}   # grade de contatos de terceiros


def imagens():
    out = []
    for pasta in (PASTA, os.path.join(PASTA, "selfies")):
        for n in sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []:
            if n.startswith("_") or n.lower() in EXCLUIR:
                continue
            if n.lower().endswith((".jpg", ".jpeg", ".png")):
                out.append(os.path.join(pasta, n))
    return out


def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p / 100; f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def main():
    import cv2, numpy as np, psutil
    psutil.Process().cpu_affinity([0])              # UM nucleo: mais perto da VM, e justo
    sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
    from nudenet import NudeDetector
    from insightface.app import FaceAnalysis

    nd = NudeDetector()
    fa = FaceAnalysis(name="buffalo_s", root=os.path.join(RAIZ, "app", "test_rig"),
                      allowed_modules=["detection", "recognition"],
                      providers=["CPUExecutionProvider"])
    fa.prepare(ctx_id=-1, det_size=(640, 640))

    fotos = imagens()
    t_nude, t_face, achados = [], [], []
    por_classe = {}
    # aquece os dois (primeira chamada paga alocacao; nao e o custo de regime)
    img0 = cv2.imread(fotos[0]); nd.detect(img0); fa.get(img0)

    for cam in fotos:
        img = cv2.imdecode(np.fromfile(cam, np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        s = LONG_EDGE / max(h, w)
        if s < 1:
            img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        t = time.perf_counter(); det = nd.detect(img); t_nude.append((time.perf_counter() - t) * 1000)
        t = time.perf_counter(); fa.get(img);         t_face.append((time.perf_counter() - t) * 1000)
        for d in det:
            c, sc = d["class"], float(d["score"])
            por_classe.setdefault(c, []).append(sc)
            if c in BLOQUEIA or c in EM_ABERTO:
                achados.append({"foto": os.path.relpath(cam, PASTA), "classe": c,
                                "score": round(sc, 3), "caixa": [int(x) for x in d["box"]]})

    n = len(fotos)
    print(f"{n} fotos reais de festa (sem nudez nenhuma), reduzidas a {LONG_EDGE}px, 1 nucleo\n")
    print("TEMPO por foto (ms)      p50      p95      max")
    print(f"  NudeNet 320n       {pct(t_nude,50):7.0f}  {pct(t_nude,95):7.0f}  {max(t_nude):7.0f}")
    print(f"  buffalo_s (ja roda){pct(t_face,50):7.0f}  {pct(t_face,95):7.0f}  {max(t_face):7.0f}")
    print(f"  RAZAO NudeNet/buffalo_s (p50): {pct(t_nude,50)/pct(t_face,50):.2f}x\n")

    print("FALSO POSITIVO nas classes que o dono BLOQUEIA (toda deteccao aqui e falsa):")
    for lim in (0.3, 0.5, 0.7):
        fotos_fp = {a["foto"] for a in achados if a["classe"] in BLOQUEIA and a["score"] >= lim}
        print(f"  score >= {lim}: {len(fotos_fp)}/{n} fotos seriam retidas "
              f"({100*len(fotos_fp)/n:.1f}%)")
    print("\nclasses detectadas (quantas deteccoes, score maximo):")
    for c, v in sorted(por_classe.items(), key=lambda x: -len(x[1])):
        marca = "  <- BLOQUEIA" if c in BLOQUEIA else "  <- em aberto" if c in EM_ABERTO else ""
        print(f"  {c:26} {len(v):4d}  max {max(v):.2f}{marca}")
    json.dump(achados, open(os.path.join(PASTA, "_moderacao-achados.json"), "w",
                            encoding="utf-8"), indent=1)
    if achados:
        print(f"\n{len(achados)} achado(s) em classe bloqueada/em aberto -> "
              f"fotos-teste/_moderacao-achados.json (conferir no olho)")


if __name__ == "__main__":
    main()
