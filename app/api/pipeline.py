"""Pipeline de imagem — watermark + otimizacao + facial + embedding.

Reune o que os experimentos do S0 provaram, agora como codigo de produto:
  - watermark + resize + encode  -> EXP-04 (P95 ~533ms)
  - deteccao YuNet + embedding SFace -> EXP-05 (97,2% LFW, ~6ms/rosto)
  - match cosseno brute-force     -> EXP-06 (<1ms ate 100k)

CPU-only (ADR-0009). Sem GPU. Modelos ONNX em app/api/models/.
"""
import io
import os
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
DET_PATH = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
REC_PATH = os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx")
LONG_EDGE = 2048
JPEG_Q = 82
MATCH_THRESHOLD = 0.363  # SFace (EXP-05)

# Carregados 1x no processo (o modelo de 37MB nao pode recarregar por foto)
_det = None
_rec = None


def _models():
    global _det, _rec
    if _det is None:
        _det = cv2.FaceDetectorYN_create(DET_PATH, "", (320, 320), 0.6, 0.3, 5000)
        _rec = cv2.FaceRecognizerSF_create(REC_PATH, "")
    return _det, _rec


def _load_font(size):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def process_image(raw: bytes, watermark_text="FOTO NA HORA"):
    """Decodifica -> resize -> watermark -> encode JPEG otimizado. Retorna (bytes, dims, ms)."""
    t0 = time.perf_counter()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    scale = LONG_EDGE / max(w, h)
    if scale < 1:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    fw, fh = img.size
    draw = ImageDraw.Draw(img, "RGBA")
    font = _load_font(max(18, fw // 28))
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = int(fw * 0.02)
    x, y = fw - tw - margin, fh - th - margin * 2
    draw.text((x + 2, y + 2), watermark_text, font=font, fill=(0, 0, 0, 120))
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 190))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    ms = (time.perf_counter() - t0) * 1000
    return out.getvalue(), (fw, fh), ms


def detect_and_embed(raw: bytes):
    """Detecta rostos e devolve lista de embeddings 128-d (float32 normalizados)."""
    det, rec = _models()
    arr = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return []
    H, W = bgr.shape[:2]
    det.setInputSize((W, H))
    _, faces = det.detect(bgr)
    out = []
    if faces is None:
        return out
    for f in faces:
        aligned = rec.alignCrop(bgr, f)
        feat = rec.feature(aligned).flatten().astype(np.float32)
        feat /= (np.linalg.norm(feat) + 1e-9)
        out.append({"embedding": feat, "bbox": [float(v) for v in f[:4]]})
    return out


def match_selfie(selfie_emb: np.ndarray, gallery: np.ndarray, ids: list, threshold=MATCH_THRESHOLD):
    """Casa a selfie contra a galeria de embeddings (EXP-06). gallery: (N,128) normalizada.

    Retorna [(id, score)] acima do limiar, ordenado por score desc.
    """
    if len(gallery) == 0:
        return []
    sims = gallery @ selfie_emb  # cosseno (vetores normalizados)
    hits = np.where(sims >= threshold)[0]
    res = sorted(((ids[i], float(sims[i])) for i in hits), key=lambda x: -x[1])
    return res
