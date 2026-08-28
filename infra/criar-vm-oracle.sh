#!/usr/bin/env bash
# Fóton — cria a VM Always Free na Oracle (rodar no CLOUD SHELL da Oracle).
# O Cloud Shell já vem autenticado: não precisa configurar chave nem senha.
set -euo pipefail

echo "=== Fóton · criando a VM Always Free ==="

# 1) tenancy (compartment raiz) — o Cloud Shell já expõe
C=${OCI_TENANCY:-$(oci iam compartment list --all --query 'data[0]."compartment-id"' --raw-output 2>/dev/null)}
[ -z "${C:-}" ] && { echo "!! não achei o tenancy"; exit 1; }
echo "compartment: ${C:0:28}..."

# 2) imagem Ubuntu 24.04 para ARM (aarch64)
IMG=$(oci compute image list -c "$C" --operating-system "Canonical Ubuntu" \
      --operating-system-version "24.04" --shape VM.Standard.A1.Flex \
      --sort-by TIMECREATED --query 'data[0].id' --raw-output)
[ -z "${IMG:-}" ] && { echo "!! não achei imagem Ubuntu ARM"; exit 1; }
echo "imagem Ubuntu 24.04 ARM: ok"

# 3) rede: usa a VCN existente ou cria uma pública
VCN=$(oci network vcn list -c "$C" --query 'data[0].id' --raw-output 2>/dev/null || true)
if [ -z "${VCN:-}" ] || [ "$VCN" = "null" ]; then
  echo "criando rede..."
  VCN=$(oci network vcn create -c "$C" --display-name foton-vcn --cidr-blocks '["10.0.0.0/16"]' \
        --query 'data.id' --raw-output); sleep 5
  IGW=$(oci network internet-gateway create -c "$C" --vcn-id "$VCN" --is-enabled true \
        --display-name foton-igw --query 'data.id' --raw-output); sleep 3
  RT=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-route-table-id"' --raw-output)
  oci network route-table update --rt-id "$RT" --force \
    --route-rules "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR_BLOCK\",\"networkEntityId\":\"$IGW\"}]" >/dev/null
  SUB=$(oci network subnet create -c "$C" --vcn-id "$VCN" --display-name foton-sub \
        --cidr-block 10.0.1.0/24 --query 'data.id' --raw-output); sleep 5
else
  SUB=$(oci network subnet list -c "$C" --vcn-id "$VCN" --query 'data[0].id' --raw-output)
fi
echo "rede: ok"

# 4) libera as portas 22 (ssh), 80 e 443 (site) na Security List
SL=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-security-list-id"' --raw-output)
oci network security-list update --security-list-id "$SL" --force --ingress-security-rules '[
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},
 {"protocol":"6","source":"0.0.0.0/0","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},
 {"protocol":"1","source":"0.0.0.0/0","isStateless":false}]' >/dev/null
echo "firewall da nuvem (22/80/443): ok"

# 5) chave SSH (RSA — o Cloud Shell roda em modo FIPS e recusa ed25519)
[ -f ~/.ssh/foton.key ] || ssh-keygen -t rsa -b 4096 -f ~/.ssh/foton.key -N "" -C foton >/dev/null
echo "chave SSH: ok"

# 6) cria a instância — tenta 2/12, depois 1/6 se faltar capacidade
criar () {
  oci compute instance launch -c "$C" --display-name foton-server \
    --image-id "$IMG" --shape VM.Standard.A1.Flex \
    --shape-config "{\"ocpus\":$1,\"memoryInGBs\":$2}" \
    --subnet-id "$SUB" --assign-public-ip true \
    --availability-domain "$AD" \
    --ssh-authorized-keys-file ~/.ssh/foton.key.pub \
    --wait-for-state RUNNING --query 'data.id' --raw-output 2>/dev/null
}
OK=""
for AD in $(oci iam availability-domain list -c "$C" --query 'data[].name' --raw-output | tr -d '[",]'); do
  for CFG in "2 12" "1 6"; do
    set -- $CFG
    echo "tentando ${1} OCPU / ${2}GB em $AD ..."
    if ID=$(criar "$1" "$2"); then OK="$ID"; break 2; fi
  done
done
[ -z "$OK" ] && { echo; echo "!! SEM CAPACIDADE ARM agora (comum em São Paulo)."; echo "   Rode este script de novo mais tarde — o resto já está configurado."; exit 2; }

IP=$(oci compute instance list-vnics --instance-id "$OK" --query 'data[0]."public-ip"' --raw-output)
echo
echo "=========================================="
echo " VM CRIADA COM SUCESSO"
echo " IP público : $IP"
echo "=========================================="
echo
echo ">>> COPIE A CHAVE PRIVADA ABAIXO (tudo, incluindo BEGIN/END) <<<"
echo
cat ~/.ssh/foton.key
