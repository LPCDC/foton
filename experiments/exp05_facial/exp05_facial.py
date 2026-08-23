"""EXP-05 — Facial self-hosted (YuNet detection + SFace embedding) via OpenCV/ONNX.

Mede:
  - LATENCIA: deteccao e embedding por rosto (CPU-only; wheel do OpenCV nao tem CUDA).
  - PRECISAO: verificacao no LFW (1000 pares), acuracia no threshold do SFace e no melhor.
Codigo descartavel (S0). Sem conta, sem compilador.
"""
import json
import math
import os
import time

import cv2
import numpy as np
from sklearn.datasets import fetch_lfw_pairs

HERE = os.path.dirname(__file__)
DET = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
REC = os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx")
SFACE_COSINE_THRESHOLD = 0.363  # recomendado pelo OpenCV Zoo p/ SFace


def pct(vals, p):
    s = sorted(vals)
    k = max(0, math.ceil(p / 100 * len(s)) - 1)
    return round(s[k], 3)


def main():
    det = cv2.FaceDetectorYN_create(DET, "", (250, 250), 0.6, 0.3, 5000)
    det.setInputSize((250, 250))
    rec = cv2.FaceRecognizerSF_create(REC, "")

    print("carregando LFW (cache)...")
    data = fetch_lfw_pairs(subset="test", color=True, resize=1.0, slice_=None)
    pairs, labels = data.pairs, data.target  # (1000,2,250,250,3) float[0,1] RGB

    det_ms, emb_ms = [], []
    scores, kept_labels = [], []
    fail = 0

    def embed(img_rgb):
        bgr = np.ascontiguousarray((img_rgb * 255).astype(np.uint8)[:, :, ::-1])
        t0 = time.perf_counter()
        _, faces = det.detect(bgr)
        det_ms.append((time.perf_counter() - t0) * 1000)
        if faces is None or len(faces) == 0:
            return None
        face = faces[int(np.argmax(faces[:, -1]))]
        t0 = time.perf_counter()
        aligned = rec.alignCrop(bgr, face)
        feat = rec.feature(aligned)
        emb_ms.append((time.perf_counter() - t0) * 1000)
        return feat

    # warmup
    for i in range(3):
        embed(pairs[i, 0]); embed(pairs[i, 1])
    det_ms.clear(); emb_ms.clear()

    t_all = time.perf_counter()
    for i in range(len(pairs)):
        f1 = embed(pairs[i, 0])
        f2 = embed(pairs[i, 1])
        if f1 is None or f2 is None:
            fail += 1
            continue
        cos = rec.match(f1, f2, cv2.FaceRecognizerSF_FR_COSINE)
        scores.append(float(cos))
        kept_labels.append(int(labels[i]))
    wall = time.perf_counter() - t_all

    scores = np.array(scores)
    kept = np.array(kept_labels)
    n = len(scores)

    def acc_at(t):
        pred = (scores >= t).astype(int)
        return float((pred == kept).mean())

    acc_default = acc_at(SFACE_COSINE_THRESHOLD)
    ts = np.linspace(scores.min(), scores.max(), 200)
    accs = [acc_at(t) for t in ts]
    best_i = int(np.argmax(accs))
    best_t, best_acc = float(ts[best_i]), float(accs[best_i])

    same = scores[kept == 1]
    diff = scores[kept == 0]

    result = {
        "experiment": "S0-EXP-05 facial self-hosted (YuNet+SFace, ONNX/OpenCV)",
        "engine": "OpenCV 5.0.0 · YuNet 2023mar + SFace 2021dec · CPU-only",
        "dataset": "LFW pairs subset=test (1000 pares)",
        "coverage": {"pairs_total": len(pairs), "pairs_usados": n, "deteccao_falhou": fail},
        "precisao": {
            "acuracia_threshold_padrao_0.363": round(acc_default, 4),
            "melhor_acuracia": round(best_acc, 4),
            "melhor_threshold_cos": round(best_t, 4),
            "cos_medio_iguais": round(float(same.mean()), 4),
            "cos_medio_diferentes": round(float(diff.mean()), 4),
        },
        "latencia_ms": {
            "deteccao": {"p50": pct(det_ms, 50), "p95": pct(det_ms, 95), "p99": pct(det_ms, 99), "mean": round(sum(det_ms)/len(det_ms), 2)},
            "embedding": {"p50": pct(emb_ms, 50), "p95": pct(emb_ms, 95), "p99": pct(emb_ms, 99), "mean": round(sum(emb_ms)/len(emb_ms), 2)},
        },
        "throughput_rostos_por_s_1thread": round(len(det_ms) / wall, 1),
        "nota": "CPU-only (wheel OpenCV sem CUDA). GPU exigiria onnxruntime-gpu ou OpenCV com CUDA — pendente.",
    }

    out = os.path.join(HERE, "results")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "exp05_results.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    p = result["precisao"]; l = result["latencia_ms"]
    print(f"\nEXP-05 | LFW {n}/{len(pairs)} pares usados (det falhou {fail}) | CPU-only")
    print(f"  PRECISAO  acc@0.363={p['acuracia_threshold_padrao_0.363']*100:.1f}%  "
          f"melhor={p['melhor_acuracia']*100:.1f}% @cos={p['melhor_threshold_cos']}  "
          f"(cos iguais={p['cos_medio_iguais']} / dif={p['cos_medio_diferentes']})")
    print(f"  LATENCIA  deteccao P50={l['deteccao']['p50']} P95={l['deteccao']['p95']} ms | "
          f"embedding P50={l['embedding']['p50']} P95={l['embedding']['p95']} ms")
    print(f"  THROUGHPUT {result['throughput_rostos_por_s_1thread']} rostos/s (1 thread)")


if __name__ == "__main__":
    main()
