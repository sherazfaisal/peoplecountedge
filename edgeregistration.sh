#!/bin/bash
cd ~
sudo rm /etc/netplan/50-cloud-init.yaml
sudo cp 50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml
sudo rm listen_wifi.py
sudo rm reg.sh
sudo rm reg.py
sudo netplan generate
sudo netplan apply
sudo apt-get -y update
rm microsoft-prod.list
rm microsoft.gpg
curl https://packages.microsoft.com/config/ubuntu/18.04/multiarch/prod.list > ./microsoft-prod.list
sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
sudo apt-get -y update
sudo apt-get -y install --upgrade python3-pip
sudo apt-get -y install moby-engine
sudo apt-get -y install zfsutils-linux
sudo apt-get -y remove aziot
sudo apt-get -y install aziot-edge=1.2* aziot-identity-service=1.2*
sudo apt-get -y install --upgrade python3-pip
pip3 install azure-iot-device
rm config.txt
rm /etc/aziot/config.toml
rm reg.py
rm reg.sh
sudo docker login -u metisedgedevice -p Hypernym@ISB
sudo docker pull metisedgedevice/peoplecount:reg_py >> reg.py
sudo docker run metisedgedevice/peoplecount:reg_py >> reg.py
sudo docker pull metisedgedevice/peoplecount:reg_sh >> reg.sh
sudo docker run metisedgedevice/peoplecount:reg_sh >> reg.sh
python3 reg.py >> config.txt
sudo cp config.txt /etc/aziot/config.toml
sudo iotedge config apply
rm reg.sh
rm reg.py
sudo docker pull metisedgedevice/peoplecount:wifi_listen_py
sudo docker run metisedgedevice/peoplecount:wifi_listen_py >> listen_wifi.py
sudo docker pull metisedgedevice/peoplecount:reg_sh
sudo docker run metisedgedevice/peoplecount:reg_sh >> reg.sh
sudo docker pull metisedgedevice/peoplecount:reg_wifi_listen_py
sudo docker run metisedgedevice/peoplecount:reg_wifi_listen_py >>reg.py
sudo python3 listen_wifi.py
exit 0
