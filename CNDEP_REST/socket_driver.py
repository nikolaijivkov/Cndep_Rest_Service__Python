'''
This is actual working data driver that can open and read from UDP socket, producing whatever
data is transmited to the socket. 
This driver can be useful as it is, or can be used and turn to more useful and complex driver.

PUT: ip:port/cndep/protocol/
<protocol>
    <id>1</id>
    <name>socket_reader_protocol</name>
    <type>python</type>
    <executable>socket_driver.py</executable>
    <address>192.168.32.109</address>
    <port>1234</port>
    <sample_rate>5</sample_rate>
</protocol>

PUT: ip:port/cndep/device/
<device>
    <id>1</id>
    <name>socket_reader_device</name>
    <protocol>socket_reader_protocol</protocol>
</device>
'''

import sys, random, time
import threading
from socket import *

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

def main():
    c_exit='0\n'
    c_start='1\n'
    c_stop='2\n'
    c_wait='3\n'
    run=0
    
    try:
        address=str(sys.argv[1])
        port=int(sys.argv[2])
        sample_rate=float(sys.argv[3])
        sys.stderr.write('address: %s, port: %s, sample_rate: %s\n'% (address, port, sample_rate))
    except:
        address='192.168.0.100'
        port=1234
        sample_rate=5
    
    stdin = stdin_Reader()
    
    try:
        sd = socket(AF_INET, SOCK_DGRAM)
        sd.bind((address, port))
        sd.setblocking(0)
    except: 
        sys.stderr.write("driver: socket error\n")
        sys.stdout.write(c_exit)
        sys.stdout.flush()
        stdin.stop()
        sd.close()
        sys.stderr.write("driver: exiting...done (press any key to exit)\n")
        
        return 0
        
    sys.stderr.write("driver: starting\n")
    
    while True:
        time.sleep(1.0/float(sample_rate))# (sample_rate)#
        try:
            command_last=command
        except:
            command_last=''
        command = stdin.read()
        
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
        else:
            pass
        
        if run==1:
            
            payload=''
            
            try:
                payload, src_addr = sd.recvfrom(255)
                #if you want you can check who send that data - src_addr is for that...
            except:
                pass
            
            if( payload!=''):
                #correct payload data shoud look like that: payload='data_name,data_value,data_units'
                #if you want to temper with or check some of that data, you can split them like that:
                #data_name,data_value,data_units=payload.split(',') #just don't forget to make them whole again after you finish:
                #payload='%s,%s,%s'%(data_name,data_value,data_units)
                data=str(payload) 
                sys.stdout.write('%s\n'%data)
                sys.stdout.flush()
    
    sys.stdout.write(c_exit)
    sys.stdout.flush()
    stdin.stop()
    sd.close()
    sys.stderr.write("driver: exiting...done (press any key to exit)\n")
    
    return 0

if __name__ == '__main__':
   main()