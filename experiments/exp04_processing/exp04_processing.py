"""EXP-04 — Latencia de processamento de imagem (watermark + otimizacao web).

Pipeline medido (espelha o produto, ADR-0008):
  decode -> resize (long-edge) -> watermark -> encode/otimiza JPEG

Mede por estagio, roda N iteracoes, calcula P50/P95/P99. Codigo descartavel (S0).
Uso:
  python exp04_processing.py --input data/camera_r8_synth.jpg --iters 30
"""
import argparse
import json
import math
import os
import time
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def load_font(size):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def process_once(path, long_edge, quality):
    t = {}

    t0 = time.perf_counter()
    img = Image.open(path)
    img.load()
    img = img.convert("RGB")
    t["decode_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    w, h = img.size
    scale = long_edge / max(w, h)
    if scale < 1:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    t["resize_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    fw, fh = img.size
    draw = ImageDraw.Draw(img, "RGBA")
    font = load_font(max(18, fw // 28))
    text = "FOTO NA HORA"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = int(fw * 0.02)
    x, y = fw - tw - margin, fh - th - margin * 2
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 120))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 190))
    t["watermark_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    t["encode_ms"] = (time.perf_counter() - t0) * 1000
    t["out_bytes"] = buf.getbuffer().nbytes

    t["total_ms"] = (
        t["decode_ms"] + t["resize_ms"] + t["watermark_ms"] + t["encode_ms"]
    )
    t["out_dims"] = list(img.size)
    return t


def pct(vals, p):
    s = sorted(vals)
    k = max(0, math.ceil(p / 100 * len(s)) - 1)
    return s[k]


def summarize(name, vals):
    return {
        "stage": name,
        "p50_ms": round(pct(vals, 50), 2),
        "p95_ms": round(pct(vals, 95), 2),
        "p99_ms": round(pct(vals, 99), 2),
        "min_ms": round(min(vals), 2),
        "max_ms": round(max(vals), 2),
        "mean_ms": round(sum(vals) / len(vals), 2),
    }


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(__file__)
    ap.add_argument("--input", default=os.path.join(here, "data", "camera_r8_synth.jpg"))
    ap.add_argument("--iters", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--long-edge", type=int, default=2048)
    ap.add_argument("--quality", type=int, default=82)
    args = ap.parse_args()

    src_bytes = os.path.getsize(args.input)
    with Image.open(args.input) as im:
        src_dims = list(im.size)

    for _ in range(args.warmup):
        process_once(args.input, args.long_edge, args.quality)

    runs = [process_once(args.input, args.long_edge, args.quality) for _ in range(args.iters)]

    stages = ["decode_ms", "resize_ms", "watermark_ms", "encode_ms", "total_ms"]
    summary = {s.replace("_ms", ""): summarize(s, [r[s] for r in runs]) for s in stages}

    result = {
        "experiment": "S0-EXP-04 processing (watermark + otimizacao)",
        "note": "PROXY: imagem sintetica 24MP (cameras indisponiveis). Mede latencia de processamento, nao qualidade.",
        "env": {"lab_gpu": "N/A (CPU-only)", "iters": args.iters, "warmup": args.warmup},
        "input": {"path": os.path.basename(args.input), "bytes": src_bytes, "dims": src_dims},
        "params": {"long_edge": args.long_edge, "quality": args.quality},
        "output": {
            "dims": runs[-1]["out_dims"],
            "bytes_p50": int(pct([r["out_bytes"] for r in runs], 50)),
        },
        "latency": summary,
    }

    out_dir = os.path.join(here, "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "exp04_results.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nEXP-04 | in {src_dims[0]}x{src_dims[1]} {src_bytes/1e6:.1f}MB "
          f"-> out {runs[-1]['out_dims'][0]}x{runs[-1]['out_dims'][1]} "
          f"{result['output']['bytes_p50']/1e3:.0f}KB | iters={args.iters}")
    print(f"{'stage':<12}{'p50':>9}{'p95':>9}{'p99':>9}{'mean':>9}  (ms)")
    for s in stages:
        d = summary[s.replace('_ms', '')]
        print(f"{d['stage'].replace('_ms',''):<12}{d['p50_ms']:>9}{d['p95_ms']:>9}{d['p99_ms']:>9}{d['mean_ms']:>9}")


if __name__ == "__main__":
    main()
