"""Relatório da cadeia por trecho de um evento (ADR-0046).

    python tests/relatorio_evento.py foton-medidas-XXXX.json --relogio FOTO_ID=14:00:37.5

O JSON sai do painel do evento ("Exportar medidas"). `--relogio` diz, para a foto do
relógio de calibração, que hora a TELA mostrava na foto (lida por quem roda o relatório).
Com isso, o desvio do relógio de cada câmera sai da conta; sem isso, T0 fica como proxy
sem calibração.

O que cada horário é, e o relatório escreve isso ao lado de cada número:
  T0  disparo: EXIF da câmera. PROXY, nunca verdade; corrigido pela foto do relógio.
  T1  foto no celular: data do arquivo. PROXY; se igual à hora do envio, SUSPEITO
      (o navegador não sabia a data e usou a hora da escolha).
  T2  envio começa: relógio do celular, levado ao do servidor por /agora.
  T3  Fóton recebe, T4 pronta: relógio do servidor. MEDIDO.
  T5  apareceu na tela do convidado: relógio do celular dele, levado ao do servidor.
      Sem aviso do aparelho, NÃO OBSERVADO (a decisão de entrega do servidor não é T5).
"""
import json, math, re, sys
from datetime import datetime, timedelta, timezone

SP = timezone(timedelta(hours=-3))   # America/Sao_Paulo: sem horário de verão desde 2019

_RE_EXIF = re.compile(r"^(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})(\.\d+)?([+-]\d{2}:\d{2})?$")
_RE_LEITURA = re.compile(r"^(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)$")

TRECHOS = [("camera_celular", "câmera → celular (T1 - T0)"),
           ("espera_app", "no celular até entrar no Fóton"),
           ("fila_aparelho", "fila no aparelho (T2 - entrada)"),
           ("rede", "rede (T3 - T2)"),
           ("celular_servidor", "celular → Fóton (T3 - T1)"),
           ("processamento", "processamento (T4 - T3)"),
           ("servidor_tela", "Fóton → tela (T5 - T4, ou desde a selfie)"),
           ("ponta_a_ponta", "ponta a ponta (T5 - T0)")]


def pct(v, p):
    """Percentil pelo posto mais próximo: sempre um valor que aconteceu."""
    s = sorted(v)
    return s[min(len(s) - 1, max(0, math.ceil(p / 100 * len(s)) - 1))] if s else None


def _exif_epoch(t0):
    m = _RE_EXIF.match(t0 or "")
    if not m: return None
    ano, mes, dia, h, mi, se, frac, of = m.groups()
    tz = SP
    if of:
        sinal = 1 if of[0] == "+" else -1
        tz = timezone(sinal * timedelta(hours=int(of[1:3]), minutes=int(of[4:6])))
    base = datetime(int(ano), int(mes), int(dia), int(h), int(mi), int(se), tzinfo=tz).timestamp()
    return base + (float(frac) if frac else 0.0)


def calibra(export, leituras):
    """{camera: desvio_s}, desvio = relógio da câmera - hora real mostrada na tela."""
    por_id = {f["photo_id"]: f for f in export.get("fotos", [])}
    out = {}
    for pid, lido in (leituras or {}).items():
        f, m = por_id.get(pid), _RE_LEITURA.match((lido or "").strip())
        t_cam = _exif_epoch((f or {}).get("t0_exif"))
        if not (f and m and t_cam is not None and f.get("camera")): continue
        dia = datetime.fromtimestamp(t_cam, SP)
        real = datetime(dia.year, dia.month, dia.day, int(m.group(1)), int(m.group(2)), 0,
                        tzinfo=SP).timestamp() + float(m.group(3))
        out[f["camera"]] = t_cam - real
    return out


def _d(a, b):
    return None if a is None or b is None else a - b


