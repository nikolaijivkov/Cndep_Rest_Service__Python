import sys, random, time, serial
import threading
import binascii

def connect(s):
    s.write('+++\r\n')
        
    s.write('AT&F\r\n')
    
    s.write('AT+BTSEC,1,0\r\n')
    
    s.write('AT+BTKEY="810657"\r\n')
    
    s.write('ATD0013D36804B5\r\n')
    
    s.flushinput()
    
    print s.read(4)
    
    print s.read(4)
    
    s.write('+++\r\n')
    
    s.write('ATH\r\n')

def main():
    
    port='/dev/ttyS0'
    s = serial.Serial(
       port,                         #port number
       baudrate=9600,                #baudrate
       bytesize=serial.EIGHTBITS,    #number of databits
       parity=serial.PARITY_NONE,    #enable parity checking
       stopbits=serial.STOPBITS_ONE, #number of stopbits
       timeout=4,                    #set a timeout value
       xonxoff=0,                    #enable software flow control
       rtscts=0,                     #enable RTS/CTS flow control
    )
    
    start = time.clock()
    connect(s)
    elapsed = (time.clock() - start)
    
    print 'with clock:', elapsed
    
    
    start = time.clock()
    connect(s)
    elapsed = (time.clock() - start)
    
    print 'with clock:', elapsed
    
    
    start = time.clock()
    connect(s)
    elapsed = (time.clock() - start)
    
    print 'with clock:', elapsed
    
    
    start = time.time()
    connect(s)
    elapsed = (time.time() - start)
    
    print 'with time:', elapsed
    
    start = time.time()
    connect(s)
    elapsed = (time.time() - start)
    
    print 'with time:', elapsed
    
    start = time.time()
    connect(s)
    elapsed = (time.time() - start)
    
    print 'with time:', elapsed
    
    return 0

if __name__ == '__main__':
   main()