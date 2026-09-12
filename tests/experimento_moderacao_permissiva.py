"""Foton -- moderacao com licenca PERMISSIVA: tres candidatos nas mesmas 80 fotos de festa.

Por que existe: o candidato anterior (NudeNet) e AGPL-3.0 -- o repositorio e os pesos. O
dono pediu alternativa MIT / Apache 2.0 / BSD (2026-09-12). Os permissivos que existem
julgam a IMAGEM INTEIRA, nao a parte do corpo, e a regra do dono e por parte do corpo
("decote passa, mamilo nao"). A pergunta que so a medicao responde:

    quantas fotos REAIS de festa, SEM nudez nenhuma, cada modelo reteria?

Toda retencao aqui e falso positivo. Mede tambem o custo por foto num nucleo, nas mesmas
condicoes do experimento anterior (fotos reduzidas a 2048 px, processo preso a 1 nucleo).

    python tests/experimento_moderacao_permissiva.py

Candidatos (licenca lida da API do Hugging Face em 2026-09-12):
  Freepik/nsfw_image_detector       MIT        4 niveis: neutral / low / medium / high
  Marqo/nsfw-image-detection-384    Apache-2.0 binario
  AdamCodd/vit-base-nsfw-detector   Apache-2.0 binario, ONNX 4-bit

Dependencias SO do experimento (torch CPU, timm, transformers, huggingface_hub,
onnxruntime). Nada disto entra no produto sem ADR. Modelos ficam no cache do HF apontado
por HF_HOME; nada sai da maquina alem do download dos pesos.
"""
import os, sys, time, json

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
from experimento_moderacao import imagens, pct, LONG_EDGE   # mesmas fotos, mesma reducao

LIMIARES = (0.3, 0.5, 0.7, 0.9)
SAIDA = os.path.join(RAIZ, "fotos-teste", "_moderacao-permissiva.json")


def carregar_foto(cam):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(cam)).convert("RGB")
    w, h = im.size
    s = LONG_EDGE / max(w, h)
    if s < 1:
        im = im.resize((int(w * s), int(h * s)), Image.BILINEAR)
    return im


def modelo_freepik():
    """Uso exatamente como o README: transformers + transform do EVA02 no timm.
    Desvio declarado: float32 (o README usa bfloat16 em GPU; aqui e CPU)."""
    import torch
    from transformers import AutoModelForImageClassification
    from timm.data import resolve_data_config
    from timm.data.transforms_factory import create_transform
    from timm.models import get_pretrained_cfg
    m = AutoModelForImageClassification.from_pretrained("Freepik/nsfw_image_detector").eval()
    cfg = get_pretrained_cfg("eva02_base_patch14_448.mim_in22k_ft_in22k_in1k")
    tf = create_transform(**resolve_data_config(cfg.__dict__))

    def rodar(im):
        with torch.inference_mode():
            p = torch.softmax(m(tf(im).unsqueeze(0)).logits, dim=-1)[0].tolist()
        # ordem do README: 0 neutral, 1 low, 2 medium, 3 high
        return {"neutral": p[0], "low": p[1], "medium": p[2], "high": p[3],
                "retem": p[3],                          # gatilho: "alto" = explicito
                "medium_ou_mais": p[2] + p[3]}
    return "Freepik (MIT, 4 niveis)", rodar


def modelo_marqo():
    import torch, timm
    m = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True).eval()
    dc = timm.data.resolve_model_data_config(m)
    tf = timm.data.create_transform(**dc, is_training=False)
    nomes = [str(n).lower() for n in (m.pretrained_cfg.get("label_names") or [])]
    i_nsfw = next((i for i, n in enumerate(nomes) if "nsfw" in n), None)
    if i_nsfw is None:
        raise SystemExit(f"Marqo: nao achei o rotulo NSFW em {nomes} -- nao vou chutar o indice")

    def rodar(im):
        with torch.inference_mode():
            p = torch.softmax(m(tf(im).unsqueeze(0)), dim=-1)[0].tolist()
        return {"rotulos": nomes, "retem": p[i_nsfw]}
    return f"Marqo (Apache-2.0, binario; rotulos {nomes})", rodar


