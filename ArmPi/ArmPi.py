#!/usr/bin/python3
# coding=utf8
import sys
import os
import cv2
import time
import queue
import Camera
import logging
import threading
import RPCServer
import MjpgServer
import HiwonderSDK.Board as Board
import Functions.Running as Running

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

QUEUE_RPC = queue.Queue(10)

def startArmPi():
    global HWEXT, HWSONIC

    RPCServer.QUEUE = QUEUE_RPC

    threading.Thread(target=RPCServer.startRPCServer,
                     daemon=True).start()  # rpc server
    threading.Thread(target=MjpgServer.startMjpgServer,
                     daemon=True).start()  # mjpg streamer server
    
    loading_picture = cv2.imread('/home/pi/ArmPi/CameraCalibration/loading.jpg')
    cam = Camera.Camera()  # camera reading
    Running.cam = cam

    while True:
        time.sleep(0.03)

        # executive RPC command that need to be executed in this thread
        while True:
            try:
                req, ret = QUEUE_RPC.get(False)
                event, params, *_ = ret
                ret[2] = req(params)  # executive RPC command
                event.set()
            except:
                break
        #####
        # executive function games program：
        try:
            if Running.RunningFunc > 0 and Running.RunningFunc <= 6:
                if cam.frame is not None:
                    MjpgServer.img_show = Running.CurrentEXE().run(cam.frame.copy())
                else:
                    MjpgServer.img_show = loading_picture
            else:
                cam.frame = None
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    startArmPi()
