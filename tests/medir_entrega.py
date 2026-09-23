"""Fóton — mede RECEBIDA → ENTREGUE (plano 6′ da lista de 2026-09-22).

    python tests/medir_entrega.py            # 20 fotos, 3 convidados
    python tests/medir_entrega.py 40 5       # 40 fotos, 5 convidados

O que isto mede: o tempo que o Fóton leva **de a foto chegar ao servidor até ela estar
entregue no feed do convidado** — detecção, embedding, comparação com cada convidado,
gravação e leitura do feed. Roda o pipeline de verdade (buffalo_s), com as fotos reais
de `fotos-teste/`, contra um banco temporário. Nada sai da máquina e nada toca produção.

O que isto NÃO mede, e não pode:
  1. **o clique → servidor** (a câmera e o 4G do salão). Decisão do dono em 2026-09-22:
     não haverá teste de campo, então esse trecho segue `UNKNOWN` para sempre;
  2. **a VM.** Aqui é o PC do dono. A VM tem 1/8 de OCPU e vai ser mais lenta — quanto,
     é `UNKNOWN` até rodar lá;
  3. **o download da imagem** no celular do convidado.

E há um tempo fixo que não é processamento e conta na percepção: o app do convidado
pergunta ao servidor a cada **2,5 s** (`startPolling`, app/web/index.html). Então o que a
pessoa sente é o processamento **mais** até 2,5 s de espera pela próxima pergunta.
"""
import io, json, os, statistics, sys, tempfile, time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "fotos-teste")
sys.path.insert(0, os.path.join(RAIZ, "app", "test_rig"))
os.environ["FOTON_DB"] = os.path.join(tempfile.mkdtemp(), "medicao.db")

from fastapi.testclient import TestClient          # noqa: E402
import rig                                          # noqa: E402

C = TestClient(rig.app)
POLL_MS = 2500        # de app/web/index.html: startPolling()


def fotos(limite):
    nomes = sorted(n for n in os.listdir(PASTA)
                   if n.lower().endswith((".jpg", ".jpeg", ".png")) and not n.startswith("_"))
    return [os.path.join(PASTA, n) for n in nomes][:limite]


def pct(v, p):
    """Percentil por posição (nearest-rank), nunca interpolando além do dado.

    `statistics.quantiles` extrapola em amostra pequena e chegou a devolver p95 MAIOR
    que o máximo observado (229 ms contra 208 ms, n=12) — um número que não existe.
    """
    s = sorted(v)
    import math
    return s[min(len(s) - 1, max(0, math.ceil(p / 100 * len(s)) - 1))]


def main(n_fotos=20, n_convidados=3):
    if not os.path.isdir(PASTA):
        print("fotos-teste/ não existe — esta medição precisa de fotos reais."); return 2
    arquivos = fotos(n_fotos + n_convidados)
    if len(arquivos) < n_convidados + 2:
        print(f"poucas fotos em fotos-teste/ ({len(arquivos)})"); return 2

    tok = C.post("/signup", data={"email": "medicao@local", "senha": "medicao123",
                                  "nome": "Medição"}).json()["token"]
    hdr = {"Authorization": f"Bearer {tok}"}
    C.post("/event", data={"code": "MEDE", "brand": "Medição"}, headers=hdr)

    print(f"modelo: {rig.MODELO} · limiar: {rig.THRESH} · fotos: {len(arquivos)}")
    print("carregando o modelo (primeira detecção paga o carregamento)…")

    # Convidados: cada um entra com uma foto real como selfie.
    guests, usados = [], []
    for caminho in arquivos:
        if len(guests) >= n_convidados:
            break
        with open(caminho, "rb") as f:
            r = C.post("/selfie", data={"event": "MEDE", "consent": "true"},
                       files={"file": (os.path.basename(caminho), f.read(), "image/jpeg")})
        if r.status_code == 200:
            guests.append(r.json()["guest_id"]); usados.append(caminho)
            rig._selfies_por_ip.clear()          # o freio (ADR-0041) não é o objeto da medição
    if not guests:
        print("nenhuma selfie deu rosto — sem convidados, não há entrega para medir."); return 1
    print(f"convidados registrados: {len(guests)}")

    servidor, total, entregues, rostos, tamanhos = [], [], 0, [], []
    for caminho in arquivos:
        if caminho in usados:
            continue
        raw = open(caminho, "rb").read()
        t0 = time.perf_counter()
        r = C.post("/ingest", data={"event": "MEDE"}, headers=hdr,
                   files={"file": (os.path.basename(caminho), raw, "image/jpeg")})
        if r.status_code != 200:
            print(f"  {os.path.basename(caminho)}: {r.status_code} {r.text[:60]}"); continue
        j = r.json()
        # feed logo em seguida: é o que o celular do convidado faz na próxima pergunta
        for gid in guests:
            C.get("/feed", params={"event": "MEDE", "guest_id": gid})
        t_total = (time.perf_counter() - t0) * 1000
        servidor.append(j["latency_ms"]); total.append(t_total)
        rostos.append(j.get("n_faces", 0)); tamanhos.append(len(raw) / 1024 / 1024)
        entregues += len(j.get("matched_guests", []))

    if not servidor:
        print("nenhuma foto processada."); return 1

    print("\n--- RECEBIDA → ENTREGUE (nesta máquina, não na VM) ---")
    for nome, v in (("processamento no servidor", servidor), ("recebida → visível no feed", total)):
        print(f"{nome:30} p50 {statistics.median(v):7.0f} ms   p95 {pct(v, 95):7.0f} ms   "
              f"máx {max(v):7.0f} ms   n={len(v)}")
    print(f"{'espera pela próxima pergunta':30} fixo   0–{POLL_MS} ms (o app pergunta a cada {POLL_MS} ms)")
    print(f"\nfotos: {len(servidor)} · rostos por foto: {statistics.median(rostos):.0f} (mediana), "
          f"máx {max(rostos)} · tamanho: {statistics.median(tamanhos):.1f} MB (mediana), "
          f"máx {max(tamanhos):.1f} MB")
    print(f"entregas geradas: {entregues} · convidados: {len(guests)}")
    print(f"\nPior caso sentido pelo convidado, nesta máquina: "
          f"{pct(total, 95) + POLL_MS:.0f} ms (p95 + a espera pela pergunta).")
    print("Na VM (1/8 de OCPU) este número é UNKNOWN. O clique → servidor não entra aqui.")
    return 0


if __name__ == "__main__":
    a = [int(x) for x in sys.argv[1:3]] or [20, 3]
    sys.exit(main(*(a + [3])[:2]))
