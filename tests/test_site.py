"""Acessibilidade do site de marca (plano 1B).

    python tests/test_site.py

O site é outro produto que o app: aceite separado, de propósito. Aqui trava-se o que
exclui gente — não o que é feio (isso é o redesenho, plano 12).
Publicado pelo Cloudflare Pages a partir de `site/` (ADR-0032): `git push` publica.
"""
import io, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = io.open(os.path.join(RAIZ, "site", "index.html"), encoding="utf-8").read()

def sem_comentarios(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", html, flags=re.S)

LIMPO = sem_comentarios(SITE)

FALHAS = []
def checa(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA") + f" {nome}: {obtido!r} (esperado {esperado!r})")
    if not ok: FALHAS.append(nome)

print("[1] navegação no celular — os links não podem simplesmente sumir")
botao = re.search(r'<button[^>]*class="[^"]*navbtn[^"]*"[^>]*>', LIMPO)
checa("existe botão de menu", bool(botao), True)
attrs = botao.group(0) if botao else ""
checa("o botão diz se está aberto ou fechado", "aria-expanded" in attrs, True)
checa("o botão aponta para o painel que controla", "aria-controls" in attrs, True)
checa("o botão tem nome acessível", "aria-label" in attrs, True)
alvo = re.search(r'aria-controls="([^"]+)"', attrs)
checa("o painel existe no HTML", bool(alvo) and f'id="{alvo.group(1)}"' in LIMPO, True)
checa("o menu fecha com Escape", "Escape" in LIMPO, True)
checa("os três links de seção continuam no HTML",
      all(f'href="#{s}"' in LIMPO for s in ("como", "quem", "verdade")), True)

print("\n[2] foco visível e atalho para o conteúdo")
checa("existe regra global de foco visível", bool(re.search(r"(^|[}\s]):focus-visible\s*\{", LIMPO)), True)
checa("existe link para pular ao conteúdo", "pular" in LIMPO.lower(), True)

print("\n[3] ícones e nomes")
soltos = [t[:50] for t in re.findall(r"<svg\b[^>]*>", LIMPO)
          if "aria-hidden" not in t and "aria-label" not in t]
checa("ícone svg sem aria-hidden nem rótulo", soltos, [])
sem_nome = []
for m in re.finditer(r"<(a|button)\b([^>]*)>(.*?)</\1>", LIMPO, re.S):
    texto = re.sub(r"<[^>]+>", "", m.group(3)).strip()
    if not texto and "aria-label" not in m.group(2):
        sem_nome.append((m.group(1), m.group(2).strip()[:50]))
checa("link ou botão sem nome acessível", sem_nome, [])

print("\n[4] movimento e prova do vermelho")
checa("respeita movimento reduzido", "prefers-reduced-motion" in LIMPO, True)
falso = LIMPO.replace("aria-expanded", "xxx", 1)
checa("prova do vermelho: sem aria-expanded o teste acusa", "aria-expanded" in falso.split("navbtn")[1][:400] if "navbtn" in falso else False, False)

print("\n[5] site no design system, imagens com procedência (docs/DIRECAO-VISUAL.md)")
import json
DS_APP = io.open(os.path.join(RAIZ, "app", "web", "ds", "foton.css"), encoding="utf-8").read()
DS_SITE = io.open(os.path.join(RAIZ, "site", "ds", "foton.css"), encoding="utf-8").read()
checa("o site usa a MESMA cópia do design system do app", DS_SITE == DS_APP, True)
checa("o site carrega o design system", 'href="ds/foton.css?v=' in SITE, True)
IMG = os.path.join(RAIZ, "site", "img")
refs = set(re.findall(r'img/([\w.-]+\.(?:webp|jpg|png))', LIMPO))
checa("toda imagem citada existe", sorted(r for r in refs if not os.path.exists(os.path.join(IMG, r))), [])
PROC = json.load(io.open(os.path.join(IMG, "PROCEDENCIA.json"), encoding="utf-8"))
arquivos = sorted(f for f in os.listdir(IMG) if f != "PROCEDENCIA.json")
checa("toda imagem tem procedência registrada", sorted(set(arquivos) - set(PROC["arquivos"])), [])
checa("nenhuma procedência sobra sem arquivo", sorted(set(PROC["arquivos"]) - set(arquivos)), [])
checa("toda pessoa das imagens é fictícia", sorted(k for k, v in PROC["arquivos"].items() if v.get("pessoa") != "ficticia"), [])
checa("a página diz que as fotos são geradas por IA", "geradas por IA" in LIMPO, True)
# O número do site sai da medição (tests/site_reconhecimento.py), não de memória.
rec = PROC["reconhecimento"]
checa("a medição confirmou a história da página", rec.get("historia_verdadeira"), True)
def br(x): return f"{x:.2f}".replace(".", ",")
sem = rec["semelhanca"]
checa("o número da capa bate com a medição", f"<b>{br(sem['capa-1200.webp'])}</b> de semelhança" in LIMPO, True)
dela = [v for k, v in sem.items() if k.startswith(("capa", "ela-"))]
checa("a faixa da galeria bate com a medição", f"de {br(min(dela))} a {br(max(dela))}" in LIMPO, True)
checa("o limiar citado é o da produção", f"a partir de {br(rec['limiar'])}" in LIMPO, True)
checa("nenhum script de fora (leveza e CSP)", re.findall(r"<script[^>]+src=", LIMPO), [])
imgs = re.findall(r"<img\b[^>]*>", LIMPO)
checa("toda imagem tem alt", [t[:60] for t in imgs if " alt=" not in t], [])
primeira = [t for t in imgs if "capa-800" in t or ("selfie-240" in t and "sizes=" in t)]
checa("só a primeira tela carrega na hora; o resto é preguiçoso",
      [t[:60] for t in imgs if t not in primeira and 'loading="lazy"' not in t], [])
checa("a abertura só anima sem pedido de menos movimento",
      LIMPO.find("@media (prefers-reduced-motion: no-preference)") < LIMPO.find(".capa__selfie { animation"), True)
checa("sem travessão nem meia-risca no site", SITE.count("—") + SITE.count("–"), 0)

print("\n[6] o site não promete o que não foi provado (PRODUCT.md, 2026-09-28)")
# Servidor rápido não é produto rápido: o tempo do servidor não vira promessa até o
# caminho câmera → celular → Fóton ser medido num evento real.
checa("o tempo do servidor não aparece como promessa", re.search(r"1 segundo|~ ?1 s\b", LIMPO) is None, True)
# Nunca houve evento real (dono, 2026-09-28): nada pode sugerir uso que não aconteceu.
checa("não diz que há fotógrafa usando", re.search(r"com fotógrafa real|eventos de verdade", LIMPO) is None, True)
checa("o modo empresa saiu do site", "Empresa e esporte" in LIMPO, False)

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
