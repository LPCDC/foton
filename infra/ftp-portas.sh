#!/usr/bin/env bash
# Libera as portas do FTP da camera (na VM). A Security List da Oracle precisa
# do mesmo — o script principal ja cuidou de 22/80/443; aqui vao 2121 e passivas.
set -euo pipefail
sudo iptables -I INPUT 5 -p tcp --dport 2121 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -p tcp --dport 30000:30020 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save >/dev/null 2>&1 || true
echo "firewall da VM (2121 + passivas): ok"
mkdir -p /var/lib/foton/ftp && sudo chown -R ubuntu:ubuntu /var/lib/foton/ftp
sudo systemctl restart foton && sleep 25
curl -s localhost:8000/health; echo
journalctl -u foton -n 20 --no-pager 2>/dev/null | grep -o '"stage":"ftp"[^}]*}' | tail -2 || true
