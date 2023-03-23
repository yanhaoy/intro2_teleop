#!/usr/bin/env python3
import sys
import zmq
import time
import numpy as np
import cv2 as cv


# Set the port
port = "5557"  # It should be fine to use the default
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.CONFLATE, 1)  # Take only the last element
socket.connect("tcp://192.168.31.5:%s" % port)  # pi's IP

# Set subscriber
socket.setsockopt(zmq.SUBSCRIBE, bytes("", "utf-8"))

while True:
    try:
        res = socket.recv(flags=zmq.NOBLOCK)  # Asynchronous communication using noblock

        # Recover image from message
        img = cv.imdecode(np.frombuffer(res, dtype="uint8"), cv.IMREAD_COLOR)

        # Plot
        cv.imshow("img", img)

        cv.waitKey(1)

    except zmq.Again as e:
        pass
        # No message received
