import zmq
import sys
import time
import pygame

# initialising pygame
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)

# creating display
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

count = 0

while True:
    time.sleep(0.01)

    # creating a loop to check events that
    # are occurring
    for event in pygame.event.get():
        message = None

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 2 or event.axis == 5:
                if event.value > 0.9:
                    if event.axis == 2:
                        message = "q"
                    else:
                        message = "e"
            elif abs(event.value) > 0.9:
                if event.axis == 0:
                    if event.value > 0:
                        message = "d"
                    else:
                        message = "a"
                elif event.axis == 1:
                    if event.value > 0:
                        message = "s"
                    else:
                        message = "w"

        if event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:
                message = 'r'
            elif event.value[1] == -1:
                message = 'f'

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:
                message = 't'
            elif event.button == 1:
                message = 'g'

        if message is None:
            continue

        print("server sends: " + message + " at the topic: " + topic, end="\r")

        # The full message is topic_space_message
        fullmessage = bytes(topic + " " + message, "utf-8")

        socket.send(fullmessage)
