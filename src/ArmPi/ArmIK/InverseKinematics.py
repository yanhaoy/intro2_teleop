#!/usr/bin/env python3
# encoding: utf-8
# 4-DOF manipulator inverse kinematics: according to corresponding coordinates (X, Y, Z), and the pitch angle, calculate the rotation angle of each joint
# 2020/07/20 Aiden
import logging
from math import *

# CRITICAL, ERROR, WARNING, INFO, DEBUG
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class IK:
    # counting the servo from bottom to top
    # common parameter,is 4-DOF robot arm connecting level parameter
    l1 = 6.10    # the distance from the robot arm chassis center to the second servo center axis is 6.10cm
    l2 = 10.16   # the distance from the second servo to third servo is 10.16cm 
    l3 = 9.64    # the distancee from the thrid servo to fourth servo is  9.64cm 
    l4 = 0.00    # there is no specific assignment, accroding to the selection during initialization to re-assignment 

    # air pump specific parameters
    l5 = 4.70  # the distance from the fourth servo to above the nozzle is 4.7cm
    l6 = 4.46  # the distance from the top of the nozzle to the nozzle is 4.46cm
    alpha = degrees(atan(l6 / l5))  # calculate the angle between 15 and 14

    def __init__(self, arm_type): # accroding to different types of grippers, adapt parameter
        self.arm_type = arm_type
        if self.arm_type == 'pump': # if it is an the air pump robot arm 
            self.l4 = sqrt(pow(self.l5, 2) + pow(self.l6, 2))  # the fourth servo to the nozzle as the fourth stand
        elif self.arm_type == 'arm':
            self.l4 = 16.65  # the distance from the fourth servo to the end of the robot arm is 16.6cm. The end robot arm is means the claws are fully closed

    def setLinkLength(self, L1=l1, L2=l2, L3=l3, L4=l4, L5=l5, L6=l6):
        # change the robot arm stand leght,in order to adapt to the same structure and different length of the robotic arm
        self.l1 = L1
        self.l2 = L2
        self.l3 = L3
        self.l4 = L4
        self.l5 = L5
        self.l6 = L6
        if self.arm_type == 'pump':
            self.l4 = sqrt(pow(self.l5, 2) + pow(self.l6, 2))
            self.alpha = degrees(atan(self.l6 / self.l5))

    def getLinkLength(self):
        # get the currently set stand length
        if self.arm_type == 'pump':
            return {"L1":self.l1, "L2":self.l2, "L3":self.l3, "L4":self.l4, "L5":self.l5, "L6":self.l6}
        else:
            return {"L1":self.l1, "L2":self.l2, "L3":self.l3, "L4":self.l4}

    def getRotationAngle(self, coordinate_data, Alpha):
        # False given the specified coordinates and pitch angle, return the angle that each joint should rotate, if there is no solution, return False
        # coordinate_data is the end coordinates of the gripper, the coordinate unit is cm, which is passed in as a tuple, for example (0, 5, 10)
        # Alpha is the angle between the holder and the horizontal plane, in degrees

        # set the end of the holder be P(X, Y, Z), the origin of the coordinates is O, the origin is the projection of the center of the gimbal on the ground, and the projection of point P on the ground is P_
        # the intersection of l1 and l2 is A, the intersection of l2 and l3 is B, and the intersection of l3 and l4 is C
        # CD and PD are perpendicular, CD and z axis are perpendicular, the pitch angle Alpha is the angle between DC and PC, AE is perpendicular to DP_, and E is on DP_, CF is perpendicular to AE, and F is on AE
        # included angle representation: For example, the included angle between AB and BC is expressed as ABC
        X, Y, Z = coordinate_data
        if self.arm_type == 'pump':
            Alpha -= self.alpha
        # get the rotation angle of the base
        theta6 = degrees(atan2(Y, X))
 
        P_O = sqrt(X*X + Y*Y) # the distance from p_to origin o 
        CD = self.l4 * cos(radians(Alpha))
        PD = self.l4 * sin(radians(Alpha)) # when the pitch angle is positive, PD is positive, when the pitch angle is negative, PD is negative
        AF = P_O - CD
        CF = Z - self.l1 - PD
        AC = sqrt(pow(AF, 2) + pow(CF, 2))
        if round(CF, 4) < -self.l1:
            logger.debug('高度低于0, CF(%s)<l1(%s)', CF, -self.l1)
            return False
        if self.l2 + self.l3 < round(AC, 4): # the sum of the two sides length is less than the third side 
            logger.debug('不能构成连杆结构, l2(%s) + l3(%s) < AC(%s)', self.l2, self.l3, AC)
            return False

        # get theat4
        cos_ABC = round(-(pow(AC, 2)- pow(self.l2, 2) - pow(self.l3, 2))/(2*self.l2*self.l3), 4) # The Law of Cosines
        if abs(cos_ABC) > 1:
            logger.debug('不能构成连杆结构, abs(cos_ABC(%s)) > 1', cos_ABC)
            return False
        ABC = acos(cos_ABC) # inverse triangle to calculate radians
        theta4 = 180.0 - degrees(ABC)

        # get theta5
        CAF = acos(AF / AC)
        cos_BAC = round((pow(AC, 2) + pow(self.l2, 2) - pow(self.l3, 2))/(2*self.l2*AC), 4) # The Law of Cosines
        if abs(cos_BAC) > 1:
            logger.debug('不能构成连杆结构, abs(cos_BAC(%s)) > 1', cos_BAC)
            return False
        if CF < 0:
            zf_flag = -1
        else:
            zf_flag = 1
        theta5 = degrees(CAF * zf_flag + acos(cos_BAC))

        # get theta3
        theta3 = Alpha - theta5 + theta4
        if self.arm_type == 'pump':
            theta3 += self.alpha

        return {"theta3":theta3, "theta4":theta4, "theta5":theta5, "theta6":theta6} # when there is a solution return to angle dictionary
            
if __name__ == '__main__':
    ik = IK('arm')
    ik.setLinkLength(L1=ik.l1 + 0.89, L4=ik.l4 - 0.3)
    print('连杆长度：', ik.getLinkLength())
    print(ik.getRotationAngle((0, 0, ik.l1 + ik.l2 + ik.l3 + ik.l4), 90))
