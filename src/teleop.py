import json
import sys
import time
from typing import Tuple, Callable, Optional, Any

import cv2
import numpy as np
import pygame
import zmq


class JoydeviceBinder:
    """Bind a joydevice part to a specific message callback"""

    _binds = {}  # type: ignore
    _topic_name = ""

    def __init__(
        self,
        event_id: int,
        event_type: int,
        cmd_id: Tuple[int],
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
        cls._topic_name = topic

    @classmethod
    def get_bind(
        cls,
        event: pygame.event.Event,
        event_attr: str,
    ) -> Optional[Any]:
        event_id = getattr(event, event_attr)
        return cls._binds.get((event.type, event_id))

    def create_msg(self):
        """Create message for the"""

        return [
            bytes(self._topic_name + " " + str(self.cmd_id[i]) + msg, "utf-8")
            for i, msg in enumerate(self.msg_cb(self.event_id))
        ]


class TeleOpInterface:
    def __init__(self) -> None:
        pass
