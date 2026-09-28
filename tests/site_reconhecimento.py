"""O site afirma que o Fóton entregaria as fotos da capa à selfie da capa. Isto mede.

    .venv-experimento/Scripts/python.exe tests/site_reconhecimento.py

Mede os arquivos PUBLICADOS em site/img (não os originais do Higgsfield), com o mesmo
motor e o mesmo limiar da produção (rig.py: buffalo_s, det 640, THRESH). As pessoas são
fictícias, geradas por IA (site/img/PROCEDENCIA.json). Grava o resultado no próprio
PROCEDENCIA.json: é de lá que o número do site sai.
"""
import json, os, sys

import cv2
from insightface.app import FaceAnalysis

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(RAIZ, "site", "img")
sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
LIMIAR = 0.40   # igual a rig.THRESH (ADR-0034); conferido abaixo sem importar o rig inteiro

with open(os.path.join(RAIZ, "app", "test_rig", "rig.py"), encoding="utf-8") as f:
    assert f"THRESH = {LIMIAR:.2f}" in f.read(), "o limiar da produção mudou: atualize este script"

fa = FaceAnalysis(name="buffalo_s", allowed_modules=["detection", "recognition"],
                  providers=["CPUExecutionProvider"])
fa.prepare(ctx_id=-1, det_size=(640, 640))


def rostos(nome):
    im = cv2.imread(os.path.join(IMG, nome))
    assert im is not None, nome
    return fa.get(im)


selfie = max(rostos("selfie-480.webp"), key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
# Mede nas versoes de 800 px: em producao o servidor recebe a foto inteira, e na miniatura
# de 360 px o rosto encolhe a ponto de mudar o resultado (medido: a da pista caiu de 0,41
# para 0,29). A da pista saiu do site por isso: raspava o limiar ate no original.
fotos = ["capa-1200.webp", "ela-brinde-800.webp", "ela-abraco-800.webp", "ela-saida-800.webp",
         "fotografa-800.webp", "trilha-800.webp", "bar-800.webp"]
res = {}
for n in fotos:
    fs = rostos(n)
    sim = max((float(f.normed_embedding @ selfie.normed_embedding) for f in fs), default=0.0)
    res[n] = round(sim, 3)
    print(f"{n:24} rostos={len(fs)}  semelhança={sim:.3f}  {'ENTREGA' if sim >= LIMIAR else 'não entrega'}")

ela = [n for n in fotos if n.startswith(("capa", "ela-"))]
outras = [n for n in fotos if n not in ela]
ok = all(res[n] >= LIMIAR for n in ela) and all(res[n] < LIMIAR for n in outras)
print("\nA história do site é verdadeira:" if ok else "\nFALHA: a história do site NÃO se sustenta",
      f"as {len(ela)} fotos dela passam do limiar {LIMIAR}; as {len(outras)} de outras pessoas não.")

p = os.path.join(IMG, "PROCEDENCIA.json")
proc = json.load(open(p, encoding="utf-8"))
proc["reconhecimento"] = {
    "o_que": "selfie-480.webp contra cada foto publicada, no motor e limiar da produção",
    "script": "tests/site_reconhecimento.py", "limiar": LIMIAR, "adr": "ADR-0034",
    "semelhanca": res, "historia_verdadeira": ok,
}
json.dump(proc, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
sys.exit(0 if ok else 1)
