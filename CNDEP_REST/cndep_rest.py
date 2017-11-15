"""\ 
CNDEP Restful Web Service.    
Provide a meaning to do Restful oriented service, capable of extracting sensor data (real or emulated) and converting that data in simple xml.

EXAMPLE:
http://192.168.0.100:8080/cndep/data/all?from=2012-9-20,16:27:0&to=2012-9-20,16:27:50

#===============================================================
METHOD: GET
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/data/all[?last&from=2012-09-20,16:20:0&to=2012-09-21,16:20:0]

URL: http://192.168.0.100:8080/cndep/data/{id}[?last&from=2012-09-20,16:20:0&to=2012-09-21,16:20:0]

URL: http://192.168.0.100:8080/cndep/data/{name}[?last&from=2012-09-20,16:20:0&to=2012-09-21,16:20:0]

URL: http://192.168.0.100:8080/cndep/data/{id}/{name}[?last&from=2012-09-20,16:20:0&to=2012-09-21,16:20:0]
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/device/all[?last]
URL: http://192.168.0.100:8080/cndep/device/{id}[?last]
URL: http://192.168.0.100:8080/cndep/device/{name}[?last]
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/protocol/all[?last]
URL: http://192.168.0.100:8080/cndep/protocol/{id}[?last]
URL: http://192.168.0.100:8080/cndep/protocol/{name}[?last]
#---------------------------------------------------------------
#===============================================================
METHOD: PUT, POST
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/device
Body:
<?xml version="1.0" ?>
<device>
    <id>1</id>
    <name>null_device</name>
    <protocol>random_temp</protocol>
    <sample_rate>5</sample_rate>
    <monitoring_data>temperature,humidity</monitoring_data>
</device>
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/device
Body:
<?xml version="1.0" ?>
<device>
    <id>1</id>
    <name>socket_device</name>
    <protocol>socket_reader</protocol>
    <address>192.168.32.109</address>
    <port>1234</port>
    <sample_rate>5</sample_rate>
</device>
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/protocol
Body:
<?xml version="1.0" ?>
<protocol>
    <id>1</id>
    <name>random_temp</name>
    <type>python</type>
    <executable>random_temp_driver.py</executable>
    <address>none</address>
    <port>none</port>
    <sample_rate>5</sample_rate>
</protocol>
#---------------------------------------------------------------
#===============================================================
METHOD: DELETE
#---------------------------------------------------------------
URL: http://192.168.0.100:8080/cndep/device/{id}
URL: http://192.168.0.100:8080/cndep/protocol/{id}
#deleting a device will delete all data that it produced
#---------------------------------------------------------------
"""
from itty import * #web REST framework
try:
    import xml.etree.ElementTree as ET
except:
    import etree.ElementTree as ET
try:
    import sqlite3 as lite
except:
    from pysqlite2 import dbapi2 as lite
import sys, subprocess, threading, time, datetime, inspect, socket
#-----------------------------------------------------------------------------------
debug=0
#-----------------------------------------------------------------------------------
@error(404)
def not_found(request, exception):
    #'Not Found'
    builder=ET.TreeBuilder()
    
    builder.start('response', {'status':'404'})
    
    builder.start('message', {})
    builder.data('Not Found: '+str(exception))
    builder.end('message')
    
    xml=builder.end('response')
    
    xml_str=ET.tostring(xml, encoding="utf8")
    response = Response(xml_str, status=404, content_type='text/xml')
    return response.send(request._start_response)

@error(409)
def conflict(request, exception):
    #'Conflict'
    builder=ET.TreeBuilder()
    
    builder.start('response', {'status':'409'})
    
    builder.start('message', {})
    builder.data('conflict: '+str(exception))
    builder.end('message')
    
    xml=builder.end('response')
    
    xml_str=ET.tostring(xml, encoding="utf8")
    response = Response(xml_str, status=409, content_type='text/xml')
    return response.send(request._start_response)
    
@error(500)
def app_error(request, exception):
    #'Application Error'
    builder=ET.TreeBuilder()
    
    builder.start('response', {'status':'500'})
    
    builder.start('message', {})
    builder.data('application error: '+str(exception))
    builder.end('message')
    
    xml=builder.end('response')
    
    xml_str=ET.tostring(xml, encoding="utf8")
    response = Response(xml_str, status=500, content_type='text/xml')
    return response.send(request._start_response)

ClassHolder={'last_added':0}

#path initialization
path=os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))+os.sep
if sys.platform.startswith('win'): alt_path=os.environ['USERPROFILE']+os.sep
elif sys.platform.startswith('linux'): alt_path=os.environ['HOME']+os.sep

db_path=path

