#!/usr/bin/env bash
# Foton — INSTALA a copia diaria do banco PARA FORA DA VM (Cloudflare R2).
#
# O buraco que isto fecha (docs/BACKUP.md, item 1): as 7 copias diarias moram no
# MESMO disco da MESMA VM que o banco. Isso protege contra apagar por engano e
# contra corrupcao do arquivo. Nao protege contra PERDER A MAQUINA — disco,
# instancia Always Free recuperada por inatividade, conta suspensa. Nesse caso o
# banco e as 7 copias somem juntos, e o acervo vai junto. E o unico risco
# irreversivel do sistema.
#
# COMO RODAR (uma vez, no Cloud Shell, com as chaves do R2 em maos):
#   export R2_CONTA=xxxxxxxxxxxxxxxx        # Account ID da Cloudflare
#   export R2_CHAVE=...                     # Access Key ID   (R2 > API tokens)
#   export R2_SEGREDO=...                   # Secret Access Key
#   export R2_BALDE=foton-backup            # crie o bucket no painel do R2 antes
#   ssh -i ~/.ssh/foton.key ubuntu@152.67.46.113 'bash -s' < infra/backup-externo.sh
#
# As chaves NAO ficam neste arquivo nem no repositorio: entram por ambiente e o
# script as grava so na VM, em arquivo 600 lido apenas pelo root (regra da secao 7
# do CLAUDE.md — credencial nunca no codigo).
set -euo pipefail

: "${R2_CONTA:?defina R2_CONTA}"; : "${R2_CHAVE:?defina R2_CHAVE}"
: "${R2_SEGREDO:?defina R2_SEGREDO}"; : "${R2_BALDE:=foton-backup}"

echo "== instalando copia externa do backup =="

# 1) rclone: fala S3 (o R2 e compativel) e nao exige python nem AWS CLI
if ! command -v rclone >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq rclone
fi
echo "rclone: ok"

# 2) credenciais so na VM, so para o root
sudo mkdir -p /root/.config/rclone
sudo tee /root/.config/rclone/rclone.conf >/dev/null <<CFG
[r2]
type = s3
provider = Cloudflare
access_key_id = ${R2_CHAVE}
secret_access_key = ${R2_SEGREDO}
endpoint = https://${R2_CONTA}.r2.cloudflarestorage.com
acl = private
CFG
sudo chmod 600 /root/.config/rclone/rclone.conf
echo "credenciais: gravadas em /root/.config/rclone (600)"

# 3) o envio. Roda DEPOIS do backup local e so manda copia que PRESTA:
#    mandar para fora um arquivo corrompido e trocar um backup ruim por dois.
sudo tee /usr/local/bin/foton-backup-externo >/dev/null <<'ENV'
#!/usr/bin/env bash
set -uo pipefail
BKP=/var/lib/foton/backup
BALDE="$(cat /etc/foton-r2-balde 2>/dev/null || echo foton-backup)"
ULT="$(ls -1t "$BKP"/foton-*.db 2>/dev/null | head -1)"
[ -n "$ULT" ] || { echo "sem backup local para enviar"; exit 1; }

# so envia o que passa no integrity_check do proprio SQLite
INT="$(sqlite3 "$ULT" 'PRAGMA integrity_check;' 2>&1 | head -1)"
if [ "$INT" != "ok" ]; then
  echo "RECUSADO: o backup local nao passa no integrity_check ($INT) — nada enviado"
  exit 1
fi

# nome com a DATA: no R2 nao se sobrescreve por dia da semana. Assim uma corrupcao
# que passe despercebida por uma semana nao come todas as copias (docs/BACKUP.md, item 2).
NOME="foton-$(date +%Y-%m-%d).db"
rclone copyto "$ULT" "r2:${BALDE}/${NOME}" --s3-no-check-bucket --retries 3 \
  && echo "enviado: ${NOME} ($(du -h "$ULT" | cut -f1))" \
  || { echo "FALHA ao enviar para o R2"; exit 1; }

# retencao: 30 dias la fora (o local continua com 7)
rclone delete "r2:${BALDE}" --min-age 30d --retries 2 2>/dev/null || true
ENV
sudo chmod +x /usr/local/bin/foton-backup-externo
echo "${R2_BALDE}" | sudo tee /etc/foton-r2-balde >/dev/null

# 4) timer diario, logo depois do backup local
sudo tee /etc/systemd/system/foton-backup-externo.service >/dev/null <<'B1'
[Unit]
Description=Foton copia do backup para fora da VM (R2)
After=foton-backup.service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/foton-backup-externo
B1
sudo tee /etc/systemd/system/foton-backup-externo.timer >/dev/null <<'B2'
[Unit]
Description=Foton copia externa diaria
[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=900
[Install]
WantedBy=timers.target
B2
sudo systemctl daemon-reload
sudo systemctl enable -q --now foton-backup-externo.timer
echo "timer diario: ok"

# 5) PROVA: envia agora e confere que o arquivo chegou mesmo la
echo
echo "-- enviando agora para provar que funciona --"
sudo /usr/local/bin/foton-backup-externo
echo
echo "-- o que existe no R2 hoje --"
sudo rclone ls "r2:${R2_BALDE}" | tail -5
echo
echo "PRONTO. O acervo agora sobrevive a perda da VM."
echo "Conferir depois:  sudo rclone ls r2:${R2_BALDE}"
