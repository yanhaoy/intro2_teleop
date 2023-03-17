import time
import Board
import ActionGroupControl as AGC

print('''
**********************************************************
*********Function:Hiwonder Raspberry Pi expansion board, action group control routine********
**********************************************************
----------------------------------------------------------
Official website:http://www.lobot-robot.com/pc/index/index
Online mall:https://lobot-zone.taobao.com/
----------------------------------------------------------
The following commands need to be used in the LX terminal, which can be opened by ctrl+alt+t, or click
Click the black LX terminal icon in the upper bar.
----------------------------------------------------------
Usage:
    sudo python3 ActionGroupControlDemo.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close the program, if it fails, please try multiple times！
----------------------------------------------------------
''')

# the action group needs to be saved in the path/home/pi/ArmPi/ActionGroups下
AGC.runAction('1') # parameter as action group name, without the suffix, and is passed in as characters
AGC.runAction('2')
