import time
import Board

print('''
**********************************************************
********Function:Hiwonder Raspberry Pi expansion board, serial servo control routine*******
**********************************************************
----------------------------------------------------------
Official website:http://www.lobot-robot.com/pc/index/index
Online mall:https://lobot-zone.taobao.com/
----------------------------------------------------------

The following commands need to be used in the LX terminal, which can be opened by ctrl+alt+t, or click
Click the black LX terminal icon in the upper bar.
----------------------------------------------------------
Usage:
    sudo python3 BusServoMove.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close the program, if it fails, please try multiple times！
----------------------------------------------------------
''')

while True:
    # Parameter：Parameter1：servo id：parameter1：servo id; parameter 2：position; parameter3：running time
    Board.setBusServoPulse(2, 500, 500) # the servo NO.2 turn to 500 position,it takes 500ms
    time.sleep(0.5) # delay time is the same as running time 
    
    Board.setBusServoPulse(2, 200, 500) # the rotation range of the servo is 0-240°，and thecorresponding pulse width is 0-1000,that is, the range of parameter 2 is 0-1000
    time.sleep(0.5)
    
    Board.setBusServoPulse(2, 500, 200)
    time.sleep(0.2)
    
    Board.setBusServoPulse(2, 200, 200)
    time.sleep(0.2)
    
    Board.setBusServoPulse(2, 500, 500)  
    Board.setBusServoPulse(3, 300, 500)
    time.sleep(0.5)
    
    Board.setBusServoPulse(2, 200, 500)  
    Board.setBusServoPulse(3, 500, 500)
    time.sleep(0.5)    
