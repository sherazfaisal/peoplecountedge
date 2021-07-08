from azure.iot.hub import IoTHubRegistryManager

CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=lp5GJ78EcbwUWcwi5Z5McEGdE4lpHZIReZOVdqnzLjQ="
DEVICE_ID = "edge-test-device" ## Change device id for different devices

def iothub_send_c2d(value):
    try:
        # Create IoTHubRegistryManager
        registry_manager = IoTHubRegistryManager(CONNECTION_STRING)

        print('Sending to Device with ID {}'.format(DEVICE_ID))

        registry_manager.send_c2d_message(DEVICE_ID, value)

    except Exception as ex:
        print ( "Unexpected error {0}" % ex )
        return
    except KeyboardInterrupt:
        print ( "IoT Hub C2D Messaging service sample stopped" )

if __name__=='__main__':
    text = '{"status":"device_initialized"}'
    iothub_send_c2d(text)