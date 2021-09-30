# Import packages
import os
import argparse
import cv2
import numpy as np
import sys
import time
import datetime
from threading import Thread
from imutils.video import FPS 
import importlib.util
import json
from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device import MethodResponse
from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(main(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

TOTAL_FRAMES = 0
FRAMES_TO_SKIP = 10
TEXT_TO_SEND = ""
RECEIVE_DATA = True
CAMERA_SOURCE = 0#"http://192.168.137.152:8080/video"#0
DEFAULT_CAMERA_SOURCE = 0
MINIMUM_COUNT = 0
CONFIDENCE_THRESHOLD = 0.4
SEND_DATA = True
SEND_AFTER_FRAMES = 0
WRITE_VIDEO = False
RESTART_SOURCE_AFTER = 30*30*0
WRITE_FRAMES_PER_VIDEO = 500
CONNECTION_STRING = "HostName=IoTHWLabs.azure-devices.net;DeviceId=edge-test-device;SharedAccessKey=yOlOAk/OBHLX3Ty2cwGxJ1+KxGxc+uTqKBMTgqotorg="#os.getenv("cs")
DEVICE_ID = "edge-test-device"#os.getenv("id")
LIVE_STREAM = True

def is_usb_mounted():
    return len(os.listdir("/dev/bus/usb/001/"))==5

def send_to_iot_hub():

    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    while True:
        try:
            global TEXT_TO_SEND, TOTAL_FRAMES, MINIMUM_COUNT
            if (TOTAL_FRAMES % (SEND_AFTER_FRAMES+1)==0) and TEXT_TO_SEND!="": 
                if 'pc' in TEXT_TO_SEND.keys() and int(TEXT_TO_SEND['pc'])>=MINIMUM_COUNT:
                    message = Message(str(TEXT_TO_SEND))
                    CLIENT.send_message(message)
                    TEXT_TO_SEND=""
                elif 'pc' not in TEXT_TO_SEND.keys():
                    message = Message(str(TEXT_TO_SEND))
                    CLIENT.send_message(message)
                    print ("Message '{}' successfully sent".format(LIST_MESSAGES))
                    TEXT_TO_SEND=""

        except: continue
    while True:
        time.sleep(1000)

class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        global CAMERA_SOURCE, TEXT_TO_SEND, DEFAULT_CAMERA_SOURCE
        if type(CAMERA_SOURCE) not in [str,int]:
            CAMERA_SOURCE = CAMERA_SOURCE.decode("utf-8") 
        if type(CAMERA_SOURCE)==str and CAMERA_SOURCE.isnumeric(): CAMERA_SOURCE = int(CAMERA_SOURCE)
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(CAMERA_SOURCE)#'http://192.168.137.99:8080/video'
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('m','p','4','v'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])

        now = datetime.datetime.now()
        time_ = now.strftime("%H:%M:%S") 
        date_ = now.strftime("%Y-%m-%d")
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

        if not self.grabbed:
            text = "Failed to access "+str(CAMERA_SOURCE)+" Going back to the previous camera Source if available"
            TEXT_TO_SEND = {"id":DEVICE_ID,"d":date_,"t":time_,"message":str(text)}
            if type(DEFAULT_CAMERA_SOURCE) not in [str,int]:
                DEFAULT_CAMERA_SOURCE = DEFAULT_CAMERA_SOURCE.decode("utf-8") 
            if type(DEFAULT_CAMERA_SOURCE) == str and DEFAULT_CAMERA_SOURCE.isnumeric(): DEFAULT_CAMERA_SOURCE = int(DEFAULT_CAMERA_SOURCE)
            self.stream = cv2.VideoCapture(DEFAULT_CAMERA_SOURCE)#'http://192.168.137.99:8080/video'
            ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            ret = self.stream.set(3,resolution[0])
            ret = self.stream.set(4,resolution[1])
            time.sleep(5)
        else:
            text = "Accessing "+str(CAMERA_SOURCE)
            TEXT_TO_SEND = {"id":DEVICE_ID,"d":date_,"t":time_,"message":str(text)}         
            time.sleep(5)

	# Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	# Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
	# Return the most recent frame
        return self.frame

    def stop(self):
	# Indicate that the camera and thread should be stopped
        self.stopped = True

def main():
    global TOTAL_FRAMES,TEXT_TO_SEND
    # Define and parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                        default='Sample_TFLite_model')
    parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                        default='detect.tflite')
    parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                        default='labelmap.txt')
    parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                        default= CONFIDENCE_THRESHOLD)
    parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                        default='1280x720')
    parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                        action='store_true')

    args = parser.parse_args()

    MODEL_NAME = args.modeldir
    GRAPH_NAME = args.graph
    LABELMAP_NAME = args.labels
    min_conf_threshold = float(args.threshold)
    resW, resH = args.resolution.split('x')
    imW, imH = int(resW), int(resH)
    use_TPU = args.edgetpu

    pkg = importlib.util.find_spec('tflite_runtime')
    if pkg:
        from tflite_runtime.interpreter import Interpreter
        if use_TPU:
            from tflite_runtime.interpreter import load_delegate
    else:
        from tensorflow.lite.python.interpreter import Interpreter
        if use_TPU:
            from tensorflow.lite.python.interpreter import load_delegate

    # If using Edge TPU, assign filename for Edge TPU model
    if use_TPU:
        # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
        if (GRAPH_NAME == 'detect.tflite'):
            GRAPH_NAME = 'edgetpu.tflite'       

    # Get path to current working directory
    CWD_PATH = os.getcwd()

    # Path to .tflite file, which contains the model that is used for object detection
    PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

    # Path to label map file
    PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

    # Load the label map
    with open(PATH_TO_LABELS, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Have to do a weird fix for label map if using the COCO "starter model" from
    # https://www.tensorflow.org/lite/models/object_detection/overview
    # First label is '???', which has to be removed.
    if labels[0] == '???':
        del(labels[0])

    # Load the Tensorflow Lite model.
    # If using Edge TPU, use special load_delegate argument
    if use_TPU:
        interpreter = Interpreter(model_path=PATH_TO_CKPT,
                                experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        print(PATH_TO_CKPT)
    else:
        interpreter = Interpreter(model_path=PATH_TO_CKPT)

    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    floating_model = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Initialize frame rate calculation
    frame_rate_calc = 1
    freq = cv2.getTickFrequency()

    if SEND_DATA: 
        message_sender_thread = Thread(target=send_to_iot_hub, args=())
        message_sender_thread.daemon = True
        message_sender_thread.start()

    if RECEIVE_DATA:
        with open('video_source.json','r') as json_file:
            source = json.load(json_file)
            MINIMUM_COUNT = 1 if source['zone'] == "Geozone" else 0
            CAMERA_SOURCE = source['source']

    # Initialize video stream
    videostream = VideoStream(resolution=(imW,imH),framerate=30).start()
    time.sleep(1)

    fps = FPS().start()
    video_initialized = False
        
    #for frame1 in camera.capture_continuous(rawCapture, format="bgr",use_video_port=True):
    while True:

        # Grab frame from video stream
        frame1 = videostream.read()
        try:
            # Acquire frame and resize to expected shape [1xHxWx3]
            frame = frame1.copy()
            TOTAL_FRAMES+=1
            if TOTAL_FRAMES % (FRAMES_TO_SKIP+1) == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (width, height))
                input_data = np.expand_dims(frame_resized, axis=0)

                # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
                if floating_model:
                    input_data = (np.float32(input_data) - input_mean) / input_std

                # Perform the actual detection by running the model with the image as input
                interpreter.set_tensor(input_details[0]['index'],input_data)
                interpreter.invoke()

                # Retrieve detection results
                boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
                classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
                scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects
                num = interpreter.get_tensor(output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)

                person_count=[num for num,class_ in zip(scores,classes) if num >= 0.5 and class_==0] 
                current_Persons=len(person_count)
                print(current_Persons)

            if LIVE_STREAM:
                cv2.putText(frame1, str(time.ctime(time.time())), (10, 15),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2) 
                cv2.putText(frame1, "People Count: "+str(current_Persons), (10, 35),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2) 
                ret, buffer = cv2.imencode('.jpg', frame1)
                frame1 = buffer.tobytes()
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame1 + b'\r\n')


            if WRITE_VIDEO and is_usb_mounted():
                if not video_initialized:
                    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
                    time_string=time.strftime("%Y%m%d-%H%M%S")
                    time_string=str(time_string)
                    time_string=time_string+".m4v"
                    time_string="/media/external/"+time_string
                    try: out = cv2.VideoWriter(time_string, fourcc, 30.0, (640, 480))
                    except: pass
                    video_initialized = True
                try:
                    cv2.putText(frame1, str(time.ctime(time.time())), (10, 15),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2) 
                    cv2.putText(frame1, "People Count: "+str(current_Persons), (10, 35),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2) 
                    res_fram = cv2.resize(frame1, (640,480))
                    out.write(res_fram)
                except: pass

            if WRITE_VIDEO and not is_usb_mounted() and video_initialized: video_initialized = False

            now = datetime.datetime.now()
            time_ = now.strftime("%H:%M:%S") 
            date_ = now.strftime("%Y-%m-%d") 
            if SEND_DATA: TEXT_TO_SEND = {"id":DEVICE_ID,"d":date_,"t":time_,"pc":str(current_Persons),"ip":str(CAMERA_SOURCE)}

        except: 
            TOTAL_FRAMES+=1 
            if TOTAL_FRAMES%(RESTART_SOURCE_AFTER+1)==0 and TEXT_TO_SEND=="":
                videostream.stop()
                videostream = VideoStream(resolution=(imW,imH),framerate=30).start()
        if RECEIVE_DATA: 
            with open('video_source.json','r') as json_file:
                source = json.load(json_file)
                MINIMUM_COUNT = 1 if source['zone'] == "Geozone" else 0
                source = source['source']
            if type(source) not in [str,int]:
                source = source.decode("utf-8") 
            if type(source)==str and source.isnumeric(): source = int(source)
            if source!=CAMERA_SOURCE:
                videostream.stop()
                DEFAULT_CAMERA_SOURCE = CAMERA_SOURCE
                CAMERA_SOURCE = source
                videostream = VideoStream(resolution=(imW,imH),framerate=30).start()

        if (TOTAL_FRAMES % (WRITE_FRAMES_PER_VIDEO+1)) == 0 and WRITE_VIDEO and is_usb_mounted():
            fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
            time_string=time.strftime("%Y%m%d-%H%M%S")
            time_string=str(time_string)
            time_string=time_string+".m4v"
            time_string="/media/external/"+time_string
            try:
                out.release()
                out = cv2.VideoWriter(time_string, fourcc, 30.0, (640, 480))
            except: pass
        fps.update()

    # Clean up
    fps.stop()
    print("[Info] Elapsed time: {:.2f}".format(fps.elapsed()))
    print("[Info] Approximate FPS:  {:.2f}".format(fps.fps()))
    if WRITE_VIDEO: out.release()
    videostream.stop()

if __name__ == "__main__":
    if LIVE_STREAM: app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    main()
