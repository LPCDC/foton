#!/usr/bin/env bash
# Fóton — protege a VM da "recuperação por ociosidade" da Oracle.
# Regra da Oracle: se o 95º percentil de CPU ficar < 10% por 7 dias, ela PODE
# recuperar a instância Always Free. Este job gera carga leve o suficiente para
# ficar acima do limiar, sem desperdício (roda ~6 min por hora, 1 núcleo).
set -euo pipefail

sudo tee /usr/local/bin/foton-keepalive >/dev/null <<'KA'
#!/usr/bin/env bash
# 6 minutos de trabalho leve = ~10% da hora -> sai da faixa de "ocioso"
timeout 360 nice -n 19 bash -c 'while :; do echo "scale=2000;a(1)*4" | bc -l >/dev/null 2>&1 || sleep 1; done' || true
KA
sudo chmod +x /usr/local/bin/foton-keepalive
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq bc >/dev/null 2>&1 || true

sudo tee /etc/systemd/system/foton-keepalive.service >/dev/null <<'K1'
[Unit]
Description=Foton keepalive (evita recuperacao por ociosidade da Oracle)
[Service]
Type=oneshot
Nice=19
ExecStart=/usr/local/bin/foton-keepalive
K1
sudo tee /etc/systemd/system/foton-keepalive.timer >/dev/null <<'K2'
[Unit]
Description=Foton keepalive de hora em hora
[Timer]
OnBootSec=10min
OnUnitActiveSec=1h
[Install]
WantedBy=timers.target
K2
sudo systemctl daemon-reload && sudo systemctl enable -q --now foton-keepalive.timer
echo "protecao contra ociosidade: ok (roda 6min/hora em prioridade minima)"
