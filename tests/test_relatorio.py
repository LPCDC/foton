"""Relatório da cadeia por trecho (ADR-0046): a conta que transforma o export em
"disparada aqui, no celular aqui, na tela aqui", sem inventar o que não foi medido.

    python tests/test_relatorio.py

Dados sintéticos com resposta conhecida: a câmera está 37 s ATRASADA de propósito, e a
calibração pela foto do relógio tem de achar exatamente isso.
"""
import os, sys
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))
import relatorio_evento as R

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

SP = timezone(timedelta(hours=-3))
def ep(h, m, s):  # hora de São Paulo em 28/09/2026 -> epoch
    return datetime(2026, 9, 28, h, m, 0, tzinfo=SP).timestamp() + s

CEL = -250.0   # o celular da fotógrafa está 250 ms ADIANTADO: servidor - celular = -250 ms
EXPORT = {
    "evento": "ENSA", "aberturas": 5,
    "convidados": [{"c": "c1", "t_selfie": ep(14, 0, 5)}, {"c": "c2", "t_selfie": ep(14, 2, 0)}],
    "fotos": [
        # K: a foto do relogio. A tela mostrava 14:00:37.5; o EXIF da camera dizia 14:00:00.5.
        {"photo_id": "K", "camera": "Canon EOS R8", "seq": 99, "t0_exif": "2026:09:28 14:00:00.50",
         "t1_arquivo": None, "t_app": None, "t2_envio": None, "relogio_ms": None, "rtt_ms": None,
         "t3_recebida": ep(14, 0, 50), "t4_pronta": ep(14, 0, 51), "n_faces": 0, "entregas": 0,
         "recusas": 0, "duplicatas": 0, "telas": []},
        # A: caminho inteiro. Disparo real 14:00:47 (EXIF 14:00:10 + 37 s).
        {"photo_id": "A", "camera": "Canon EOS R8", "seq": 100, "t0_exif": "2026:09:28 14:00:10.00",
         "t1_arquivo": ep(14, 0, 49) + 0.25, "t_app": ep(14, 0, 55) + 0.25, "t2_envio": ep(14, 0, 56) + 0.25,
         "relogio_ms": CEL, "rtt_ms": 90.0,
         "t3_recebida": ep(14, 0, 58), "t4_pronta": ep(14, 0, 59),
         "n_faces": 2, "entregas": 2, "recusas": 0, "duplicatas": 1,
         "telas": [{"c": "c1", "t5_tela": ep(14, 1, 0) - 0.1, "relogio_ms": 100.0, "rtt_ms": 60.0, "origem": "ao_vivo"}]},
        # B: sem EXIF e sem ninguem ver na tela; depois de um buraco de 2 na sequencia.
        {"photo_id": "B", "camera": None, "seq": 103, "t0_exif": None,
         "t1_arquivo": None, "t_app": None, "t2_envio": None, "relogio_ms": None, "rtt_ms": None,
         "t3_recebida": ep(14, 1, 30), "t4_pronta": ep(14, 1, 31), "n_faces": 1, "entregas": 1,
         "recusas": 0, "duplicatas": 0, "telas": []},
        # C: data do arquivo igual a hora do envio: o navegador nao sabia a data real.
        {"photo_id": "C", "camera": "Canon EOS R8", "seq": 104, "t0_exif": "2026:09:28 14:01:40.00",
         "t1_arquivo": ep(14, 2, 30) + 0.25, "t_app": ep(14, 2, 30) + 0.25, "t2_envio": ep(14, 2, 30) + 0.55,
         "relogio_ms": CEL, "rtt_ms": 90.0, "t3_recebida": ep(14, 2, 32), "t4_pronta": ep(14, 2, 33),
         "n_faces": 1, "entregas": 1, "recusas": 1, "duplicatas": 0,
         "telas": [{"c": "c2", "t5_tela": ep(14, 2, 34), "relogio_ms": 0.0, "rtt_ms": 40.0, "origem": "ao_vivo"}]},
        # D: ja existia quando c2 fez a selfie: o tempo ate a tela conta a partir da selfie.
        {"photo_id": "D", "camera": None, "seq": None, "t0_exif": None, "t1_arquivo": None, "t_app": None,
         "t2_envio": None, "relogio_ms": None, "rtt_ms": None,
         "t3_recebida": ep(14, 1, 0), "t4_pronta": ep(14, 1, 1), "n_faces": 1, "entregas": 1,
         "recusas": 0, "duplicatas": 0,
         "telas": [{"c": "c2", "t5_tela": ep(14, 2, 3), "relogio_ms": 0.0, "rtt_ms": 40.0, "origem": "selfie"}]},
    ],
}

