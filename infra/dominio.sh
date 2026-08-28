#!/usr/bin/env bash
# Fóton — coloca o app num domínio próprio, SEM derrubar o antigo.
#
# Por que existe: o Chrome mostra "Site perigoso" em getfoton.duckdns.org — não é o
# certificado (é válido), é a reputação do duckdns.org, muito usado em golpe. O
# convidado escaneia o QR e vê tela vermelha. Domínio próprio resolve.
#
# O duckdns CONTINUA funcionando de propósito: QR já impresso, app instalado no
# celular de alguém e o monitor não podem quebrar na troca.
#
# Antes de rodar: os nomes já têm que apontar para o IP da VM (registro A).
# Uso, no Cloud Shell da Oracle (ou dentro da VM):
#   bash dominio.sh app.foton.app.br foton.app.br www.foton.app.br getfoton.duckdns.org
set -euo pipefail
MAIL="${FOTON_MAIL:-luizoak@gmail.com}"
DOMS=("$@")
[ ${#DOMS[@]} -eq 0 ] && { echo "uso: bash dominio.sh dominio1 [dominio2 ...]"; exit 1; }
PRINCIPAL="${DOMS[0]}"
echo "=== dominio proprio: ${DOMS[*]} ==="

# 1) checar o DNS ANTES — certbot falha feio se um nome nao aponta para ca
IP_VM="$(curl -s -m 10 ifconfig.me || true)"
echo "IP desta maquina: ${IP_VM:-desconhecido}"
OK=()
for d in "${DOMS[@]}"; do
  IP="$(getent hosts "$d" | awk '{print $1}' | head -1 || true)"
  if [ "$IP" = "$IP_VM" ]; then echo "  $d -> $IP  ok"; OK+=("$d")
  else echo "  $d -> ${IP:-nao resolve}  IGNORADO (nao aponta para esta VM)"; fi
done
[ ${#OK[@]} -eq 0 ] && { echo "!! nenhum nome aponta para ca. Crie os registros A e espere o DNS."; exit 1; }

# 2) nginx responde por todos os nomes que passaram
sudo tee /etc/nginx/sites-available/foton >/dev/null <<NGX
server {
  listen 80 default_server;
  server_name ${OK[*]};
  client_max_body_size 50M;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 300s;
  }
}
NGX
sudo nginx -t >/dev/null && sudo systemctl reload nginx
echo "nginx respondendo por ${OK[*]}: ok"

# 3) um certificado cobrindo todos (--expand deixa acrescentar nome depois)
ARGS=(); for d in "${OK[@]}"; do ARGS+=(-d "$d"); done
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot python3-certbot-nginx >/dev/null
sudo certbot --nginx "${ARGS[@]}" --non-interactive --agree-tos --expand -m "$MAIL" --redirect \
  || { echo "!! certbot falhou — rodar na mao: sudo certbot --nginx ${ARGS[*]}"; exit 1; }
sudo systemctl enable -q --now certbot.timer 2>/dev/null || true
echo "certificado + renovacao automatica: ok"

# 4) o painel mostra este host na configuracao de FTP da camera
sudo mkdir -p /etc/systemd/system/foton.service.d
sudo tee /etc/systemd/system/foton.service.d/dominio.conf >/dev/null <<CFG
[Service]
Environment=FOTON_HOST=$PRINCIPAL
CFG
sudo systemctl daemon-reload && sudo systemctl restart foton
echo "painel passa a mostrar $PRINCIPAL como servidor de FTP: ok"

sleep 4
echo; echo "=== TESTE ==="
for d in "${OK[@]}"; do
  printf "  https://%s/health -> " "$d"
  curl -s -m 20 "https://$d/health" || echo "FALHOU"
  echo
done
echo ">>> app no ar em https://$PRINCIPAL"
