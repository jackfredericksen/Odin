#!/bin/bash

# Update and install dependencies
sudo apt update && sudo apt install -y python3-pip docker.io

# Clone the repository
git clone https://github.com/jackfredericksen/Odin.git
cd Odin

# Install Python dependencies
pip3 install -r requirements.txt

# Start Docker containers
docker-compose up -d
