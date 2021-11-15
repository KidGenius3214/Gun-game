import socket
import subprocess
from threading import Thread
from _thread import *
import random
import json
import os
import time
    
def setup():
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode()#get ip config data as a string
    data_list = data.split("\n")
    index = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        ip = ""
    else:
        ip = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+4].lstrip().split("IPv4 Address. . . . . . . . . . . : ")[1].split("\r")[0] #get ip address if connected to a wifi network
    return ip


server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

ip = setup()
MAX_LIMIT = 80
connections = 0
with open("../data/Game_data/settings.json","r") as file:
    network_data = json.load(file)["networking"]
    file.close()

port = network_data["port"]

gamemode = ""

try:
    server.bind((ip,port))
    server.listen()
    if ip == "":
        server.close()
        print(1+"hello")
    print(f"[SERVER] running on ip {ip}")
    print("[SERVER] Waiting for connections")
except Exception as e:
    print(e)
    print("[SERVER] Can't Connect,please check your port or ip")
    input("Press any key to quit")
    quit()


players = {}
bullets = {}
items = []
entities = {}
_id = 0
host = None
level = ""
map_type = "Normal"
maps_path = "../data/maps/"
spawn_points = [[0,0]]

def player_spawn():
    return random.choice(spawn_points)

def client(conn,_id):
    global level,players,connections,bullets,items,entities

    current_id = _id
    
    while True:
        try:
            command = conn.recv(2048*8).decode('utf-8')
            if command == "get":
                print(items)
                data = [players,bullets,items,entities,[map_type,level],_id]
                conn.send(json.dumps(data).encode())
            if command.split(':')[0] == "move":
                pos = [int(command.split(':')[1]),int(command.split(':')[2])]
                players[_id]["loc"] = pos
                data = [players,bullets,items,entities]
                conn.send(json.dumps(data).encode('utf-8'))
            if command.split(":")[0] == "send_map":
                game_map = command.split(':')[1]
                with open(f"{maps_path}custom_maps/{game_map}.level","r") as file:
                    map_data = pickle.load(file)
                    file.close()

                map_data = json.loads(map_data).encode('utf-8')
                conn.send(str(len(map_data)).encode())
                conn.send(map_data)
                
            if command == 'quit':
                break
        except Exception as e:
            print(e)
            break

        time.sleep(0.001)

    #when user disconnects
    print(f"[SERVER] {players[_id]['name']}-id:{_id} has disconnected")

    connections -= 1
    del players[current_id]
    conn.close()
    

while True:
    conn,addr = server.accept()
    print(addr,"connected")
    test_host = conn.recv(1024).decode('utf-8')

    if test_host == "True":
        host = [_id,addr]
        conn.send("Send game info".encode('utf-8'))
        gamemode,player_limit,spawn_points,map_type,items,level = json.loads(conn.recv(2048*8).decode('utf-8'))
        
    player_data = json.loads(conn.recv(2048*8).decode('utf-8'))
    player_data["loc"] = player_spawn()[1]
    players[_id] = player_data
    conn.send(json.dumps([player_data["loc"],_id]).encode())
    connections += 1

    p_thread = Thread(target=client,args=(conn,_id))
    p_thread.start()
    print(f"[SERVER] {player_data['name']} has connected on id: {_id}")
    _id += 1
