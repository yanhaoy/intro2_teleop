#!/usr/bin/env python3
# coding=utf8
'''
 * Only Chinese characters can be recognized, and the Chinese characters to be recognized are converted into pinyin letters, with spaces between each Chinese character, such as:Hiwonder --> huan er ke ji
 * Add up to 50 entries, each entry can be up to 79 characters long, and each entry can have up to 10 Chinese characters
 * each entry corresponds to an identification number (optionally set from 1 to 255). Different voice entries can correspond to the same identification number.
 * for example, the identification number can be set to the same value for both "Hiwonder Technology" and "Hiwonder"
 * STA status light on the module: when it is on, it means that the voice is being recognized, and when it is off, it means that the voice will not be recognized. When the voice is recognized, the status light will dim or flash, and the current status indication will be restored after waiting for reading.
'''
import smbus
import time
import numpy
# Hiwonder Voice Recognition Module Routine #

class ASR:

    # Global Variables
    address = 0x79
    bus = None
    
    ASR_RESULT_ADDR = 100
    # recognition result storage place, by constantly reading the value of this address to judge whether the voice is recognized, different values correspond to different voices

    ASR_WORDS_ERASE_ADDR = 101
    # erase all entries

    ASR_MODE_ADDR = 102
    # recognition mode setting, value range 1~3
    #1：cycle recognition mode. The status light is always on (default mode)    
    #2：password mode, with the first entry as the password. The status light is always off, when the password is recognized, it is always on, waiting for a new voice to be recognized, and the recognition result will be off after reading the recognition result
    #3：in key mode, press to start recognition, not to not recognize. Support power-down save. The status light will light up when the button is pressed, and it will not light up if it is not pressed

    ASR_ADD_WORDS_ADDR = 160
    # entry add address, support power-down save

    def __init__(self, bus=1):
        self.bus = smbus.SMBus(bus)
        
    def readByte(self):
        try:
            result = self.bus.read_byte(self.address)
        except:
            return None
        return result

    def writeByte(self, val):
        try:
            value = self.bus.write_byte(self.address, val)
        except:
            return False
        if value != 0:
            return False
        return True
    
    def writeData(self, reg, val):
        try:
            self.bus.write_byte(self.address,  reg)
            self.bus.write_byte(self.address,  val)
        except:
            pass

    def getResult(self):
        if ASR.writeByte(self, self.ASR_RESULT_ADDR):
            return -1        
        try:
            value = self.bus.read_byte(self.address)
        except:
            return None
        return value

    '''
    * add entry function
    * idNum：entry corresponding to the identification number, from 1 to 255. When the voice of the entry corresponding to the number is recognized
    *        the identification number will be stored in ASR_RESULT_ADDR, waiting for the mainframe to read, and cleared after reading
    * words：to identify the pinyin of Chinese character entries, separate Chinese characters with spaces
    * 
    * when this function is executed, the entries are automatically added in the queue later.   
    '''
    def addWords(self, idNum, words):
        buf = [idNum]       
        for i in range(0, len(words)):
            buf.append(eval(hex(ord(words[i]))))
        try:
            self.bus.write_i2c_block_data(self.address, self.ASR_ADD_WORDS_ADDR, buf)
        except:
            pass
        time.sleep(0.1)
        
    def eraseWords(self):
        try:
            result = self.bus.write_byte_data(self.address, self.ASR_WORDS_ERASE_ADDR, 0)
        except:
            return False
        time.sleep(0.1)
        if result != 0:
           return False
        return True
    
    def setMode(self, mode): 
        try:
            result = self.bus.write_byte_data(self.address, self.ASR_MODE_ADDR, mode)
        except:
            return False
        time.sleep(0.1)
        if result != 0:
           return False
        return True
        
if __name__ == "__main__":
    asr = ASR()

    # added entry and recognition mode can be saved after power-off. After the first setting is completed, you can change 1 to 0
    if 1:
        asr.eraseWords()
        asr.setMode(2)
        asr.addWords(1, 'kai shi')
        asr.addWords(2, 'fen jian hong se')
        asr.addWords(3, 'fen jian lv se')
        asr.addWords(4, 'fen jian lan se')
    while 1:
        data = asr.getResult()
        if data:
            print("result:", data)
