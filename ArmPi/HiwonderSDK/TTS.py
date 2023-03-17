#!/usr/bin/env python3
# coding=utf8
import time
import smbus  # call the Raspberry Pi IIC library
# Hiwonder voice synthesis module using example# 

class TTS:
      
    address = 0x40
    bus = None

    def __init__(self, bus=1):
        self.bus = smbus.SMBus(bus)
    
    def WireReadTTSDataByte(self):
        try:
            val = self.bus.read_byte(self.address)
        except:
            return False
        return True
    
    def TTSModuleSpeak(self, sign, words):
        head = [0xFD,0x00,0x00,0x01,0x00]             # text play command
        wordslist = words.encode("gb2312")            # set the text encoding format to GB2312
        signdata = sign.encode("gb2312")    
        length = len(signdata) + len(wordslist) + 2
        head[1] = length >> 8
        head[2] = length
        head.extend(list(signdata))
        head.extend(list(wordslist))       
        try:
            self.bus.write_i2c_block_data(self.address, 0, head) # send data to slaveframe
        except:
            pass
        time.sleep(0.05)
        
if __name__ == '__main__':
    v = TTS()
    #[h0] set the pronunciation of the word, 0 is automatically determine the pronunciation of the word method, 1 is the letter pronunciation method, 2 is the word pronunciation method
    #[v10] set volume, the volume range is 0-10,10 is the maximum volume
    #[m53] choose the speaker, 3 is Xiaoyan (female), 51 is Xu Jiu (male), 52 is xuduo (male), 53 is Xiaoping (female)
    # for more methods, please refer to the data sheet
    v.TTSModuleSpeak("[h0][v10][m53]","Hello")   
    # note that the length of the characters in the brackets cannot exceed 32, if it exceeds, please divide it into multiple times
    time.sleep(1) # wait for the speech to complete
