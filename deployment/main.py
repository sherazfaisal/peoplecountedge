from subprocess import check_output
import json
json_ = check_output(["az","iot","dps","registration", "list","--dps-name","IoT-dps-labs","-g","rg-iothw-labs","--enrollment-id","peoplecount"], shell=True)
json_ = str(json_).replace('\'', '\"').replace('\\n', '').replace('\\r','').replace('[','').replace(']','').replace("'","").replace("\\","").replace("\\t", "").replace("    ","").replace("  ","")
json_ = [element+"}" for element in json_.split("},")]

all_devices = []
for element in json_:
    try: all_devices.append(json.loads(element))
    except: 
        try: all_devices.append(json.loads(element[2:]))
        except: 
            try: all_devices.append(json.loads(element[:-1]))
            except: all_devices.append(json.loads(element[:-2]))

all_device_ids = [device["registrationId"] for device in all_devices]

for device_id in all_device_ids:
    try: 
        output = check_output(["az","iot","hub","module-twin","show","-n","IoTHWLabs","-d",device_id,"-m","$edgeAgent","--query","properties.reported.modules"], shell=True)
        if "pplcountSSD" not in str(output) and str(output)[2]=='{': 
            check_output(["az","iot","edge","set-modules", "--hub-name","IoTHWLabs","--device-id",device_id,"--content","deployment.json"], shell=True)
            print("edge device with id ", device_id, " deployed successfully!")
    except: pass
print("Deployment Completed")