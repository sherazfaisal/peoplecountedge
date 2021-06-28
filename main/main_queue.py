import cv2
import time
import json
import imutils
import numpy as np
import datetime
import threading
from six.moves import input
from queue import Queue
from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device import MethodResponse

from imutils.video import FPS 
from imutils.video import VideoStream
from imutils.video import WebcamVideoStream
from imutils.video import FileVideoStream

#----------------------- SSD_INITIALIZATIONS ----------------------#
PROTOTXT_PATH = "./models/SSD_MobileNet_prototxt.txt"
MODEL_PATH = "./models/SSD_MobileNet.caffemodel"
CONFIDENCE_THRESHOLD = 0.7

#--------------------- LIVESTREAM_INITIALIZATIONS------------------#
ENABLE_PERSON_COUNT = True
ENABLE_VEHICLE_COUNT = False
ENABLE_ANIMAL_COUNT = False
DEFAULT_CAMERA_SOURCE = "http://192.168.2.131:8080/video"
CAMERA_SOURCE = "http://192.168.2.131:8080/video"#"http://192.168.137.32:8080/video"#"./test_videos/animals.mp4"
RESTART_SOURCE_AFTER = 30*30*0 # restart loading video source after 2 minutes of exit
TOTAL_FRAMES = 0
BUFFER_SIZE = 60
FRAMES_TO_SKIP = 20

#------------------------ IOT-HUB INITIALIZATION -------------------- #
RECIEVE_C2D_MESSAGES = True
CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;DeviceId=edge-test-device;SharedAccessKey=yOlOAk/OBHLX3Ty2cwGxJ1+KxGxc+uTqKBMTgqotorg="
DEVICE_ID = "edge-test-device"
SEND_COUNTER_TO_IOT_HUB = True
#TEXT_TO_SEND = ""
SEND_AFTER_FRAMES = 30*0 # After 4 seconds

def livestream():

    global TOTAL_FRAMES, CAMERA_SOURCE, VS, Q
    Q = Queue(maxsize = 1000)
    if SEND_COUNTER_TO_IOT_HUB:
        message_sender_thread = threading.Thread(target=send_to_iot_hub, args=())
        message_sender_thread.daemon = True
        message_sender_thread.start()

    if RECIEVE_C2D_MESSAGES:
        message_listener_thread = threading.Thread(target=recieve_from_cloud, args=())
        message_listener_thread.daemon = True
        message_listener_thread.start()
        with open('video_source.json','r') as json_file:
            CAMERA_SOURCE = json.load(json_file)['source']

    if not((ENABLE_PERSON_COUNT or ENABLE_ANIMAL_COUNT or ENABLE_VEHICLE_COUNT)):
        print('Please enable only one of the following modes. \n 1. PERSON_COUNT \n 2. VEHICLE_COUNT \n 3. ANIMAL_COUNT')
        return
    nn, labels = load_SSD()
    # Initializing a queue
    colors = np.random.uniform(0, 255, size=(len(labels["all_labels"]), 3))
    print('[Status] Starting Video Stream...')
    VS = start_camera_source()
    while True:
        try:
            frame = VS.read()
            frame = imutils.resize(frame, width=600)
            TOTAL_FRAMES+=1
            if (TOTAL_FRAMES % (FRAMES_TO_SKIP+1)) == 0:
                # Process your frame here using algorithm
                blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
                #Passing Blob through network to detect and predict
                nn.setInput(blob)
                detections = nn.forward()
                counter = show_label_on_frame_and_counter(detections, frame , labels , colors)
            #else:
            #    try: show_label_on_frame_and_counter(detections, frame , labels, colors)
            #    except: pass
        except:
            TOTAL_FRAMES+=1 
            if TOTAL_FRAMES%(RESTART_SOURCE_AFTER+1)==0:
                VS.stop()
                VS = start_camera_source()
        if RECIEVE_C2D_MESSAGES: 
            with open('video_source.json','r') as json_file:
                source = json.load(json_file)
                source = source['source']
            if type(source) not in [str,int]:
                source = source.decode("utf-8") 
            if type(source)==str and source.isnumeric(): source = int(source)
            if source!=CAMERA_SOURCE:
                VS.stop()
                DEFAULT_CAMERA_SOURCE = CAMERA_SOURCE
                CAMERA_SOURCE = source
                VS = start_camera_source()
    cv2.destroyAllWindows()
    VS.stop()

def load_SSD():

    #Initialize Objects and corresponding colors which the model can detect
    all_labels = ["background", "aeroplane", "bicycle", "bird", 
    "boat","bottle", "bus", "car", "cat", "chair", "cow", 
    "diningtable","dog", "horse", "motorbike", "person", "pottedplant", 
    "sheep","sofa", "train", "tvmonitor"]

    animal_labels = ['bird','cat','cow','dog','horse','sheep']
    vehicle_labels = ['bicycle','boat','bus','car','motorbike','train']

    labels = {"all_labels":all_labels,"animal_labels":animal_labels, "vehicle_labels":vehicle_labels}

    #Loading Caffe Model
    print('[Status] Loading Model...')
    nn = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, MODEL_PATH)

    return nn,labels

