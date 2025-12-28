#!/bin/bash

# 1. Navigate to the folder where this script is located
cd "$(dirname "$0")"

nohup python3 main.py > /dev/null 2>&1 &

osascript -e 'tell application "Terminal" to close first window' & exit