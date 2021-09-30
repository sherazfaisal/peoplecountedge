import cv2
import time
import json
import imutils
import os
import numpy as np
import datetime
import threading
from six.moves import input
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
DEFAULT_CAMERA_SOURCE = "http://192.168.2.131:8080/video"
CAMERA_SOURCE = 0#"http://192.168.2.131:8080/video"#"http://192.168.137.32:8080/video"#"./test_videos/animals.mp4"
TOTAL_FRAMES = 0
BUFFER_SIZE = 60
FRAMES_TO_SKIP = 10

#------------------------ IOT-HUB INITIALIZATION -------------------- #
RECIEVE_C2D_MESSAGES = False
CONNECTION_STRING = os.getenv("cs")
DEVICE_ID = os.getenv("id")
SEND_COUNTER_TO_IOT_HUB = False
TEXT_TO_SEND = ""
SEND_AFTER_FRAMES = 30*0 # After 4 seconds

def livestream():

    global TOTAL_FRAMES, CAMERA_SOURCE, VS
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

    nn, labels = load_SSD()
    colors = np.random.uniform(0, 255, size=(len(labels), 3))
    print('[Status] Starting Video Stream...')
    VS = start_camera_source()
    while True:
        try:
            frame = VS.read()
            frame = imutils.resize(frame, width=600)
            TOTAL_FRAMES+=1
            if (TOTAL_FRAMES % (FRAMES_TO_SKIP+1)) == 0:
                blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
                nn.setInput(blob)
                detections = nn.forward()
                counter = show_label_on_frame_and_counter(detections, frame , labels , colors)
            else:
                try: show_label_on_frame_and_counter(detections, frame , labels, colors)
                except: pass
        except:
            TOTAL_FRAMES+=1 
            if TEXT_TO_SEND=="":
                VS.stop()
                VS = start_camera_source()
        if RECIEVE_C2D_MESSAGES: 
            with open('video_source.json','r') as json_file:
                source = json.load(json_file)
                source = source['source']
            if type(source) not in [str,int]: source = source.decode("utf-8") 
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
    labels = ["background", "aeroplane", "bicycle", "bird", 
    "boat","bottle", "bus", "car", "cat", "chair", "cow", 
    "diningtable","dog", "horse", "motorbike", "person", "pottedplant", 
    "sheep","sofa", "train", "tvmonitor"]

    #Loading Caffe Model
    print('[Status] Loading Model...')
    nn = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, MODEL_PATH)

    return nn,labels

def show_label_on_frame_and_counter(detections, frame, labels, colors):

    global TOTAL_FRAMES, TEXT_TO_SEND, CAMERA_SOURCE
    
    (h, w) = frame.shape[:2]
    person_count = 0

    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        idx = int(detections[0, 0, i, 1])
        if ENABLE_PERSON_COUNT: condition_ = labels[idx] == 'person' and confidence>CONFIDENCE_THRESHOLD
        if condition_ and ENABLE_PERSON_COUNT: person_count+=1 
    now = datetime.datetime.now()
    time_ = now.strftime("%H:%M:%S") 
    date_ = now.strftime("%Y-%m-%d")      
    if ENABLE_PERSON_COUNT and SEND_COUNTER_TO_IOT_HUB: TEXT_TO_SEND = {"id":DEVICE_ID,"d":date_,"t":time_,"pc":str(person_count),"ip":str(CAMERA_SOURCE)}
        
    return [person_count]

def start_camera_source():

    global CAMERA_SOURCE, DEFAULT_CAMERA_SOURCE, VS, TEXT_TO_SEND
    if type(CAMERA_SOURCE) not in [str,int]: CAMERA_SOURCE = CAMERA_SOURCE.decode("utf-8") 
    if type(CAMERA_SOURCE)==str and CAMERA_SOURCE.isnumeric(): CAMERA_SOURCE = int(CAMERA_SOURCE)
    if type(CAMERA_SOURCE) == int or ('.mp4' or '.avi') not in CAMERA_SOURCE: VS = WebcamVideoStream(src=CAMERA_SOURCE).start()
    else: VS = FileVideoStream(CAMERA_SOURCE).start()
    now = datetime.datetime.now()
    time_ = now.strftime("%H:%M:%S") 
    date_ = now.strftime("%Y-%m-%d")
    frame = VS.read()
    if frame is None:
        text = "Failed to access "+str(CAMERA_SOURCE)+" Going back to the previous camera Source if available"
        TEXT_TO_SEND = {"id":DEVICE_ID,"d":date_,"t":time_,"message":str(text)}
        if type(DEFAULT_CAMERA_SOURCE) not in [str,int]: DEFAULT_CAMERA_SOURCE = DEFAULT_CAMERA_SOURCE.decode("utf-8") 
        if type(DEFAULT_CAMERA_SOURCE) == str and DEFAULT_CAMERA_SOURCE.isnumeric(): DEFAULT_CAMERA_SOURCE = int(CAMERA_SOURCE)
        if type(DEFAULT_CAMERA_SOURCE) == int or ('.mp4' or '.avi') not in DEFAULT_CAMERA_SOURCE: VS = WebcamVideoStream(src=DEFAULT_CAMERA_SOURCE).start()
        else: VS = FileVideoStream(DEFAULT_CAMERA_SOURCE).start()
        time.sleep(5)
    else:
        text = "Accessing "+str(CAMERA_SOURCE)
        TEXT_TO_SEND = {"id":DEVICE_ID,"d":date_,"t":time_,"message":str(text)}         
        time.sleep(5)
    return VS

def send_to_iot_hub():

    CONNECTION_STRING = os.getenv("cs")
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    while True:
        try:
            global TEXT_TO_SEND, TOTAL_FRAMES
            if (TOTAL_FRAMES % (SEND_AFTER_FRAMES+1)==0) and TEXT_TO_SEND!="": 
                message = Message(str(TEXT_TO_SEND))
                CLIENT.send_message(message)
                print ("Message '{}' successfully sent".format(TEXT_TO_SEND))
                TEXT_TO_SEND=""
        except: continue
    while True:
        time.sleep(1000)

def recieve_from_cloud():

    CONNECTION_STRING = os.getenv("cs")
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