def cadeia(export, desvios, relogios=()):
    selfie = {c["c"]: c.get("t_selfie") for c in export.get("convidados", [])}
    linhas = []
    for f in export.get("fotos", []):
        if f["photo_id"] in relogios: continue            # a foto do relógio não é foto do evento
        t0_cam = _exif_epoch(f.get("t0_exif"))
        desvio = desvios.get(f.get("camera")) if f.get("camera") else None
        if t0_cam is None: t0, st0 = None, "UNKNOWN"
        elif desvio is not None: t0, st0 = t0_cam - desvio, "proxy calibrado"
        else: t0, st0 = t0_cam, "proxy sem calibração"
        rel = (f.get("relogio_ms") or 0) / 1000
        cel = lambda t: None if t is None else t + rel      # relógio do celular -> do servidor
        t1, tapp, t2 = cel(f.get("t1_arquivo")), cel(f.get("t_app")), cel(f.get("t2_envio"))
        st1 = "UNKNOWN" if t1 is None else ("suspeito" if t2 is not None and abs(t2 - t1) < 1 else "proxy")
        t3, t4 = f.get("t3_recebida"), f.get("t4_pronta")
        telas = []
        for t in f.get("telas", []):
            t5 = t["t5_tela"] + (t.get("relogio_ms") or 0) / 1000
            base = [x for x in (t4, selfie.get(t["c"])) if x is not None]
            telas.append({"c": t["c"], "t5": t5, "origem": t.get("origem"),
                          "servidor_tela": t5 - max(base) if base else None})
        primeira = min(telas, key=lambda x: x["t5"]) if telas else None
        t5 = primeira["t5"] if primeira else None
        linhas.append({
            "photo_id": f["photo_id"], "camera": f.get("camera"), "seq": f.get("seq"),
            "n_faces": f.get("n_faces"), "entregas": f.get("entregas", 0), "recusas": f.get("recusas", 0),
            "duplicatas": f.get("duplicatas", 0), "via": f.get("via"), "tentativa": f.get("tentativa"),
            "instrumentada": f.get("instrumentada", True),
            "t0": t0, "t0_status": st0, "t1": t1, "t1_status": st1, "t_app": tapp, "t2": t2,
            "t3": t3, "t4": t4, "t5": t5, "t5_status": "observado" if t5 is not None else "não observado",
            "telas": telas,
            "trechos": {"camera_celular": _d(t1, t0), "espera_app": _d(tapp, t1), "fila_aparelho": _d(t2, tapp),
                        "rede": _d(t3, t2), "celular_servidor": _d(t3, t1), "processamento": _d(t4, t3),
                        "servidor_tela": primeira["servidor_tela"] if primeira else None,
                        "ponta_a_ponta": _d(t5, t0)}})
    return linhas


def _perdas(fotos):
    """Buracos na sequência de arquivos da câmera = fotos disparadas que não chegaram
    (ou que a fotógrafa apagou). Foto sem câmera conhecida entra na única câmera, se só
    houver uma."""
    cams = {f.get("camera") for f in fotos if f.get("camera")}
    grupos = {}
    for f in fotos:
        if f.get("seq") is None: continue
        cam = f.get("camera") or (next(iter(cams)) if len(cams) == 1 else None)
        grupos.setdefault(cam, set()).add(f["seq"])
    return sum((max(s) - min(s) + 1) - len(s) for s in grupos.values() if len(s) > 1)


def resumo(export, linhas):
    S = {"fotos": len(linhas), "aberturas": export.get("aberturas", 0),
         "convidados": len(export.get("convidados", [])),
         "com_t0": sum(1 for l in linhas if l["t0"] is not None),
         "t0_calibrado": sum(1 for l in linhas if l["t0_status"] == "proxy calibrado"),
         "t1_suspeito": sum(1 for l in linhas if l["t1_status"] == "suspeito"),
         "sem_rosto": sum(1 for l in linhas if not l["n_faces"]),
         "duplicatas": sum(l["duplicatas"] or 0 for l in linhas),
         "entregas": sum(l["entregas"] or 0 for l in linhas),
         "telas_observadas": sum(len(l["telas"]) for l in linhas),
         "recusas": sum(l["recusas"] or 0 for l in linhas),
         "perdas_provaveis": _perdas(export.get("fotos", [])),
         "trechos": {}}
    for k, _ in TRECHOS:
        v = [l["trechos"][k] for l in linhas if l["trechos"][k] is not None]
        S["trechos"][k] = {"n": len(v), "p50": pct(v, 50), "p95": pct(v, 95), "max": max(v) if v else None}
    # Criterio #4 do PILOTO-1: disparo ate a foto APARECER NA GALERIA do convidado. So entra
    # entrega observada (houve T5) que chegou com a galeria aberta (ao vivo) e tem T0. Foto
    # que ja existia quando a pessoa entrou mede a espera dela, nao o produto. Entrega nao
    # observada fica fora da conta e contada a parte: nao observado NAO e atraso.
    obs, sem_t0, calib = [], 0, True
    for l in linhas:
        for t in l["telas"]:
            if t["origem"] != "ao_vivo": continue
            if l["t0"] is None: sem_t0 += 1; continue
            obs.append(t["t5"] - l["t0"])
            if l["t0_status"] != "proxy calibrado": calib = False
    p = pct(obs, 95)
    S["criterio4"] = {"limite_s": 30.0, "n": len(obs), "p95": p, "dentro": (p <= 30.0) if p is not None else None,
                      "nao_observadas": S["entregas"] - S["telas_observadas"], "ao_vivo_sem_t0": sem_t0,
                      "t0_calibrado": calib if obs else None}
    return S


