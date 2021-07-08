KEY=HVGPqFvhOBufYS9ZsP0DlXaqFWYLOKBCNjnu0ftAkZ0/zX3CTa27XD6reUd5HIWMqcEkUMrYDsK$
keybytes=$(echo $KEY | base64 --decode | xxd -p -u -c 1000)
id=$(echo -n $(cat /sys/class/net/wlan0/address | sed s/://g) | openssl sha256 $
echo $id