def show_label_on_frame_and_counter(detections, frame, labels, colors):

    global TOTAL_FRAMES, TEXT_TO_SEND, CAMERA_SOURCE, Q
    
    (h, w) = frame.shape[:2]
    person_count = 0
    animal_count = 0
    vehicle_count = 0

    #Loop over the detections
    #idxs = [] 
    for i in np.arange(0, detections.shape[2]):

        #Extracting the confidence of predictions
        confidence = detections[0, 0, i, 2]
       
        idx = int(detections[0, 0, i, 1])
        #idxs.append(idx)
        condition_ = None
        if ENABLE_PERSON_COUNT: condition_ = condition_ or labels["all_labels"][idx] == 'person' if condition_!=None else labels["all_labels"][idx] == 'person' 
        if ENABLE_ANIMAL_COUNT: condition_ = condition_ or labels["all_labels"][idx] in labels["animal_labels"] if condition_!=None else labels["all_labels"][idx] in labels["animal_labels"]
        if ENABLE_VEHICLE_COUNT: condition_ = condition_ or labels["all_labels"][idx] in labels["vehicle_labels"] if condition_!=None else labels["all_labels"][idx] in labels["vehicle_labels"] 
        #Filtering out weak predictions
        if condition_ and confidence>CONFIDENCE_THRESHOLD:

            if ENABLE_PERSON_COUNT and labels["all_labels"][idx] == 'person': person_count+=1 
            if ENABLE_ANIMAL_COUNT and labels["all_labels"][idx] in labels["animal_labels"]: animal_count+=1 
            if ENABLE_VEHICLE_COUNT and labels["all_labels"][idx] in labels["vehicle_labels"]: vehicle_count+=1
    now = datetime.datetime.now()
    time_ = now.strftime("%H:%M:%S") 
    date_ = now.strftime("%Y-%m-%d")       
    if ENABLE_PERSON_COUNT and SEND_COUNTER_TO_IOT_HUB: Q.put({"id":DEVICE_ID,"d":date_,"t":time_,"pc":str(person_count),"ip":str(CAMERA_SOURCE)})
    if ENABLE_ANIMAL_COUNT and SEND_COUNTER_TO_IOT_HUB: Q.put({"id":DEVICE_ID,"d":date_,"t":time_,"pc":str(animal_count),"ip":str(CAMERA_SOURCE)})
    if ENABLE_VEHICLE_COUNT and SEND_COUNTER_TO_IOT_HUB: Q.put({"id":DEVICE_ID,"d":date_,"t":time_,"pc":str(vehicle_count),"ip":str(CAMERA_SOURCE)})
        
    return [person_count, animal_count, vehicle_count]

def start_camera_source():

    global CAMERA_SOURCE, DEFAULT_CAMERA_SOURCE, VS, TEXT_TO_SEND, Q
    if type(CAMERA_SOURCE) not in [str,int]:
        CAMERA_SOURCE = CAMERA_SOURCE.decode("utf-8") 
    if type(CAMERA_SOURCE)==str and CAMERA_SOURCE.isnumeric(): CAMERA_SOURCE = int(CAMERA_SOURCE)
    if type(CAMERA_SOURCE) == int or ('.mp4' or '.avi') not in CAMERA_SOURCE:
        VS = WebcamVideoStream(src=CAMERA_SOURCE).start()
    else: VS = FileVideoStream(CAMERA_SOURCE).start()
    now = datetime.datetime.now()
    time_ = now.strftime("%H:%M:%S") 
    date_ = now.strftime("%Y-%m-%d")
    frame = VS.read()
    if frame is None:
        text = "Failed to access "+str(CAMERA_SOURCE)+" Going back to the previous camera Source if available"
        for i in range(3):
            Q.put({"id":DEVICE_ID,"d":date_,"t":time_,"message":str(text)})
        if type(DEFAULT_CAMERA_SOURCE) not in [str,int]:
            DEFAULT_CAMERA_SOURCE = DEFAULT_CAMERA_SOURCE.decode("utf-8") 
        if type(DEFAULT_CAMERA_SOURCE) == str and DEFAULT_CAMERA_SOURCE.isnumeric(): DEFAULT_CAMERA_SOURCE = int(CAMERA_SOURCE)
        if type(DEFAULT_CAMERA_SOURCE) == int or ('.mp4' or '.avi') not in DEFAULT_CAMERA_SOURCE:
            VS = WebcamVideoStream(src=DEFAULT_CAMERA_SOURCE).start()
        else: VS = FileVideoStream(DEFAULT_CAMERA_SOURCE).start()
        time.sleep(5)
    else:
        text = "Accessing "+str(CAMERA_SOURCE)
        for i in range(3):
            Q.put({"id":DEVICE_ID,"d":date_,"t":time_,"message":str(text)})         
        time.sleep(5)
    return VS

def send_to_iot_hub():

    CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;DeviceId=edge-test-device;SharedAccessKey=yOlOAk/OBHLX3Ty2cwGxJ1+KxGxc+uTqKBMTgqotorg="
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    while True:
        try:
            global Q, TOTAL_FRAMES
            if (TOTAL_FRAMES % (SEND_AFTER_FRAMES+1)==0): 
                text = str(Q.get())
                message = Message(text)
                CLIENT.send_message(message)
                print ("Message '{}' successfully sent".format(text))
        except: continue
    while True:
        time.sleep(1000)

def recieve_from_cloud():

    CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;DeviceId=edge-test-device;SharedAccessKey=yOlOAk/OBHLX3Ty2cwGxJ1+KxGxc+uTqKBMTgqotorg="
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    while True:
        try:
            MESSAGE = CLIENT.receive_message()
            CAMERA_SOURCE = str(MESSAGE.data).split('b')[1].split("'")[1]
            print("\nMessage received:")
            print("Data: {}".format(str(MESSAGE.data)))
            SOURCE = str(MESSAGE.data).split('b')[1].split("'")[1]
            source = {"source":str(MESSAGE.data).split('b')[1].split("'")[1]}
            with open('video_source.json', 'w') as outfile:
                json.dump(source, outfile)
            print(MESSAGE.data)

        except: continue 
    while True:
        time.sleep(1000)

if __name__ == "__main__":
    livestream()

