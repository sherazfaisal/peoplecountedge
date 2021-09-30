from io import TextIOWrapper
import json
from os import path
import os
import pathlib
import logging
import time
from builtins import input
import ssl
import http.client
import urllib.request
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod, CloudToDeviceMethodResult

def get_device_id():
    return os.getenv('id')

def read_url(url):
    url = url.replace(path.sep, '/')
    resp = urllib.request.urlopen(url, context=ssl._create_unverified_context())
    return resp.read()

class LivePipelineManager:
    
    def __init__(self):
        config_data = pathlib.Path('appsettings.json').read_text()
        config = json.loads(config_data)

        self.device_id = config['deviceId']
        self.module_id = config['moduleId']
        self.api_version = '1.0'

        self.registry_manager = IoTHubRegistryManager(config['IoThubConnectionString'])

    def invoke(self, method_name, payload):
        if method_name=='pipelineTopologySet':
            self.pipeline_topology_set(payload)
            return

        if method_name=='WaitForInput':
            print(payload['message'])
            input()
            return

        self.invoke_module_method(method_name, payload)

    def invoke_module_method(self, method_name, payload):
        # make sure '@apiVersion' has been set
        payload['@apiVersion'] = self.api_version

        module_method = CloudToDeviceMethod(
            method_name=method_name,
            payload=payload,
            response_timeout_in_seconds=30)
        
        print("\n-----------------------  Request: %s  --------------------------------------------------\n" % method_name)
        print(json.dumps(payload, indent=4))
        
        resp = self.registry_manager.invoke_device_module_method(self.device_id, self.module_id, module_method)
        
        print("\n---------------  Response: %s - Status: %s  ---------------\n" % (method_name, resp.status))

        if resp.payload is not None:
            print(json.dumps(resp.payload, indent=4))

    def pipeline_topology_set(self, op_parameters):
        if op_parameters is None:
            raise Exception('Operation parameters missing')

        if op_parameters.get('pipelineTopologyUrl') is not None:
            topology_json = read_url(op_parameters['pipelineTopologyUrl'])
        elif op_parameters.get('pipelineTopologyFile') is not None:
            topology_path = pathlib.Path(__file__).parent.joinpath(op_parameters['pipelineTopologyFile'])
            topology_json = topology_path.read_text()
        else:
            raise Exception('Neither pipelineTopologyUrl nor pipelineTopologyFile is specified')

        topology = json.loads(topology_json)

        self.invoke_module_method('pipelineTopologySet', topology)

def start_pipeline():
    manager = LivePipelineManager()
    
    operations_data_json = pathlib.Path('operations.json').read_text()
    operations_data = json.loads(operations_data_json)
    operations_data['operations'] = operations_data['operations'][:6] 

    for operation in operations_data['operations']:
        manager.invoke(operation['opName'], operation['opParams'])

def remove_pipeline():
    manager = LivePipelineManager()
    
    operations_data_json = pathlib.Path('operations.json').read_text()
    operations_data = json.loads(operations_data_json)
    operations_data['operations'] = operations_data['operations'][6:] 

    for operation in operations_data['operations']:
        manager.invoke(operation['opName'], operation['opParams'])

def activate_pipeline(name):
    device_id = get_device_id()
    # ----------- Set Device ID ------------- #
    appsettings = json.loads(pathlib.Path('appsettings.json').read_text())
    appsettings['deviceId'] = device_id
    with open('appsettings.json', 'w', encoding='utf-8') as f:
        json.dump(appsettings, f, ensure_ascii=False, indent=4)
    # ----------- Set Video Source and topology name----------- #
    topology = device_id+"-"+name
    operations = json.loads(pathlib.Path('operations.json').read_text())
    operations['operations'][3]["opParams"]['properties']['parameters'][0]['value'] = json.loads(pathlib.Path('video_source.json').read_text())[name+'_url']
    operations['operations'][3]["opParams"]['name'] = topology
    operations['operations'][4]["opParams"]['name'] = topology
    operations['operations'][7]["opParams"]['name'] = topology
    operations['operations'][8]["opParams"]['name'] = topology
    operations['operations'][10]["opParams"]['name'] = topology
    operations['operations'][3]['opParams']['properties']['topologyName'] = topology
    with open('operations.json', 'w', encoding='utf-8') as f:
        json.dump(operations, f, ensure_ascii=False, indent=4)
    
    # ----------- Set video Name ------------- #
    video_name = device_id+"-"+name
    temp = topology
    topology = json.loads(pathlib.Path("topology_"+name+".json").read_text())
    topology['name'] = temp
    topology['properties']['sinks'][0]['videoCreationProperties']['title'] = video_name
    topology['properties']['sinks'][0]['videoName'] = video_name
    with open('topology.json', 'w', encoding='utf-8') as f:
        json.dump(topology, f, ensure_ascii=False, indent=4)
    manager = LivePipelineManager()

    operations_data_json = pathlib.Path('operations.json').read_text()
    operations_data = json.loads(operations_data_json)
    operations_data['operations'] = [operations_data['operations'][4]] 

    for operation in operations_data['operations']:
        manager.invoke(operation['opName'], operation['opParams'])

