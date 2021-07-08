
from uuid import getnode as get_mac
from subprocess import check_output

def get_mac_and_key():
        mac = hex(get_mac())[2:]
        key = check_output(["bash","reg.sh"])
        key = str(key)[2:-3]
        return mac, key
