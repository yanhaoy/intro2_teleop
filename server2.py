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
import json


def mogrify(topic, msg):
    """json encode the message and prepend the topic"""
    return topic + " " + json.dumps(msg)


my_camera = Camera.Camera()
my_camera.camera_open()

# Set the port
port = "5556"  # It should be fine to use the default
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

# Socket to publish
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

# Set topic
topic = "perception"  # This should match the server's topic name

count = 0

while True:
    time.sleep(1/30)

    img = my_camera.frame
    if img is None:
        continue

    message = cv.imencode(".jpg", img)[1].tolist()

    # print("server sends: the image at the topic: " + topic)

    socket.send(bytes(mogrify(topic, message), "utf-8"))
