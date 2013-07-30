'''
This is not really emulator, actually 1 random value trown at serial port.
For this to work, we must have 2 serial ports in bridge, or one with Serial Loopback.
Used for initial testing of hr_spo2_monitor_driver.py.
'''
import sys, random, time, serial
import threading
import binascii

def connect(s):
    while True:
        data=s.read(60).strip('\r\n')
        if('+++' in data or 'AT&F' in data or 'AT+BTSEC,1,0' in data or 'AT+BTKEY="810657' in data):
            s.write('OK\r\n')
        
        if('ATD' in data):
            s.write('CONNECT\r\n')
            break
        
    while True:
        data=binascii.unhexlify('80FF80FF')
        s.write(data)#+'\r\n')
        time.sleep(1)

def main():
    #port='COM1'
    port='/dev/ttyS0'
    s = serial.Serial(
       port,                         #port number
       baudrate=9600,                #baudrate
       bytesize=serial.EIGHTBITS,    #number of databits
       parity=serial.PARITY_NONE,    #enable parity checking
       stopbits=serial.STOPBITS_ONE, #number of stopbits
       timeout=0.5,                    #set a timeout value
       xonxoff=0,                    #enable software flow control
       rtscts=0,                     #enable RTS/CTS flow control
    )
    
    connect(s)
    
    return 0

if __name__ == '__main__':
   main()