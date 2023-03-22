import atexit
import json
import os
import sys
import threading
import time
from argparse import ArgumentParser, Namespace
from typing import Callable, Tuple

import cv2
import zmq

sys.path.append(os.path.join(os.path.dirname(__file__), "ArmPi"))

import ArmIK.ArmMoveIK as arm_ik  # noqa
import Camera  # noqa
import HiwonderSDK.Board as Board  # noqa

AK = arm_ik.ArmIK()


class ArmStateInterface:
    """State of the ArmPi robotic arm."""

    def __init__(
        self,
        x: int,
        y: int,
        z: int,
        alpha: int,
        claw_open: bool,  # Initial claw state
        claw_rotate: int,  # Initial claw angle value
        x_range: Tuple[int, int],
        y_range: Tuple[int, int],
        z_range: Tuple[int, int],
        alpha_range: Tuple[int, int],
    ):
        """
        Create a new arm state interface.

        Args:
            x (int): The initial x position.
            y (int): The initial y position.
            z (int): The initial z position.
            alpha (int): The initial pitch angle of the end effector.
            claw_open (bool): Indicates whether or not the claw is open at startup.
            claw_rotate (int): The initial end effector rotation angle.
            x_range (Tuple[int, int]): The range of valid x positions.
            y_range (Tuple[int, int]): The range of valid y positions.
            z_range (Tuple[int, int]): The range of valid z positions.
            alpha_range (Tuple[int, int]): The range of valid alpha values.
        """
        # Set coordinates
        self._x = x
        self._y = y
        self._z = z
        self._alpha = alpha
        self._claw_open = claw_open
        self._claw_rotate = claw_rotate

        # Set coordinate ranges
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.alpha_range = alpha_range

    def __repr__(self):
        return f"(x: {self._x}, y: {self._y}, z: {self._z}, alpha: {self._alpha})"

    @property
    def x(self) -> int:
        """
        The x coordinate of the robot end effector.

        Returns:
            int: The current x coordinate.
        """
        return self._x

    @x.setter
    def x(self, x: int):
        """
        Set the x coordinate of the robot end effector.

        Note that this must be within the valid x range.

        Args:
            x (int): The current x coordinate of the end effector.
        """
        if x in self.x_range:
            self._x = x

    @property
    def y(self) -> int:
        """
        The y coordinate of the robot end effector.

        Returns:
            int: The current y coordinate.
        """
        return self._y

    @y.setter
    def y(self, y: int):
        """
        Set the y coordinate of the robot end effector.

        Note that this must be within the valid y range.

        Args:
            y (int): The current y coordinate of the end effector.
        """
        if y in self.y_range:
            self._y = y

    @property
    def z(self) -> int:
        """
        The z coordinate of the robot end effector.

        Returns:
            int: The current z coordinate.
        """
        return self._z

    @z.setter
    def z(self, z: int):
        """
        Set the z coordinate of the robot end effector.

        Note that this must be within the valid z range.

        Args:
            z (int): The current z coordinate of the end effector.
        """
        if z in self.z_range:
            self._z = z

    @property
    def alpha(self) -> int:
        """
        The pitch angle of the end effector.

        Returns:
            int: The current pitch angle.
        """
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: int):
        """
        Set the pitch angle of the robot end effector.

        Note that this must be within the valid alpha range.

        Args:
            alpha (int): The current pitch angle of the end effector.
        """
        if alpha in self.alpha_range:
            self._alpha = alpha

    @property
    def claw_open(self) -> bool:
        """
        The current state of the claw (i.e., open or closed).

        Returns:
            bool: True if the claw is open, false if otherwise.
        """
        return self._claw_open

    @property
    def claw_rotate(self) -> int:
        """
        The rotation angle of the gripper.

        Returns:
            int: The current rotation angle of the gripper.
        """
        return self._claw_rotate

    def set_coord(
        self,
        coord: str,
        mod_val: int,
    ):
        """
        Increment/decrement the value of the given coordinate.

        Args:
            coord (str): The coordinate to modify. This should be a property of the
                ArmState class.
            mod_val (int): The amount to modify the coordinate by.
        """
        curr_val = getattr(self, coord)

        if curr_val is not None:
            setattr(self, coord, curr_val + mod_val)
            AK.setPitchRangeMoving(
                (self.x, self.y, self.z),
                self.alpha,
                self.alpha_range[0],
                self.alpha_range[1],
                1500,
            )

            if self.claw_open:
                Board.setBusServoPulse(1, 220, 500)
            else:
                Board.setBusServoPulse(1, 500, 500)

            Board.setBusServoPulse(2, self.claw_rotate, 500)


class Command:
    """Command to call through"""

    _cmds = {}  # type: ignore

    def __init__(
        self,
        cmd_id: int,
        cmd: Callable[[str], None],
    ):
        """
        Register a new command.

        Args:
            cmd_id (int): The ID to associate the command with.
            cmd (Callable[[str], None]): The callback to execute when a command with the
                associated ID is received.
        """
        self.cmd = cmd
        self.cmd_id = cmd_id

        self._cmds[cmd_id] = self  # Register command into class

    @classmethod
    def run_command(cls, cmd_id: int, *args):
        """Run command with the given command id"""
        cmd_obj = cls._cmds.get(cmd_id)

        if cmd_obj is not None:
            cmd_obj.cmd(*args)
        else:
            print(f"Command with id {cmd_id} has not been registered")


