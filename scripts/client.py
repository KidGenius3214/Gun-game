import socket
import subprocess
import json,base64

class TCPClient:
    def __init__(self,port,ip):
        self.port = port
        self.id = 0 #default value
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = ip
        self.server_is_closed = base64.b64encode(b"SERVER_CLOSED")
        self.connected = False

    def connect(self):
        try:
            self.socket.connect((self.ip,self.port))
            self.connected = True
        except Exception as e:
            return "Connection_ERROR"

    def disconnect(self):
        self.socket.close() # disconnect the socket

    def set_id(self,_id):
        self.id = _id

    def send(self,data,json_encode=False):
        if json_encode == True:
            self.socket.send(json.dumps(data).encode())
        else:
            self.socket.send(data.encode('utf-8'))

    def recv(self,json_encode=False,val=1):
        if json_encode != True:
            data = self.socket.recv(2048*val).decode("utf-8")
            print(data)
            if data == self.server_is_closed.decode():
                self.disconnect()
                return "Server is closed!"
            if data != "":
                return data
            else:
                return "No data"
        else:
            data = self.socket.recv(2048*val).decode('utf-8')
            if data == self.server_is_closed.decode():
                self.disconnect()
                return "Server is closed!"
            if data != "":
                new_data = json.loads(data)
                return new_data
            else:
                return "No Data"

class UDPClient:
    def __init__(self,port,ip):
        self.port = port
        self.id = 0 #default value
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.ip = ip
        self.serv_addr = (ip,port)
        self.server_is_closed = base64.b64encode(b"SERVER_CLOSED")
        self.connected = False

    def connect(self):
        connection_packet = base64.b64encode("Make connection:Gun Game".encode('utf-8'))
        self.socket.sendto(connection_packet,self.serv_addr)
        data,_ = self.socket.recvfrom(2048)
        if data.decode('utf-8') == "Connection Established":
            self.connected = True
        else:
            return "Connection_ERROR"

    def disconnect(self):
        self.connected = False
        self.socket.close() # disconnect the socket

    def set_id(self,_id):
        self.id = _id

    def send(self,data,json_encode=False):
        if self.connected == True:
            if json_encode == True:
                self.socket.sendto(json.dumps(data).encode(),self.serv_addr)
            else:
                self.socket.sendto(data.encode('utf-8'),self.serv_addr)

    def recv(self,json_encode=False,val=1):
        if self.connected == True:
            if json_encode != True:
                data,_ = self.socket.recvfrom(2048*val)
                data = data.decode('utf-8')
                if data == self.server_is_closed.decode():
                    self.disconnect()
                    return "Server is closed!"
                if data != "":
                    return data
                else:
                    return "No data"
            else:
                data,_ = self.socket.recvfrom(2048*val)
                data = data.decode('utf-8')
                if data == self.server_is_closed.decode():
                    self.disconnect()
                    return "Server is closed!"
                if data not in ["FAILED!",""]:
                    new_data = json.loads(data)
                    return new_data
                else:
                    for i in range(1): # Try to recv the data again just in case the client does not get the data
                        data,_ = self.socket.recvfrom(2048*val)
                        data = data.decode('utf-8') 
                        if data == self.server_is_closed.decode():
                            self.disconnect()
                            return "Server is closed!"
                        if data not in ["FAILED!",""]:
                            new_data = json.loads(data)
                            return new_data
                    return "No data"
