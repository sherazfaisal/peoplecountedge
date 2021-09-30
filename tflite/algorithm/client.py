import cv2, socket, numpy, pickle

from flask import Flask, render_template, Response
import sys
from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device import MethodResponse
import time
import os

def start_client():

    def init_webhooks(base_url):
        # Update inbound traffic via APIs to use the public-facing ngrok URL
        pass

    def create_app():
        app = Flask(__name__)

        # Initialize our ngrok settings into Flask
        app.config.from_mapping(
            BASE_URL="http://127.0.0.1:5000",
            USE_NGROK=True
        )

        # pyngrok will only be installed, and should only ever be initialized, in a dev environment
        from pyngrok import ngrok

        # Get the dev server port (defaults to 5000 for Flask, can be overridden with `--port`
        # when starting the server
        port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 5000

        # Open a ngrok tunnel to the dev server
        public_url = ngrok.connect(port).public_url
        print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))

        # Update any base URLs or webhooks to use the public ngrok URL
        app.config["BASE_URL"] = public_url
        init_webhooks(public_url)

        # ... Initialize Blueprints and the rest of our app

        return app,public_url

    def send_to_iot_hub(public_url):
        CONNECTION_STRING = os.getenv("cs")
        CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
        for i in range(5):
            TEXT_TO_SEND = f"STREAMING LIVE ON {public_url}/video_feed"
            message = Message(str(TEXT_TO_SEND))
            CLIENT.send_message(message)
        CLIENT.disconnect()

    app, public_url = create_app()
    with open('public_url.txt', 'w') as f:
        f.write(public_url)
    send_to_iot_hub(public_url)

    @app.route('/video_feed')
    def video_feed():
        #Video streaming route. Put this in the src attribute of an img tag
        return Response(main(), mimetype='multipart/x-mixed-replace; boundary=frame')


    @app.route('/')
    def index():
        """Video streaming home page."""
        return render_template('index.html')

    def main():
        s=socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
        ip=socket.gethostbyname(socket.gethostname())
        port=6666
        s.bind((ip,port))

        while True:
            x=s.recvfrom(1000000)
            clientip = x[1][0]
            data=x[0]
            data=pickle.loads(data)
            data = cv2.imdecode(data, cv2.IMREAD_COLOR)
            ret, buffer = cv2.imencode('.jpg', data)
            data = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')

    app.run()

if __name__ == "__main__":
    while True:
        try: start_client()
        except:
            time.sleep(5)
            start_client()