class NetworkInterface:
    """Network interface used to facilitate communication between robot and teleop."""

    def __init__(
        self,
        ip: str,
        video_port_out: int,
        command_port_in: int,
        command_topic: str = "control",
        perception_topic: str = "perception",
    ) -> None:
        """
        Create a new network interface.

        Args:
            ip (str): The IP address of the teleop computer.
            video_port_out (int): The port that the video feed should be streamed over.
            command_port_in (int): The port that the commands will be sent over.
            command_topic (str, optional): The topic that commands will be sent on.
                Defaults to "control".
            perception_topic (str, optional): The topic that the video will be streamed
                over. Defaults to "perception".
        """
        self.camera = Camera.Camera()
        self.camera.camera_open()

        # We only need one I/O thread; we are processing less than 1 GB/s
        self.context = zmq.Context()

        # Flag used to control the threads
        self._running = False

        self._control_thread = threading.Thread(
            target=self._handle_control_cmds,
            args=(f"tcp://{ip}:{command_port_in}", command_topic),
        )
        self._control_thread.setDaemon(True)

        self._video_thread = threading.Thread(
            target=self._stream_video_feed,
            args=(f"tcp://*:{video_port_out}", perception_topic),
        )
        self._video_thread.setDaemon(True)

        # Register a destructor to join the threads
        atexit.register(self._stop)

    def start(self) -> None:
        """Start the network interface."""
        self._running = True
        self._control_thread.start()
        self._video_thread.start()

    def _stop(self) -> None:
        """Stop the network interface."""
        self._running = False
        self._control_thread.join()
        self._video_thread.join()

    def _handle_control_cmds(self, address: str, topic: str) -> None:
        """
        Read control commands and execute them on the robot.

        This method is responsible for polling the command topic and executing any
        commands sent using the RobotStateInterface.

        Args:
            address (str): The address create a new socket at.
            topic (str): The topic that will control commands will be published on.
        """
        # Configure a subscriber to receive the control commands
        socket = self.context.socket(zmq.SUB)
        socket.setsockopt(zmq.CONFLATE, 1)  # Take only the last element
        socket.connect(address)
        socket.setsockopt(zmq.SUBSCRIBE, bytes(topic, "utf-8"))

        while self._running:
            try:
                res = socket.recv(flags=zmq.NOBLOCK)

                topic, msg = res.decode("utf-8").split()
                cmd_id = int(msg[0])
                args = msg[1:]

                Command.run_command(cmd_id, args)
            except zmq.Again:
                ...

            time.sleep(0.01)

    def _stream_video_feed(self, address: str, topic: str) -> None:
        """
        Stream the robot video feed.

        Args:
            address (str): The address that should be used to create the video feed
                socket.
            topic (str): The topic that should be used to publish the video feed.
        """
        socket = self.context.socket(zmq.PUB)
        socket.bind(address)

        def mogrify(topic, msg):
            """Encode the message into JSON and prepend the topic"""
            return topic + " " + json.dumps(msg)

        while self._running:
            img = self.camera.frame

            if img is None:
                continue

            message = cv2.imencode(".jpg", img)[1].tolist()
            socket.send(bytes(mogrify(topic, message), "utf-8"))

            time.sleep(0.5)


def wrap_command(arm_state: ArmStateInterface, move: str, coord: str):
    """
    Wrap a command to support integration with the network interface.

    Args:
        arm_state (ArmStateInterface): The arm state interface to use for executing
            commands.
        move (str): The direction to move.
        coord (str): The end effector coordinate that should be configured.
    """

    value = 0
    if move == "f":
        value = 1
    elif move == "b":
        value = -1

    arm_state.set_coord(coord, value)


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
        default="192.168.149.39",
        help="IP address of the teleop computer.",
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
        help="The topic that should be subscribed to to receive control commands.",
    )
    parser.add_argument(
        "video_port",
        type=int,
        default=5557,
        help="The port that the video will be streamed on.",
    )

    return parser.parse_args()


def main() -> None:
    args = get_args()

    # Arm interface used to track the current position of the arm and control its pose.
    arm_state = ArmStateInterface(
        0, 10, 10, -90, False, 500, (0, 10), (0, 10), (3, 10), (-90, 0)
    )

    # Register commands for the robot
    Command(0, lambda move: wrap_command(arm_state, move, "x"))
    Command(1, lambda move: wrap_command(arm_state, move, "y"))
    Command(2, lambda move: wrap_command(arm_state, move, "alpha"))
    Command(
        3, lambda direction: arm_state.set_coord("z", 0 if direction == "f" else -1)
    )
    Command(4, lambda direction: arm_state.set_coord("z", 0 if direction == "f" else 1))

    # Create a new control interface to process commands and stream video feed.
    control_interface = NetworkInterface(
        args.ip, args.video_port, args.command_port, args.command_topic
    )
    control_interface.start()

    while True:
        ...


if __name__ == "__main__":
    main()
