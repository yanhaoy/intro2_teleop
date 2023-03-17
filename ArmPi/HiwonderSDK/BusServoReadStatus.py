import time
import Board

print('''
**********************************************************
*****Function:Hiwonder Raspberry Pi expansion board, serial servo control routine******
**********************************************************
----------------------------------------------------------
Official website:http://www.lobot-robot.com/pc/index/index
Online mall:https://lobot-zone.taobao.com/
----------------------------------------------------------
The following commands need to be used in the LX terminal, which can be opened by ctrl+alt+t, or click
Click the black LX terminal icon in the upper bar.
----------------------------------------------------------
Usage:
    sudo python3 BusServoReadStatus.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close the program, if it fails, please try multiple times！
----------------------------------------------------------
''')

def getBusServoStatus():
    Pulse = Board.getBusServoPulse(2) # get the NO.2 servo postion information
    Temp = Board.getBusServoTemp(2) # get the NO.2 servo temperature information
    Vin = Board.getBusServoVin(2) # get the NO.2 servo voltage information
    print('Pulse: {}\nTemp:  {}\nVin:   {}\n'.format(Pulse, Temp, Vin)) # print statue information
    time.sleep(0.5) # delay easy to view

while True:   
    Board.setBusServoPulse(2, 500, 1000) # the servo NO.2 turn to 500 position,it takes 500ms
    time.sleep(1)
    getBusServoStatus()
    Board.setBusServoPulse(2, 300, 1000)
    time.sleep(1)
    getBusServoStatus()
