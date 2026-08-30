# Prompt para a próxima sessão

> Cole isto numa sessão nova (ou diga só: **"continua do PROMPT-PROXIMA-SESSAO.md"**).
>
> **Versão de 2026-08-30, madrugada.** O dono respondeu às perguntas do plano anterior
> na mesma noite; esta versão incorpora as decisões e as ideias novas dele. É um
> **plano aprovado** — a sessão que o ler implementa, na ordem daqui.

---

Fóton — continuação. Antes de tocar em qualquer coisa: `BLUEPRINT.md` (estado e
armadilhas §7), `docs/PRODUTO.md` §1–§3, `docs/DECISIONS.md` da ADR-0025 em diante.
Onde documento e código divergirem, **o código ganha** e corrigir o documento é parte
da tarefa. Nada é "pronto" sem rodar e ler a saída.

## Decisões do dono (2026-08-30, noite) — não rediscutir

- **P1 (reencontro por selfie): CONFIRMADO.** GLAMON: selfie nova reencontra todo o
  histórico (biometria permanente). Patrícia e Ana: dentro da janela de retenção do
  evento. **Adendo registrado:** a interface da Ana não mostra NADA de câmera
  profissional (a pele `social` da ADR-0030 já esconde); "conectar DSLR" vira, no
  futuro, **bônus de um plano plus** — anotado como diferencial de upsell, não fazer agora.
- **P2 (Ana): versão FÓTON FESTA** — ela E os convidados mandam fotos (PRODUTO §2).
  Consequências que o dono apontou: login/persistência do convidado ficam centrais
  (a sessão persistente de 24h já existe — validar se basta) e o **lag da câmera**
  importa (item 6 abaixo). Branding do Fóton Festa: pensar como expert **quando formos
  fazer**, não agora (pedido dele).
- **P4 (DNS): AUTORIZADO** — mover a zona para a Cloudflare. Runbook no item 7.
- **P3 (contrato):** pesquisa feita (ver `docs/CONTRATO-ORGANIZADOR.md`, nota de
  aceite): mercado (SpotMyPhotos) põe a responsabilidade primária no
  fotógrafo/organizador com registro digital de consentimento — igual ao nosso
  desenho. Recomendação entregue ao dono: **quem cria o evento assina** (Patrícia,
  não os noivos) por **clickwrap com trilha de auditoria** (conta + data/hora +
  versão do texto), e **assinatura eletrônica** só para conta empresa/contratos com
  preço. Aguarda o "ok" dele para virar item de código (checkbox + tabela `aceite`).
- **P5 (despejo GLAMON): FEITO pelo dono** — todas as fotos, ~2000×2000 px, do PC via
  wi-fi. `/health` medido depois: 80–150 ms, VM saudável. Os números de dentro
  (contagem, bytes, disco, carga) dependem do comando de admin que o dono roda —
  saída dele abre o item 0.
- **Pré-cadastro como roteiro de venda (ideia do dono, registrada):** ver PRODUTO §3b —
  o que falta de código é `photo.oculta` (foto de referência fora da galeria) + texto
  de orientação no painel. Entra como item 10.

## Ordem de trabalho

### 0. Relatório do despejo GLAMON — antes de qualquer código
Com o token de admin (dono fornece; `foton-acessos.md` fora do repo): `/admin/saude`,
contagem/bytes do álbum GLAMON, crescimento de banco+backup; P95 do `/ingest` no
período se houver Cloud Shell. Números em `docs/BENCHMARKS.md`. **Decide a urgência do R2.**

### 1. Galeria do convidado: teto de 50 + "Mostrar mais"
`renderGuestGrid()` reconstrói a grade inteira a cada foto nova. `guestState.limite=50`
por aba; slice + botão "Mostrar mais 50"; foto nova não empurra foto vista para fora;
ZIP/seleção/contadores usam a LISTA CHEIA. Benchmark: bytes e tempo do primeiro render
no álbum GLAMON, antes vs depois.

### 2. Ordenação da galeria: data | pessoas (ideia do dono, avaliada VIÁVEL)
`photo.n_faces` **já existe** no banco — ordenar "todas" por quantidade de gente é
expor um campo que já está lá. Para quem ligou nome (§3b-2): "pessoas" também pode
agrupar por identificado (a tabela `match` já liga foto↔convidado). Fazer como um
seletor simples (Data · Pessoas) na aba "todas"; client-side sobre a lista carregada,
`n_faces` incluído na resposta de `/photos` (mudança de 1 campo).

### 3. Coração na foto (double-tap) — VIÁVEL, com uma ressalva de gesto
É a primeira fatia do chat de emoji já desenhado em PRODUTO §3d (pega carona no poll
de 2,5 s; tabela `evento, guest_id, foto_id, ts`; POST + contador no `/feed`).
**Ressalva:** double-tap na GRADE briga com toque-abre e segurar-seleciona (o dedo
que abre viraria espera de 300 ms). O lugar certo do double-tap é a **foto aberta**
(lightbox, estilo Instagram) + badge de contagem na miniatura. Um coração por
convidado por foto (idempotente). Sem texto — a regra do §3d vale aqui.

### 4. "Adicionar rosto" — associação manual de foto sem rosto (GLAMON, VIÁVEL)
Caso real do dono: foto artística/zoom (a mão da profissional) não tem rosto para o
motor. A tabela `match` já é separada de `face`: associar manualmente = **uma linha
de match com flag `manual`**, sem biometria nova — LGPD mais leve, não mais pesada.
UI no painel do dono do evento/álbum: foto com `n_faces=0` ganha "atribuir a alguém"
→ escolhe da lista de convidados registrados. Só o dono do evento pode (`_pode()`);
rota com dono e teste de contrato. **Só para conta empresa** por ora (decisão dele:
"especialmente GLAMON; nos outros é fundamental aparecer rosto").

