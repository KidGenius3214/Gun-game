# Menu manager
import pygame
pygame.init()
from . import *
import socket,threading,json
import sys,pickle,subprocess

def get_wifi_ip():
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode() #get ipconfig data as a string
    data_list = data.split("\n")
    index = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        ip = ""
    else:
        ip = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+4].lstrip().split("IPv4 Address. . . . . . . . . . . : ")[1].split("\r")[0] # get ip when connected to wifi
    return ip

class Menu:
    def __init__(self, game):
        self.state = "Menu"
        self.game = game
        self.clicked = False
        self.click_tick = 30

        #Main menu screen
        self.play_button = Button(30, 35, 2, "SinglePlayer", 4,"Big", True)
        self.multiplayer_btn = Button(30, 90, 2, "Multiplayer", 4, "Big",True)
        self.level_btn = Button(30, 145, 2, "Level Editor", 4, "Big",True)
        
        #Multiplayer screen
        self.LAN_btn = Button(45,70,3,"LAN Game",5,"Big",True)
        self.Online_btn = Button(275,70,3,"Online",5,"Big",True)
        self.Host_btn = Button(45,70,3,"Host",5,"small",True)
        self.Join_btn = Button(275,70,3,"Join",5,"small",True)
        self.port = self.game.settings["networking"]["port"]
        self.clock = pygame.time.Clock()
        self.games = []
        self.udp_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def find_games(self):
        while True:
            self.games = []
            for i in range(257):
                try:
                    if self.search_ip != "":
                        ip = self.search_ip.split('.')
                        host = f"{ip[0]}.{ip[1]}.{ip[2]}.{i}"
                        self.udp_sock.sendto(b"Find Server",(host,self.port))
                except Exception as e:
                    break
            
            try:
                data,addr = self.udp_sock.recvfrom(2048*8)
                self.games.append(json.loads(data.decode('utf-8')))
            except:
                pass          
    
    def run(self):
        self.game.display.fill((90,90,90))
        self.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        size_dif = float(self.game.screen.get_width()/self.game.display.get_width())
        pos = [int(pos[0]/size_dif), int(pos[1]/size_dif)]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        if self.state == "Menu":
            self.play_button.update(self.game.display, pos)
            self.multiplayer_btn.update(self.game.display,pos)
            self.level_btn.update(self.game.display, pos)

            self.Online_btn.disabled = True
            self.LAN_btn.disabled = True

            if self.play_button.clicked == True and self.clicked == False:
                self.game.create_game_manager("Singleplayer")
                self.game.state = "Play"
                self.clicked = True
            if self.level_btn.clicked == True and self.clicked == False:
                self.game.state = 'Level_Editor'
                self.game.create_Level_editor()
                self.clicked = True
            if self.multiplayer_btn.clicked == True and self.clicked == False:
                self.Online_btn.disabled = False
                self.LAN_btn.disabled = False
                self.clicked = True
                self.state = "Mult_Screen"
                
        if self.state == "Mult_Screen":
            self.LAN_btn.update(self.game.display,pos)
            self.Online_btn.update(self.game.display,pos)

            self.play_button.disabled = True
            self.multiplayer_btn.disabled = True
            self.level_btn.disabled = True
            
            if self.LAN_btn.clicked == True and self.clicked == False:
                self.state = "LAN screen"
                self.clicked = True
            if self.Online_btn.clicked == True and self.clicked == False:
                self.state = "Online screen"
                self.clicked = True

        if self.state == "LAN screen":
            self.Host_btn.update(self.game.display, pos)
            self.Join_btn.update(self.game.display,pos)

            if self.Host_btn.clicked == True and self.clicked == False:
                self.game.create_game_manager("Multiplayer")
                #subprocess.run(["python", "scripts/", "server.py"])
                map_name = "Debug_level_0"
                map_type = "Normal"
                data = None
                game_info = ["Classic",12,[]]
                
                try:
                    with open(f"data/maps/{map_name}.level","rb") as file:
                        data = pickle.load(file)
                        file.close()
                        game_info[2] = data["data"]["spawnpoints"]
                except:
                    with open(f"data/maps/custom_maps/{map_name}.level","rb") as file:
                        data = pickle.load(file)
                        file.close()
                        game_info[2] = data["data"]["spawnpoints"]
                    map_type = "Custom"

                game_info.append(map_type)
                items = []
                for item in data["data"]["guns"]:
                    items.append([item,"Guns"])

                game_info.append(items)
                game_info.append(map_name)

                self.game.game_manager.setup_mult(True,self.port,"0", game_info)
                self.game.state = "Play"
                self.clicked = True
                
            if self.Join_btn.clicked == True and self.clicked == False:
                self.search_ip = get_wifi_ip()
                f_game_thread = threading.Thread(target=self.find_games, name="find_servers")
                f_game_thread.start()
                self.game.create_game_manager("Multiplayer")
                self.game.game_manager.setup_mult(False,5555,"192.168.43.232")
                self.game.state = 'Play'
                self.clicked = True
                
        if self.state == "Join_screen":
            self.Host_btn.update(self.game.display, pos)

        if self.clicked == True:
            self.click_tick -= 1
            if self.click_tick <= 0:
                self.clicked = False
                self.click_tick = 30

        self.game.screen.blit(pygame.transform.scale(self.game.display, (self.game.screen.get_width(),self.game.screen.get_height())), (0,0))
        pygame.display.update()
