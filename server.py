import zmq
import sys
import time

# Set the port
port = "5556" # It should be fine to use the default
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

# Socket to publish
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

# Set topic
topic = "control" # This should match the server's topic name

count = 0

while True:
    message = "command%d" % count
    print("server sends: " + message + " at the topic: " + topic)

    # The full message is topic_space_message
    fullmessage = bytes(topic + " " + message, "utf-8")
    
    socket.send(fullmessage)

    count += 1
    time.sleep(1)
