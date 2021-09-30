"""
from azure.iot.device import IoTHubDeviceClient, Message
from threading import Thread
import os
import json
class Recieve_C2D_Message():
    def __init__(self,cs):
        self.cs = cs
        self.message = None
        self.camera_source = None

    def receive_message(self):
        while True:
            try: 
                self.client = IoTHubDeviceClient.create_from_connection_string(self.cs)
                self.message = self.client.receive_message(timeout=120)
                self.camera_source = str(self.message.data).split('b')[1].split("'")[1]
                print("\nMessage received:")
                print("Data: {}".format(str(self.message.data)))
                temp = str(self.message.data).split('b')[1].split("'")[1]
                with open('video_source.json','r') as json_file:
                    json_ = json.load(json_file)
                    source = json_['source']
                    zone = json_['zone']
                if temp in ["Geozone", "Default"]: source = {"source": source, "zone": temp}
                else: source = {"source":temp, "zone": zone}
                with open('video_source.json', 'w') as outfile:
                    json.dump(source, outfile)
                self.client.disconnect()
            except: self.client.disconnect()

        while True:
            time.sleep(1000)

    def start(self):
        self.receive_message()





if __name__ == '__main__':
    receive_ = Recieve_C2D_Message("HostName=IoTHWLabs.azure-devices.net;DeviceId=b827eb6fce4e;SharedAccessKey=9+q5mnl79Rcrc/rvvPuoJ5TFWfo7OK2mEtSTFPrwzL4=")
    receive_.start()


from azure.iot.device import IoTHubDeviceClient
from subprocess import check_output
from uuid import getnode as get_mac
import json
import time
def recieve_from_cloud():

    while True:
        #try:
            CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;DeviceId=edge-test-device;SharedAccessKey=yOlOAk/OBHLX3Ty2cwGxJ1+KxGxc+uTqKBMTgqotorg="
            CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)            
            try:
                MESSAGE = CLIENT.receive_message(timeout=60)
                print("..")
                CREDENTIALS = str(MESSAGE.data).split('b')[1]
                camera_source = str(MESSAGE).split('b')[1].split("'")[1]
                print("\nMessage received:")
                print("Data: {}".format(str(MESSAGE)))
                temp = str(MESSAGE).split('b')[1].split("'")[1]
                with open('video_source.json','r') as json_file:
                    json_ = json.load(json_file)
                    source = json_['source']
                    zone = json_['zone']
                if temp in ["Geozone", "Default"]: source = {"source": source, "zone": temp}
                else: source = {"source":temp, "zone": zone}
                with open('video_source.json', 'w') as outfile:
                    json.dump(source, outfile)
                CLIENT.disconnect()
            except:
                print("...")
                CLIENT.disconnect()
            print("....")    
        #except: continue

recieve_from_cloud()

"""

import time
import datetime
from azure.iot.device import IoTHubDeviceClient, MethodResponse
import json
import pathlib
import os
CONNECTION_STRING = os.getenv('cs') #"HostName=IoTHWLabs.azure-devices.net;DeviceId=e45f0121a9fc;SharedAccessKey=bXO1G4/DkDf795WobneLl84352dyWmob7LCLEB20snw="
def create_client():
    # Instantiate the client
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    # Define the handler for method requests
    def method_request_handler(method_request):
        if method_request.name == "videoConfig":
            # Act on the method by rebooting the device
            with open('video_source.json', 'w', encoding='utf-8') as f:
                json.dump(json.loads(method_request.payload), f, ensure_ascii=False, indent=4)
            print("Changing Video Configurations.")

            # Create a method response indicating the method request was resolved
            resp_status = 200
            resp_payload = {"Response": "Successful"}
            method_response = MethodResponse(method_request.request_id, resp_status, resp_payload)
        
        else:
            # Create a method response indicating the method request was for an unknown method
            resp_status = 404
            resp_payload = {"Response": "Unknown method"}
            method_response = MethodResponse(method_request.request_id, resp_status, resp_payload)

        # Send the method response
        client.send_method_response(method_response)

    try:
        # Attach the handler to the client
        client.on_method_request_received = method_request_handler
    except:
        # In the event of failure, clean up
        client.shutdown()

    return client

def main():
    print ("Starting the IoT Hub Python sample...")
    client = create_client()

    print ("Waiting for commands, press Ctrl-C to exit")
    try:
        # Wait for program exit
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        print("IoTHubDeviceClient sample stopped")
    finally:
        # Graceful exit
        print("Shutting down IoT Hub Client")
        client.shutdown()

if __name__ == '__main__':
    main()


