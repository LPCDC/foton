"""Foton -- a cascata de moderacao (Marqo -> Freepik) cabe no stack da VM?

A VM de producao NAO tem PyTorch, o auto-update nao instala dependencia e ha 1 GB de RAM
dividida com o reconhecimento facial. A cascata medida em 2026-09-12 rodou em PyTorch.
Este script responde, com numero, o que falta antes da ADR de moderacao:

  exportar   PyTorch -> ONNX (os dois modelos), no mesmo onnxruntime que a VM ja usa
  paridade   pre-processamento reescrito SEM torch == o do timm (pixel a pixel), e
             ONNX decide IGUAL ao PyTorch nas 80 fotos de festa (a decisao da cascata)
  recursos   memoria que cada modelo ACRESCENTA ao processo que ja carrega o buffalo_s,
             e tempo por foto com 1 thread, processo preso a 1 nucleo

    python tests/experimento_moderacao_onnx.py exportar
    python tests/experimento_moderacao_onnx.py paridade
    python tests/experimento_moderacao_onnx.py recursos

Os .onnx ficam em .venv-experimento/modelos-onnx/ (fora do git: o Freepik tem ~170 MB e
nada disso entra no produto sem ADR).
"""
import os, sys, time, json, subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
DIR_ONNX = os.path.join(RAIZ, ".venv-experimento", "modelos-onnx")
MARQO_ONNX = os.path.join(DIR_ONNX, "marqo_vit_tiny_384.onnx")
FREEPIK_ONNX = os.path.join(DIR_ONNX, "freepik_eva02_base_448.onnx")
PORTAO_MARQO, GATILHO_ALTO = 0.15, 0.5        # a cascata recomendada em FIESTA-IMPLEMENTACAO §3.4

# ---------------- pre-processamento SEM torch (e o que iria para a VM) ----------------
MARQO_CFG = dict(lado=384, media=(0.5, 0.5, 0.5), desvio=(0.5, 0.5, 0.5), modo="center")
FREEPIK_CFG = dict(lado=448, media=(0.48145466, 0.4578275, 0.40821073),
                   desvio=(0.26862954, 0.26130258, 0.27577711), modo="squash")


def preparar(im, cfg):
    """Reproduz o transform de avaliacao do timm com crop_pct=1.0, so com PIL e numpy.
    center: redimensiona o LADO MENOR para `lado` (bicubico) e corta o centro.
    squash: redimensiona direto para lado x lado (bicubico), sem manter proporcao."""
    import numpy as np
    from PIL import Image
    s = cfg["lado"]
    if cfg["modo"] == "squash":
        im = im.resize((s, s), Image.BICUBIC)
    else:
        w, h = im.size
        if w <= h:
            nw, nh = s, int(s * h / w)
        else:
            nw, nh = int(s * w / h), s
        im = im.resize((nw, nh), Image.BICUBIC)
        left = int(round((nw - s) / 2.0)); top = int(round((nh - s) / 2.0))
        im = im.crop((left, top, left + s, top + s))
    x = np.asarray(im, dtype=np.float32) / 255.0
    x = (x - np.array(cfg["media"], np.float32)) / np.array(cfg["desvio"], np.float32)
    return x.transpose(2, 0, 1)[None].astype(np.float32)


def softmax(z):
    import numpy as np
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# ---------------- modelos PyTorch (referencia) ----------------
def torch_marqo():
    import timm
    m = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True).eval()
    tf = timm.data.create_transform(**timm.data.resolve_model_data_config(m), is_training=False)
    nomes = [str(n).lower() for n in m.pretrained_cfg["label_names"]]
    return m, tf, nomes.index("nsfw")


def torch_freepik(float32=True):
    """Os pesos carregam em bfloat16 (config do repositorio), e o forward do wrapper converte
    a entrada sozinho -- por isso o experimento de 2026-09-12 rodou em bf16 sem avisar.
    float32=True e o que vai para ONNX; float32=False reproduz o experimento anterior.

    A atencao "fundida" (scaled_dot_product_attention) nao passa pelo exportador classico
    do ONNX. timm.layers.set_fused_attn(False) troca pelo caminho matematico explicito --
    so na versao exportada; a de referencia (bf16) fica como o experimento anterior rodou.
    A chave e lida na CRIACAO do modelo, por isso vem antes do from_pretrained."""
    import timm.layers
    timm.layers.set_fused_attn(not float32)
    from transformers import AutoModelForImageClassification
    from timm.data import resolve_data_config
    from timm.data.transforms_factory import create_transform
    from timm.models import get_pretrained_cfg
    w = AutoModelForImageClassification.from_pretrained("Freepik/nsfw_image_detector").eval()
    if float32:
        w = w.float()
    cfg = get_pretrained_cfg("eva02_base_patch14_448.mim_in22k_ft_in22k_in1k")
    tf = create_transform(**resolve_data_config(cfg.__dict__))
    return w, tf


