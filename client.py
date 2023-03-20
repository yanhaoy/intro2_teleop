#!/usr/bin/env python3

import os  # nopep8
import sys  # nopep8
import time
import typing

import zmq

fpath = os.path.join(os.path.dirname(__file__), "ArmPi")  # nopep8
sys.path.insert(0, fpath)  # nopep8

from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *


AK = ArmIK()

class Command:
    """Command to call through"""
    
    _cmds = {}  # Registered commands
    
    def __init__(
        self,
        cmd_id: int,
        cmd: typing.Callable[[str], None],
    ):
        
        self.cmd = cmd
        self.cmd_id = cmd_id

        self._cmds[cmd_id] = self  # Register command into class
    
    @classmethod
    def run_command(
        cls,
        cmd_id: int,
        *args
    ):
        """Run command with the given command id"""
        
        cmd_obj = cls._cmds.get(cmd_id)
        if cmd_obj is not None:
            cmd_obj.cmd(*args)
        else:
            print(f"Command with id {cmd_id} has not been registered")


class ArmState:
    """State of the ArmPi robotic arm"""
    
    def __init__(
        self,
        x: int,  # Initial x value
        y: int,  # Initial y value
        z: int,  # Initial z value
        alpha: int,  # Initial alpha value
        x_range: typing.Tuple[int, int],
        y_range: typing.Tuple[int, int],
        z_range: typing.Tuple[int, int],
        alpha_range: typing.Tuple[int, int],
    ):
        # Set coordinates
        self._x = x
        self._y = y
        self._z = z
        self._alpha = alpha
        
        # Set coordinate ranges
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.alpha_range = alpha_range
    
    def __repr__(self):
        
        return f"(x: {self._x}, y: {self._y}, z: {self._z}, alpha: {self._alpha})"
    
    @property
    def x(self):
        """X coordinate of the gripper"""
        
        return self._x

    @x.setter
    def x(self, x: int):
        
        if self.x_range[0] <= x <= self.x_range[1]:
            self._x = x
    
    @property
    def y(self):
        """Y coordinate of the gripper"""
        
        return self._y

    @y.setter
    def y(self, y: int):
        
        if self.y_range[0] <= y <= self.y_range[1]:
            self._y = y

    @property
    def z(self):
        """Z coordinate of the gripper"""
        
        return self._z

    @z.setter
    def z(self, z: int):
        
        if self.z_range[0] <= z <= self.z_range[1]:
            self._z = z
    
    @property
    def alpha(self):
        """Pitch angle of the gripper"""
        
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: int):
        
        if self.alpha_range[0] <= alpha <= self.alpha_range[1]:
            self._alpha = alpha
            
    def set_coord(
        self,
        coord: str,
        mod_val: int,
    ):
        """Shorthand to increment/decrement value of given coordinate by the given value"""
        
        curr_val = getattr(self, coord)
        if curr_val is not None:
            setattr(self, coord, curr_val + mod_val)
            AK.setPitchRangeMoving((self.x, self.y, self.z), self.alpha, self.alpha_range[0], self.alpha_range[1], 1500)


def run_client(
    socket: zmq.Socket
):
    
    while True:
        try:
            res = socket.recv(flags=zmq.NOBLOCK)  # Asynchronous communication using noblock
            topic, msg = res.decode("utf-8").split()
            print("Client receives: " + msg + " at the topic: " + topic)
            cmd_id = int(msg[0])
            args = msg[1:]
            Command.run_command(cmd_id, args)

        except zmq.Again as e:
            # If not received, do something else
            print("No new message received yet")
    
    

# Helper function for the set coordinate method

def command_wrapper(arm_state: ArmState, move: str, coord: str):
    """Shorthand wrapper to facilitate """
    
    value = 0
    if move == "f":
        value = 1
    elif move == "b":
        value = -1
    
    arm_state.set_coord(coord, value)


if __name__ == "__main__":

    # Set the port
    port = "5556"  # It should be fine to use the default
    if len(sys.argv) > 1:
        port = sys.argv[1]
        int(port)
    
    # Arm state to keep track and manipulate the arm
    arm_state = ArmState(0, 10, 10, -30, (0, 10), (0, 10), (3, 10), (-30, -90))

    # Commands for manipulating the arm (these can be replaced by something more elaborate later)
    
    Command(0, lambda move: command_wrapper(arm_state, move, "x"))
    Command(1, lambda move: command_wrapper(arm_state, move, "y"))
    Command(2, lambda move: command_wrapper(arm_state, move, "alpha"))
    Command(3, lambda direction: arm_state.set_coord("z", 0 if direction == "f" else -1))
    Command(4, lambda direction: arm_state.set_coord("z", 0 if direction == "f" else 1))

    # Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.CONFLATE, 1)  # Take only the last element
    socket.connect(
        "tcp://192.168.149.39:%s" % port
    )  # I hope this IP is constant, otherwise change it to your laptop's IP

    # Set topic filter
    topicfilter = "control"  # This should match the server's topic name
    socket.setsockopt(zmq.SUBSCRIBE, bytes(topicfilter, "utf-8"))

