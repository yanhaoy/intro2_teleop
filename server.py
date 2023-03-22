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
        
        cls._topic_name = topic
    
    @classmethod
    def get_bind(
        cls,
        event: pygame.event,
        event_attr: str,
    ) -> typing.Union[None, JoydeviceBinder]:
        
        event_id = getattr(event, event_attr)  # Extract event id
        return cls._binds.get((event.type, event_id))       
    
    def create_msg(self):
        """Create message the message that will be sent to the client"""

        return [bytes(self._topic_name + " " + str(self.cmd_id[i]) + msg, "utf-8") for i, msg in enumerate(self.msg_cb(self.event_id))]


class JoydeviceAxisBinder(JoydeviceBinder):
    """Bind and regulate joyaxis from an xbox controller"""
    
    def __init__(
        self,
        event_id: int,
        cmd_id: typing.Tuple[int],
        msg_cb: typing.Callable,
        cb_delay: float = 0.5,
    ):
        
        self.cb_delay = cb_delay  # By how much do we want to wait between message callbacks
        self._cb_timer = time.time()  # Timer to keep track of last message sent
        super().__init__(event_id, pygame.JOYAXISMOTION, cmd_id, msg_cb)
    
    def create_msg(self):
        """Create and regulate message sending for joysticks"""
        
        # Check if enough time has passed before passing message
        curr_time = time.time()
        if curr_time - self._cb_timer > self.cb_delay:
            self._cb_timer = curr_time    
            return super().create_msg()
        return []


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

def read_axis_horz(
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


def read_axis_vert(
    event_id: int,
    joydevice: pygame.joystick.Joystick,
) -> typing.List[str]:
    """Shorthand to send message from axis component"""
    
    value = joydevice.get_axis(event_id)
    if abs(value) < .2:
        return ["n"]
    elif value > 0:
        return ["b"]
    return ["f"]


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


def read_button(
    event_id: int,
    joydevice: pygame.joystick.Joystick,
) -> typing.List[str]:
    
    return ["f"]


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
    
    # Left stick (control gripper angle)
    JoydeviceAxisBinder(1, (2,), lambda event_id: read_axis_horz(event_id, joystick), cb_delay = 0.25)
    
    # Right stick (control x, y position)
    JoydeviceAxisBinder(2, (0,), lambda event_id: read_axis_vert(event_id, joystick), cb_delay = 0.4)
    JoydeviceAxisBinder(3, (1,), lambda event_id: read_axis_horz(event_id, joystick), cb_delay = 0.4)
    
    # Triggers (control z position)
    JoydeviceAxisBinder(4, (3,), lambda event_id: read_axis_horz(event_id, joystick), cb_delay = 0.2)
    JoydeviceAxisBinder(5, (4,), lambda event_id: read_axis_horz(event_id, joystick), cb_delay = 0.2)
    
    # D-pad (control x, y position)
    JoydeviceBinder(0, pygame.JOYHATMOTION, (0, 1), lambda event_id: read_hat(event_id, joystick))
    
    # A button (Toggle claw)
    JoydeviceBinder(0, pygame.JOYBUTTONDOWN, (5,), lambda event_id: read_button(event_id, joystick))

    run_server(socket)  # Run server
