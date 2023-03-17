import time
import Board

print('''
**********************************************************
********Function:Hiwonder Raspberry Pi expansion board, serial servo control routine，buzzer control routine*********
**********************************************************
----------------------------------------------------------
Official website:http://www.lobot-robot.com/pc/index/index
Online mall:https://lobot-zone.taobao.com/
----------------------------------------------------------
The following commands need to be used in the LX terminal, which can be opened by ctrl+alt+t, or click
Click the black LX terminal icon in the upper bar
----------------------------------------------------------
Usage:
    sudo python3 BuzzerControlDemo.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close the program, if it fails, please try multiple times!
----------------------------------------------------------
''')

Board.setBuzzer(0) # close

Board.setBuzzer(1) # open 
time.sleep(0.1) # delay
Board.setBuzzer(0) # close 

time.sleep(1) # delay

Board.setBuzzer(1)
time.sleep(0.5)
Board.setBuzzer(0)