print("[1] calibracao pela foto do relogio")
off = R.calibra(EXPORT, {"K": "14:00:37.5"})
checa("acha os 37 s de atraso da camera", round(off.get("Canon EOS R8", 0), 3), -37.0)
checa("leitura mal escrita e recusada, nao vira numero", R.calibra(EXPORT, {"K": "meio-dia"}), {})

print("\n[2] cada trecho, com o que e medido, proxy ou UNKNOWN")
L = {l["photo_id"]: l for l in R.cadeia(EXPORT, off, {"K"})}
a = L["A"]
checa("T0 calibrado = EXIF + 37 s", round(a["t0"], 3), round(ep(14, 0, 47), 3))
checa("T0 marcado como proxy calibrado (e EXIF, nao disparo)", a["t0_status"], "proxy calibrado")
checa("T1 do celular vai para o relogio do servidor", round(a["t1"], 3), round(ep(14, 0, 49), 3))
checa("camera -> celular", round(a["trechos"]["camera_celular"], 3), 2.0)
checa("celular -> Fóton (T3 - T1)", round(a["trechos"]["celular_servidor"], 3), 9.0)
checa("dentro dele: espera ate entrar no app", round(a["trechos"]["espera_app"], 3), 6.0)
checa("processamento (T4 - T3)", round(a["trechos"]["processamento"], 3), 1.0)
checa("T5 no relogio do servidor (celular do convidado +100 ms)", round(a["t5"], 3), round(ep(14, 1, 0), 3))
checa("servidor -> tela", round(a["trechos"]["servidor_tela"], 3), 1.0)
checa("ponta a ponta", round(a["trechos"]["ponta_a_ponta"], 3), 13.0)

b = L["B"]
checa("sem EXIF, T0 e UNKNOWN (nada inventado)", (b["t0"], b["t0_status"]), (None, "UNKNOWN"))
checa("sem aviso da tela, T5 nao observado", (b["t5"], b["t5_status"]), (None, "não observado"))
checa("e sem T5 nao ha trecho ate a tela", (b["trechos"].get("servidor_tela"), b["trechos"].get("ponta_a_ponta")), (None, None))
checa("T1 marcado suspeito quando igual a hora do envio", L["C"]["t1_status"], "suspeito")
checa("EXIF sem foto do relogio fica proxy sem calibracao",
      R.cadeia(EXPORT, {})[1]["t0_status"], "proxy sem calibração")
checa("foto que ja existia: tela conta da selfie, nao da foto", round(L["D"]["trechos"]["servidor_tela"], 3), 3.0)
checa("a foto do relogio nao entra como foto do evento", "K" in L, False)

print("\n[3] resumo do evento")
S = R.resumo(EXPORT, R.cadeia(EXPORT, off, {"K"}))
checa("perdas provaveis pelo buraco na sequencia da camera", S["perdas_provaveis"], 2)
checa("duplicatas", S["duplicatas"], 1)
checa("entregas decididas x vistas na tela", (S["entregas"], S["telas_observadas"]), (5, 3))
checa("funil: abriu x selfie", (S["aberturas"], S["convidados"]), (5, 2))
checa("recusas ('nao sou eu')", S["recusas"], 1)
checa("percentil pelo posto mais proximo", R.pct([1, 2, 3, 4, 100], 95), 100)
md = R.markdown(EXPORT, R.cadeia(EXPORT, off, {"K"}), S)
checa("o relatorio diz o que e UNKNOWN", "UNKNOWN" in md and "não observado" in md, True)
checa("o relatorio nao tem travessao", chr(0x2014) in md or chr(0x2013) in md, False)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
