
FROM arm64v8/ubuntu:20.10

# Install dependencies
RUN apt-get update && \
  apt-get install -yq \
    python3 \
    python3-pip \
    build-essential \
    libssl-dev \
    uuid-dev \
    cmake \
    libcurl4-openssl-dev \
    pkg-config \
    python3-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*


RUN pip3 install --upgrade pip 
RUN pip3 install imutils
RUN pip3 install azure-iot-device
RUN pip3 install azure-iot-hub
RUN pip3 install opencv-python-headless
RUN pip3 install --index-url https://google-coral.github.io/py-repo/ tflite_runtime
RUN pip3 install flask
RUN pip3 install scikit-image
RUN pip3 install pyngrok
RUN pip3 install certifi
WORKDIR /algorithm/

COPY algorithm .

CMD ["bash","-u", "/algorithm/run.sh"]