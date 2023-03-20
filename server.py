from __future__ import annotations

import sys
import time
import typing

import zmq
import pygame


class JoydeviceBinder:
    """Bind a joydevice part to a specific message callback"""
    
    _binds = {}
    topic = None
    
    def __init__(
        self,
        event_id: int,
        event_type: int,
        cmd_id: typing.Tuple[int],
        msg_cb: typing.Callable
    ):

        self.msg_cb = msg_cb
        self.cmd_id = cmd_id
        self.event_id = event_id
        self.event_type = event_type
        
        self._binds[(event_type, event_id)] = self  # Register bind 
    
    @classmethod
    def set_topic_name(
        cls,
        topic: str,
    ):
        
        cls.topic = topic
    
    @classmethod
    def get_bind(
        cls,
        event: pygame.event,
        event_attr: str,
    ) -> typing.Union[None, JoydeviceBinder]:
        
        event_id = getattr(event, event_attr)  # Extract event id
        return cls._binds.get((event.type, event_id))       
    
    def create_msg(self):
        """Create message for the """

        return [bytes(self._topic_name + " " + str(self.cmd_id[i]) + msg, "utf-8") for i, msg in enumerate(self.msg_cb(self.event_id))]


def run_server(
    socket: zmq.Socket,
):
    """Main server function"""
    
    # Map to each
    TYPE_ATTR_MAP = {
        pygame.JOYAXISMOTION: "axis",
        pygame.JOYBUTTONDOWN: "button",
        pygame.JOYHATMOTION: "hat",
    }
    
    while True:
        
        for event in pygame.event.get():
        
            if event.type == pygame.QUIT or event.type == pygame.JOYDEVICEREMOVED:
                shutdown_system()   
            else:
                event_attr = TYPE_ATTR_MAP.get(event.type)
                if event_attr is not None:
                    joydev_bind = JoydeviceBinder.get_bind(event=event, event_attr=event_attr)
                    if joydev_bind is not None:
                        send_messages(socket, joydev_bind.create_msg())
        
        time.sleep(0.01)


# Helper functions/binds for controllers

def read_axis(
    event_id: int,
    joydevice: pygame.joystick.Joystick,
) -> typing.List[str]:
    """Shorthand to send message from axis component"""
    
    value = joydevice.get_axis(event_id)
    if abs(value) < .2:
        return ["n"]
    elif value > 0:
        return ["f"]
    return ["b"]


def read_hat(
    event_id: int,
    joydevice: pygame.joystick.Joystick,
) -> typing.List[str]:
    """Shorthand to send message from d-pad component"""
    
    msgs = []
    values = joydevice.get_hat(event_id)
    for value in values:
        if abs(value) < .2:
            msgs.append("n")
        elif value > 0:
            msgs.append("f")
        else:
            msgs.append("b")

    return msgs


def shutdown_system():
    pygame.quit()
    sys.exit()


def send_messages(
    socket: zmq.Socket,
    msgs: typing.List[bytes],
):
    """Send messages to client"""
    
    for msg in msgs:
        socket.send(msg)


if __name__ == "__main__":
    
    # Initializing pygame
    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)

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
    JoydeviceBinder.set_topic_name("control")  # This should match the server's topic name
    
    # Joydevice binds
    
    # Left stick (control pitch angle)
    JoydeviceBinder(1, pygame.JOYAXISMOTION, (2,), lambda event_id: read_axis(event_id, joystick))  
    
    # Right stick (control x, y position)
    JoydeviceBinder(2, pygame.JOYAXISMOTION, (0,), lambda event_id: read_axis(event_id, joystick))
    JoydeviceBinder(3, pygame.JOYAXISMOTION, (1,), lambda event_id: read_axis(event_id, joystick))
    
    # Triggers (control z position)
    JoydeviceBinder(4, pygame.JOYAXISMOTION, (3,), lambda event_id: read_axis(event_id, joystick))
    JoydeviceBinder(5, pygame.JOYAXISMOTION, (4,), lambda event_id: read_axis(event_id, joystick))
    
    # D-pad
    JoydeviceBinder(0, pygame.JOYHATMOTION, (0, 1), lambda event_id: read_hat(event_id, joystick))

    run_server(socket)  # Run server
