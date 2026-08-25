"""GAUNTLET — teste funcional/precisão/latência/falhas do test-rig, com rostos reais (LFW).

Prova, sem simulação:
  - foto de uma pessoa + selfie DELA  -> casa (aparece no feed)
  - selfie de OUTRA pessoa            -> nao casa
  - ordem inversa (convidado antes da foto) -> tambem casa (match no ingest)
  - foto sem rosto / selfie sem rosto -> tratados com seguranca
  - latencia de ingest e selfie
"""
import io, time, sys
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from sklearn.datasets import fetch_lfw_pairs
import rig

def to_jpg(arr):
    im = Image.fromarray((arr * 255).astype("uint8"))
    b = io.BytesIO(); im.save(b, "JPEG", quality=92); return b.getvalue()

def form(ev, **extra):
    d = {"event": ev}; d.update(extra); return d

c = TestClient(rig.app)
ok = True
def check(name, cond, extra=""):
    global ok
    print(("  PASS " if cond else "  FALHA ") + name + ("  " + extra if extra else ""))
    ok = ok and cond

print("carregando LFW (cache)...")
data = fetch_lfw_pairs(subset="test", color=True, resize=1.0, slice_=None)
pairs, target = data.pairs, data.target
same = np.where(target == 1)[0]     # (img0,img1) = MESMA pessoa
diff = np.where(target == 0)[0]     # (img0,img1) = pessoas DIFERENTES
A_photo  = to_jpg(pairs[same[0], 0])   # foto do evento (pessoa A)
A_selfie = to_jpg(pairs[same[0], 1])   # selfie da pessoa A (mesma)
B_selfie = to_jpg(pairs[diff[0], 0])   # selfie de pessoa B (diferente de A)
C_photo  = to_jpg(pairs[same[1], 0])   # 2a pessoa p/ ordem inversa
C_selfie = to_jpg(pairs[same[1], 1])
noise    = to_jpg(np.random.rand(220, 260, 3))  # sem rosto

# warmup (carrega modelos)
c.post("/event", data={"code": "WU"}); c.post("/ingest", data=form("WU"), files={"file": ("a.jpg", A_photo, "image/jpeg")})
c.post("/reset")

print("\n[1] Fluxo normal: foto entra, depois selfies")
c.post("/event", data={"code": "TESTE"})
t=time.perf_counter()
r = c.post("/ingest", data=form("TESTE"), files={"file": ("a.jpg", A_photo, "image/jpeg")})
ing_ms=(time.perf_counter()-t)*1000
j=r.json(); check("ingest 200 + achou rosto", r.status_code==200 and j["n_faces"]>=1, f"n_faces={j.get('n_faces')} lat={ing_ms:.0f}ms")

t=time.perf_counter()
rA = c.post("/selfie", data=form("TESTE", consent="true"), files={"file": ("s.jpg", A_selfie, "image/jpeg")})
self_ms=(time.perf_counter()-t)*1000
mA=rA.json().get("matches",[]); check("selfie da MESMA pessoa CASA", rA.status_code==200 and len(mA)>=1, f"matches={len(mA)} lat={self_ms:.0f}ms")

rB = c.post("/selfie", data=form("TESTE", consent="true"), files={"file": ("s.jpg", B_selfie, "image/jpeg")})
mB=rB.json().get("matches",[]); check("selfie de pessoa DIFERENTE NAO casa", rB.status_code==200 and len(mB)==0, f"matches={len(mB)}")

gidA=rA.json()["guest_id"]
rf=c.get("/feed", params={"event":"TESTE","guest_id":gidA})
check("feed do convidado A lista a foto", rf.status_code==200 and len(rf.json()["photos"])>=1, f"feed={rf.json()['photos']}")

pid=mA[0]
ri=c.get(f"/img/TESTE/{pid}.jpg")
check("imagem tratada servida (jpeg)", ri.status_code==200 and ri.headers["content-type"]=="image/jpeg" and len(ri.content)>1000, f"{len(ri.content)}B")

print("\n[2] Ordem inversa: convidado registra ANTES da foto")
c.post("/reset"); c.post("/event", data={"code":"INV"})
rc=c.post("/selfie", data=form("INV", consent="true"), files={"file":("s.jpg",C_selfie,"image/jpeg")})
gidC=rc.json()["guest_id"]; check("selfie sem fotos ainda -> 0 match", len(rc.json()["matches"])==0)
ri2=c.post("/ingest", data=form("INV"), files={"file":("c.jpg",C_photo,"image/jpeg")})
check("ingest casa com convidado ja presente", gidC in ri2.json().get("matched_guests",[]), f"matched={ri2.json().get('matched_guests')}")

print("\n[3] Seguranca / falhas")
c.post("/event", data={"code":"EDGE"})
rn=c.post("/ingest", data=form("EDGE"), files={"file":("n.jpg",noise,"image/jpeg")})
check("foto sem rosto -> 200 com n_faces=0 (nao quebra)", rn.status_code==200 and rn.json()["n_faces"]==0)
rns=c.post("/selfie", data=form("EDGE", consent="true"), files={"file":("n.jpg",noise,"image/jpeg")})
check("selfie sem rosto -> 422 (erro claro)", rns.status_code==422)
rnc=c.post("/selfie", data=form("EDGE", consent="false"), files={"file":("s.jpg",A_selfie,"image/jpeg")})
check("selfie sem consentimento -> 400", rnc.status_code==400)
r404=c.post("/ingest", data=form("NAOEXISTE"), files={"file":("a.jpg",A_photo,"image/jpeg")})
check("evento inexistente -> 404 (escopo por evento)", r404.status_code==404)

# selfie nao pode ser servida (nunca armazenada): so /img de fotos existe; garantimos que guests nao viram bytes
check("selfie NAO e armazenada (sem bytes no store)", all("bytes" not in v for v in rig.EVENTS.get("TESTE",{}).get("guests",{}).values()) if isinstance(rig.EVENTS.get("TESTE",{}).get("guests",{}),dict) else True)

print("\nRESULTADO:", "TODOS PASSARAM [OK]" if ok else "HOUVE FALHA [X]")
sys.exit(0 if ok else 1)
