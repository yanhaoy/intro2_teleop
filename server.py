import zmq
import sys
import time
import pygame

# initialising pygame
pygame.init()

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
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # checking if keydown event happened or not
        if event.type == pygame.KEYDOWN:
            # checking if key "A" was pressed
            if event.key == pygame.K_w:
                message = "w"
            elif event.key == pygame.K_a:
                message = "a"
            elif event.key == pygame.K_s:
                message = "s"
            elif event.key == pygame.K_d:
                message = "d"
            elif event.key == pygame.K_q:
                message = "q"
            elif event.key == pygame.K_e:
                message = "e"
            else:
                continue

            print("server sends: " + message + " at the topic: " + topic)

            # The full message is topic_space_message
            fullmessage = bytes(topic + " " + message, "utf-8")

            socket.send(fullmessage)
