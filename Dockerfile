FROM arm64v8/ubuntu

# Install dependencies
RUN apt-get update && \
  apt-get install -yq \	
    python3 \
    python3-pip	\	
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get install bash
RUN pip3 install --upgrade pip 
RUN pip3 install imutils
RUN pip3 install azure-iot-device
RUN pip3 install opencv-python-headless

WORKDIR /algorithm/

COPY algorithm .

CMD ["python3", "-u", "/algorithm/main.py"]


