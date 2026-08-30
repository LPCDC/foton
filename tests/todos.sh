#!/usr/bin/env bash
# Roda TUDO e FALHA se qualquer suite falhar. Use antes de todo git push:
#   bash tests/todos.sh && git push origin main
set -e
cd "$(dirname "$0")/.."
falhou=0
for t in test_front test_autorizacao test_ftp_camera test_logo; do
  printf "  %-18s " "$t"
  if saida=$(python "tests/$t.py" 2>&1); then
    printf "%s ok\n" "$(printf '%s' "$saida" | grep -c '  ok  ')"
  else
    echo "FALHOU"
    printf '%s\n' "$saida" | grep -E "FALHA|Error" | head -5
    falhou=1
  fi
done
[ "$falhou" = "0" ] || { echo; echo "NAO SUBA: alguma suite falhou."; exit 1; }
echo; echo "tudo verde — pode subir"
