import socket
#from binascii import hexlify, unhexlify
UDP_IP="192.168.32.101"
UDP_PORT=1234

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM ) # UDP

data_name='humidity'
data_value='50'
data_units='%'
data='%s,%s,%s'%(data_name,data_value,data_units).strip(' ')

sock.sendto( data, (UDP_IP, UDP_PORT) )
sock.close()
