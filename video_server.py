#!/usr/bin/env python3
import os  # nopep8
import sys  # nopep8

fpath = os.path.join(os.path.dirname(__file__), "ArmPi")  # nopep8
sys.path.insert(0, fpath)  # nopep8

import cv2 as cv
import time
import Camera
from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
from CameraCalibration.CalibrationConfig import *
import zmq
import sys
import time


# Init camera
my_camera = Camera.Camera()
my_camera.camera_open()

# Set the port
port = "5557"  # It should be fine to use the default
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

# Socket to publish
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

while True:
    time.sleep(1 / 60)

    # Capture a frame
    img = my_camera.frame
    if img is None:
        continue

    # Convert frame to message
    message = cv.imencode(".jpg", img)[1].tobytes()

    # Send message
    socket.send(message)
