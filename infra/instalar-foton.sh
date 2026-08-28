#!/usr/bin/env bash
# Fóton — instala o servidor na VM Oracle. Rodar DENTRO da VM (via ssh).
set -euo pipefail
echo "=== instalando o Fóton ==="

# 1) swap (a E2.1.Micro tem 1GB de RAM — o modelo precisa de folga)
if ! swapon --show | grep -q swapfile; then
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
  echo "swap de 2GB: ok"
fi

# 2) pacotes
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  python3-venv python3-pip git nginx libgl1 libglib2.0-0 >/dev/null
echo "pacotes: ok"

# 3) firewall DA VM (a 2a armadilha da Oracle: iptables bloqueia mesmo com a
#    Security List aberta). Libera 80/443 e persiste.
sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iptables-persistent >/dev/null 2>&1 || true
sudo netfilter-persistent save >/dev/null 2>&1 || true
echo "firewall da VM (80/443): ok"

# 4) código
sudo rm -rf /opt/foton
sudo git clone -q https://github.com/LPCDC/foton.git /opt/foton
sudo chown -R ubuntu:ubuntu /opt/foton
python3 -m venv /opt/foton/venv
/opt/foton/venv/bin/pip install -q --upgrade pip
/opt/foton/venv/bin/pip install -q -r /opt/foton/app/test_rig/requirements.txt
echo "app + dependencias: ok"

# 5) serviço (sobe sozinho no boot e reinicia se cair)
sudo tee /etc/systemd/system/foton.service >/dev/null <<'UNIT'
[Unit]
Description=Foton
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/opt/foton/app/test_rig
Environment=OMP_NUM_THREADS=1
Environment=FOTON_DB=/opt/foton/data/foton.db
ExecStart=/opt/foton/venv/bin/uvicorn rig:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
mkdir -p /opt/foton/data
sudo systemctl daemon-reload && sudo systemctl enable -q foton && sudo systemctl restart foton
echo "servico: ok"

# 6) nginx na frente (porta 80) — o HTTPS entra depois com o domínio
sudo tee /etc/nginx/sites-available/foton >/dev/null <<'NGX'
server {
  listen 80 default_server;
  client_max_body_size 50M;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
  }
}
NGX
sudo ln -sf /etc/nginx/sites-available/foton /etc/nginx/sites-enabled/foton
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t >/dev/null && sudo systemctl restart nginx
echo "nginx: ok"

echo
echo "aguardando o modelo carregar (1a vez demora)..."
for i in $(seq 1 30); do
  if curl -s -m 5 http://127.0.0.1:8000/health | grep -q ok; then
    echo "=== FOTON NO AR ==="; curl -s http://127.0.0.1:8000/health; echo; exit 0
  fi
  sleep 10
done
echo "!! nao respondeu a tempo — ver: sudo journalctl -u foton -n 50"
exit 1
