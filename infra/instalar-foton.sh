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

# 4) DADOS ficam FORA do código (/var/lib/foton). O passo abaixo apaga /opt/foton;
#    quando o banco morava lá dentro, toda reinstalação zerava contas e eventos.
sudo mkdir -p /var/lib/foton
if [ -f /opt/foton/data/foton.db ] && [ ! -f /var/lib/foton/foton.db ]; then
  sudo cp /opt/foton/data/foton.db* /var/lib/foton/ 2>/dev/null || true
  echo "banco antigo migrado para /var/lib/foton: ok"
fi
sudo chown -R ubuntu:ubuntu /var/lib/foton

# código
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
Environment=FOTON_DB=/var/lib/foton/foton.db
ExecStart=/opt/foton/venv/bin/uvicorn rig:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload && sudo systemctl enable -q foton && sudo systemctl restart foton
echo "servico: ok"

# 4b) BACKUP diário do banco (7 cópias) — protege contra corrupção e erro humano
sudo tee /usr/local/bin/foton-backup >/dev/null <<'BKP'
#!/usr/bin/env bash
mkdir -p /var/lib/foton/backup
[ -f /var/lib/foton/foton.db ] || exit 0
sqlite3 /var/lib/foton/foton.db ".backup /var/lib/foton/backup/foton-$(date +%u).db" 2>/dev/null \
  || cp /var/lib/foton/foton.db "/var/lib/foton/backup/foton-$(date +%u).db"
BKP
sudo chmod +x /usr/local/bin/foton-backup
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq sqlite3 >/dev/null 2>&1 || true
sudo tee /etc/systemd/system/foton-backup.service >/dev/null <<'B1'
[Unit]
Description=Foton backup do banco
[Service]
Type=oneshot
ExecStart=/usr/local/bin/foton-backup
B1
sudo tee /etc/systemd/system/foton-backup.timer >/dev/null <<'B2'
[Unit]
Description=Foton backup diario
[Timer]
OnCalendar=daily
Persistent=true
[Install]
WantedBy=timers.target
B2
sudo systemctl enable -q --now foton-backup.timer
sudo /usr/local/bin/foton-backup
echo "backup diario do banco: ok"

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

# 7) auto-update: a VM busca a versao nova sozinha (a cada 2 min) e reinicia se mudou.
#    Sem isso, cada correcao exigiria SSH manual pelo Cloud Shell.
sudo git config --global --add safe.directory /opt/foton 2>/dev/null || true
sudo tee /usr/local/bin/foton-update >/dev/null <<'UPD'
#!/usr/bin/env bash
# roda como root: o git recusa repo de outro dono sem safe.directory
export HOME=/root
git config --global --add safe.directory /opt/foton 2>/dev/null || true
cd /opt/foton || exit 0
ANTES=$(git rev-parse HEAD 2>/dev/null || echo none)
git fetch -q origin main 2>/dev/null || { logger -t foton "fetch falhou"; exit 0; }
git reset -q --hard origin/main 2>/dev/null || exit 0
DEPOIS=$(git rev-parse HEAD 2>/dev/null || echo none)
if [ "$ANTES" != "$DEPOIS" ]; then
  chown -R ubuntu:ubuntu /opt/foton 2>/dev/null || true
  /opt/foton/venv/bin/pip install -q -r /opt/foton/app/test_rig/requirements.txt 2>/dev/null || true
  systemctl restart foton
  logger -t foton "atualizado: ${ANTES:0:7} -> ${DEPOIS:0:7}"
fi
UPD
sudo chmod +x /usr/local/bin/foton-update
sudo tee /etc/systemd/system/foton-update.service >/dev/null <<'U1'
[Unit]
Description=Foton auto-update
[Service]
Type=oneshot
ExecStart=/usr/local/bin/foton-update
U1
sudo tee /etc/systemd/system/foton-update.timer >/dev/null <<'U2'
[Unit]
Description=Foton auto-update a cada 2 min
[Timer]
OnBootSec=2min
OnUnitActiveSec=2min
[Install]
WantedBy=timers.target
U2
sudo systemctl daemon-reload && sudo systemctl enable -q --now foton-update.timer
echo "auto-update (a cada 2min): ok"

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
