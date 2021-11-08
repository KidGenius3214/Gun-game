import socket
import subprocess
import json

class Client:
    def __init__(self,player,port,ip):
        self.port = port
        self.id = 0 #default value
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = ip
        self.player = player
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
            self.socket.send(json.dumps(data))
        else:
            self.socket.send(data.encode('utf-8'))

    def recv(self,jason_encode=False,val=1):
        if json_encode != True:
            data = self.socket.recv(2048*val).decode("utf-8")
        else:
            data = json.loads(self.socket.recv(2048*val))
        return data
