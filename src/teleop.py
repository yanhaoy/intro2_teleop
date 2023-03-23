import atexit
import json
import threading
import time
from argparse import ArgumentParser, Namespace
from typing import Any, Callable, List, Optional, Tuple, Union

import cv2
import numpy as np
import pygame
import zmq


class JoydeviceBinder:
    """Bind a joydevice button to a specific message callback"""

    _binds = {}  # type: ignore
    _topic_name = ""

    def __init__(
        self,
        event_id: int,
        event_type: int,
        cmd_id: Union[Tuple[int], Tuple[int, int]],
        msg_cb: Callable,
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
        """
        Set the topic that commands will be published on.

        Args:
            topic (str): The topic that commands will be published to.
        """
        cls._topic_name = topic

    @classmethod
    def get_bind(
        cls,
        event: pygame.event.Event,
        event_attr: str,
    ) -> Optional[Any]:
        """
        Get the binding for the given event.

        Args:
            event (pygame.event.Event): The event to get.
            event_attr (str): The name of the attribute to access.

        Returns:
            Optional[Any]: _description_
        """
        event_id = getattr(event, event_attr)
        return cls._binds.get((event.type, event_id))

    def create_msg(self) -> List[bytes]:
        """
        Create a command to publish to the robot.

        Returns:
            List[bytes]: The converted bytes message with the prepended topic.
        """
        return [
            bytes(self._topic_name + " " + str(self.cmd_id[i]) + msg, "utf-8")
            for i, msg in enumerate(self.msg_cb(self.event_id))
        ]


class TeleOpInterface:
    """Interface used to facilitate network communication from a remote system."""

    def __init__(
        self,
        ip: str,
        video_port_in: int,
        command_port_out: int,
        command_topic: str = "control",
        perception_topic: str = "perception",
    ) -> None:
        """
        Create a new teleop interface.

        Args:
            ip (str): The IP address of the robot
            video_port_in (int): The port that the video feed will be streamed on.
            command_port_out (int): The port that commands should be sent on.
            command_topic (str, optional): The topic that commands will be sent over.
                Defaults to "control".
            perception_topic (str, optional): The topic that video feed will be sent on.
                Defaults to "perception".
        """
        self.context = zmq.Context()

        self._running = False

        self._video_thread = threading.Thread(
            target=self._read_video_stream,
            args=(f"tcp://{ip}:{video_port_in}", perception_topic),
        )
        self._video_thread.setDaemon(True)

        self._command_thread = threading.Thread(
            target=self._send_commands,
            args=(f"tcp://{ip}:{command_port_out}", command_topic),
        )
        self._command_thread.setDaemon(True)

        # Register a destructor to join the threads
        atexit.register(self.stop)

    def start(self) -> None:
        """Start the teleop interface."""
        self._running = True
        self._video_thread.start()
        self._command_thread.start()

    def stop(self) -> None:
        """Stop the teleop interface and join all threads."""
        self._running = False
        self._video_thread.join()
        self._command_thread.join()

    def _read_video_stream(self, address: str, topic: str) -> None:
        """
        Read the video stream from the ArmPi.

        Args:
            address (str): The IP address of the ArmPi.
            topic (str): The topic that video feed will be published over.
        """
        socket = self.context.socket(zmq.SUB)
        socket.setsockopt(zmq.CONFLATE, 1)
        socket.connect(address)
        socket.setsockopt(zmq.SUBSCRIBE, bytes(topic, "utf-8"))

        def demogrify(msg):
            """Inverse of mogrify()"""
            json0 = msg.find("[")
            topic = msg[0:json0].strip()
            msg = json.loads(msg[json0:])
            return topic, msg

        while self._running:
            try:
                res = socket.recv(flags=zmq.NOBLOCK)
                topic, message = demogrify(res.decode("utf-8"))
                img = cv2.imdecode(np.asarray(message, dtype="uint8"), cv2.IMREAD_COLOR)
                cv2.imshow("img", img)

                cv2.waitKey(1)

            except zmq.Again:
                ...

            time.sleep(0.5)

    def _send_commands(self, address: str, topic: str) -> None:
        """
        Proxy the control commands published by the user.

        Args:
            address (str): The IP address create a socket on.
            topic (str): The topic that commands should be published to.
        """
        socket = self.context.socket(zmq.PUB)
        socket.bind(address)

        JoydeviceBinder.set_topic_name(topic)

        # Map to each button type
        TYPE_ATTR_MAP = {
            pygame.JOYAXISMOTION: "axis",
            pygame.JOYBUTTONDOWN: "button",
            pygame.JOYHATMOTION: "hat",
        }

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.JOYDEVICEREMOVED:
                    pygame.quit()
                    self.stop()
                else:
                    event_attr = TYPE_ATTR_MAP.get(event.type)
                    if event_attr is not None:
                        joydev_bind = JoydeviceBinder.get_bind(
                            event=event, event_attr=event_attr
                        )
                        if joydev_bind is not None:
                            msgs = joydev_bind.creat_msg()

                            for msg in msgs:
                                socket.send(msg)

            time.sleep(0.01)


def read_axis(event_id: int, joydevice: pygame.joystick.JoystickType) -> List[str]:
    """Shorthand to send message from axis component"""
    value = joydevice.get_axis(event_id)
    if abs(value) < 0.2:
        return ["n"]
    elif value > 0:
        return ["f"]
    return ["b"]


def read_hat(event_id: int, joydevice: pygame.joystick.JoystickType) -> List[str]:
    """Shorthand to send message from d-pad component"""
    msgs = []

    values = joydevice.get_hat(event_id)
    for value in values:
        if abs(value) < 0.2:
            msgs.append("n")
        elif value > 0:
            msgs.append("f")
        else:
            msgs.append("b")

    return msgs


def get_args() -> Namespace:
    """
    Parse the command line arguments.

    Returns:
        Namespace: The argument namespace.
    """
    parser = ArgumentParser()

    parser.add_argument(
        "ip",
        type=str,
        default="192.168.31.5",
        help="IP address of the arm pi.",
    )
    parser.add_argument(
        "command_port",
        type=int,
        default=5556,
        help="The port that the teleop computer will publish control commands over.",
    )
    parser.add_argument(
        "command_topic",
        type=str,
        default="control",
        help="The topic that control commands should be published on.",
    )
    parser.add_argument(
        "video_port",
        type=int,
        default=5557,
        help="The port that the video will be streamed on.",
    )
    parser.add_argument(
        "perception_topic",
        type=str,
        default="perception",
        help="The topic that should be subscribed to for video feed.",
    )

    return parser.parse_args()


def main() -> None:
    args = get_args()

    # Initializing pygame
    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)

    # Left stick (control pitch angle)
    JoydeviceBinder(
        1, pygame.JOYAXISMOTION, (2,), lambda event_id: read_axis(event_id, joystick)
    )

    # Right stick (control x, y position)
    JoydeviceBinder(
        2, pygame.JOYAXISMOTION, (0,), lambda event_id: read_axis(event_id, joystick)
    )
    JoydeviceBinder(
        3, pygame.JOYAXISMOTION, (1,), lambda event_id: read_axis(event_id, joystick)
    )

    # Triggers (control z position)
    JoydeviceBinder(
        4, pygame.JOYAXISMOTION, (3,), lambda event_id: read_axis(event_id, joystick)
    )
    JoydeviceBinder(
        5, pygame.JOYAXISMOTION, (4,), lambda event_id: read_axis(event_id, joystick)
    )

    # D-pad
    JoydeviceBinder(
        0, pygame.JOYHATMOTION, (0, 1), lambda event_id: read_hat(event_id, joystick)
    )

    teleop_interface = TeleOpInterface(
        args.ip,
        args.video_port,
        args.command_port,
        args.command_topic,
        args.perception_topic,
    )

    teleop_interface.start()

    while True:
        ...


if __name__ == "__main__":
    main()
