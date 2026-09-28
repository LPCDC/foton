"""Ensaio simulado do P2: o relatório responde certo com dados no formato do ensaio de mesa?

    python tests/ensaio_simulado_p2.py            # roda os cenários e compara com a verdade
    python tests/ensaio_simulado_p2.py --salvar   # grava também os exports na pasta temporária (foton-p2sim)

NÃO mede o produto. Não passa por servidor, câmera nem celular: monta o export que o painel
exportaria num ensaio de mesa, com a verdade de cada disparo guardada, e confere o que
`tests/relatorio_evento.py` conclui. O P1 já validou a instrumentação contra o app real
(docs/BENCHMARKS.md); aqui a pergunta é outra: com o jeito do P2 (lotes pelo Compartilhar,
convidado com a tela apagada, foto perdida no fim, nome de arquivo e data do arquivo que o
Android pode não passar), o relatório erra sem avisar?

A verdade do cenário (determinística, sem sorteio):
  câmera 12,4 s adiantada; celular da fotógrafa 0,8 s atrasado em relação ao servidor;
  foto do relógio IMG_0201; 20 fotos do evento IMG_0202 a IMG_0221;
  IMG_0209 perdida no meio e IMG_0221 perdida no fim (nunca chegaram ao celular);
  3 lotes pelo Compartilhar; IMG_0212 e IMG_0213 compartilhadas de novo no lote 3;
  c1 a c3 com a galeria aberta; c4 com a tela apagada; c5 fez a selfie no fim.

Variantes da data do arquivo (T1), porque é UNKNOWN o que o Android passa:
  honesto     a hora em que a foto chegou ao celular (o que o T1 promete)
  carimbo     a hora do toque em Compartilhar, igual para o lote inteiro
  agora       nenhuma data: o app usa a hora em que remontou o arquivo
  exif        o Android copia o relógio da câmera (EXIF) para a data do arquivo
e uma variante do nome do arquivo:
  sem_nome    o Compartilhar entrega "1000012345.jpg" em vez de IMG_0201.JPG (sem seq)
"""
import json, os, sys, tempfile
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
import relatorio_evento as R

SP = timezone(timedelta(hours=-3))
DESVIO_CAM = 12.4          # câmera adiantada: EXIF = real + 12,4 s
CEL_MS = 800.0             # servidor - celular da fotógrafa, em ms
BOOT = 4.0                 # do toque em Compartilhar até o app começar o lote (proxy, UNKNOWN real)


def ep(h, m, s):
    return datetime(2026, 9, 28, h, m, 0, tzinfo=SP).timestamp() + s


def exif(t_real):
    d = datetime.fromtimestamp(t_real + DESVIO_CAM, SP)
    return d.strftime("%Y:%m:%d %H:%M:%S.") + f"{int(round(d.microsecond / 1e4)):02d}"


