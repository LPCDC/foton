"""Foto na Hora — worker do pipeline (FastAPI).

Dois caminhos:
  POST /ingest        -> chega uma foto da camera (ou do painel). Trata, detecta rostos,
                         sobe pro R2, registra no banco, casa com convidados ja presentes,
                         e o Supabase Realtime empurra pro feed. (SLA: shutter->celular P95<10s)
  POST /guest/selfie  -> chega a selfie do convidado. Vira embedding (efemero, ADR-0005),
                         casa contra os rostos do evento e devolve as fotos dele.

Observabilidade (§6 CLAUDE.md): cada foto carrega photo_id e latency_ms por estagio.
Este arquivo e o esqueleto de integracao: o storage (R2) e o banco (Supabase) entram
pelos clientes em storage.py/db.py — aqui deixamos os pontos de conexao explicitos.
"""
import time
import uuid

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

import pipeline

app = FastAPI(title="Foto na Hora — pipeline", version="0.1.0")


@app.get("/health")
def health():
    return {"ok": True, "engine": "YuNet+SFace CPU", "ts": time.time()}


@app.post("/ingest")
async def ingest(event_id: str = Form(...), file: UploadFile = File(...),
                 taken_at: float = Form(None)):
    """Recebe 1 foto -> trata -> facial -> R2 -> banco -> match -> feed ao vivo."""
    raw = await file.read()
    photo_id = str(uuid.uuid4())
    t_shutter = taken_at or time.time()

    # 1) tratamento (EXP-04)
    treated, dims, proc_ms = pipeline.process_image(raw)

    # 2) facial (EXP-05)
    faces = pipeline.detect_and_embed(treated)

    # 3) storage no R2 (ADR-0011) — TODO storage.put(key, treated) -> cdn_url
    r2_key = f"events/{event_id}/{photo_id}.jpg"
    cdn_url = f"{_R2_BASE}/{r2_key}"  # placeholder ate storage.py
    # storage.put(r2_key, treated, content_type="image/jpeg")

    latency_ms = int((time.time() - t_shutter) * 1000)

    # 4) banco: photo + faces (ADR-0010) — TODO db.insert_photo(...) / db.insert_faces(...)
    # db.insert_photo(photo_id, event_id, r2_key, cdn_url, t_shutter, latency_ms, len(faces))
    # db.insert_faces(photo_id, event_id, faces)

    # 5) match com convidados ja presentes -> Realtime empurra pro feed pessoal
    # for guest in db.guests_of(event_id):
    #     for f in faces:
    #         if float(guest.emb @ f["embedding"]) >= pipeline.MATCH_THRESHOLD:
    #             db.insert_match(guest.id, photo_id, ...)  # -> feed ao vivo

    return {
        "photo_id": photo_id, "cdn_url": cdn_url, "dims": dims,
        "n_faces": len(faces), "processing_ms": round(proc_ms, 1),
        "latency_ms": latency_ms,
    }


@app.post("/guest/selfie")
async def guest_selfie(event_id: str = Form(...), file: UploadFile = File(...),
                       consent: bool = Form(...)):
    """Selfie do convidado -> embedding efemero -> match -> fotos dele."""
    if not consent:
        raise HTTPException(400, "Consentimento obrigatorio (LGPD, ADR-0005).")
    raw = await file.read()
    faces = pipeline.detect_and_embed(raw)
    if not faces:
        raise HTTPException(422, "Nenhum rosto detectado na selfie. Tente novamente.")
    selfie_emb = faces[0]["embedding"]  # rosto principal

    # carrega os rostos do evento (banco) e casa (EXP-06)
    # rows = db.faces_of(event_id)  -> gallery (N,128), photo_ids
    gallery = np.zeros((0, 128), np.float32)  # placeholder ate db.py
    photo_ids: list[str] = []
    hits = pipeline.match_selfie(selfie_emb, gallery, photo_ids)

    # registra o convidado (embedding efemero) e os matches
    guest_id = str(uuid.uuid4())
    # db.insert_guest(guest_id, event_id, selfie_emb)
    # db.insert_matches(guest_id, [(pid, sc) for pid, sc in hits])

    return {
        "guest_id": guest_id, "event_id": event_id,
        "matches": [{"photo_id": pid, "score": round(sc, 3)} for pid, sc in hits],
        "note": "esqueleto: conecte db.py/storage.py para dados reais",
    }


# placeholder — vem de env no deploy real (nunca commitar segredo, §7 CLAUDE.md)
import os
_R2_BASE = os.environ.get("R2_PUBLIC_BASE", "https://cdn.example.r2.dev")