# ---------------- 1) exportar ----------------
def exportar():
    import torch
    os.makedirs(DIR_ONNX, exist_ok=True)
    m, _, _ = torch_marqo()
    w, _ = torch_freepik()
    for nome, modelo, lado, destino in (("Marqo", m, 384, MARQO_ONNX),
                                        ("Freepik", w.timm_model, 448, FREEPIK_ONNX)):
        t = time.perf_counter()
        torch.onnx.export(modelo, torch.zeros(1, 3, lado, lado), destino,
                          input_names=["pixel_values"], output_names=["logits"],
                          opset_version=17, dynamo=False, do_constant_folding=True)
        print(f"{nome}: {os.path.relpath(destino, RAIZ)}  "
              f"{os.path.getsize(destino)/1e6:.1f} MB  ({time.perf_counter()-t:.1f} s)")


# ---------------- 2) paridade ----------------
def sessao(caminho, threads=1, pouca_memoria=False):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
    if pouca_memoria:
        so.enable_cpu_mem_arena = False; so.enable_mem_pattern = False
    return ort.InferenceSession(caminho, so, providers=["CPUExecutionProvider"])


def paridade():
    import numpy as np, torch
    from experimento_moderacao import imagens
    from experimento_moderacao_permissiva import carregar_foto
    torch.set_num_threads(4)
    m, tf_m, i_nsfw = torch_marqo()
    w, tf_f = torch_freepik(float32=True)
    w16, _ = torch_freepik(float32=False)        # a precisao em que o experimento anterior rodou
    s_m, s_f = sessao(MARQO_ONNX, 4), sessao(FREEPIK_ONNX, 4)
    dif_pre_m = dif_pre_f = dif_prob_m = dif_prob_f = dif_bf16 = 0.0
    decisoes_iguais = iguais_bf16 = n = 0
    detalhe = []
    for cam in imagens():
        im = carregar_foto(cam)
        # pre-processamento: timm (referencia) x numpy (o da VM)
        ref_m = tf_m(im).unsqueeze(0).numpy(); np_m = preparar(im, MARQO_CFG)
        ref_f = tf_f(im).unsqueeze(0).numpy(); np_f = preparar(im, FREEPIK_CFG)
        dif_pre_m = max(dif_pre_m, float(np.abs(ref_m - np_m).max()))
        dif_pre_f = max(dif_pre_f, float(np.abs(ref_f - np_f).max()))
        # PyTorch com o pre-processamento dele x ONNX com o nosso
        with torch.inference_mode():
            pt_m = torch.softmax(m(torch.from_numpy(ref_m)), -1)[0].numpy()
            pt_f = torch.softmax(w(torch.from_numpy(ref_f)).logits, -1)[0].numpy()
            pt_f16 = torch.softmax(w16(torch.from_numpy(ref_f)).logits.float(), -1)[0].numpy()
        ox_m = softmax(s_m.run(None, {"pixel_values": np_m})[0][0])
        ox_f = softmax(s_f.run(None, {"pixel_values": np_f})[0][0])
        dif_prob_m = max(dif_prob_m, float(np.abs(pt_m - ox_m).max()))
        dif_prob_f = max(dif_prob_f, float(np.abs(pt_f - ox_f).max()))
        dif_bf16 = max(dif_bf16, float(np.abs(pt_f16 - ox_f).max()))
        dec_pt = bool(pt_m[i_nsfw] >= PORTAO_MARQO and pt_f[3] >= GATILHO_ALTO)
        dec_ox = bool(ox_m[i_nsfw] >= PORTAO_MARQO and ox_f[3] >= GATILHO_ALTO)
        dec_16 = bool(pt_m[i_nsfw] >= PORTAO_MARQO and pt_f16[3] >= GATILHO_ALTO)
        sobe_pt, sobe_ox = pt_m[i_nsfw] >= PORTAO_MARQO, ox_m[i_nsfw] >= PORTAO_MARQO
        decisoes_iguais += (dec_pt == dec_ox and sobe_pt == sobe_ox)
        iguais_bf16 += (dec_16 == dec_ox)
        n += 1
        detalhe.append((os.path.basename(cam), round(float(pt_m[i_nsfw]), 4),
                        round(float(ox_m[i_nsfw]), 4), round(float(pt_f[3]), 4), round(float(ox_f[3]), 4)))
    print(f"{n} fotos")
    print(f"pre-processamento numpy x timm, maior diferenca por pixel:  Marqo {dif_pre_m:.2e}   Freepik {dif_pre_f:.2e}")
    print(f"probabilidade ONNX x PyTorch, maior diferenca:              Marqo {dif_prob_m:.2e}   Freepik {dif_prob_f:.2e}")
    print(f"Freepik ONNX fp32 x PyTorch bf16 (o experimento anterior):  {dif_bf16:.2e}")
    print(f"decisao da cascata identica ONNX x PyTorch fp32:            {decisoes_iguais}/{n}")
    print(f"decisao identica ONNX x PyTorch bf16 (o experimento anterior): {iguais_bf16}/{n}")
    pior = sorted(detalhe, key=lambda d: -abs(d[1] - d[2]))[:3]
    print("maiores diferencas no score do Marqo (foto, torch, onnx, freepik-alto torch, onnx):", pior)


