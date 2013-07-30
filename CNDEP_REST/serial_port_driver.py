'''
This is a sample of data driver that can read/write from serial port, it is not actual working device driver.
It writes '...something...' and reads from serial port and pring the result. Produces random 'humidity' data,
only to show how exactly result data can be transfered to cndep_rest.py.
This sample can be turned to useful driver vary easily and that is his main purpose.

PUT: ip:port/cndep/protocol/
<protocol>
    <id>1</id>
    <name>serial_port_protocol</name>
    <type>python</type>
    <executable>serial_port_driver.py</executable>
    <address>none</address>
    <port>/dev/ttyAM0</port>
    <sample_rate>5</sample_rate>
</protocol>

PUT: ip:port/cndep/device/
<device>
    <id>1</id>
    <name>serial_port_device</name>
    <protocol>serial_port_protocol</protocol>
</device>
'''

import sys, random, time, serial
import threading

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
        address=sys.argv[1]
        port=sys.argv[2]
        sample_rate=float(sys.argv[3])
        sys.stderr.write('address: %s, port: %s, sample_rate: %s\n'% (address, port, sample_rate))
    except:
        address=1
        port=0
        sample_rate=3
        
    sys.stderr.write("driver: starting\n")
    stdin = stdin_Reader()
    s = serial.Serial(port, timeout=1)
    
    print s.portstr
    
    while True:
        time.sleep(sample_rate)
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
            continue
        else:
            pass
        
        if run==1:
            s.write('...something...\r\n')
            data=s.read(30).strip('\r\n')
            if(data!=''):
                sys.stderr.write('%s\r\n'%data)
                sys.stderr.flush()
            
            #'''
            #data_value is random generated!!! 
            #On the line down you can see:(data_name ,data_value ,data_units)
            data_name='humidity'
            data_value=random.randint(10,80)
            data_units='%'
            sys.stdout.write('%s,%s,%s\n'%(data_name,data_value,data_units))
            sys.stdout.flush()
            #'''
    sys.stdout.write(c_exit)
    sys.stdout.flush()
    stdin.stop()
    sys.stderr.write("driver: exiting...done (press any key to exit)\n")
    
    return 0

if __name__ == '__main__':
   main()