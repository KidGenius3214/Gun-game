import socket
import subprocess
import threading
import random
import json
import os
import time
import base64
from copy import deepcopy
    
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
        self.player_addrs = {}
        self.bullets = []
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
            return False
        print(f"[SERVER] Running on IP:{self.ip}")
        print("[SERVER] Listening for connections")
        return True
    
    def get_player_spawn(self):
        return random.choice(self.spawn_points)
    
    def disconnect_player(self,_id):
        print(f"[SERVER] Player {self.players[_id]['name']}  id:{_id} disconnected!")
        self.connections -= 1
        del self.players[_id]
    
    
    def RunGame(self):
        while True:
            try:
                data,addr = self.socket.recvfrom(2048*8)
                if data.decode('utf-8') == "FIND_GAME:GUN_GAME":
                    self.socket.sendto("I_AM_HERE".encode(),addr)

                if data == CONNECTION_PACKET:
                    if self.connections < self.player_limit+1 and self.connections != self.player_limit:
                        self.socket.sendto("Connection Established".encode(), addr)
                    elif self.connections >= self.player_limit:
                        self.socket.sendto("FAILED!".encode(),addr)
                else:
                    if data.decode('utf-8').split(':')[0] not in ["update","get","DISCONNECT"]:
                        self.socket.sendto("FAILED!".encode(),addr)

                if data.decode('utf-8').split(';')[0].replace('"',"") == 'CREATE_PLAYER':
                    data_d = json.loads(data)
                    player_data = json.loads(data_d.split(';')[1])
                    for player in self.players:
                        if self.players[player]["name"] == player_data["name"]:
                            player_data["name"] += str(self._id)
                    self.players[self._id] = player_data
                    if player_data["is_host"] == True:
                        self.host = [self._id,addr,self.players[self._id]]
                        game_data = json.loads(data_d.split(';')[2])
                        self.gamemode,self.player_limit,self.spawn_points,self.map_type,self.items,self.level = game_data
                    player_data["loc"] = self.get_player_spawn()
                    self.player_addrs[self._id] = {"address":()}
                    self.player_addrs[self._id]["address"] = addr
                    player_data["no_send_time"] = 0
                    self.socket.sendto(json.dumps([player_data["loc"],self._id]).encode(),self.player_addrs[self._id]["address"])
                    self.connections += 1
                    print(f"[SERVER] {player_data['name']} has connected on id: {self._id}")
                    self._id += 1
                
                elif data.decode('utf-8').split(':')[0] == "get":
                    p_id = int(data.decode('utf-8').split(':')[1])
                    data = [self.players,self.bullets,self.items,self.entities,[self.map_type,self.level],self._id]
                    self.players[p_id]["no_send_time"] = 0
                    self.socket.sendto(json.dumps(data).encode(),self.player_addrs[p_id]["address"])
                
                elif data.decode('utf-8').split(';')[0] == "bullet":
                    bullet_data = json.loads(data.decode('utf-8').split(';')[1])
                    self.bullets.append(bullet_data)
                
                elif data.decode('utf-8').split(':')[0] == "bullet_collide":
                    b_id = int(data.decode('utf-8').split(':')[1])
                    for i,bullet in enumerate(self.bullets):
                        if bullet[-1] == b_id:
                            self.bullets.remove(bullet)
                
                elif data.decode('utf-8').split(':')[0] == "bullet_life_ended":
                    b_id = int(data.decode('utf-8').split(':')[1])
                    for i,bullet in enumerate(self.bullets):
                        if bullet[-1] == b_id:
                            self.bullets.remove(bullet)

                elif data.decode('utf-8').split(";")[0] == "update":
                    update_info = data.decode('utf-8').split(';')
                    pos = [int(update_info[1]), int(update_info[2])]
                    angle = float(update_info[3]) # angle is in radians
                    e_weapon = json.loads(update_info[4]) # The equipped weapon
                    p_id = int(update_info[-1])
                    self.players[p_id]["loc"] = pos
                    self.players[p_id]["angle"] = angle
                    self.players[p_id]["health"] = int(update_info[5])
                    self.players[p_id]["shield"] = int(update_info[6])
                    self.players[p_id]["no_send_time"] = 0
                    self.players[p_id]["equipped_weapon"] = e_weapon
                    data = [self.players,self.items,self.bullets]
                    self.socket.sendto(json.dumps(data).encode(),self.player_addrs[p_id]["address"])
                
                elif data.decode('utf-8').split(':')[0] == "remove_item":
                    item_id = int(data.decode('utf-8').split(':')[1])
                    for i,item in enumerate(self.items):
                        if item_id == item[4]:
                            self.items.pop(i)
                
                elif data.decode('utf-8').split(';')[0] == "add_item":
                    item_data = json.loads(data.decode('utf-8').split(';')[1])
                    self.items.insert(-1,item_data)
                
                elif data.decode('utf-8').split(':')[0] == "DISCONNECT":
                    p_id = int(data.decode('utf-8').split(':')[1])
                    self.disconnect_player(p_id)
                
                if isinstance(data,bytes) == True:
                    if base64.b64encode(data) == CLOSE_SERVER_PACKET:
                        if addr == self.host[1]:
                            for player in self.players:
                                for i in range(3): # send it three times to make sure the clients recieve the message
                                    self.socket.sendto(base64.b64encode(b"SERVER_CLOSED"),self.player_addrs[player]["address"])
                            print("Server closed")
                            self.closed = True
                        else:
                            print(addr, "You are not the host!!!")
                
            except Exception as e:
                print(e)
            
            if self.closed == True:
                break


Server = UDPserver()

if Server.Verify() == True:
    Server.RunGame()