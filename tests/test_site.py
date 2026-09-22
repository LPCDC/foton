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

print("\n" + ("TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S): {FALHAS}"))
sys.exit(1 if FALHAS else 0)
