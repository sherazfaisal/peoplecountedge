from subprocess import check_output
import json
json_ = check_output(["az","iot","dps","registration", "list","--dps-name","IoT-dps-labs","-g","rg-iothw-labs","--enrollment-id","peoplecount"], shell=True)
json_ = str(json_).replace('\'', '\"').replace('\\n', '').replace('\\r','').replace('[','').replace(']','').replace("'","").replace("\\","").replace("\\t", "").replace("    ","").replace("  ","")
token = check_output(["az","acr","login","--name","IotcontLabs","--expose-token"], shell=True)
token = json.loads(token)["accessToken"]
if len(json_.split("},"))>1: 
    json_ = [element+"}" for element in json_.split("},")]
    all_devices = []
    print(json_)
    for element in json_:
        try: all_devices.append(json.loads(element))
        except: 
            try: all_devices.append(json.loads(element[2:]))
            except: 
                try: all_devices.append(json.loads(element[:-1]))
                except:
                    try:
                        all_devices.append(json.loads(element[1:-1]))
                    except: all_devices.append(json.loads(element[:-2]))
else: 
    print(json_)
    all_devices = [json.loads(json_[2:-1])]

all_device_ids = [device["registrationId"] for device in all_devices]

for device_id in all_device_ids:
    try: 
        output = check_output(["az","iot","hub","module-twin","show","-n","IoTHWLabs","-d",device_id,"-m","$edgeAgent","--query","properties.reported.modules"], shell=True)
        if "tflite" not in str(output):
            cs = check_output(["az", "iot", "hub", "device-identity", "connection-string", "show", "--device-id", device_id, "--hub-name", "IoTHWLabs"], shell=True)
            cs = json.loads(cs)["connectionString"]             
            deployment_json = json.loads(str(open('deployment.json' , 'r').read()))
            deployment_json["modulesContent"]["$edgeAgent"]["properties.desired"]["modules"]["peoplecountSSD"]["env"]["cs"]["value"] = str(cs)
            deployment_json["modulesContent"]["$edgeAgent"]["properties.desired"]["modules"]["peoplecountSSD"]["env"]["id"]["value"] = str(device_id)
            deployment_json["modulesContent"]["$edgeAgent"]["properties.desired"]['runtime']['settings']['registryCredentials']['peoplecountSSD']['password'] = str(token)
            with open('temp.json' , 'w') as outfile: json.dump(deployment_json, outfile)
            check_output(["az","iot","edge","set-modules", "--hub-name","IoTHWLabs","--device-id",device_id,"--content","temp.json"], shell=True)
            print("edge device with id ", device_id, " deployed successfully!")
    except: pass
print("Deployment Completed")