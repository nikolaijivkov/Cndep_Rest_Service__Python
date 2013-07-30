"""\
Devepoled in 2012 
@author: eng. Nikolay Jivkov, master student at Technical University of Sofia, branch Plovdiv
email: nikolaijivkov@gmail.com

Useful data driver that comunicate and get data from EKG monitoring bluetooth device,
connected with bluetooth_to_serial communication device (Parani-SD100/200).

This data driver produces 12 values: EKG_I,EKG_II,EKG_III,EKG_avR,EKG_avL,EKG_avF,EKG_V1,EKG_V2,EKG_V3,EKG_V4,EKG_V5,EKG_V6.

To use this driver we must:
- add protocol that use this driver;
- add device that use this protocol.
//simple as it sounds//

PUT: ip:port/cndep/protocol/
<protocol>
    <id>1</id>
    <name>ekg_monitor_protocol</name>
    <type>python</type>
    <executable>ekg_monitor_driver.py</executable>
    <address>none</address>
    <port>/dev/ttyAM0</port>
    <sample_rate>2</sample_rate>
</protocol>

PUT: ip:port/cndep/device/
<device>
    <id>1</id>
    <name>ekg_monitor_device</name>
    <protocol>ekg_monitor_protocol</protocol>
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
                break
            
            s.write('ATD\r\n')
            time.sleep(4)
            data=s.read(30)
            sys.stderr.write(data)
            
            if('CONNECT' in data):
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
        
        s.write('AT+BTKEY="0000"\r\n')
        time.sleep(0.5)
        sys.stderr.write( s.read(10).strip('\r\n'))
        
        while True:
            command = stdin.read()
            if command == c_exit:
                sys.stderr.write("driver: reconnect aborted...\n")
                break
            
            s.write('ATD0013D36804B5\r\n')
            time.sleep(4)
            data=s.read(30)
            sys.stderr.write(data)
            
            if('CONNECT' in data):
                break #Connected!!!
            
        s.read(16)
    
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
    
    #port='/dev/ttyAM0'
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
    
    abort=connect(s, stdin)
    
    errcount=0
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
                data= s.read(16)
                if(data=='' or len(data)!=16): raise Exception('no data')
                
                #sys.stdout.write('%s,%s,%s\n'%('EKG',data.encode('hex'),'HEX'))
                #sys.stdout.flush()
                
                Ch0=int(data[0:2].encode('hex'),16)
                Ch1=int(data[2:4].encode('hex'),16)
                Ch2=int(data[4:6].encode('hex'),16)
                Ch3=int(data[6:8].encode('hex'),16)
                Ch4=int(data[8:10].encode('hex'),16)
                Ch5=int(data[10:12].encode('hex'),16)
                Ch6=int(data[12:14].encode('hex'),16)
                Ch7=int(data[14:16].encode('hex'),16)
                
                I=Ch4-Ch0
                II=-Ch0
                III=-Ch4
                avR=Ch0-Ch4/2
                avL=Ch4-Ch0/2
                avF=-(Ch0+Ch4)/2
                V1=Ch1-(Ch0+Ch4)/3
                V2=Ch5-(Ch0+Ch4)/3
                V3=Ch2-(Ch0+Ch4)/3
                V4=Ch6-(Ch0+Ch4)/3
                V5=Ch3-(Ch0+Ch4)/3
                V6=Ch7-(Ch0+Ch4)/3
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_I',I,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_II',II,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_III',III,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_avR',avR,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_avL',avL,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_avF',avF,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_V1',V1,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_V2',V2,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_V3',V3,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_V4',V4,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_V5',V5,'mV'))
                sys.stdout.flush()
                
                sys.stdout.write('%s,%s,%s\n'%('EKG_V6',V6,'mV'))
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