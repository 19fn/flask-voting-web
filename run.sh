#!/bin/bash

# You should have docker and docker-compose (v1.29.0)
# installed to run this script and a docker-compose.yaml 
# file to create a database that the application can connect to.

if [ $(id -u) -ne 0 ]; then
        echo;echo "[!] You should run this script as root (sudo $0).";echo
else
        git pull && \
                sudo docker build . --tag "flask:v1.0" && \
                        sudo docker-compose up --detach && \
                echo;echo "[+] "$0" has terminated successfully.";echo
fi