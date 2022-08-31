#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	echo;echo "[!] You must run this script as root (sudo $0).";echo
else
	sudo docker build . --tag "voting-app-img:2.0" && \
	sudo docker-compose up --detach && \
	echo
	echo -ne "[!] 'Initialize.sh' is still finishing wait...  (10%)\r"
        sleep 1
        echo -ne "[!] 'Initialize.sh' is still finishing wait...  (28%)\r"
        sleep 1
	echo -ne "[!] 'Initialize.sh' is still finishing wait...  (45%)\r"
	sleep 1
	echo -ne "[!] 'Initialize.sh' is still finishing wait...  (78%)\r"
	sleep 1
	echo -ne "[!] 'Initialize.sh' finished.  (100%)\r"
	echo -n ""
fi