def cenario(t1_modo="honesto", sem_nome=False):
    """Devolve (export, verdade). Tempos do celular vão no relógio do celular, como no app."""
    # disparos reais: relógio, rajada de 5, 7 espaçadas, rajada de 5, 3 espaçadas
    disparos = {201: ep(20, 0, 5.3)}
    for i, s in enumerate(range(202, 207)): disparos[s] = ep(20, 1, 0) + 0.25 * i
    for i, s in enumerate(range(207, 214)): disparos[s] = ep(20, 1, 30) + 20.0 * i
    for i, s in enumerate(range(214, 219)): disparos[s] = ep(20, 4, 0) + 0.3 * i
    for i, s in enumerate(range(219, 222)): disparos[s] = ep(20, 5, 0) + 25.0 * i
    perdidas = {209, 221}
    # Camera Connect: uma de cada vez, 3,0 a 4,4 s cada (padrão fixo)
    chegada, livre = {}, 0.0
    for s in sorted(disparos):
        if s in perdidas: continue
        chegada[s] = max(livre, disparos[s]) + 3.0 + (s % 5) * 0.35
        livre = chegada[s]
    toques = [(ep(20, 2, 30), [s for s in chegada if chegada[s] < ep(20, 2, 30)]),
              (ep(20, 4, 20), [s for s in chegada if ep(20, 2, 30) <= chegada[s] < ep(20, 4, 20)]),
              (ep(20, 6, 30), [s for s in chegada if chegada[s] >= ep(20, 4, 20)] + [212, 213])]
    rostos = {s: ([] if s in (201, 216) else ["c1", "c2", "c3", "c4", "c5"][: 1 + s % 3] + (["c4", "c5"] if s % 4 == 0 else []))
              for s in disparos}
    selfie = {"c1": ep(20, 0, 40), "c2": ep(20, 0, 55), "c3": ep(20, 1, 10), "c4": ep(20, 1, 20), "c5": ep(20, 8, 0)}
    cel = lambda t_srv: t_srv - CEL_MS / 1000        # hora do servidor -> relógio do celular
    fotos, verdade, vistas = {}, {}, set()
    for toque, lote in toques:
        t_app = toque + BOOT
        cursor = t_app + 0.3
        for k, s in enumerate(lote):
            if s in vistas:                             # reenvio: o servidor só conta duplicata
                fotos[s]["duplicatas"] += 1; continue
            vistas.add(s)
            t2 = cursor; t3 = t2 + 0.9 + (s % 3) * 0.3; t4 = t3 + 0.25
            cursor = t4 + 0.1
            t1 = {"honesto": chegada[s], "carimbo": toque, "agora": t_app - 0.05,
                  "exif": disparos[s] + DESVIO_CAM}[t1_modo]
            quem = sorted(set(rostos[s]))
            telas = []
            for c in quem:
                if c == "c4": continue                                     # tela apagada
                if selfie[c] > t4:
                    telas.append({"c": c, "t5_tela": selfie[c] + 2.0 - 0.1, "relogio_ms": 100.0, "rtt_ms": 80.0, "origem": "selfie"})
                else:
                    telas.append({"c": c, "t5_tela": t4 + 0.6 + (s % 4) * 0.2 - 0.1, "relogio_ms": 100.0, "rtt_ms": 80.0, "origem": "ao_vivo"})
            fotos[s] = {
                "photo_id": f"p{s}", "n_faces": len(quem), "instrumentada": True,
                "t0_exif": exif(disparos[s]), "t0_fonte": "aparelho", "camera": "Canon EOS R8",
                "seq": None if sem_nome else s,
                "t1_arquivo": round(cel(t1), 3), "t_app": round(cel(t_app) + k * 0.02, 3), "t2_envio": round(cel(t2), 3),
                "tentativa": 1, "via": "compartilhar", "relogio_ms": CEL_MS, "rtt_ms": 120.0,
                "t3_recebida": t3, "t4_pronta": t4, "duplicatas": 0,
                "entregas": len(quem), "recusas": 1 if s == 214 else 0, "telas": telas}
            verdade[s] = {"t0": disparos[s], "t1": chegada[s], "t5_primeira": min((t["t5_tela"] + 0.1 for t in telas if t["origem"] == "ao_vivo"), default=None)}
    export = {"evento": "P2SIM", "criado": ep(19, 58, 0), "aberturas": 6,
              "convidados": [{"c": c, "t_selfie": t} for c, t in selfie.items()],
              "fotos": [fotos[s] for s in sorted(fotos)]}
    ao_vivo = [verdade[s]["t5_primeira"] - verdade[s]["t0"] for s in verdade if s != 201 and verdade[s]["t5_primeira"]]
    todos_ao_vivo = []
    for f in export["fotos"]:
        s = int(f["photo_id"][1:])
        if s == 201: continue
        todos_ao_vivo += [t["t5_tela"] + 0.1 - disparos[s] for t in f["telas"] if t["origem"] == "ao_vivo"]
    return export, {"disparos": disparos, "perdidas": perdidas, "chegada": chegada, "lotes": len(toques),
                    "p95_c4": R.pct(todos_ao_vivo, 95), "n_c4": len(todos_ao_vivo), "ao_vivo_primeira": ao_vivo}


