'''
This emulator actually get his values from from actual EKG data, writen in EKG_proba.bin file.
For this to work, we must have 2 serial ports in bridge, or one with Serial Loopback.
Used for initial testing of hr_spo2_monitor_driver.py.
'''
import binascii
import time
import inspect
import os
import serial
path=os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))+os.sep

def connect(s):
    while True:
        data=s.read(60).strip('\r\n')
        if('+++' in data or 'AT&F' in data or 'AT+BTSEC,1,0' in data or 'AT+BTKEY="0000' in data):
            s.write('OK\r\n')
        
        if('ATD' in data):
            s.write('CONNECT\r\n')
            print 'conected'
            break
        
    while True:
        fd=open(path+"ekg_proba.bin")
        read_size=16
        while True:
            data=fd.read(read_size)
            if(not data or len(data)!=16): 
                break
            s.write(data)#+'\r\n')
            print 'sending...'
            time.sleep(1)

def main():
    port='COM8'
    #port='/dev/ttyS0'
    s = serial.Serial(
       port,                         #port number
       baudrate=9600,                #baudrate
       bytesize=serial.EIGHTBITS,    #number of databits
       parity=serial.PARITY_NONE,    #enable parity checking
       stopbits=serial.STOPBITS_ONE, #number of stopbits
       timeout=0.5,                  #set a timeout value
       xonxoff=0,                    #enable software flow control
       rtscts=0,                     #enable RTS/CTS flow control
    )
    
    connect(s)
    
    return 0

if __name__ == '__main__':
   main()