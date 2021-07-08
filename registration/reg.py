from uuid import getnode as get_mac
from subprocess import check_output
mac = hex(get_mac())[2:]
key = check_output(["bash","reg.sh"])
key = str(key)[2:-3]

config = \
'# DPS provisioning with symmetric key \n'+ \
'[provisioning] \n'+ \
'source = "dps" \n'+ \
'global_endpoint = "https://global.azure-devices-provisioning.net" \n'+ \
'id_scope = "0ne00319FB9" \n'+ \
'[provisioning.attestation] \n' + \
'method = "symmetric_key" \n'+ \
'registration_id ="' +str(mac)+'" \n'+ \
'symmetric_key = { value= "'+str(key)+'" } \n'
print(config)
