import zmq
import sys
import time
import pygame

# Initialize pygame
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)

# Creat display
display = pygame.display.set_mode((300, 300))

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
topic = "control"  # This should match the server's topic name

while True:
    time.sleep(0.01)

    # Create a loop to check events that are occurring
    for event in pygame.event.get():
        message = None

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Map joystick input to message
        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 2 or event.axis == 5:
                if event.value > 0.9:
                    if event.axis == 2:
                        message = "r_forward"
                    else:
                        message = "r_backward"
            elif abs(event.value) > 0.9:
                if event.axis == 0:
                    if event.value > 0:
                        message = "y_forward"
                    else:
                        message = "y_backward"
                elif event.axis == 1:
                    if event.value > 0:
                        message = "x_bakcward"
                    else:
                        message = "x_forward"

        if event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:
                message = "z_forward"
            elif event.value[1] == -1:
                message = "z_backward"

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:
                message = "c_open"
            elif event.button == 1:
                message = "c_close"

        if message is None:
            continue

        # Print message
        print("server sends: " + message + " at the topic: " + topic, end="\r")

        # The full message is topic_space_message
        fullmessage = bytes(topic + " " + message, "utf-8")

        # Send message
        socket.send(fullmessage)
