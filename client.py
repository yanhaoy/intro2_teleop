import sys
import zmq
import time

# Set the port
port = "5556" # It should be fine to use the default
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.CONFLATE, 1) # Take only the last element
socket.connect("tcp://192.168.149.39:%s" % port) # I hope this IP is constant, otherwise change it to your laptop's IP

# Set topic filter
topicfilter = "control" # This should match the server's topic name
socket.setsockopt(zmq.SUBSCRIBE, bytes(topicfilter, "utf-8"))

while True:
    time.sleep(0.5)
    try:
        res = socket.recv(flags=zmq.NOBLOCK) # Asynchronous communication using noblock
        topic, message = res.decode("utf-8").split()
        print("client receives: " + message + " at the topic: " + topic)
    except zmq.Again as e:
        # If not received, do something else
        print("No new message received yet")