# ---------------- 3) recursos (cada medicao num processo limpo) ----------------
_FILHO = r"""
import os, sys, time, json, gc
import psutil
psutil.Process().cpu_affinity([0])
os.environ["OMP_NUM_THREADS"] = "1"
sys.path.insert(0, {tests!r}); sys.path.insert(0, {rig!r})
p = psutil.Process()
def rss(): gc.collect(); return p.memory_info().rss / 1e6
import numpy as np, onnxruntime as ort, cv2
from PIL import Image
from experimento_moderacao import imagens
from experimento_moderacao_permissiva import carregar_foto
from experimento_moderacao_onnx import preparar, sessao, MARQO_CFG, FREEPIK_CFG, MARQO_ONNX, FREEPIK_ONNX
out = {{"base": rss()}}
fotos = imagens()[:{n}]
if {com_face}:
    from insightface.app import FaceAnalysis
    fa = FaceAnalysis(name="buffalo_s", root={rig!r}, allowed_modules=["detection", "recognition"],
                      providers=["CPUExecutionProvider"])
    fa.prepare(ctx_id=-1, det_size=(640, 640))
    fa.get(cv2.imread(fotos[0])); out["com_buffalo_s"] = rss()
ses = {{}}
for nome, cam, cfg in {modelos}:
    antes = rss()
    s = sessao(cam, 1, {pouca})
    x0 = preparar(carregar_foto(fotos[0]), cfg); s.run(None, {{"pixel_values": x0}})   # aquece
    depois = rss()
    ts, pico = [], depois
    for f in fotos:
        x = preparar(carregar_foto(f), cfg)
        t = time.perf_counter(); s.run(None, {{"pixel_values": x}}); ts.append((time.perf_counter() - t) * 1000)
        pico = max(pico, rss())
    ts.sort()
    out[nome] = {{"acrescenta_mb": round(depois - antes, 1), "pico_mb": round(pico, 1),
                 "p50_ms": round(ts[len(ts)//2]), "p95_ms": round(ts[int(len(ts)*0.95)-1])}}
    ses[nome] = s
out["final"] = rss()
print("JSON" + json.dumps(out))
"""


def rodar_filho(modelos, com_face, pouca, n=80):
    cod = _FILHO.format(tests=os.path.join(RAIZ, "tests"), rig=os.path.join(RAIZ, "app", "test_rig"),
                        n=n, com_face=com_face, pouca=pouca,
                        modelos="[" + ",".join(f"({nm!r}, {cm!r}, {cf})" for nm, cm, cf in modelos) + "]")
    r = subprocess.run([sys.executable, "-c", cod], capture_output=True, text=True, timeout=1800)
    linha = next((l for l in r.stdout.splitlines() if l.startswith("JSON")), None)
    if not linha:
        print(r.stdout[-1500:], r.stderr[-2500:]); raise SystemExit("processo de medicao falhou")
    return json.loads(linha[4:])


def recursos():
    for f in (MARQO_ONNX, FREEPIK_ONNX):
        print(f"{os.path.basename(f)}: {os.path.getsize(f)/1e6:.1f} MB em disco")
    M = ("marqo", MARQO_ONNX, "MARQO_CFG")
    F = ("freepik", FREEPIK_ONNX, "FREEPIK_CFG")
    for rotulo, pouca in (("padrao do onnxruntime", False), ("arena de memoria desligada", True)):
        r = rodar_filho([M, F], com_face=True, pouca=pouca)
        print(f"\n== processo com buffalo_s + Marqo + Freepik ({rotulo}), 1 nucleo, 1 thread ==")
        print(f"  python + libs:                 {r['base']:.0f} MB")
        print(f"  + buffalo_s carregado:         {r['com_buffalo_s']:.0f} MB")
        for nome in ("marqo", "freepik"):
            x = r[nome]
            print(f"  + {nome:8} acrescenta {x['acrescenta_mb']:6.1f} MB | pico do processo {x['pico_mb']:6.0f} MB"
                  f" | {x['p50_ms']} ms p50 · {x['p95_ms']} ms p95")
        print(f"  processo final:                {r['final']:.0f} MB")


