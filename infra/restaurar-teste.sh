#!/usr/bin/env bash
# Foton — PROVA DE RESTAURACAO do backup.
#
# Por que existe: ate aqui o backup era FE. Havia copia diaria, e ninguem nunca
# tinha restaurado nenhuma. Backup que nunca foi restaurado nao e backup — e a
# esperanca de que um dia va funcionar. Este script transforma essa esperanca em
# um numero, e nao toca no banco de producao em momento nenhum.
#
# O que faz: pega a copia mais recente, restaura numa pasta temporaria, roda a
# verificacao de integridade do proprio SQLite, conta as linhas que importam e
# compara com o banco vivo. Sai 0 se o backup presta, 1 se nao presta.
#
#   bash restaurar-teste.sh                  # usa os caminhos de producao
#   BD=/tmp/x.db BKP=/tmp/bkp bash ...       # ou aponta para onde quiser (teste)
#
# Rodar DEPOIS de qualquer mudanca no banco e antes de todo evento grande.
set -u

BD="${BD:-/var/lib/foton/foton.db}"
BKP="${BKP:-/var/lib/foton/backup}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

falhou=0
erro(){ echo "  FALHA  $*"; falhou=1; }
ok(){   echo "  ok     $*"; }

echo "== Prova de restauracao do backup =="
echo "banco vivo : $BD"
echo "backups em : $BKP"

[ -d "$BKP" ] || { erro "a pasta de backup nao existe"; exit 1; }

# a copia mais recente (o rotativo grava foton-1.db .. foton-7.db, um por dia da semana)
ULT="$(ls -1t "$BKP"/foton-*.db 2>/dev/null | head -1)"
[ -n "$ULT" ] || { erro "nenhum arquivo de backup encontrado em $BKP"; exit 1; }

IDADE_S=$(( $(date +%s) - $(date -r "$ULT" +%s) ))
IDADE_H=$(( IDADE_S / 3600 ))
echo "mais recente: $(basename "$ULT") ($(du -h "$ULT" | cut -f1), ${IDADE_H}h atras)"
if [ "$IDADE_H" -gt 48 ]; then
  erro "o backup mais novo tem ${IDADE_H}h — o timer diario pode estar parado"
else
  ok "backup recente (${IDADE_H}h)"
fi

# 1) restaurar para uma copia de trabalho — nunca mexer no original
cp "$ULT" "$TMP/restaurado.db" || { erro "nao consegui copiar o backup"; exit 1; }
ok "restaurado em $TMP/restaurado.db"

# 2) o SQLite conferindo a si mesmo: e o unico veredito que vale sobre corrupcao
INT="$(sqlite3 "$TMP/restaurado.db" 'PRAGMA integrity_check;' 2>&1 | head -1)"
[ "$INT" = "ok" ] && ok "integrity_check: ok" || erro "integrity_check: $INT"

# 3) as tabelas existem e sao legiveis?
for t in photographer event photo guest match contact; do
  n="$(sqlite3 "$TMP/restaurado.db" "SELECT COUNT(*) FROM $t;" 2>&1)"
  case "$n" in
    ''|*[!0-9]*) erro "tabela $t ilegivel no backup: $n" ;;
    *)           ok "$t: $n linhas" ;;
  esac
done

# 4) a foto do backup ABRE? Conferir a contagem nao prova que o BLOB veio inteiro.
#    Le a maior foto e confere que os bytes comecam com a assinatura de JPEG.
FOTO="$(sqlite3 "$TMP/restaurado.db" \
  "SELECT hex(substr(bytes,1,3)) FROM photo ORDER BY LENGTH(bytes) DESC LIMIT 1;" 2>/dev/null)"
if [ -z "$FOTO" ]; then
  echo "  --     nenhuma foto no backup (banco novo?) — nada a conferir"
elif [ "$FOTO" = "FFD8FF" ]; then
  ok "a maior foto do backup e um JPEG valido (assinatura FFD8FF)"
else
  erro "a maior foto do backup nao comeca como JPEG (veio $FOTO) — BLOB possivelmente truncado"
fi

# 5) comparar com o banco vivo: o backup deve estar perto, nunca MAIOR
if [ -f "$BD" ]; then
  vf="$(sqlite3 "$BD" 'SELECT COUNT(*) FROM photo;' 2>/dev/null || echo '?')"
  bf="$(sqlite3 "$TMP/restaurado.db" 'SELECT COUNT(*) FROM photo;' 2>/dev/null || echo '?')"
  echo "  --     fotos: vivo=$vf backup=$bf"
  if [ "$vf" != "?" ] && [ "$bf" != "?" ] && [ "$bf" -gt "$vf" ]; then
    erro "o backup tem MAIS fotos que o banco vivo — alguem apagou dados em producao?"
  fi
else
  echo "  --     banco vivo nao encontrado em $BD (comparacao pulada)"
fi

echo
if [ "$falhou" = "0" ]; then
  echo "BACKUP RESTAURAVEL — provado, nao presumido."
else
  echo "BACKUP NAO CONFIAVEL. Nao rode um evento grande antes de resolver."
fi
exit "$falhou"
