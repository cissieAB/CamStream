#!/bin/bash

IMAGE_NAME="test_$(date +"%s%N").jpg"
# Take a pic after 5 milliseconds
libcamera-still -o test_images/${IMAGE_NAME} -t 5
