import socket
import subprocess
import threading
import random
import json
import os
import time
import base64
    
def setup():
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode()#get ip config data as a string
    data_list = data.split("\n")
    index = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        ip = ""
    else:
        ip = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+4].lstrip().split("IPv4 Address. . . . . . . . . . . : ")[1].split("\r")[0] #get ip address if connected to a wifi network
    return ip

MAX_LIMIT = 80
TIME_LIMIT = 120
with open("../data/Game_data/settings.json","r") as file:
    network_data = json.load(file)["networking"]
    file.close()

#Packet Definitions
CONNECTION_PACKET = base64.b64encode(b"Make connection:Gun Game")
CLOSE_SERVER_PACKET = base64.b64encode(b"CLOSE_SERVER")

class TCPserver:
    pass

class UDPserver:
    def __init__(self):
        #Setup the socket
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ip = setup()
        self.port = network_data["port"]
        self.addr = (self.ip,self.port)
        self.socket.bind(self.addr)

        #Managment of the server
        self.connections = 0
        self._id = 0
        self.player_limit = 100
        self.gamemode = ""
        self.level = ""
        self.map_type = "NORMAL"
        self.host = None
        self.players = {}
        self.bullets = {}
        self.items = []
        self.entities = {}
        self.maps_path = "../data/maps/"
        self.spawn_points = [[0,0]]
        self.addresses = {}
        self.closed = False

    def Verify(self):
        if self.ip == "":
            self.socket.close()
            print("[SERVER] IP address is not valid")
        print(self.addr)
        #self.socket.bind(self.addr)
        print(f"[SERVER] Running on IP:{self.ip}")
        print("[SERVER] Listening for connections")
        #self.game_thread = threading.Thread(target=self.get_data)
        #self.game_thread.daemon = True
    
    def get_player_spawn(self):
        return random.choice(self.spawn_points)
    
    def disconnect_player(self,_id):
        print(f"[SERVER] Player {self.players[_id]}  id:{_id} disconnected!")
        self.connections -= 1
        del self.players[_id]
    
    
    def RunGame(self):
        while True:
            # update the players off time
            # if a client does not send for some time the server disconnects that client
            """
            del_list = []
            for player_id in self.players:
                self.players[player_id]["no_send_time"] += time.time()/10000
                print(self.players[player_id])
                if self.players[player_id]["no_send_time"] >= TIME_LIMIT:
                    del_list.append(player_id)
            
            for id in del_list:
                self.disconnect_player(id)
            """

            # Socket stuff
            print("waiting for data")
            data,addr = self.socket.recvfrom(2048*8)
            try:
                if data == CONNECTION_PACKET:
                    if self.connections < self.player_limit+1:
                        self.socket.sendto("Connection Established".encode(), addr)
                        print("connected")
                    if self.connections > self.player_limit:
                        self.socket.sendto("FAILED!".encode(),addr)
                        print("Game is full")
                    print("Connection is being made")
                else:
                    if data.decode('utf-8').split(':')[0] not in ["update","get","DISCONNECT"]:
                        self.socket.sendto("FAILED!".encode(),addr)
                    print("Connection that was made was not approved")

                if data.decode('utf-8').split(';')[0].replace('"',"") == 'CREATE_PLAYER':
                    print("creating_player")
                    data_d = json.loads(data)
                    player_data = json.loads(data_d.split(';')[1])
                    player_data["loc"] = self.get_player_spawn()
                    player_data["address"] = addr
                    player_data["no_send_time"] = 0
                    self.players[self._id] = player_data
                    if player_data["is_host"] == True:
                        self.host = [self._id,addr,self.players[self._id]]
                        game_data = json.loads(data_d.split(';')[2])
                        self.gamemode,self.player_limit,self.spawnpoints,self.map_type,self.items,self.level = game_data
                    self.socket.sendto(json.dumps([player_data["loc"],self._id]).encode(),self.players[self._id]["address"])
                    self.connections += 1
                    print(f"[SERVER] {player_data['name']} has connected on id: {self._id}")
                    self._id += 1
                
                if data.decode('utf-8').split(':')[0] == "get":
                    p_id = int(data.decode('utf-8').split(':')[1])
                    data = [self.players,self.bullets,self.items,self.entities,[self.map_type,self.level],self._id]
                    self.players[p_id]["no_send_time"] = 0
                    self.socket.sendto(json.dumps(data).encode(),self.players[p_id]["address"])

                elif data.decode('utf-8').split(":")[0] == "update":
                    update_info = data.decode('utf-8').split(':')
                    pos = [int(update_info[1]), int(update_info[2])]
                    angle = float(update_info[3]) # angle is in radians
                    p_id = int(update_info[4])
                    self.players[p_id]["loc"] = pos
                    self.players[p_id]["angle"] = angle
                    self.players[p_id]["no_send_time"] = 0
                    data = [self.players,self.items]
                    self.socket.sendto(json.dumps(data).encode(),self.players[p_id]["address"])
                
                elif data.decode('utf-8').split(':') == "DISCONNECT":
                    p_id = int(data.decode('utf-8').split(':')[1])
                    self.disconnect_player(p_id)

                if data == CLOSE_SERVER_PACKET:
                    if addr == self.host[1]:
                        for player in self.players:
                            for i in range(3): # send it three times to make sure the clients recieve the message
                                self.socket.sendto(base64.b64encode(b"SERVER_CLOSED"),player["address"])
                        print("Server closed")
                        raise Exception("Server closed!")
                    else:
                        print(addr, "You are not the host!!!")
            except Exception as e:
                print(e)
                self.socket.close()
                self.closed = True
            
            if self.closed == True:
                break


Server = UDPserver()

Server.Verify()
#Server.game_thread.start()
Server.RunGame()