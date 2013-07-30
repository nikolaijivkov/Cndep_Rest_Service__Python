"""\
Devepoled in 2012 
@author: eng. Nikolay Jivkov, master student at Technical University of Sofia, branch Plovdiv
email: nikolaijivkov@gmail.com

Useful data driver that comunicate and get data from heart_rate/SPO2 monitoring bluetooth device,
connected with bluetooth_to_serial communication device.
This driver uses:
Parani-SD100/200 - device that create bluethooth_to_serial communication possible.
NONIN Onyx II Model 9560 Bluetooth Fingertip Oximeter - Heart_Rate and SPO2 monitoring device.

This data driver produces 2 values: HR,SPO2.

To use this driver we must:
- add protocol that use this driver;
- add device that use this protocol.
//simple as it sounds//

PUT: ip:port/cndep/protocol/
<protocol>
    <id>1</id>
    <name>hr_spo2_monitor_protocol</name>
    <type>python</type>
    <executable>hr_spo2_monitor_driver.py</executable>
    <address>none</address>
    <port>/dev/ttyAM0</port>
    <sample_rate>5</sample_rate>
</protocol>

PUT: ip:port/cndep/device/
<device>
    <id>1</id>
    <name>hr_spo2_monitor_device</name>
    <protocol>hr_spo2_monitor_protocol</protocol>
</device>
"""

import sys, random, time, serial
import threading
import binascii

class stdin_Reader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.run_flag=1
        self.buff=''
        self.start()
    def run(self):
        while self.run_flag:
            self.buff = sys.stdin.readline()
        print 'stdin_Reader stoped'
    def read(self):
        buff=self.buff
        #self.buff=''
        return buff
    def stop(self):
        self.run_flag=0

def connect(s, stdin, reconnect=0):
    c_exit='0\n'
    
    if(reconnect):
        while True:
            command = stdin.read()
            if command == c_exit:
                sys.stderr.write("driver: reconnect aborted...\n")
                abort=1
                break
            
            s.write('ATD\r\n')
            time.sleep(4)
            data=s.read(30).strip('\r\n')
            sys.stderr.write(data)
            
            if('CONNECT' in data):
                abort=0
                sys.stderr.write('Conected\r\n')
                break #Connected!!!
    else:
        s.write('+++\r\n')
        time.sleep(0.5)
        sys.stderr.write( s.read(10).strip('\r\n'))
            
        s.write('AT&F\r\n')
        time.sleep(0.5)
        sys.stderr.write( s.read(10).strip('\r\n'))
        
        s.write('AT+BTSEC,1,0\r\n')
        time.sleep(0.5)
        sys.stderr.write( s.read(10).strip('\r\n'))
        
        s.write('AT+BTKEY="810657"\r\n')
        time.sleep(0.5)
        sys.stderr.write( s.read(10).strip('\r\n'))
        
        while True:
            command = stdin.read()
            if command == c_exit:
                sys.stderr.write("driver: connect aborted...\n")
                abort=1
                break
            
            s.write('ATD001C050018EA\r\n')
            time.sleep(4)
            data=s.read(30).strip('\r\n')
            #sys.stderr.write(data)
            
            if('CONNECT' in data):
                abort=0
                sys.stderr.write('Conected\r\n')
                break #Connected!!!
        
        if(not abort):
            data=binascii.unhexlify('027002020803')
            s.write(data)#+'\r\n')
            time.sleep(0.5)
            sys.stderr.write( s.read(10))
    
    return abort

def disconnect(s):
    s.write('ATH\r\n')
    time.sleep(0.5)
    sys.stderr.write( s.read(10).strip('\r\n'))
    
    s.write('AT+BTMODE,1\r\n')
    time.sleep(0.5)
    sys.stderr.write( s.read(10).strip('\r\n'))
    
    s.write('ATZ\r\n')
    time.sleep(0.5)
    sys.stderr.write( s.read(10).strip('\r\n'))

def main():
    c_exit='0\n'
    c_start='1\n'
    c_stop='2\n'
    c_wait='3\n'
    run=0
    
    try:
        #address=sys.argv[1]
        port=sys.argv[2]
        sample_rate=float(sys.argv[3])
    except:
        #address=1 #not used in this driver!!!
        port='/dev/ttyAM0'
        sample_rate=2
    
    sys.stderr.write('port: %s, sample_rate: %s\n'% (port, sample_rate))
        
    sys.stderr.write("driver: starting\n")
    stdin = stdin_Reader()
    
    s = serial.Serial(
       port, #port='/dev/ttyAM0',    #port number
       baudrate=9600,                #baudrate
       bytesize=serial.EIGHTBITS,    #number of databits
       parity=serial.PARITY_NONE,    #enable parity checking
       stopbits=serial.STOPBITS_ONE, #number of stopbits
       timeout=1.5,                  #set a timeout value
       xonxoff=0,                    #enable software flow control
       rtscts=0,                     #enable RTS/CTS flow control
    )
    
    abort=connect(s, stdin)
    
    errcount=0
    
    s.flushInput()
    
    #command = c_start
    while True:
        if(abort): 
            break
        time.sleep(sample_rate)# (sample_rate)#
        try:
            command_last=command
        except:
            command_last=''
        command = stdin.read()#command = sys.stdin.readline()
        #sys.stderr.write("Command: %s\n" %command)
        if command == c_exit:
            sys.stderr.write("driver: exiting...\n")
            break
        elif command == c_start:
            if command_last!=command: sys.stderr.write("driver: stared\n")
            run=1
        elif command == c_stop:
            if command_last!=command: sys.stderr.write("driver: stoped\n")
            run=0
        elif command == c_wait:
            sys.stderr.write("driver: waiting\n")
            time.sleep(5)
            continue
        else:
            pass
        
        if run==1:
            try:
                data= s.read(4)
                if(data==''): raise Exception('no data')
                sys.stderr.write(data+'\n')
                xdata0=int(binascii.hexlify(data[0]),16)
                xdata1=int(binascii.hexlify(data[1]),16)
                xdata2=int(binascii.hexlify(data[2]),16)
                
                hr=((xdata0&0x03)<<7)|(xdata1&0x7f)
                spo2=xdata2
                
                sys.stderr.write('SPO2:' + str(spo2) +'\n')
                sys.stdout.write('%s,%s,%s\n'%('SPO2',spo2,'%'))
                sys.stdout.flush()
                
                sys.stderr.write('Heart Rate:' + str(hr) +'\n')
                sys.stdout.write('%s,%s,%s\n'%('HR',hr,'bpm'))
                sys.stdout.flush()
            except Exception,e:
                sys.stderr.write( 'Exception: %s\n' % e)
                if(errcount%5==0):
                    #time.sleep(5)
                    pass
                if(errcount>10):
                    errcount=0
                    sys.stderr.write('Connection Lost! Trying to reconect...\n')
                    if(connect(s, stdin, 1)):
                        break
                else:
                    errcount+=1
    
    if(not abort):
        disconnect(s)
    
    s.close()
    
    sys.stdout.write(c_exit)
    sys.stdout.flush()
    stdin.stop()
    sys.stderr.write("driver: exiting...done (press any key to exit)\n")
    
    return 0

if __name__ == '__main__':
   main()