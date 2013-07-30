"""\
Devepoled in 2012 
@author: eng. Nikolay Jivkov, master student at Technical University of Sofia, branch Plovdiv
email: nikolaijivkov@gmail.com

This is a sample of data driver that can produce random 'humidity' and 'temp' data, 
only to show how exactly result data can be transfered to cndep_rest.py.
This sample can be turned to useful driver vary easily and that is his main purpose.

PUT: ip:port/cndep/protocol/
<protocol>
    <id>1</id>
    <name>random_temp_protocol</name>
    <type>python</type>
    <executable>random_temp_driver.py</executable>
    <address>none</address>
    <port>none</port>
    <sample_rate>5</sample_rate>
</protocol>

PUT: ip:port/cndep/device/
<device>
    <id>1</id>
    <name>random_temp_device</name>
    <protocol>random_temp_protocol</protocol>
</device>
"""

import sys, random, time
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
        port=2
        sample_rate=5
        
    sys.stderr.write("driver: starting\n")
    stdin = stdin_Reader()
    
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
        else:
            pass
        
        if run==1:
            rand=random.randint(1,100)
            if rand<=33:
                sys.stdout.write('%s,%s,%s\n'%('temperature',random.randint(-20,70),'C degree'))
            elif rand<=66:
                sys.stdout.write('%s,%s,%s\n'%('humidity',random.randint(10,80),'%'))
            else:
                sys.stdout.write('%s,%s,%s\n'%('temperature',random.randint(-20,70),'C degree'))
                sys.stdout.write('%s,%s,%s\n'%('humidity',random.randint(10,80),'%'))
            sys.stdout.flush()
    
    sys.stdout.write(c_exit)
    sys.stdout.flush()
    stdin.stop()
    sys.stderr.write("driver: exiting...done (press any key to exit)\n")
    
    return 0

if __name__ == '__main__':
   main()