def modelo_adamcodd():
    import numpy as np, onnxruntime as ort
    from huggingface_hub import hf_hub_download
    repo = "AdamCodd/vit-base-nsfw-detector"
    onx = hf_hub_download(repo, "onnx/model_bnb4.onnx")
    cfg = json.load(open(hf_hub_download(repo, "config.json"), encoding="utf-8"))
    pre = json.load(open(hf_hub_download(repo, "preprocessor_config.json"), encoding="utf-8"))
    id2label = {int(k): v.lower() for k, v in cfg["id2label"].items()}
    i_nsfw = next((i for i, n in id2label.items() if "nsfw" in n), None)
    if i_nsfw is None:
        raise SystemExit(f"AdamCodd: nao achei o rotulo NSFW em {id2label} -- nao vou chutar")
    tam = pre.get("size", {})
    lado = tam.get("height") or tam.get("shortest_edge") or 384
    media = np.array(pre.get("image_mean", [0.5] * 3), np.float32)
    desvio = np.array(pre.get("image_std", [0.5] * 3), np.float32)
    so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
    ses = ort.InferenceSession(onx, so, providers=["CPUExecutionProvider"])
    entrada = ses.get_inputs()[0].name

    def rodar(im):
        from PIL import Image
        x = np.asarray(im.resize((lado, lado), Image.BILINEAR), np.float32) / 255.0
        x = ((x - media) / desvio).transpose(2, 0, 1)[None]
        z = ses.run(None, {entrada: x})[0][0]
        p = np.exp(z - z.max()); p = p / p.sum()
        return {"rotulos": id2label, "retem": float(p[i_nsfw])}
    return f"AdamCodd (Apache-2.0, binario, ONNX 4-bit, {lado}px)", rodar


def main():
    import psutil, torch
    psutil.Process().cpu_affinity([0])          # UM nucleo, como no experimento anterior
    torch.set_num_threads(1)
    fotos = imagens()
    print(f"{len(fotos)} fotos reais de festa, SEM nudez -- toda retencao e falso positivo\n")
    resultado = {}
    for construtor in (modelo_freepik, modelo_marqo, modelo_adamcodd):
        nome, rodar = construtor()
        rodar(carregar_foto(fotos[0]))          # aquece: a 1a chamada nao e custo de regime
        tempos, por_foto = [], []
        for cam in fotos:
            im = carregar_foto(cam)
            t = time.perf_counter(); r = rodar(im); tempos.append((time.perf_counter() - t) * 1000)
            por_foto.append({"foto": os.path.relpath(cam, os.path.join(RAIZ, "fotos-teste")),
                             **{k: v for k, v in r.items() if k != "rotulos"}})
        scores = sorted(x["retem"] for x in por_foto)
        print("=" * 72)
        print(nome)
        print(f"  tempo por foto (ms, 1 nucleo): p50 {pct(tempos,50):.0f} · p95 {pct(tempos,95):.0f} · max {max(tempos):.0f}")
        print(f"  score de retencao: p50 {pct(scores,50):.3f} · p95 {pct(scores,95):.3f} · max {scores[-1]:.3f}")
        for lim in LIMIARES:
            n = sum(s >= lim for s in scores)
            print(f"  retidas com score >= {lim}: {n}/{len(fotos)} ({100*n/len(fotos):.1f}%)")
        if "medium_ou_mais" in por_foto[0]:
            n = sum(x["medium_ou_mais"] >= 0.5 for x in por_foto)
            print(f"  (se o gatilho fosse 'medio ou mais' >= 0.5: {n}/{len(fotos)})")
        top = sorted(por_foto, key=lambda x: -x["retem"])[:5]
        print("  5 fotos com maior score:", [(x["foto"], round(x["retem"], 3)) for x in top])
        resultado[nome] = {"tempos_ms": tempos, "por_foto": por_foto}
    json.dump(resultado, open(SAIDA, "w", encoding="utf-8"), indent=1)
    print(f"\nbruto em {os.path.relpath(SAIDA, RAIZ)}")


if __name__ == "__main__":
    main()
