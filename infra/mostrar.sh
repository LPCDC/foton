#!/usr/bin/env bash
# Mostra o IP da VM criada e a chave SSH (rodar no Cloud Shell da Oracle)
C=${OCI_TENANCY:-$(oci iam compartment list --all --query 'data[0]."compartment-id"' --raw-output)}
ID=$(oci compute instance list -c "$C" --lifecycle-state RUNNING --query 'data[0].id' --raw-output)
[ -z "$ID" ] && { echo "nenhuma VM rodando"; exit 1; }
NOME=$(oci compute instance get --instance-id "$ID" --query 'data."display-name"' --raw-output)
SHAPE=$(oci compute instance get --instance-id "$ID" --query 'data.shape' --raw-output)
IP=$(oci compute instance list-vnics --instance-id "$ID" --query 'data[0]."public-ip"' --raw-output)
echo "=================================="
echo " VM   : $NOME  ($SHAPE)"
echo " IP   : $IP"
echo "=================================="
