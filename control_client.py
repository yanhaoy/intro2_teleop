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
socket.connect("tcp://192.168.31.246:%s" % port)  # Laptop's IP

# Set topic filter
topicfilter = "control"  # This should match the server's topic name
socket.setsockopt(zmq.SUBSCRIBE, bytes(topicfilter, "utf-8"))

# Initial states
x, y, z, r, c = 0, 10, 10, 500, False

# Back to home position
AK.setPitchRangeMoving((x, y, z), -90, -30, -90, 1500)
if c:
    Board.setBusServoPulse(1, 200, 500)
else:
    Board.setBusServoPulse(1, 500, 500)
Board.setBusServoPulse(2, r, 500)

while True:
    time.sleep(0.5)
    try:
        res = socket.recv(flags=zmq.NOBLOCK)  # Asynchronous communication using noblock
        topic, message = res.decode("utf-8").split()

        # Map message to operation
        if message == "x_forward":
            x += 1
        elif message == "y_backward":
            y -= 1
        elif message == "x_bakcward":
            x -= 1
        elif message == "y_forward":
            y += 1
        elif message == "z_forward":
            z += 1
        elif message == "z_backward":
            z -= 1
        elif message == "r_forward":
            r += 25
        elif message == "r_backward":
            r -= 25
        elif message == "c_open":
            c = True
        elif message == "c_close":
            c = False
        else:
            continue

        # Print states
        print("x: %d, y: %d, z: %d, rot: %d, claw: %r" % (x, y, z, r, c), end="\r")

        # Control
        AK.setPitchRangeMoving((x, y, z), -90, -30, -90, 1500)
        if c:
            Board.setBusServoPulse(1, 200, 500)
        else:
            Board.setBusServoPulse(1, 500, 500)
        Board.setBusServoPulse(2, r, 500)

    except zmq.Again as e:
        pass
        # No message received