### 5. Reencontro por selfie (P1 confirmada)
Dentro de UM evento, sempre (busca global continua proibida — PRODUTO §3b). Selfie
nova compara contra convidados já registrados; casa com limiar duro + margem → reata
ao guest_id (histórico volta); senão cria novo em silêncio. **Limiar: experimento
ANTES do código** (selfie↔selfie mesma pessoa vs pessoas diferentes, fotos-teste/,
número em BENCHMARKS). Copy LGPD: "Já esteve aqui? Tire uma selfie nova — ela é
comparada só com quem já se registrou neste evento e descartada."

### 6. Câmera do app: lag/motion blur (relato do dono, hipótese JÁ localizada)
`app/web/index.html:2379` — depois de abrir o stream, o app aplica
`applyConstraints({width:{ideal:3840},height:{ideal:2160}})`: preview em 4K derruba o
FPS em Android mediano, e é desperdício (o servidor reduz a 2048px). Experimento:
medir FPS/fluidez do preview no aparelho com e sem a linha; capturar em ≥2048 e
manter o preview leve (ou `ImageCapture.takePhoto()` para foto cheia sem stream 4K).
Só aceitar com número dos dois lados. Importa dobrado agora que o Fóton Festa (P2)
faz todo convidado virar câmera.

### 7. DNS — AUTORIZADO; executar TUDO NO MESMO DIA, nesta ordem
Zona atual: **só 3 registros A** — `foton.app.br`, `www` e `app` → `152.67.46.113`.
Sem MX, sem TXT. Cert real (saída do dono, 2026-08-31): **cert-name
`getfoton.duckdns.org`**, cobre app+raiz+www+duckdns, expira 2026-11-27.
⚠️ Depois do passo 1, raiz/`www` mostram aviso de certificado até o passo 3 terminar
— por isso os três passos são da MESMA sessão/dia.
1. **Certificado** (Cloud Shell, dono):
   ```
   ssh -o StrictHostKeyChecking=no -i ~/.ssh/foton.key ubuntu@152.67.46.113 \
     'sudo certbot --nginx --cert-name getfoton.duckdns.org \
        -d app.foton.app.br -d getfoton.duckdns.org \
        --non-interactive --agree-tos && sudo certbot renew --dry-run'
   ```
   Se o certbot pedir confirmação para REMOVER domínios, rodar sem
   `--non-interactive` e responder Update. (`infra/dominio.sh` só EXPANDE — não usar.)
2. **Cloudflare** (conta já existe — é a do R2): adicionar o site `foton.app.br`,
   copiar os 3 registros A; `app` **DNS-only (nuvem cinza)** — proxy laranja quebra o
   certbot da VM; raiz e `www` já podem apontar para o Netlify
   (`getfoton.netlify.app` / apex conforme o painel do Netlify instruir).
3. **registro.br**: trocar os NS pelos dois que a Cloudflare der. Propaga em horas.
4. Validar com curl: `https://app.foton.app.br/health`, raiz e `www` servindo o site,
   HTTPS dos três. Números/estado em BENCHMARKS. O R2 vem depois do primeiro sucesso
   em evento médio (palavra do dono) — a zona na Cloudflare deixa `fotos.foton.app.br`
   a um passo.

### 8. Perfil `social` atribuível + coluna (completa a ADR-0030 — pré-requisito do Festa)
Coluna `photographer.perfil` (ALTER guardado); `_perfil()`: coluna vence, senão deriva.
Toggle no admin. O Fóton Festa (P2) vem em cima disto: papéis `dono`/`participante`
por evento, participante envia via a sessão de convidado que já existe, limite POR
PARTICIPANTE (PRODUTO §2 — nunca por IP). As perguntas abertas do §2 (quantas fotos,
apagar a própria, conteúdo impróprio) precisam do dono ANTES do código do Festa.

### 9-b. Pré-cadastro pronto para a porta da festa
Coluna `photo.oculta` (rosto entra no índice, foto NÃO entra na galeria — a "foto de
referência" da abordagem) + texto curto no painel do criador ensinando o roteiro de
15 s (PRODUTO §3b). O motor já funciona; isto é acabamento + material de venda.

### 9. Contrato — quando o dono confirmar a recomendação da P3
Checkbox no 1º evento + tabela `aceite` (conta, data/hora, versão) + `/termo` com o
texto integral. Vira ADR.

## O que o dono dá a esta sessão

Token de admin (item 0) · Cloud Shell (itens 0 e 7.1) · cliques na Cloudflare e no
registro.br (7.2–7.3, ou deixa a sessão guiar tela a tela) · resposta da P5 e o fim
da frase cortada ("4 e para…") · confirmação da recomendação da P3 · aprovação de
edições, `tests/todos.sh`, `git push`, `curl`.

## O que NÃO fazer (continua)

Login e-mail/senha fica (ADR-0019/0026) · crédito cortado fica (ADR-0024) · FTP quieto ·
nenhuma credencial no repo · não reprocessar foto entregue (ADR-0028) · `ensaio.py`
nunca em massa · busca global de rosto NÃO · menores fora de escopo (ADR-0029) ·
double-tap NUNCA na grade (briga com abrir/selecionar — só no lightbox).

## Comandos

```
bash tests/todos.sh                                         # 4 suítes, 280 checagens
git add -A && git commit -m "..." && git push origin main   # deploy (~2 min)
curl -s https://app.foton.app.br/health                     # validar depois
```
