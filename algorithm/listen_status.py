from azure.iot.device import IoTHubDeviceClient
import os
def recieve_from_cloud():

    CONNECTION_STRING = os.getenv("cs")
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    while True:
        try:
            print("Waiting for device registeration status...")
            MESSAGE = CLIENT.receive_message()
            CREDENTIALS = str(MESSAGE.data).split('b')[1]
            if '{"status":"device_initialized"}' in CREDENTIALS:
                print("\nStarting module configuration..")
                print("Data: {}".format(str(MESSAGE.data)))
                return
        except: continue 

def main():
    recieve_from_cloud()