class DeviceClass: #threading.Thread
    def __init__(self, id, name, protocol='', address='', port='', sample_rate='', monitoring_data=''):
        #threading.Thread.__init__(self)
        self.id=id
        self.name=name
        self.protocol=protocol
        self.address=address
        self.port=port
        self.sample_rate=sample_rate
        self.monitoring_data=monitoring_data
        
        self.thread_starter()
        
        if( debug): print 'Object %s named %s created!'% (id, name)
        
    def thread_starter(self):
        self.run_flag=1
        self.save_to_del=0
        
        self.t=threading.Thread(None,self.run)
        self.t.start()
        #self.start()
        
    def thread_stoper(self):
        c_exit='0\n'
        self.command=c_exit
        try:
            self.process.stdin.write(self.command)
        except:
            pass
        time.sleep(0.5)
        self.run_flag=0
        
    #def worker_thread(self):
    def run(self):
        c_exit='0\n'
        c_start='1\n'
        c_stop='2\n'
        c_wait='3\n'
        
        data={}
        data['table']='Data_Table'
        data['device_id']=self.id
        
        rows=SQL_to_Data(name=self.protocol, table='Protocol_Table')
        if( rows==[]) :
            if( debug): print "No records found in DB for protocol %s!"% self.protocol
            self.save_to_del=1
            return
            
        row=rows[0]
        if self.address=='': self.address=row['Address']#'192.168.0.1'
        if self.port=='': self.port=row['Port']#8080
        if self.sample_rate=='': self.sample_rate=row['Sample_rate']#10
        
        execute=row['Type']
        
        if(os.path.exists(path+row['Executable'])):
            self.process = subprocess.Popen([execute , path+row['Executable'], str(self.address), str(self.port), str(self.sample_rate)],  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        elif(os.path.exists(alt_path+row['Executable'])):
            self.process = subprocess.Popen([execute , alt_path+row['Executable'], str(self.address), str(self.port), str(self.sample_rate)],  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        elif(os.path.exists(row['Executable'])):
            self.process = subprocess.Popen([execute , row['Executable'], str(self.address), str(self.port), str(self.sample_rate)],  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        else: 
            if( debug): print "Executable %s not found!"%row['Executable']
            self.save_to_del=1
            return
        self.command=c_start
        
        self.process.stdin.write(self.command)
        while(self.run_flag==1):
            result=self.process.stdout.readline().strip('\r\n')
            
            if( result==c_exit.strip('\n')):
                break
            else:
                try:
                    data['name'],data['value'],data['unit']=result.split(',')
                except Exception, e:
                    if( debug): print "Exception: %s"%e
                    if( debug): print "Except result: "+result
                    time.sleep(10)
                    continue

                if( self.monitoring_data=='' or data['name'] in self.monitoring_data.split(',')):
                    if( debug): print result
                    Data_to_SQL(data)
                else: 
                    if( debug): print "data ignored"
        
        self.process.stdin.write(self.command)
        if( debug): print 'Subprocess ended!'
        self.save_to_del=1
        
    def __del__(self):
        try:
            self.thread_stoper()
            
            while(self.save_to_del==0):
                time.sleep(0.5)
        except: 
            pass

def Pre_Add_device():
    rows=SQL_to_Data(table='Device_Table')
    for row in rows:
        Add_device(row['Id'], row['Name'], row['Protocol'], row['Address'], row['Port'], row['Sample_Rate'], row['Monitoring_Data'], 1)

def Add_device(id, name='', protocol='', address='', port='', sample_rate='', monitoring_data='', is_from_DB=0):
    if( type(id)!=int):
        if( debug): print 'Device id not integer!'
        return -1
    
    else:
        while(True):
            if ClassHolder.has_key(id):
                id+=1
            else: break
            
        ClassHolder['last_added']=id
        ClassHolder[id]=DeviceClass(id, name, protocol, address, port, sample_rate, monitoring_data)
        
        if( is_from_DB==0):
            data={}
            data['table']='Device_Table'
            data['id']=id
            data['name']=name
            data['protocol']=protocol
            data['address']=address
            data['port']=port
            data['sample_rate']=sample_rate
            data['monitoring_data']=monitoring_data
            Data_to_SQL(data,'INSERT')
        
        return id

def Edit_device(id, name='', protocol='', address='', port='', sample_rate='', monitoring_data=''):
    if( type(id)!=int):
        if( debug): print 'Device id not integer!'
        return -1
    
    elif( ClassHolder.has_key(id)==False):
        if( debug): print 'Device not found!'
        return -2
    
    else:
        if name=='' : name=ClassHolder[id].name
        if protocol=='' : protocol=ClassHolder[id].protocol
        if address=='' : address=ClassHolder[id].address
        if port=='' : port=ClassHolder[id].port
        if sample_rate=='' : sample_rate=ClassHolder[id].sample_rate
        if monitoring_data=='' : monitoring_data=ClassHolder[id].monitoring_data
        
        old_sample_rate=ClassHolder[id].sample_rate
        
        if( protocol==ClassHolder[id].protocol and address==ClassHolder[id].address and port==ClassHolder[id].port and sample_rate==ClassHolder[id].sample_rate):
            ClassHolder[id].name=name
            ClassHolder[id].monitoring_data=monitoring_data
        else:
            ClassHolder[id].thread_stoper()
            
            ClassHolder[id].name=name
            ClassHolder[id].protocol=protocol
            ClassHolder[id].address=address
            ClassHolder[id].port=port
            ClassHolder[id].sample_rate=sample_rate
            ClassHolder[id].monitoring_data=monitoring_data
            
            #time.sleep(1/float(old_sample_rate))
            
            ClassHolder[id].thread_starter()
        
        data={}
        data['table']='Device_Table'
        data['id']=id
        data['name']=name
        data['protocol']=protocol
        data['address']=address
        data['port']=port
        data['sample_rate']=sample_rate
        data['monitoring_data']=monitoring_data
        
        Data_to_SQL(data,'UPDATE')
        
        return id

def Remove_device(id,DB_Remove=0):
    if( type(id)!=int):
        if( debug): print 'Device id not integer!'
        return -1
    
    elif( ClassHolder.has_key(id)==False):
        if( debug): print 'Device not found!'
        return -2
    
    else:
        ClassHolder[id].__del__()
        del ClassHolder[id]
        if( debug): print 'Device deleted!'
        
        if(DB_Remove):
            data={}
            
            data['id']=id
            
            data['table']='Device_Table'
            Data_to_SQL(data,'DELETE')
            
            data['table']='Data_Table'
            Data_to_SQL(data,'DELETE')
        return 1

def Data_to_SQL(data='', command='INSERT'):
    db=db_path+'rest.db'
    
    con = lite.connect(db)
    
    if command=='CREATE':
        try:
            cur = con.cursor()    
            
            cur.execute("DROP TABLE IF EXISTS Data_Table")
            cur.execute("CREATE TABLE Data_Table (Id INTEGER PRIMARY KEY, Device_Id INT, Name TEXT, Value TEXT, Unit TEXT, Time_Stamp TEXT)")
            
            cur.execute("DROP TABLE IF EXISTS Device_Table")
            cur.execute("CREATE TABLE Device_Table (Id INTEGER PRIMARY KEY, Name TEXT, Protocol TEXT, Address TEXT, Port TEXT, Sample_Rate TEXT, Monitoring_Data TEXT)")
            
            cur.execute("DROP TABLE IF EXISTS Protocol_Table")
            cur.execute("CREATE TABLE Protocol_Table (Id INTEGER PRIMARY KEY, Name TEXT, Type TEXT, Executable TEXT, Address TEXT, Port TEXT, Sample_Rate TEXT)")
            
            con.commit()
            
        except lite.Error, e:
            if( debug): print "Error %s:" %e.args[0]
            con.rollback()
            
        if con:
            con.close()
        
    elif command=='INSERT':
        try:
            cur = con.cursor()
            #time_stamp=('%s'% datetime.datetime.now())[:19]
            time_stamp=time.time()
            if(data['table']=='Data_Table'): 
                cur.execute("INSERT INTO %s VALUES(NULL,?,?,?,?,?)"% data['table'],(data['device_id'],data['name'],data['value'],data['unit'],time_stamp))
            elif(data['table']=='Device_Table'):
                if(data['id']=='NULL'): cur.execute("INSERT INTO %s VALUES(NULL,?,?,?,?,?,?)"% data['table'],(data['name'],data['protocol'],data['address'],data['port'],data['sample_rate'],data['monitoring_data']))
                else: cur.execute("INSERT INTO %s VALUES(?,?,?,?,?,?,?)"% data['table'],(data['id'],data['name'],data['protocol'],data['address'],data['port'],data['sample_rate'],data['monitoring_data']))
            elif(data['table']=='Protocol_Table'):
                if(data['id']=='NULL'): cur.execute("INSERT INTO %s VALUES(NULL,?,?,?,?,?,?)"% data['table'],(data['name'],data['type'],data['executable'],data['address'],data['port'],data['sample_rate']))
                else: cur.execute("INSERT INTO %s VALUES(?,?,?,?,?,?,?)"% data['table'],(data['id'],data['name'],data['type'],data['executable'],data['address'],data['port'],data['sample_rate']))
            con.commit()
            
        except lite.Error, e:
            if( debug): print "Error %s:" %e.args[0]
            con.rollback()
            
    elif command=='UPDATE':
        try:
            cur = con.cursor()
            if(data['table']=='Data_Table'): 
                cur.execute("UPDATE %s SET Value=? WHERE Id=?"% data['table'], (data['value'], data['id']))
            elif(data['table']=='Device_Table'):
                cur.execute("UPDATE %s SET Name=?, Protocol=?, Address=?, Port=?, Sample_Rate=?, Monitoring_Data=? WHERE Id=?"% data['table'], (data['name'],data['protocol'],data['address'],data['port'],data['sample_rate'],data['monitoring_data'],data['id']))
            elif(data['table']=='Protocol_Table'):
                cur.execute("UPDATE %s SET Name=?, Type=?, Executable=?, Address=?, Port=?, Sample_Rate=? WHERE Id=?"% data['table'],(data['name'],data['type'],data['executable'],data['address'],data['port'],data['sample_rate'],data['id']))
            con.commit()

        except lite.Error, e:
            if( debug): print "Error %s:" %e.args[0]
            con.rollback()
        
    elif command=='DELETE':
        try:
            cur = con.cursor()
            if(data['table']=='Data_Table'): 
                cur.execute("DELETE FROM %s WHERE Device_Id=?"% data['table'], (data['id'],))
            elif(data['table']=='Device_Table' or data['table']=='Protocol_Table'):
                cur.execute("DELETE FROM %s WHERE Id=?"% data['table'], (data['id'],))
            con.commit()

        except lite.Error, e:
            if( debug): print "Error %s:" %e.args[0]
            con.rollback()
    
    con.close()

def SQL_to_Data(id='', name='', table='Data_Table', last=0, mod=''):
    db=db_path+'rest.db'
    
    con = lite.connect(db)
    
    try:
        con.row_factory = lite.Row
        
        cur = con.cursor()
        
        if( mod==''):
            if( id==''):
                if( name==''):
                    cur.execute("SELECT * FROM %s" % table)
                else:
                    cur.execute("SELECT * FROM %s WHERE Name=?" % table, (name,))
            else:
                if( name==''):
                    if( table=='Data_Table'): cur.execute("SELECT * FROM %s WHERE Device_Id=?" % table, (id,))
                    elif( table=='Device_Table' or table=='Protocol_Table'): cur.execute("SELECT * FROM %s WHERE Id=?" % table, (id,))
                else:
                    if( table=='Data_Table'): cur.execute("SELECT * FROM %s WHERE Device_Id=? AND Name=?" % table, (id, name,))
                    else: cur.execute("SELECT * FROM %s WHERE Id=? and Name=?" % table, (id, name,))
            
            rows = cur.fetchall()
            
        elif( table=='Data_Table'):
            try:
                time_stamp1, time_stamp2=mod.split(',')
                
                if( id==''):
                    if( name==''):
                        cur.execute("SELECT * FROM %s WHERE Time_Stamp>? AND Time_Stamp<?" % table, (time_stamp1, time_stamp2,))
                    else:
                        cur.execute("SELECT * FROM %s WHERE Name=? AND Time_Stamp>? AND Time_Stamp<?" % table, (name, time_stamp1, time_stamp2,))
                else:
                    if( name==''):
                        cur.execute("SELECT * FROM %s WHERE Device_Id=? AND Time_Stamp>? AND Time_Stamp<?" % (table,mod), (id, time_stamp1, time_stamp2,))
                    else:
                        cur.execute("SELECT * FROM %s WHERE Device_Id=? AND Name=? AND Time_Stamp>? AND Time_Stamp<?" % (table,mod), (id, name, time_stamp1, time_stamp2,))
            except:
                time_stamp=mod
                
                if( id==''):
                    if( name==''):
                        cur.execute("SELECT * FROM %s WHERE Time_Stamp>?" % table, (time_stamp,))
                    else:
                        cur.execute("SELECT * FROM %s WHERE Name=? AND Time_Stamp>?" % table, (name, time_stamp,))
                else:
                    if( name==''):
                        cur.execute("SELECT * FROM %s WHERE Device_Id=? AND Time_Stamp>?" % (table,mod), (id, time_stamp,))
                    else:
                        cur.execute("SELECT * FROM %s WHERE Device_Id=? AND Name=? AND Time_Stamp>? AND Time_Stamp<?" % (table,mod), (id, name, time_stamp,))
            
            rows = cur.fetchall()
        
        else:
            #mod!='' and mod!='last' and table!='Data_Table'
            if( debug): print 'Error : mod value and table name is incorrect combination!'
            rows=[]
        
        if( last):
            try:
                rows_last= rows[-1]
                rows=[]
                rows.append(rows_last)
            except:
                rows=[]
        
    except lite.Error, e:
        if( debug): print "Error %s:" %e.args[0]
    
    con.close()
    
    return rows

class Restful(threading.Thread):
    
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        http_path="/cndep/"
        self.ip=ip
        self.port=port
        
        #itty Rest functions for get, put, post, delete requests
        
        @get(http_path+'data/all')
        def GET_Data_All(request): #Obtain all data
            last,mod=self.mod_generator(request)
            xml_response=self.xml_creator(last=last, mod=mod)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'data/(?P<device_id>\d+)')
        def GET_Data_by_Id(request, device_id=None): #Obtain object data with id
            last,mod=self.mod_generator(request)
            xml_response=self.xml_creator(id=device_id, last=last, mod=mod)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'data/(?P<data_name>\w+)')
        def GET_Data_by_Name(request, data_name=None): #Obtain object data with name
            last,mod=self.mod_generator(request)
            xml_response=self.xml_creator(name=data_name, last=last, mod=mod)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'data/(?P<device_id>\d+)/(?P<data_name>\w+)')
        def GET_Data_by_Id_and_Name(request, device_id=None, data_name=None): #Obtain object data with id and name
            last,mod=self.mod_generator(request)
            xml_response=self.xml_creator(id=device_id, name=data_name, last=last, mod=mod)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'device/all')
        def GET_Device_All(request): #Obtain all objects' information
            last=self.mod_generator(request)[0]
            xml_response=self.xml_creator(table='Device_Table', last=last)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'device/(?P<device_id>\d+)')
        def GET_Device_by_Id(request, device_id=None): #Obtain object information with id
            last=self.mod_generator(request)[0]
            xml_response=self.xml_creator(id=device_id, table='Device_Table', last=last)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'device/(?P<data_name>\w+)')
        def GET_Device_by_Name(request, data_name=None): #Obtain object information with name
            last=self.mod_generator(request)[0]
            xml_response=self.xml_creator(name=data_name, table='Device_Table', last=last)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'protocol/all')
        def GET_Protocol_All(request): #Obtain all objects' information
            last=self.mod_generator(request)[0]
            xml_response=self.xml_creator(table='Protocol_Table', last=last)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'protocol/(?P<protocol_id>\d+)')
        def GET_Protocol_by_Id(request, protocol_id=None): #Obtain protocol information with id
            last=self.mod_generator(request)[0]
            xml_response=self.xml_creator(id=protocol_id, table='Protocol_Table', last=last)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @get(http_path+'protocol/(?P<protocol_name>\w+)')
        def GET_Protocol_by_Name(request, protocol_name=None): #Obtain protocol information with name
            last=self.mod_generator(request)[0]
            xml_response=self.xml_creator(name=protocol_name, table='Protocol_Table', last=last)
            return Response(xml_response, status=200, content_type='text/xml')
        
        @put(http_path+'device')
        def PUT_device(request): #Create object
            xml_request = request.body
            
            root  = ET.fromstring(xml_request)
            
            device_id = root.find('id')
            if(device_id==None or device_id.text=='NULL'):
                device_id=1
            elif(not device_id.text.isdigit()):
                raise Conflict('Device Id is not integer!')
            else:    
                device_id=int(device_id.text)
            
            device_name = root.find('name')
            if(device_name==None):
                raise Conflict('Device Name is empty!')
            else:
                device_name=device_name.text#.lower()
            
            device_protocol = root.find('protocol')
            if(device_protocol==None):
                raise Conflict('Device Protocol is empty!')
            else:
                device_protocol=device_protocol.text#.lower()
            
            device_address = root.find('address')
            if(device_address==None):
                device_address=''
            else:
                device_address=device_address.text#.lower()
            
            device_port = root.find('port')
            if(device_port==None):
                device_port=''
            else:
                device_port=device_port.text#.lower()
            
            device_sample_rate = root.find('sample_rate')
            if(device_sample_rate==None):
                device_sample_rate=''
            else: device_sample_rate=device_sample_rate.text
            
            device_monitoring_data = root.find('monitoring_data')
            if(device_monitoring_data==None):
                device_monitoring_data=''
            else:
                device_monitoring_data=device_monitoring_data.text#.lower()
            #'''
            if(not sys.version[:3].startswith('3') and sys.version[:3]!='2.7'):
                print "Old python detected, please install python 2.7 if posible!"
                self.data=(device_id, device_name, device_protocol, device_address, device_port, device_sample_rate, device_monitoring_data)
                threading.Thread(None,self.Add_device_thread).start()
                time.sleep(0.2)
                device_id=ClassHolder['last_added']
                return Response(str(device_id), status=200, content_type='text/xml')
            else:
                device_id=Add_device(device_id, device_name, device_protocol, device_address, device_port, device_sample_rate, device_monitoring_data)
            #'''
            builder=ET.TreeBuilder()
            
            builder.start('response', {'status':'201'})
            
            builder.start('message', {'device_id':str(device_id)})
            builder.data("device added successful!")
            builder.end('message')
            
            builder.start('device_id', {})
            builder.data(str(device_id))
            builder.end('device_id')
            
            xml=builder.end('response')
            
            xml_str=ET.tostring(xml, encoding="utf8")
            return Response(xml_str, status=201, content_type='text/xml')
        
        @put(http_path+'protocol')
        def PUT_protocol(request): #Create object
            xml_request = request.body
            
            root  = ET.fromstring(xml_request)
            
            protocol_id = root.find('id')
            if(protocol_id==None or protocol_id.text=='NULL'):
                #raise Conflict('Protocol Id is empty!')
                protocol_id=1
            elif(not protocol_id.text.isdigit()):
                raise Conflict('Protocol Id is not integer!')
            else:    
                protocol_id=int(protocol_id.text)
            
            while(True):
                if SQL_to_Data(id=protocol_id,table='Protocol_Table')!=[]:
                    protocol_id+=1
                else: break
            
            protocol_name = root.find('name')
            if(protocol_name==None):
                raise Conflict('Protocol Name is empty!')
            else:
                protocol_name=protocol_name.text#.lower()
            
            protocol_type = root.find('type')
            if(protocol_type==None):
                #raise Conflict('Protocol Type is empty!')
                protocol_type=''
            else:
                protocol_type=protocol_type.text#.lower()
            
            protocol_executable = root.find('executable')
            if(protocol_executable==None):
                raise Conflict('Protocol Executable is empty!')
            else:
                protocol_executable=protocol_executable.text
            
            protocol_address = root.find('address')
            if(protocol_address==None):
                protocol_address=''
            else:
                protocol_address=protocol_address.text#.lower()
            
            protocol_port = root.find('port')
            if(protocol_port==None):
                protocol_port=''
            else:
                protocol_port=protocol_port.text#.lower()
            
            protocol_sample_rate = root.find('sample_rate')
            if(protocol_sample_rate==None):
                protocol_sample_rate=''
            else: protocol_sample_rate=protocol_sample_rate.text
            
            data={}
            data['table']='Protocol_Table'
            data['id']=protocol_id
            data['name']=protocol_name
            data['type']=protocol_type
            data['executable']=protocol_executable
            data['address']=protocol_address
            data['port']=protocol_port
            data['sample_rate']=protocol_sample_rate
            Data_to_SQL(data)
            
            builder=ET.TreeBuilder()
            
            builder.start('response', {'status':'201'})
            
            builder.start('message', {'protocol_id':str(protocol_id)})
            builder.data("protocol added successful!")
            builder.end('message')
            
            #builder.start('protocol_id', {})
            #builder.data(str(protocol_id))
            #builder.end('protocol_id')
            
            xml=builder.end('response')
            
            xml_str=ET.tostring(xml, encoding="utf8")
            return Response(xml_str, status=201, content_type='text/xml')
        
        @post(http_path+'device')
        def POST_device(request): #Update object
            xml_request = request.body
            
            root  = ET.fromstring(xml_request)
            
            device_id = root.find('id')
            if(device_id==None):
                raise Conflict('Device Id is empty!')
            elif(not device_id.text.isdigit()):
                raise Conflict('Device Id is not integer!')
            else:
                device_id=int(device_id.text)
            
            device_name = root.find('name')
            if(device_name==None):
                device_name=''
            else:
                device_name=device_name.text#.lower()
            
            device_protocol = root.find('protocol')
            if(device_protocol==None):
                device_protocol=''
            else:
                device_protocol=device_protocol.text#.lower()
            
            device_address = root.find('address')
            if(device_address==None):
                device_address=''
            else:
                device_address=device_address.text#.lower()
            
            device_port = root.find('port')
            if(device_port==None):
                device_port=''
            else:
                device_port=device_port.text#.lower()
            
            device_sample_rate = root.find('sample_rate')
            if(device_sample_rate==None):
                device_sample_rate=''
            else:
                device_sample_rate=device_sample_rate.text
            
            device_monitoring_data = root.find('monitoring_data')
            if(device_monitoring_data==None):
                device_monitoring_data=''
            else:
                device_monitoring_data=device_monitoring_data.text#.lower()
            
            status=Edit_device(device_id, device_name, device_protocol, device_address, device_port, device_sample_rate, device_monitoring_data)
            if(status==-2): raise NotFound('Device with that Id not found!')
            
            builder=ET.TreeBuilder()
    
            builder.start('response', {'status':'202'})
            
            builder.start('message', {'device_id':str(device_id)})
            builder.data("device edited successful!")
            builder.end('message')
            
            #builder.start('device_id', {})
            #builder.data(str(device_id))
            #builder.end('device_id')
            
            xml=builder.end('response')
            
            xml_str=ET.tostring(xml, encoding="utf8")
            return Response(xml_str, status=202, content_type='text/xml')
        
        @post(http_path+'protocol')
        def POST_protocol(request): #Update object
            xml_request = request.body
            
            root  = ET.fromstring(xml_request)
            
            protocol_id = root.find('id')
            if(protocol_id==None):
                raise Conflict('Protocol Id is empty!')
            elif(not protocol_id.text.isdigit()):
                raise Conflict('Protocol Id is not integer!')
            else:
                protocol_id=int(protocol_id.text)
            
            protocol_name = root.find('name')
            if(protocol_name==None):
                protocol_name=''
            else:
                protocol_name=protocol_name.text#.lower()
            
            protocol_type = root.find('type')
            if(protocol_type==None):
                protocol_type=''
            else:
                protocol_type=protocol_type.text#.lower()
            
            protocol_executable = root.find('executable')
            if(protocol_executable==None):
                protocol_executable=''
            else:
                protocol_executable=protocol_executable.text
            
            protocol_address = root.find('address')
            if(protocol_address==None):
                protocol_address=''
            else:
                protocol_address=protocol_address.text#.lower()
            
            protocol_port = root.find('port')
            if(protocol_port==None):
                protocol_port=''
            else:
                protocol_port=protocol_port.text#.lower()
            
            protocol_sample_rate = root.find('sample_rate')
            if(protocol_sample_rate==None):
                protocol_sample_rate=''
            else:
                protocol_sample_rate=protocol_sample_rate.text
            
            rows=SQL_to_Data(id=protocol_id,table='Protocol_Table')
            if(rows==[]):
                raise NotFound('Protocol with that Id not found!')
            else:
                if( protocol_name==''): protocol_name=rows[0]['Name']
                if( protocol_type==''): protocol_type=rows[0]['Type']
                if( protocol_executable==''): protocol_executable=rows[0]['Executable']
                if( protocol_address==''): protocol_address=rows[0]['Address']
                if( protocol_port==''): protocol_port=rows[0]['Port']
                if( protocol_sample_rate==''): protocol_sample_rate=rows[0]['Sample_Rate']
                
                data={}
                data['table']='Protocol_Table'
                data['id']=protocol_id
                data['name']=protocol_name
                data['type']=protocol_type
                data['executable']=protocol_executable
                data['address']=protocol_address
                data['port']=protocol_port
                data['sample_rate']=protocol_sample_rate
                Data_to_SQL(data, 'UPDATE')
                
            builder=ET.TreeBuilder()
    
            builder.start('response', {'status':'202'})
            
            builder.start('message', {'protocol_id':str(protocol_id)})
            builder.data("protocol edited successful!")
            builder.end('message')
            
            #builder.start('protocol_id', {})
            #builder.data(str(protocol_id))
            #builder.end('protocol_id')
            
            xml=builder.end('response')
            
            xml_str=ET.tostring(xml, encoding="utf8")
            return Response(xml_str, status=202, content_type='text/xml')
        
        @delete(http_path+'device/(?P<device_id>\d+)') #Delete object
        def DELETE(request, device_id=None):
            device_id=int(device_id)
            if ClassHolder.has_key(device_id):
                Remove_device(device_id, 1)
                
                builder=ET.TreeBuilder()
                
                builder.start('response', {'status':'200'})
                
                builder.start('message', {'device_id':str(device_id)})
                builder.data("delete success!")
                builder.end('message')
                
                xml=builder.end('response')
                
                xml_str=ET.tostring(xml, encoding="utf8")
                return Response(xml_str, status=200, content_type='text/xml')
                
            else:
                raise NotFound('Device with that Id not found!')
        
        @delete(http_path+'protocol/(?P<protocol_id>\d+)') #Delete object
        def DELETE(request, protocol_id=None):
            protocol_id=int(protocol_id)
            rows=SQL_to_Data(id=protocol_id, table='Protocol_Table',)
            
            if rows!=[]:
                #'''
                data={}
                data['table']='Protocol_Table'
                data['id']=protocol_id
                Data_to_SQL(data, 'DELETE')
                #'''
                
                builder=ET.TreeBuilder()
                
                builder.start('response', {'status':'200'})
                
                builder.start('message', {'protocol_id':str(protocol_id)})
                builder.data("delete success!")
                builder.end('message')
                
                xml=builder.end('response')
                
                xml_str=ET.tostring(xml, encoding="utf8")
                return Response(xml_str, status=200, content_type='text/xml')
            
            else:
                raise NotFound('Protocol with that Id not found!')
            
        self.start()
    #------------------------------------------------------------------------------------
    ##Rest help functions
    def mod_generator(self, request):
        last=0
        mod=''
        
        if('last'in request.GET):
            last=1
        
        if('from'in request.GET):
            try:
                try:
                    Ymd,HMS= request.GET['from'].split(',')
                    Y1,m1,d1=Ymd.split('-')
                    H1,M1,S1=HMS.split(':')
                    time_stamp1=time.mktime(datetime.datetime(int(Y1),int(m1),int(d1),int(H1),int(M1),int(S1)).timetuple())
                except:
                    Y1,m1,d1=request.GET['from'].split('-')
                    time_stamp1=time.mktime(datetime.datetime(int(Y1),int(m1),int(d1)).timetuple())
                mod=str(time_stamp1)
                
                if('to'in request.GET):
                    try:
                        Ymd,HMS= request.GET['to'].split(',')
                        Y2,m2,d2=Ymd.split('-')
                        H2,M2,S2=HMS.split(':')
                        time_stamp2=time.mktime(datetime.datetime(int(Y2),int(m2),int(d2),int(H2),int(M2),int(S2)).timetuple())
                    except:
                        Y2,m2,d2=request.GET['to'].split('-')
                        time_stamp2=time.mktime(datetime.datetime(int(Y2),int(m2),int(d2)).timetuple())
                    mod=mod+','+str(time_stamp2)
            except:
                raise Conflict('Querry parameter error. Proper format is: from/to=YYYY-mm-dd[,HH:MM:SS]')
                mod=''
        return last, mod
    
    def xml_creator(self , id='', name='', table='Data_Table', last=0, mod=''):
        rows=SQL_to_Data(id, name, table, last, mod)
        
        if( rows==[]): raise NotFound('Data not found!')
        
        builder=ET.TreeBuilder()
        
        builder.start('response', {'status':'200'})
        
        for row in rows:
            if( table=='Data_Table'):
                id,dev_id,name,value,unit,time_stamp=row["Id"], row["Device_Id"], row["Name"], row["Value"], row["Unit"], row["Time_Stamp"]
                
                builder.start('data', {'row_id':str(id)})
                
                builder.start('id',{})
                builder.data(str(id))
                builder.end('id')
    
                builder.start('device_id',{})
                builder.data(str(dev_id))
                builder.end('device_id')
                
                builder.start('name',{})
                builder.data(name)
                builder.end('name')
                
                builder.start('value',{})
                builder.data(str(value))
                builder.end('value')
                
                builder.start('unit',{})
                builder.data(str(unit))
                builder.end('unit')
                
                builder.start('time_stamp',{})
                #builder.data(time_stamp)
                builder.data(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(time_stamp)))) 
                builder.end('time_stamp')
                
                builder.end('data')
            
            elif( table=='Device_Table'):
                id,name,protocol,address,port,sample_rate, monitoring_data=row["Id"], row["Name"], row["Protocol"], row["Address"], row["Port"], row["Sample_Rate"], row["Monitoring_Data"]
                
                builder.start('device', {})
                
                builder.start('id',{})
                builder.data(str(id))
                builder.end('id')
                
                builder.start('name',{})
                builder.data(name)
                builder.end('name')
                
                builder.start('protocol',{})
                builder.data(protocol)
                builder.end('protocol')

                builder.start('address',{})
                builder.data(address)
                builder.end('address')

                builder.start('port',{})
                builder.data(port)
                builder.end('port')
                
                builder.start('sample_rate',{})
                builder.data(sample_rate)
                builder.end('sample_rate')
                
                builder.start('monitoring_data',{})
                builder.data(monitoring_data)
                builder.end('monitoring_data')
                
                builder.end('device')
            
            elif( table=='Protocol_Table'):
                id,name,type,executable,address,port,sample_rate=row["Id"],row["Name"],row["Type"],row["Executable"],row["Address"],row["Port"],row["Sample_Rate"]
                
                builder.start('protocol', {})
                
                builder.start('id',{})
                builder.data(str(id))
                builder.end('id')
                
                builder.start('name',{})
                builder.data(name)
                builder.end('name')
                
                builder.start('type',{})
                builder.data(type)
                builder.end('type')
                
                builder.start('executable',{})
                builder.data(executable)
                builder.end('executable')
                
                builder.start('address',{})
                builder.data(address)
                builder.end('address')

                builder.start('port',{})
                builder.data(port)
                builder.end('port')
                
                builder.start('sample_rate',{})
                builder.data(sample_rate)
                builder.end('sample_rate')
                
                builder.end('protocol')
                
        xml=builder.end('response')
        
        xml_str=ET.tostring(xml, encoding="utf8")
        
        return xml_str
    
    def get_lan_ip(self):
        if os.name != "nt":
            import struct, fcntl
            
            def get_interface_ip(ifname):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])
        ip = socket.gethostbyname(socket.gethostname())
        
        if ip.startswith("127.") and os.name != "nt":
            interfaces = ["eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break;
                except IOError:
                    pass
        return ip
    
    # Threading related functions:
    def run(self):
        Pre_Add_device()
        if(self.ip==''): run_itty('wsgiref', self.get_lan_ip(), self.port)
        else: run_itty('wsgiref', self.ip, self.port)
    
    def Add_device_thread(self):
        (device_id, device_name, device_protocol, device_address, device_port, device_sample_rate, device_monitoring_data)=self.data
        Add_device(device_id, device_name, device_protocol, device_address, device_port, device_sample_rate, device_monitoring_data)

def main():
    if not os.path.exists(path+'rest.db'):
        Data_to_SQL(command='CREATE')
    try:
        [ip,port]=sys.argv[1].split(':')
        ip=str(ip)
        port=int(port)
    except:
        try:
            ip=''
            port=sys.argv[1]
            port=int(port)
        except:
            ip=''
            port=8080
        
    REST=Restful(ip, port)

if __name__ == '__main__':
    import sys
    main()