FREEPIK_INT8 = os.path.join(DIR_ONNX, "freepik_eva02_base_448_int8.onnx")


def quantizar():
    """O Freepik em float32 acrescenta 363-496 MB -- demais para 1 GB. Quantizacao dinamica
    INT8 (onnxruntime.quantization, ja instalado) SO vale se decidir igual: compara com o
    ONNX float32, que ja foi provado igual ao PyTorch em 80/80."""
    import numpy as np
    from onnxruntime.quantization import quantize_dynamic, QuantType
    from experimento_moderacao import imagens
    from experimento_moderacao_permissiva import carregar_foto
    t = time.perf_counter()
    quantize_dynamic(FREEPIK_ONNX, FREEPIK_INT8, weight_type=QuantType.QInt8)
    print(f"INT8: {os.path.getsize(FREEPIK_INT8)/1e6:.1f} MB (era {os.path.getsize(FREEPIK_ONNX)/1e6:.1f}) "
          f"em {time.perf_counter()-t:.0f} s")
    s_m, s32, s8 = sessao(MARQO_ONNX, 4), sessao(FREEPIK_ONNX, 4), sessao(FREEPIK_INT8, 4)
    dif_alto = 0.0; iguais = n = 0; maior_alto = 0.0; linhas = []
    for cam in imagens():
        im = carregar_foto(cam)
        pm = softmax(s_m.run(None, {"pixel_values": preparar(im, MARQO_CFG)})[0][0])
        xf = preparar(im, FREEPIK_CFG)
        p32 = softmax(s32.run(None, {"pixel_values": xf})[0][0])
        p8 = softmax(s8.run(None, {"pixel_values": xf})[0][0])
        dif_alto = max(dif_alto, abs(float(p32[3] - p8[3])))
        maior_alto = max(maior_alto, float(p8[3]))
        i_nsfw = 0                                # Marqo: rotulos ['nsfw', 'sfw']
        d32 = pm[i_nsfw] >= PORTAO_MARQO and p32[3] >= GATILHO_ALTO
        d8 = pm[i_nsfw] >= PORTAO_MARQO and p8[3] >= GATILHO_ALTO
        iguais += (d32 == d8); n += 1
        linhas.append((os.path.basename(cam), [round(float(v), 3) for v in p32], [round(float(v), 3) for v in p8]))
    print(f"'alto' INT8 x float32, maior diferenca: {dif_alto:.3f} | maior 'alto' no INT8: {maior_alto:.3f}")
    print(f"decisao da cascata identica INT8 x float32: {iguais}/{n}")
    # nivel mais provavel: o INT8 muda a CLASSE de alguma foto (ex.: neutro -> medio)?
    troca = [(f, np.argmax(a), np.argmax(b)) for f, a, b in linhas if np.argmax(a) != np.argmax(b)]
    print(f"fotos em que o nivel mais provavel mudou: {len(troca)}/{n}", troca[:5])


def recursos_int8():
    print(f"{os.path.basename(FREEPIK_INT8)}: {os.path.getsize(FREEPIK_INT8)/1e6:.1f} MB em disco")
    r = rodar_filho([("marqo", MARQO_ONNX, "MARQO_CFG"), ("freepik_int8", FREEPIK_INT8, "FREEPIK_CFG")],
                    com_face=True, pouca=True)
    print("== buffalo_s + Marqo + Freepik INT8 (arena desligada), 1 nucleo, 1 thread ==")
    print(f"  python + libs {r['base']:.0f} MB | + buffalo_s {r['com_buffalo_s']:.0f} MB")
    for nome in ("marqo", "freepik_int8"):
        x = r[nome]
        print(f"  + {nome:12} acrescenta {x['acrescenta_mb']:6.1f} MB | pico {x['pico_mb']:5.0f} MB"
              f" | {x['p50_ms']} ms p50 · {x['p95_ms']} ms p95")
    print(f"  processo final {r['final']:.0f} MB")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    {"exportar": exportar, "paridade": paridade, "recursos": recursos,
     "quantizar": quantizar, "recursos-int8": recursos_int8}.get(modo, lambda: print(__doc__))()
