#!/usr/bin/env bash
# Fóton — liga HTTPS (Let's Encrypt) no domínio. Rodar DENTRO da VM.
# Uso: bash https.sh getfoton.duckdns.org seu@email.com
set -euo pipefail
DOM="${1:-getfoton.duckdns.org}"
MAIL="${2:-luizoak@gmail.com}"
echo "=== HTTPS para $DOM ==="

# 1) o nginx precisa responder pelo domínio antes do certificado
sudo tee /etc/nginx/sites-available/foton >/dev/null <<NGX
server {
  listen 80 default_server;
  server_name $DOM;
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
echo "nginx respondendo por $DOM: ok"

# 2) certbot emite e configura o HTTPS sozinho (e renova automático)
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot python3-certbot-nginx >/dev/null
sudo certbot --nginx -d "$DOM" --non-interactive --agree-tos -m "$MAIL" --redirect >/dev/null 2>&1 \
  || { echo "!! certbot falhou — ver: sudo certbot --nginx -d $DOM"; exit 1; }
echo "certificado emitido + redirect http->https: ok"

# 3) renovação automática (o certificado dura 90 dias)
sudo systemctl enable -q --now certbot.timer 2>/dev/null || true
echo "renovacao automatica: ok"

sleep 3
echo
echo "=== TESTE ==="
curl -s -m 15 "https://$DOM/health" && echo && echo ">>> HTTPS NO AR: https://$DOM"
