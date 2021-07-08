from azure.iot.device import IoTHubDeviceClient
from subprocess import check_output
from uuid import getnode as get_mac
import json

def recieve_from_cloud():

    CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;DeviceId="+get_mac_and_key()[0]+";SharedAccessKey="+get_mac_and_key()[1]
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    while True:
        #try:
            MESSAGE = CLIENT.receive_message()
            CREDENTIALS = str(MESSAGE.data).split('b')[1]
            if 'ssid' in CREDENTIALS and 'password' in CREDENTIALS:
                print("\nRequest has made to change WIFI Credentials:")
                print("Data: {}".format(str(MESSAGE.data)))
                dict_ = json.loads(CREDENTIALS.replace("'",'"')[1:-1])
                with open("/etc/netplan/50-cloud-init.yaml", "w") as f:
                    f.write(get_yaml(dict_['ssid'],dict_['password']))
                with open("50-cloud-init.yaml", "w") as f:
                    f.write(get_yaml(dict_['ssid'],dict_['password']))
                check_output(["netplan","generate"])
                check_output(["netplan","apply"])
                
        #except: continue 


def get_yaml(username, password):
        yaml = \
        'network: \n' + \
        '    ethernets: \n' + \
        '        eth0: \n' + \
        '            dhcp4: true \n' + \
        '            optional: true \n' + \
        '    version: 2 \n' + \
        '    wifis: \n' + \
        '        wlan0: \n' + \
        '            dhcp4: true \n' + \
        '            optional: true \n' + \
        '            access-points: \n' + \
        '                "'+username+'": \n' + \
        '                    password: "'+password+'" \n' 

        return yaml

if __name__=='__main__':
    recieve_from_cloud()