def deactivate_pipeline(name):

    device_id = get_device_id()
    # ----------- Set Device ID ------------- #
    appsettings = json.loads(pathlib.Path('appsettings.json').read_text())
    appsettings['deviceId'] = device_id
    with open('appsettings.json', 'w', encoding='utf-8') as f:
        json.dump(appsettings, f, ensure_ascii=False, indent=4)
    # ----------- Set Video Source and topology name----------- #
    topology = device_id+"-"+name
    operations = json.loads(pathlib.Path('operations.json').read_text())
    operations['operations'][3]["opParams"]['properties']['parameters'][0]['value'] = json.loads(pathlib.Path('video_source.json').read_text())[name+'_url']
    operations['operations'][3]["opParams"]['name'] = topology
    operations['operations'][4]["opParams"]['name'] = topology
    operations['operations'][7]["opParams"]['name'] = topology
    operations['operations'][8]["opParams"]['name'] = topology
    operations['operations'][10]["opParams"]['name'] = topology
    operations['operations'][3]['opParams']['properties']['topologyName'] = topology
    with open('operations.json', 'w', encoding='utf-8') as f:
        json.dump(operations, f, ensure_ascii=False, indent=4)
    
    # ----------- Set video Name ------------- #
    video_name = device_id+"-"+name
    temp = topology
    topology = json.loads(pathlib.Path("topology_"+name+".json").read_text())
    topology['name'] = temp
    topology['properties']['sinks'][0]['videoCreationProperties']['title'] = video_name
    topology['properties']['sinks'][0]['videoName'] = video_name
    with open('topology.json', 'w', encoding='utf-8') as f:
        json.dump(topology, f, ensure_ascii=False, indent=4)
    manager = LivePipelineManager()

    operations_data_json = pathlib.Path('operations.json').read_text()
    operations_data = json.loads(operations_data_json)
    operations_data['operations'] = [operations_data['operations'][7]] 

    for operation in operations_data['operations']:
        manager.invoke(operation['opName'], operation['opParams'])

def remove_pipelines():
    try:
        remove_pipeline()
        return
    except: remove_pipelines()

def run_pipeline():
    try:
        start_pipeline()
        return
    except: run_pipeline()

if __name__ == '__main__':
    temp_source = None
    start_event = None
    while True:
        try: actual_source = json.loads(pathlib.Path('video_source.json').read_text())
        except: 
            time.sleep(5)
            actual_source = json.loads(pathlib.Path('video_source.json').read_text())

        if temp_source != actual_source:
            temp_source = json.loads(pathlib.Path('video_source.json').read_text())
            for name in ['livestream', 'event-based']:
                device_id = get_device_id()
                # ----------- Set Device ID ------------- #
                appsettings = json.loads(pathlib.Path('appsettings.json').read_text())
                appsettings['deviceId'] = device_id
                with open('appsettings.json', 'w', encoding='utf-8') as f:
                    json.dump(appsettings, f, ensure_ascii=False, indent=4)
                # ----------- Set Video Source and topology name----------- #
                topology = device_id+"-"+name+"-"+actual_source['name_livestream']
                operations = json.loads(pathlib.Path('operations.json').read_text())
                operations['operations'][3]["opParams"]['properties']['parameters'][0]['value'] = json.loads(pathlib.Path('video_source.json').read_text())[name+'_url']
                operations['operations'][3]["opParams"]['name'] = topology
                operations['operations'][4]["opParams"]['name'] = topology
                operations['operations'][7]["opParams"]['name'] = topology
                operations['operations'][8]["opParams"]['name'] = topology
                operations['operations'][10]["opParams"]['name'] = topology
                operations['operations'][3]['opParams']['properties']['topologyName'] = topology
                with open('operations.json', 'w', encoding='utf-8') as f:
                    json.dump(operations, f, ensure_ascii=False, indent=4)
                
                # ----------- Set video Name ------------- #
                video_name = device_id+"-"+name+"-"+actual_source['name_livestream']
                temp = topology
                topology = json.loads(pathlib.Path("topology_"+name+".json").read_text())
                topology['name'] = temp
                topology['properties']['sinks'][0]['videoCreationProperties']['title'] = video_name
                topology['properties']['sinks'][0]['videoName'] = video_name
                with open('topology.json', 'w', encoding='utf-8') as f:
                    json.dump(topology, f, ensure_ascii=False, indent=4)
                
                manager = LivePipelineManager()
                remove_pipelines()
                if temp_source[name] == "True": run_pipeline()
        
        if bool(actual_source['event-based-stream']): 
            if start_event == None: 
                start_event = open('start-event.txt').read() if open('start-event.txt').read() in ["True", "False"] else "False"
                if start_event == "True": activate_pipeline('event-based-stream')
                elif start_event == "False": deactivate_pipeline('event-based-stream')
            elif start_event != str(open('start-event.txt').read()) and str(open('start-event.txt').read()) in ["True", "False"]:
                start_event = open('start-event.txt').read()
                if start_event == "True": activate_pipeline('event-based-stream')
                elif start_event == "False": deactivate_pipeline('event-based-stream')