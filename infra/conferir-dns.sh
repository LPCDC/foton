#!/usr/bin/env bash
# Confere se a separacao site/app funcionou. Roda de qualquer maquina.
echo "== para onde cada nome aponta =="
for h in foton.app.br www.foton.app.br app.foton.app.br; do
  printf "%-22s " "$h"
  nslookup "$h" 8.8.8.8 2>/dev/null | awk '/^Address: /{printf "%s ", $2}'
  echo
done
echo
echo "== servidores de nome (esperado: *.ns.cloudflare.com) =="
nslookup -type=NS foton.app.br 8.8.8.8 2>/dev/null | grep -i nameserver
echo
echo "== o que cada endereco entrega =="
for u in https://foton.app.br https://www.foton.app.br; do
  printf "%-26s " "$u"
  t=$(curl -s --max-time 20 "$u" | grep -o "<title>[^<]*" | head -1 | sed 's/<title>//')
  echo "${t:-(sem resposta)}"
done
printf "%-26s " "https://app.foton.app.br/health"
curl -s --max-time 20 https://app.foton.app.br/health | head -c 120; echo
echo
echo "CERTO quando: raiz e www mostram o titulo do SITE, e /health responde com versao."
