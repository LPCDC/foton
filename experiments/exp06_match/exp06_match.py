"""EXP-06 — Selfie -> match (busca vetorial por cosseno), CPU/numpy.

Simula o caminho do convidado: dado o embedding da selfie, achar correspondencias
numa galeria de N embeddings (rostos das fotos do evento). Brute-force cosine +
top-k. Mede latencia por tamanho de galeria. Embeddings sao 128-d (dim do SFace).
Latencia independe do conteudo -> vetores aleatorios normalizados sao proxy valido.
"""
import json
import math
import os
import time

import numpy as np

HERE = os.path.dirname(__file__)
DIM = 128
SIZES = [1_000, 10_000, 100_000]
ITERS = 200
THRESH = 0.363  # mesmo threshold do SFace


def pct(vals, p):
    s = sorted(vals)
    k = max(0, math.ceil(p / 100 * len(s)) - 1)
    return round(s[k], 3)


def norm(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


def main():
    rng = np.random.default_rng(42)
    out = {"experiment": "S0-EXP-06 selfie->match (cosine brute-force, CPU)",
           "dim": DIM, "iters": ITERS, "threshold_cos": THRESH, "por_galeria": []}

    for n in SIZES:
        gallery = norm(rng.standard_normal((n, DIM)).astype(np.float32))
        lat = []
        hits_last = 0
        for _ in range(ITERS):
            q = norm(rng.standard_normal(DIM).astype(np.float32))
            t0 = time.perf_counter()
            sims = gallery @ q                    # (n,) cosine (vetores normalizados)
            matches = np.where(sims >= THRESH)[0]  # todas acima do limiar
            topk = np.argpartition(-sims, min(20, n - 1))[:20]  # top-20
            _ = topk
            lat.append((time.perf_counter() - t0) * 1000)
            hits_last = int(len(matches))
        row = {"galeria": n, "p50_ms": pct(lat, 50), "p95_ms": pct(lat, 95),
               "p99_ms": pct(lat, 99), "mean_ms": round(sum(lat) / len(lat), 3),
               "mem_galeria_mb": round(gallery.nbytes / 1e6, 1)}
        out["por_galeria"].append(row)
        print(f"  galeria {n:>7}: match P50={row['p50_ms']:.3f} P95={row['p95_ms']:.3f} "
              f"P99={row['p99_ms']:.3f} ms | mem {row['mem_galeria_mb']}MB")

    d = os.path.join(HERE, "results")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "exp06_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\nnota: brute-force cosseno; para milhoes de vetores usar indice (FAISS/hnsw) — nao necessario nesta escala.")


if __name__ == "__main__":
    main()
