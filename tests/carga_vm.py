"""Fóton — teste de carga na VM de PRODUÇÃO (plano 11). Autorizado pelo dono em 2026-09-23.

    .venv-experimento/Scripts/python.exe tests/carga_vm.py [https://app.foton.app.br]

Sem sujeira: cria uma conta de teste e um EVENTO-DEMONSTRAÇÃO (ADR-0043), que se apaga
sozinho em 1 hora com tudo dentro. Só a conta vazia sobra (o admin apaga pelo painel).

O que simula: convidados com a galeria aberta (conexões de espera longa no feed, ADR-0042)
enquanto a fotógrafa manda fotos reais em degraus de simultaneidade. Cada envio leva bytes
ÚNICOS — sem isso a proteção contra duplicata responderia em ~1 ms e o número seria falso.

Para no primeiro sinal de problema: qualquer erro, ou p95 de ida-e-volta acima de 10 s.
"""
import asyncio, os, random, statistics, sys, time
import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://app.foton.app.br").rstrip("/")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "fotos-teste")
DEGRAUS = [1, 2, 4, 6]          # envios simultâneos
POR_DEGRAU = 12                 # fotos por degrau
ESPERANDO = 60                  # convidados com a galeria aberta
TETO_P95_S = 10.0


def pct(v, p):
    s = sorted(v); import math
    return s[min(len(s) - 1, max(0, math.ceil(p / 100 * len(s)) - 1))]


def fotos():
    ns = sorted(n for n in os.listdir(PASTA) if n.lower().endswith((".jpg", ".jpeg")) and not n.startswith("_"))
    return [open(os.path.join(PASTA, n), "rb").read() for n in ns]


async def espera_longa(cli, code, gid, parar, contagem):
    desde = 0
    while not parar.is_set():
        try:
            r = await cli.get(f"{BASE}/feed/espera", params={"event": code, "guest_id": gid,
                                                             "desde": desde, "max_espera": 25}, timeout=40)
            if r.status_code == 200:
                desde = r.json().get("versao", desde); contagem["ok"] += 1
            else:
                contagem["erro"] += 1; await asyncio.sleep(1)
        except Exception:
            contagem["erro"] += 1; await asyncio.sleep(1)


async def main():
    imgs = fotos()
    print(f"alvo: {BASE} · {len(imgs)} fotos reais disponíveis")
    async with httpx.AsyncClient(http2=False, timeout=60) as cli:
        h = (await cli.get(f"{BASE}/health")).json()
        print(f"versão no ar: {h.get('versao')} · motor carregado: {h.get('engine_carregado')}")
        email = f"carga-{int(time.time())}@teste.foton"
        tok = (await cli.post(f"{BASE}/signup", data={"email": email, "senha": "carga-teste-123",
                                                      "nome": "Teste de carga"})).json()["token"]
        auth = {"Authorization": f"Bearer {tok}"}
        demo = (await cli.post(f"{BASE}/evento/demo", headers=auth)).json()
        code = demo["code"]
        print(f"conta de teste: {email} · evento-demonstração {code} (some sozinho em 1 h)")

        gids = []
        for img in imgs[:12]:                       # abaixo do freio de 20 selfies por IP
            r = await cli.post(f"{BASE}/selfie", data={"event": code, "consent": "true"},
                               files={"file": ("s.jpg", img, "image/jpeg")})
            if r.status_code == 200:
                gids.append(r.json()["guest_id"])
        print(f"convidados registrados: {len(gids)}")

        parar, cont = asyncio.Event(), {"ok": 0, "erro": 0}
        esperas = [asyncio.create_task(espera_longa(cli, code, gids[i % len(gids)], parar, cont))
                   for i in range(ESPERANDO)]
        print(f"{ESPERANDO} convidados com a galeria aberta (espera longa)\n")

        print(f"{'simult.':>7} {'fotos/min':>9} {'servidor p50':>12} {'servidor p95':>12} "
              f"{'ida-volta p95':>13} {'erros':>5}")
        resultado, fila = [], list(imgs[12:]) * 4
        for n in DEGRAUS:
            lote = [fila.pop() + os.urandom(16) for _ in range(POR_DEGRAU)]   # bytes unicos
            serv, ida, erros = [], [], 0
            sem = asyncio.Semaphore(n)

            async def envia(b):
                nonlocal erros
                async with sem:
                    t0 = time.perf_counter()
                    try:
                        r = await cli.post(f"{BASE}/ingest", data={"event": code}, headers=auth,
                                           files={"file": ("f.jpg", b, "image/jpeg")}, timeout=120)
                        if r.status_code == 200 and not r.json().get("duplicada"):
                            serv.append(r.json()["latency_ms"]); ida.append(time.perf_counter() - t0)
                        else:
                            erros += 1
                    except Exception:
                        erros += 1

            t0 = time.perf_counter()
            await asyncio.gather(*(envia(b) for b in lote))
            dur = time.perf_counter() - t0
            if not serv:
                print(f"{n:>7} — nenhuma foto processada, parando"); break
            linha = (n, len(serv) / dur * 60, statistics.median(serv), pct(serv, 95), pct(ida, 95), erros)
            resultado.append(linha)
            print(f"{n:>7} {linha[1]:>9.1f} {linha[2]:>9.0f} ms {linha[3]:>9.0f} ms {linha[4]:>10.1f} s {erros:>5}")
            if erros or linha[4] > TETO_P95_S:
                print(f"\nPAROU no degrau {n}: " + ("erro" if erros else f"p95 acima de {TETO_P95_S:.0f} s"))
                break

        parar.set()
        for t in esperas: t.cancel()
        h2 = (await cli.get(f"{BASE}/health")).json()
        print(f"\nespera longa durante a carga: {cont['ok']} respostas, {cont['erro']} erros")
        print(f"/health depois: ok={h2.get('ok')} db_ok={h2.get('db_ok')} db_ms={h2.get('db_ms')}")
        print(f"evento {code} se apaga sozinho em até 1h01. Conta vazia a apagar: {email}")


if __name__ == "__main__":
    asyncio.run(main())
