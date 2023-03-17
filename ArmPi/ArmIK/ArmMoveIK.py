#!/usr/bin/env python3
# encoding:utf-8
import sys
sys.path.append('/home/pi/ArmPi/')
import time
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
from ArmIK.InverseKinematics import *
from ArmIK.Transform import getAngle
from mpl_toolkits.mplot3d import Axes3D
from HiwonderSDK.Board import setBusServoPulse, getBusServoPulse

# the robot arm moves accroding to the angle calculated by inverse kinematics
ik = IK('arm')
# set stand length
l1 = ik.l1 + 0.75
l4 = ik.l4 - 0.15
ik.setLinkLength(L1=l1, L4=l4)

class ArmIK:
    servo3Range = (0, 1000, 0, 240) # pulse width, angle 
    servo4Range = (0, 1000, 0, 240)
    servo5Range = (0, 1000, 0, 240)
    servo6Range = (0, 1000, 0, 240)

    def __init__(self):
        self.setServoRange()

    def setServoRange(self, servo3_Range=servo3Range, servo4_Range=servo4Range, servo5_Range=servo5Range, servo6_Range=servo6Range):
        # Adapt to different servos 
        self.servo3Range = servo3_Range
        self.servo4Range = servo4_Range
        self.servo5Range = servo5_Range
        self.servo6Range = servo6_Range
        self.servo3Param = (self.servo3Range[1] - self.servo3Range[0]) / (self.servo3Range[3] - self.servo3Range[2])
        self.servo4Param = (self.servo4Range[1] - self.servo4Range[0]) / (self.servo4Range[3] - self.servo4Range[2])
        self.servo5Param = (self.servo5Range[1] - self.servo5Range[0]) / (self.servo5Range[3] - self.servo5Range[2])
        self.servo6Param = (self.servo6Range[1] - self.servo6Range[0]) / (self.servo6Range[3] - self.servo6Range[2])

    def transformAngelAdaptArm(self, theta3, theta4, theta5, theta6):
        # convert the angle calculated through inverse kinematics into the pulse width value corresponding to the servo
        servo3 = int(round(theta3 * self.servo3Param + (self.servo3Range[1] + self.servo3Range[0])/2))
        if servo3 > self.servo3Range[1] or servo3 < self.servo3Range[0] + 60:
            logger.info('servo3(%s)超出范围(%s, %s)', servo3, self.servo3Range[0] + 60, self.servo3Range[1])
            return False

        servo4 = int(round(theta4 * self.servo4Param + (self.servo4Range[1] + self.servo4Range[0])/2))
        if servo4 > self.servo4Range[1] or servo4 < self.servo4Range[0]:
            logger.info('servo4(%s)超出范围(%s, %s)', servo4, self.servo4Range[0], self.servo4Range[1])
            return False

        servo5 = int(round((self.servo5Range[1] + self.servo5Range[0])/2 - (90.0 - theta5) * self.servo5Param))
        if servo5 > ((self.servo5Range[1] + self.servo5Range[0])/2 + 90*self.servo5Param) or servo5 < ((self.servo5Range[1] + self.servo5Range[0])/2 - 90*self.servo5Param):
            logger.info('servo5(%s)超出范围(%s, %s)', servo5, self.servo5Range[0], self.servo5Range[1])
            return False
        
        if theta6 < -(self.servo6Range[3] - self.servo6Range[2])/2:
            servo6 = int(round(((self.servo6Range[3] - self.servo6Range[2])/2 + (90 + (180 + theta6))) * self.servo6Param))
        else:
            servo6 = int(round(((self.servo6Range[3] - self.servo6Range[2])/2 - (90 - theta6)) * self.servo6Param))
        if servo6 > self.servo6Range[1] or servo6 < self.servo6Range[0]:
            logger.info('servo6(%s)超出范围(%s, %s)', servo6, self.servo6Range[0], self.servo6Range[1])
            return False

        return {"servo3": servo3, "servo4": servo4, "servo5": servo5, "servo6": servo6}

    def servosMove(self, servos, movetime=None):
        # mover No.3,4,5,6 servos to rotate
        time.sleep(0.02)
        if movetime is None:
            max_d = 0
            for i in  range(0, 4):
                d = abs(getBusServoPulse(i + 3) - servos[i])
                if d > max_d:
                    max_d = d
            movetime = int(max_d*4)
        setBusServoPulse(3, servos[0], movetime)
        setBusServoPulse(4, servos[1], movetime)
        setBusServoPulse(5, servos[2], movetime)
        setBusServoPulse(6, servos[3], movetime)

        return movetime

    def setPitchRange(self, coordinate_data, alpha1, alpha2, da = 1):
        # given the range of coordinate_data and pitch angle alpha1, alpha2, automatically find a suitable solution in the range
        # if there is no solution, return False, otherwise return the corresponding servo angle, pitch angle
        # coordinate unit cm, passed in as a tuple, for example (0, 5, 10)
        # da is the angle that is increased each time the pitch angle is traversed
        x, y, z = coordinate_data
        if alpha1 >= alpha2:
            da = -da
        for alpha in np.arange(alpha1, alpha2, da):# traversal solution
            result = ik.getRotationAngle((x, y, z), alpha)
            if result:
                theta3, theta4, theta5, theta6 = result['theta3'], result['theta4'], result['theta5'], result['theta6']
                servos = self.transformAngelAdaptArm(theta3, theta4, theta5, theta6)
                if servos != False:
                    return servos, alpha

        return False

    def setPitchRangeMoving(self, coordinate_data, alpha, alpha1, alpha2, movetime=None):
        # given coordinate_data and pitch angle alpha, and the range of pitch angle range alpha1, alpha2, automatically find the solution closest to the given pitch angle and turn to the target position
        # if there is no solution, return False, otherwise return the servo angle, pitch angle, and running time
        # coordinate unit cm, passed in as a tuple, for example (0, 5, 10)
        # alpha is the given pitch angle
        # alpha1 and alpha2 are the range of pitch angle
        # movetime is the rotation time of the steering gear, in ms, if no time is given, it will be calculated automatically
        x, y, z = coordinate_data
        result1 = self.setPitchRange((x, y, z), alpha, alpha1)
        result2 = self.setPitchRange((x, y, z), alpha, alpha2)
        if result1 != False:
            data = result1
            if result2 != False:
                if abs(result2[1] - alpha) < abs(result1[1] - alpha):
                    data = result2
        else:
            if result2 != False:
                data = result2
            else:
                return False
        servos, alpha = data[0], data[1]

        movetime = self.servosMove((servos["servo3"], servos["servo4"], servos["servo5"], servos["servo6"]), movetime)

        return servos, alpha, movetime
    '''
    #for test
    def drawMoveRange2D(self, x_min, x_max, dx, y_min, y_max, dy, z, a_min, a_max, da):
        # the test reachable point is displayed in the form of 2d graph, z is fixed
        # test reachable points, displayed in the form of 3d graphs, if there are too many points, the 3d graphs will be more difficult to rotate
        try:
            for y in np.arange(y_min, y_max, dy):
                for x in np.arange(x_min, x_max, dx):
                    result = self.setPitchRange((x, y, z), a_min, a_max, da)
                    if result:
                        plt.scatter(x, y, s=np.pi, c='r')

            plt.xlabel('X Label')
            plt.ylabel('Y Label')

            plt.show()
        except Exception as e:
            print(e)
            pass

    def drawMoveRange3D(self, x_min, x_max, dx, y_min, y_max, dy, z_min, z_max, dz, a_min, a_max, da):
        # the test reachable points are displayed in the form of 3d graphs. If there are too many points, the 3d graphs will be more difficult to rotate
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        try:
            for z in np.arange(z_min, z_max, dz):
                for y in np.arange(y_min, y_max, dy):
                    for x in np.arange(x_min, x_max, dx):
                        result = self.setPitchRange((x, y, z), a_min, a_max, da)
                        if result:
                            ax.scatter(x, y, z, s=np.pi, c='r')

            ax.set_xlabel('X Label')
            ax.set_ylabel('Y Label')
            ax.set_zlabel('Z Label')

            plt.show()
        except Exception as e:
            print(e)
            pass
    '''

if __name__ == "__main__":
    AK = ArmIK()
    setBusServoPulse(1, 200, 500)
    setBusServoPulse(2, 500, 500)
    #AK.setPitchRangeMoving((0, 10, 10), -30, -90, 0, 2000)
    #time.sleep(2)
    print(AK.setPitchRangeMoving((-4.8, 15, 1.5), 0, -90, 0, 2000))
    #AK.drawMoveRange2D(-10, 10, 0.2, 10, 30, 0.2, 2.5, -90, 90, 1)
