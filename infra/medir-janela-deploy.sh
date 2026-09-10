#!/usr/bin/env bash
# Foton — cronometra a JANELA REAL de indisponibilidade de um deploy.
#
# Por que existe: ate 2026-09-10 o projeto repetia "~25 s de 502" em tres documentos
# (BLUEPRINT §5, §7 e docs/TESTES.md) sem nunca ter cronometrado. Na primeira medicao
# de verdade deu ~7 s. Estimativa repetida vira folclore; este script troca o folclore
# por um numero — e permite refazer a conta a cada deploy, porque a janela depende do
# que mudou (mexer em dependencia ou subir sob carga nao custa o mesmo).
#
#   bash infra/medir-janela-deploy.sh 2982a77     # rode ANTES do push, em outro terminal
#
# Amostra /health a cada ~2 s e imprime uma linha por amostra (hora, HTTP, versao).
# Sai 0 quando o SHA esperado responde 200; 1 se estourar o tempo.
set -u

alvo="${1:-}"
[ -n "$alvo" ] || { echo "uso: bash $0 <sha-esperado-de-7-chars>"; exit 2; }

URL="${FOTON_HEALTH:-https://app.foton.app.br/health}"
LIMITE="${LIMITE_S:-480}"
corpo="$(mktemp)"
trap 'rm -f "$corpo"' EXIT

echo "cronometrando $URL ate ver versao=$alvo (limite ${LIMITE}s)"
inicio=$SECONDS
primeiro_erro=""
while [ $((SECONDS - inicio)) -lt "$LIMITE" ]; do
  agora=$(date +%H:%M:%S)
  code=$(curl -s -o "$corpo" -w '%{http_code}' --max-time 5 "$URL" 2>/dev/null)
  ver=$(grep -o '"versao":"[^"]*"' "$corpo" 2>/dev/null | head -1 | sed 's/.*:"//;s/"//')
  echo "$agora  http=$code  versao=${ver:--}"
  [ "$code" != "200" ] && [ -z "$primeiro_erro" ] && primeiro_erro="$agora"
  if [ "$code" = "200" ] && [ "$ver" = "$alvo" ]; then
    echo
    echo "CHEGOU: $alvo respondendo 200 as $agora"
    [ -n "$primeiro_erro" ] && echo "JANELA: primeiro nao-200 as $primeiro_erro -> SHA novo as $agora"
    [ -z "$primeiro_erro" ] && echo "JANELA: nenhuma amostra fora do ar (a troca caiu entre duas amostras)"
    exit 0
  fi
  sleep 2
done
echo "TEMPO ESGOTADO sem ver $alvo — o auto-update pegou? (systemd timer na VM)"
exit 1
