#!/usr/bin/env bash
# Libera o FTP da camera nas DUAS camadas (Cloud Shell da Oracle).
set -euo pipefail
echo "=== liberando FTP da camera ==="
C=${OCI_TENANCY:-$(oci iam compartment list --all --query 'data[0]."compartment-id"' --raw-output)}
VCN=$(oci network vcn list -c "$C" --query 'data[0].id' --raw-output)
SL=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-security-list-id"' --raw-output)

# 1) Security List da nuvem: 22, 80, 443, 2121 (controle) e 30000-30020 (passivas)
oci network security-list update --security-list-id "$SL" --force --ingress-security-rules '[
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":2121,"max":2121}}},
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":30000,"max":30020}}},
 {"protocol":"1","source":"0.0.0.0/0","isStateless":false}]' >/dev/null
echo "  [1/2] firewall da nuvem: ok"

# 2) iptables dentro da VM + reinicia o servico
ssh -o StrictHostKeyChecking=no -i ~/.ssh/foton.key ubuntu@152.67.46.113 \
  'curl -sL https://raw.githubusercontent.com/LPCDC/foton/main/infra/ftp-portas.sh | bash'
echo "  [2/2] firewall da VM: ok"
echo
echo "=== pronto — teste: ftp getfoton.duckdns.org 2121 ==="
