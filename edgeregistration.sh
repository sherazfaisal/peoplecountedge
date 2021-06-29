#!/bin/bash
touch config.txt
echo "# DPS provisioning with symmetric key">>config.txt
echo "[provisioning]">>config.txt
echo "source = \"dps\"">>config.txt
echo "global_endpoint = \"https://global.azure-devices-provisioning.net\"">>config.txt
SCOPE_ID="0ne00319FB9"
echo "id_scope = \"$SCOPE_ID\"">>config.txt
echo "[provisioning.attestation]">>config.txt
echo "method = \"symmetric_key\"">>config.txt
REG_ID1=$(cat /sys/class/net/eth0/address | sed s/://g)
REG_ID=$REG_ID1
echo "registration_id = \"$REG_ID\"">>config.txt
KEY=HVGPqFvhOBufYS9ZsP0DlXaqFWYLOKBCNjnu0ftAkZ0/zX3CTa27XD6reUd5HIWMqcEkUMrYDsKxKD86GBwRsQ==
keybytes=$(echo $KEY | base64 --decode | xxd -p -u -c 1000)
id=$(echo -n $REG_ID | openssl sha256 -mac HMAC -macopt hexkey:$keybytes -binary | base64)
echo "symmetric_key = { value= \"$id\" }">>config.txt
sudo cp config.txt /etc/aziot/config.toml
sudo iotedge config apply
exit 0
