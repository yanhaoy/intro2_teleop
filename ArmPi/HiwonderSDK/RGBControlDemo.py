import time
import Board
import signal

print('''
**********************************************************
********Function:Hiwonder Raspberry Pi expansion board，RGB light control routine**********
**********************************************************
----------------------------------------------------------
Official website:http://www.lobot-robot.com/pc/index/index
Online mall:https://lobot-zone.taobao.com/
----------------------------------------------------------
The following commands need to be used in the LX terminal, which can be opened by ctrl+alt+t, or click
Click the black LX terminal icon in the upper bar
----------------------------------------------------------
Usage:
    sudo python3 RGBControlDemo.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close the program, if it fails, please try multiple times!
----------------------------------------------------------
''')

start = True
# processing before closing
def Stop(signum, frame):
    global start

    start = False
    print('关闭中...')

# turn off all lights first
Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
Board.RGB.show()

signal.signal(signal.SIGINT, Stop)

while True:
    # set two lights to red
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
    Board.RGB.show()
    time.sleep(1)
    
    # set two lights to green
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
    Board.RGB.show()
    time.sleep(1)
    
    # set two lights to blue
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
    Board.RGB.show()
    time.sleep(1)
    
    # set two lights to yellow
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 255, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(255, 255, 0))
    Board.RGB.show()
    time.sleep(1)

    if not start:
        # trun off all lights
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()
        print('已关闭')
        break