def _h(t):
    return datetime.fromtimestamp(t, SP).strftime("%H:%M:%S.") + f"{int((t % 1) * 10)}" if t else "(vazio)"


def _s(x):
    return "(vazio)" if x is None else f"{x:.1f} s"


def markdown(export, linhas, S):
    o = [f"# Cadeia por trecho, evento {export.get('evento')}", "",
         "Legenda: T3 e T4 são **medidos** (relógio do servidor). T0 é o disparo pelo EXIF, "
         "corrigido pela foto do relógio: **proxy**. T1 (data do arquivo) é **proxy da chegada ao "
         "celular**, ainda não validado em Android real. T5 é a imagem **carregada na galeria** do "
         "convidado. **UNKNOWN**: não há dado. **não observado**: nenhum aviso de tela chegou (a "
         "galeria não estava visível ou desenhando); a decisão de entrega do servidor não conta como T5.", "",
         "## Resumo", "",
         f"- Fotos: {S['fotos']} · sem rosto: {S['sem_rosto']} · duplicatas: {S['duplicatas']} · "
         f"perdas prováveis (buraco na sequência da câmera): {S['perdas_provaveis']}",
         f"- T0: {S['com_t0']} com EXIF, {S['t0_calibrado']} calibradas pela foto do relógio · "
         f"T1 suspeito: {S['t1_suspeito']}",
         f"- Entregas decididas: {S['entregas']} · vistas na tela: {S['telas_observadas']} · "
         f"recusas (\"não sou eu\"): {S['recusas']}",
         f"- Funil: abriram o evento {S['aberturas']} · fizeram selfie {S['convidados']}", ""]
    c4 = S["criterio4"]
    veredito = "sem número (nenhuma entrega observada ao vivo)" if c4["p95"] is None else \
        (f"{_s(c4['p95'])}: {'dentro' if c4['dentro'] else 'FORA'} do limite de 30 s")
    o += ["## Critério #4 do piloto", "",
          f"P95 do disparo até a foto aparecer na galeria do convidado, em {c4['n']} entrega(s) "
          f"observada(s) ao vivo e com T0: **{veredito}**.",
          f"- Entregas não observadas: {c4['nao_observadas']}, fora da conta: não observado não é atraso.",
          f"- Ao vivo, mas sem T0: {c4['ao_vivo_sem_t0']}.",
          f"- T0 usado calibrado pela foto do relógio: {'sim' if c4['t0_calibrado'] else ('não' if c4['t0_calibrado'] is False else '(vazio)')}.",
          "", "| Trecho | n | p50 | p95 | máx |", "|---|---|---|---|---|"]
    for k, nome in TRECHOS:
        t = S["trechos"][k]
        o.append(f"| {nome} | {t['n']} | {_s(t['p50'])} | {_s(t['p95'])} | {_s(t['max'])} |")
    o += ["", "## Foto por foto", "",
          "| foto | T0 | T1 | T2 | T3 | T4 | T5 | câmera → celular | celular → Fóton | proc. | → tela | ponta a ponta |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for l in linhas:
        tr = l["trechos"]
        o.append(f"| {l['photo_id']} | {_h(l['t0'])} ({l['t0_status']}) | {_h(l['t1'])} ({l['t1_status']}) "
                 f"| {_h(l['t2'])} | {_h(l['t3'])} | {_h(l['t4'])} | {_h(l['t5'])} ({l['t5_status']}) "
                 f"| {_s(tr['camera_celular'])} | {_s(tr['celular_servidor'])} | {_s(tr['processamento'])} "
                 f"| {_s(tr['servidor_tela'])} | {_s(tr['ponta_a_ponta'])} |")
    return "\n".join(o) + "\n"


def main(argv):
    if not argv:
        print(__doc__); return 2
    export = json.load(open(argv[0], encoding="utf-8"))
    leituras = dict(a.split("=", 1) for a in argv[1:] if "=" in a and not a.startswith("--"))
    for i, a in enumerate(argv):
        if a == "--relogio" and i + 1 < len(argv) and "=" in argv[i + 1]:
            k, v = argv[i + 1].split("=", 1); leituras[k] = v
    desvios = calibra(export, leituras)
    linhas = cadeia(export, desvios, set(leituras))
    for cam, d in desvios.items():
        print(f"<!-- desvio do relógio da câmera {cam}: {d:+.2f} s -->")
    print(markdown(export, linhas, resumo(export, linhas)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
