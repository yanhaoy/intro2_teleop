#!/usr/bin/env python3
import sys
import zmq
import time
import numpy as np
import json
import cv2 as cv


def demogrify(topicmsg):
    """Inverse of mogrify()"""
    json0 = topicmsg.find("[")
    topic = topicmsg[0:json0].strip()
    msg = json.loads(topicmsg[json0:])
    return topic, msg


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
    "tcp://192.168.31.5:%s" % port
)  # I hope this IP is constant, otherwise change it to your laptop's IP

# Set topic filter
topicfilter = "perception"  # This should match the server's topic name
socket.setsockopt(zmq.SUBSCRIBE, bytes(topicfilter, "utf-8"))

while True:
    time.sleep(1/30)
    try:
        res = socket.recv(flags=zmq.NOBLOCK)  # Asynchronous communication using noblock
        topic, message = demogrify(res.decode("utf-8"))
        # print("client receives: image at the topic: " + topic)
        img = cv.imdecode(np.asarray(message, dtype="uint8"), cv.IMREAD_COLOR)
        cv.imshow("img", img)

        cv.waitKey(1)

    except zmq.Again as e:
        pass
        # If not received, do something else
        # print("No new message received yet")