def roda(nome, t1_modo, sem_nome=False, salvar=None):
    export, V = cenario(t1_modo, sem_nome)
    if salvar:
        os.makedirs(salvar, exist_ok=True)
        json.dump(export, open(os.path.join(salvar, f"medidas-{nome}.json"), "w", encoding="utf-8"), indent=1)
    leitura = datetime.fromtimestamp(V["disparos"][201], SP)
    lido = leitura.strftime("%H:%M:%S.") + str(leitura.microsecond // 100000)
    # o que a folha de campo anota: o número do arquivo do relógio e o primeiro e último arquivo
    leit = R.chaves_relogio(export, {"IMG_0201": lido})
    desv = R.calibra(export, leit)
    linhas = R.cadeia(export, desv, set(leit))
    S = R.resumo(export, linhas, (201, 221))
    erros_t0 = [l["t0"] - V["disparos"][int(l["photo_id"][1:])] for l in linhas if l["t0"] is not None]
    erros_cc = [l["trechos"]["camera_celular"] - (V["chegada"][int(l["photo_id"][1:])] - V["disparos"][int(l["photo_id"][1:])])
                for l in linhas if l["trechos"]["camera_celular"] is not None]
    t1_bom = t1_modo == "honesto"
    susp = S["t1_suspeito"]
    print(f"\n=== {nome} (T1 {t1_modo}{', sem nome de arquivo' if sem_nome else ''}) ===")
    print(f"  desvio da câmera achado: {desv.get('Canon EOS R8', float('nan')):+.2f} s (verdade +{DESVIO_CAM})")
    print(f"  erro do T0 calibrado: {min(erros_t0):+.2f} a {max(erros_t0):+.2f} s" if erros_t0 else "  T0: nenhum")
    print(f"  câmera → celular, erro contra a verdade: {min(erros_cc):+.1f} a {max(erros_cc):+.1f} s" if erros_cc else "  câmera → celular: sem número")
    print(f"  T1 suspeito: {susp} de {S['fotos']} · devia ser {'0' if t1_bom else S['fotos']}")
    print(f"  perdas prováveis: {S['perdas_provaveis']} · verdade {len(V['perdidas'])} (IMG_0209 no meio, IMG_0221 no fim)")
    print(f"  critério #4: p95 {S['criterio4']['p95'] and round(S['criterio4']['p95'], 1)} s em {S['criterio4']['n']} · verdade {round(V['p95_c4'], 1)} s em {V['n_c4']}"
          f" · não observadas {S['criterio4']['nao_observadas']}")
    print(f"  lotes no relatório: {len(S['lotes'])} ({', '.join(str(x['n']) for x in S['lotes'])} fotos) · verdade {V['lotes']}")
    return {"t1_enganado": (not t1_bom) and susp < S["fotos"], "perdas_certas": S["perdas_provaveis"] == len(V["perdidas"]) or (sem_nome and S["perdas_provaveis"] is None),
            "c4_certo": (S["criterio4"]["p95"] is not None and abs(S["criterio4"]["p95"] - V["p95_c4"]) < 0.3)
                or (sem_nome and S["criterio4"]["t0_calibrado"] is False)}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    salvar = os.path.join(tempfile.gettempdir(), "foton-p2sim") if "--salvar" in sys.argv else None
    res = {n: roda(n, m, sn, salvar) for n, m, sn in [("honesto", "honesto", False), ("carimbo", "carimbo", False),
                                                     ("agora", "agora", False), ("exif", "exif", False),
                                                     ("sem_nome", "honesto", True)]}
    print("\n=== o que o relatório erraria sem avisar ===")
    for n, r in res.items():
        print(f"  {n:9s} T1 aceito sem ser: {'SIM' if r['t1_enganado'] else 'não'} · perdas certas ou UNKNOWN declarado: {'sim' if r['perdas_certas'] else 'NÃO'}"
              f" · critério #4 certo ou sem calibração declarada: {'sim' if r['c4_certo'] else 'NÃO'}")
