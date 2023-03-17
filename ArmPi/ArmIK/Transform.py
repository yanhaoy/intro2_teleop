#!/usr/bin/env python3
# encoding:utf-8
import cv2
import sys
sys.path.append('/home/pi/ArmPi/')
import math
import numpy as np
from CameraCalibration.CalibrationConfig import *

# the robot arm origin is the center of the station, the distance from the center of the cemera screen, unit cm 
image_center_distance = 20

# load parameter
param_data = np.load(map_param_path + '.npz')

# calculate the actual distance corresponding to each pixel
map_param_ = param_data['map_param']

# data mapping
# mapping a number form one range to another
def leMap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# convert the pixel coordinates of the graphics to the coordinate system of the robotic arm
# upload coordinates and image resolution, for example (100, 100, (640, 320))
def convertCoordinate(x, y, size):
    x = leMap(x, 0, size[0], 0, 640)
    x = x - 320
    x_ = round(x * map_param_, 2)

    y = leMap(y, 0, size[1], 0, 480)
    y = 240 - y
    y_ = round(y * map_param_ + image_center_distance, 2)

    return x_, y_

# convert length to image pixel leght
# upload coordinates and image resolution, for example (10, (640, 320))
def world2pixel(l, size):
    l_ = round(l/map_param_, 2)

    l_ = leMap(l_, 0, 640, 0, size[0])

    return l_

# get the roi area  of the detected object
# load cv2.boxPoints(rect) reture four vertices values, and return extreme points
def getROI(box):
    x_min = min(box[0, 0], box[1, 0], box[2, 0], box[3, 0])
    x_max = max(box[0, 0], box[1, 0], box[2, 0], box[3, 0])
    y_min = min(box[0, 1], box[1, 1], box[2, 1], box[3, 1])
    y_max = max(box[0, 1], box[1, 1], box[2, 1], box[3, 1])

    return (x_min, x_max, y_min, y_max)

# all become black except for the roi area
# load graphics,roi area,graphics resolution
def getMaskROI(frame, roi, size):
    x_min, x_max, y_min, y_max = roi
    x_min -= 10
    x_max += 10
    y_min -= 10
    y_max += 10

    if x_min < 0:
        x_min = 0
    if x_max > size[0]:
        x_max = size[0]
    if y_min < 0:
        y_min = 0
    if y_max > size[1]:
        y_max = size[1]

    black_img = np.zeros([size[1], size[0]], dtype=np.uint8)
    black_img = cv2.cvtColor(black_img, cv2.COLOR_GRAY2RGB)
    black_img[y_min:y_max, x_min:x_max] = frame[y_min:y_max, x_min:x_max]
    
    return black_img

# get the center coordinates of the block
# load in the rect object returned by the minAreaRect function,the extreme point of the block, the image resolution, the side length of the block
def getCenter(rect, roi, size, square_length):
    x_min, x_max, y_min, y_max = roi
    # according to the coordinates of the center of the wood block, the vertex closest to the center of the image is selected as the basis for calculating the accurate center
    if rect[0][0] >= size[0]/2:
        x = x_max 
    else:
        x = x_min
    if rect[0][1] >= size[1]/2:
        y = y_max
    else:
        y = y_min

    # calculate the diagonal length of the block
    square_l = square_length/math.cos(math.pi/4)

    # convert length to pixel length
    square_l = world2pixel(square_l, size)

    # calculate the center point based on the rotation angle of the block
    dx = abs(math.cos(math.radians(45 - abs(rect[2]))))
    dy = abs(math.sin(math.radians(45 + abs(rect[2]))))
    if rect[0][0] >= size[0] / 2:
        x = round(x - (square_l/2) * dx, 2)
    else:
        x = round(x + (square_l/2) * dx, 2)
    if rect[0][1] >= size[1] / 2:
        y = round(y - (square_l/2) * dy, 2)
    else:
        y = round(y + (square_l/2) * dy, 2)

    return  x, y

# get the angle of rotation
# parameters: the end coordinates of the robot arm, the rotation angle of the wooden block
def getAngle(x, y, angle):
    theta6 = round(math.degrees(math.atan2(abs(x), abs(y))), 1)
    angle = abs(angle)
    
    if x < 0:
        if y < 0:
            angle1 = -(90 + theta6 - angle)
        else:
            angle1 = theta6 - angle
    else:
        if y < 0:
            angle1 = theta6 + angle
        else:
            angle1 = 90 - theta6 - angle

    if angle1 > 0:
        angle2 = angle1 - 90
    else:
        angle2 = angle1 + 90

    if abs(angle1) < abs(angle2):
        servo_angle = int(500 + round(angle1 * 1000 / 240))
    else:
        servo_angle = int(500 + round(angle2 * 1000 / 240))
    return servo_angle
