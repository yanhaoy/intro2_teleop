#!/usr/bin/env python3
# encoding: utf-8
import time
import serial
import pigpio
import ctypes
#Hiwonder bus servo communication protocol#

LOBOT_SERVO_FRAME_HEADER         = 0x55
LOBOT_SERVO_MOVE_TIME_WRITE      = 1
LOBOT_SERVO_MOVE_TIME_READ       = 2
LOBOT_SERVO_MOVE_TIME_WAIT_WRITE = 7
LOBOT_SERVO_MOVE_TIME_WAIT_READ  = 8
LOBOT_SERVO_MOVE_START           = 11
LOBOT_SERVO_MOVE_STOP            = 12
LOBOT_SERVO_ID_WRITE             = 13
LOBOT_SERVO_ID_READ              = 14
LOBOT_SERVO_ANGLE_OFFSET_ADJUST  = 17
LOBOT_SERVO_ANGLE_OFFSET_WRITE   = 18
LOBOT_SERVO_ANGLE_OFFSET_READ    = 19
LOBOT_SERVO_ANGLE_LIMIT_WRITE    = 20
LOBOT_SERVO_ANGLE_LIMIT_READ     = 21
LOBOT_SERVO_VIN_LIMIT_WRITE      = 22
LOBOT_SERVO_VIN_LIMIT_READ       = 23
LOBOT_SERVO_TEMP_MAX_LIMIT_WRITE = 24
LOBOT_SERVO_TEMP_MAX_LIMIT_READ  = 25
LOBOT_SERVO_TEMP_READ            = 26
LOBOT_SERVO_VIN_READ             = 27
LOBOT_SERVO_POS_READ             = 28
LOBOT_SERVO_OR_MOTOR_MODE_WRITE  = 29
LOBOT_SERVO_OR_MOTOR_MODE_READ   = 30
LOBOT_SERVO_LOAD_OR_UNLOAD_WRITE = 31
LOBOT_SERVO_LOAD_OR_UNLOAD_READ  = 32
LOBOT_SERVO_LED_CTRL_WRITE       = 33
LOBOT_SERVO_LED_CTRL_READ        = 34
LOBOT_SERVO_LED_ERROR_WRITE      = 35
LOBOT_SERVO_LED_ERROR_READ       = 36

pi = pigpio.pi()  # initialize pigpio library
serialHandle = serial.Serial("/dev/ttyAMA0", 115200)  # initialize serial, the baud rate is 115200

rx_pin = 4
tx_pin = 27

def portInit():  # configurate uses IO port 
    pi.set_mode(rx_pin, pigpio.OUTPUT)  # configurate RX_CON that is GPIO17 as output
    pi.write(rx_pin, 0)
    pi.set_mode(tx_pin, pigpio.OUTPUT)  # configurate TX_CON that is GPIO17 as output 
    pi.write(tx_pin, 1)

portInit()

def portWrite():  # configurate single-wire serial is output 
    pi.write(tx_pin, 1)  # pull up TX_CON that is GPIO27
    pi.write(rx_pin, 0)  # pull down RX_CON that is GPIO17

def portRead():  # configurate single-wire serial is input 
    pi.write(rx_pin, 1)  # pull up TX_CON that is GPIO17 
    pi.write(tx_pin, 0)  # pull up TX_CON that is GPIO27 

def portRest():
    time.sleep(0.1)
    serialHandle.close()
    pi.write(rx_pin, 1)
    pi.write(tx_pin, 1)
    serialHandle.open()
    time.sleep(0.1)

def checksum(buf):
    # calculate the checksum
    sum = 0x00
    for b in buf:  # sum 
        sum += b
    sum = sum - 0x55 - 0x55  # remove two 0x55 at the beginning of the command 
    sum = ~sum  # reverse
    return sum & 0xff

def serial_serro_wirte_cmd(id=None, w_cmd=None, dat1=None, dat2=None):
    '''
    写指令
    :param id:
    :param w_cmd:
    :param dat1:
    :param dat2:
    :return:
    '''
    portWrite()
    buf = bytearray(b'\x55\x55')  # frame header
    buf.append(id)
    # command hength
    if dat1 is None and dat2 is None:
        buf.append(3)
    elif dat1 is not None and dat2 is None:
        buf.append(4)
    elif dat1 is not None and dat2 is not None:
        buf.append(7)

    buf.append(w_cmd)  # command
    # wirte data
    if dat1 is None and dat2 is None:
        pass
    elif dat1 is not None and dat2 is None:
        buf.append(dat1 & 0xff)  # deviation
    elif dat1 is not None and dat2 is not None:
        buf.extend([(0xff & dat1), (0xff & (dat1 >> 8))])  # divide the lower 8 bits, the upper 8 bits into the cache
        buf.extend([(0xff & dat2), (0xff & (dat2 >> 8))])  # divide the lower 8 bits, the upper 8 bits into the cache
    # checksum
    buf.append(checksum(buf))
    # for i in buf:
    #     print('%x' %i)
    serialHandle.write(buf)  # send

def serial_servo_read_cmd(id=None, r_cmd=None):
    '''
    send read command 
    :param id:
    :param r_cmd:
    :param dat:
    :return:
    '''
    portWrite()
    buf = bytearray(b'\x55\x55')  # frame header
    buf.append(id)
    buf.append(3)  # command hength
    buf.append(r_cmd)  # command
    buf.append(checksum(buf))  # checksum
    serialHandle.write(buf)  # send
    time.sleep(0.00034)

def serial_servo_get_rmsg(cmd):
    '''
    # get the data of the specified read command
    :param cmd: read command
    :return: data
    '''
    serialHandle.flushInput()  # clear the receive cache 
    portRead()  # configure single-wire serial port as input 
    time.sleep(0.005)  # delay for a while and wait for the reception to be completed
    count = serialHandle.inWaiting()    # get the bytes number in the receive cache  
    if count != 0:  # if received data is not empty
        recv_data = serialHandle.read(count)  # read the received data
        # for i in recv_data:
        #     print('%#x' %ord(i))
        # if read id command
        try:
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == cmd:
                dat_len = recv_data[3]
                serialHandle.flushInput()  # clear the receive cache 
                if dat_len == 4:
                    # print ctypes.c_int8(ord(recv_data[5])).value    # convent the signed integer
                    return recv_data[5]
                elif dat_len == 5:
                    pos = 0xffff & (recv_data[5] | (0xff00 & (recv_data[6] << 8)))
                    return ctypes.c_int16(pos).value
                elif dat_len == 7:
                    pos1 = 0xffff & (recv_data[5] | (0xff00 & (recv_data[6] << 8)))
                    pos2 = 0xffff & (recv_data[7] | (0xff00 & (recv_data[8] << 8)))
                    return ctypes.c_int16(pos1).value, ctypes.c_int16(pos2).value
            else:
                return None
        except BaseException as e:
            print(e)
    else:
        serialHandle.flushInput()  # clear the receive cache
        return None
