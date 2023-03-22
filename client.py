#!/usr/bin/env python3
import os  # nopep8
import sys  # nopep8

fpath = os.path.join(os.path.dirname(__file__), "ArmPi")  # nopep8
sys.path.insert(0, fpath)  # nopep8

import sys
import zmq
import time
from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *

AK = ArmIK()

# Set the port
port = "5556"  # It should be fine to use the default
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.CONFLATE, 1)  # Take only the last element
socket.connect(
    "tcp://192.168.31.246:%s" % port
)  # I hope this IP is constant, otherwise change it to your laptop's IP

# Set topic filter
topicfilter = "control"  # This should match the server's topic name
socket.setsockopt(zmq.SUBSCRIBE, bytes(topicfilter, "utf-8"))

x, y, z, r, c = 0, 10, 10, 500, False

while True:
    time.sleep(0.5)
    try:
        res = socket.recv(flags=zmq.NOBLOCK)  # Asynchronous communication using noblock
        topic, message = res.decode("utf-8").split()
        print("client receives: " + message + " at the topic: " + topic)

        if message == "w":
            x += 1
        elif message == "a":
            y -= 1
        elif message == "s":
            x -= 1
        elif message == "d":
            y += 1
        elif message == "r":
            z += 1
        elif message == "f":
            z -= 1
        elif message == "q":
            r += 10
        elif message == "e":
            r -= 10
        elif message == "t":
            c = True
        elif message == "g":
            c = False
        else:
            continue

        print("current state: ", x, y, z, r, c)

        AK.setPitchRangeMoving((x, y, z), -90, -30, -90, 1500)
        if c:
            Board.setBusServoPulse(1, 200, 500)
        else:
            Board.setBusServoPulse(1, 500, 500)
        Board.setBusServoPulse(2, r, 500)

    except zmq.Again as e:
        pass
        # If not received, do something else
        # print("No new message received yet")
