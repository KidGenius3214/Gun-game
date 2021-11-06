#Game manager
#It's basically where whole gameplay stuff is 
import pygame
pygame.init()
from . import *
from .player import *
from .client import *
import sys, math, random,pickle,time
import pickle

#get the ip if this play is a host
def get_wifi_ip():
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode() #get ipconfig data as a string
    data_list = data.split("\n")
    index = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        ip = ""
    else:
        ip = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+4].lstrip().split("IPv4 Address. . . . . . . . . . . : ")[1].split("\r")[0] # get ip when connected to wifi
    return ip


class Game_manager:
    def __init__(self,game,play_type,p_name="Player"):
        self.game = game
        self.play_type = play_type
        self.player = Player(100, 0, 16, 16, 100, 3, 6, 0.3)
        self.player_name = p_name
        self.event = None
        self.clock = pygame.time.Clock()
        self.current_level = 'Debug_level_0'
        self.bullets = []
        self.particles = []
        self.level = None
        self.tiles = self.game.tiles
        self.scroll = [0,0]
        #controller stuff
        self.controller_input = self.game.json_h.files["controller_input"]
        self.right_pressed = False
        self.left_pressed = False
        self.jumped = False
        self.ip = ""
        self.port = 1
        self.tile_data = self.game.json_h.load("data/Game_data/tile_data.json", "tile_data")
        
        #Multiplayer stuff
        self.hosting = False
        self.host_server = None
        self.players = {}
        self.client = None
        
        self.camera = Camera()
        self.joystick = None
        with open(f"data/maps/{self.current_level}.level", "rb") as file:
            data = pickle.load(file)
            file.close()
            self.level = data["data"]
            self.zone = data["zone"]
            del data
        self.reload_controller()

    def reload_controller(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        joy_count = pygame.joystick.get_count()
        if joy_count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

    def handle_controller_input(self):
        controller_states = {
            "active":False,
            "pos":[0,0],
            "axis_val":[0,0],
            "buttons":{"jump":False,"right":False,"left":False,"up":False,"down":False}
        }
        if self.joystick != None:
            controller_states["active"] = True
            if self.controller_input[self.joystick.get_name()] != {}:
                for axis in range(self.joystick.get_numaxes()):
                    if axis in self.controller_input[self.joystick.get_name()]["axes"]:
                        if axis == self.controller_input[self.joystick.get_name()]["movement"]:
                            controller_states["axis_val"][0] = self.joystick.get_axis(axis)
                            if controller_states["axis_val"][0] > 0.6:
                                controller_states["buttons"]["right"] = True
                            else:
                                controller_states["buttons"]["right"] = False

                            if controller_states["axis_val"][0] < -0.6:
                                controller_states["buttons"]["left"] = True
                            else:
                                controller_states["buttons"]["left"] = False
                for button in range(self.joystick.get_numbuttons()):
                    if button in self.controller_input[self.joystick.get_name()]["buttons"]:
                        if button == self.controller_input[self.joystick.get_name()]["jump"]:
                            if self.joystick.get_button(button):
                                if controller_states["buttons"]["jump"] == False:
                                    controller_states["buttons"]["jump"] = True
                                else:
                                    controller_states["buttons"]["jump"] = False
        return controller_states

    def setup_mult(self,host,port,ip,game_info=[]):
        if host == True:
            self.client = Client(self.player,port,get_wifi_ip())
            if self.client.connect() == "Connection_ERROR":
                return "Connection ERROR!"
            else:
                self.hosting = True
                self.client.send(str(self.hosting))
                if self.client.recv() == "Send game info":
                    time.sleep(0.01) # delay seninf more of the data
                    self.client.send(game_info,pick=True)
                data = {"loc":[0,0],"name":self.player_name}
                self.client.send(data,pick=True)
                pos = self.client.recv(pick=True)
                self.client.set_id(pos[1])
                self.player.set_pos(int(pos[0][0]),int(pos[0][1]))
                self.client.send("get")
                self.players,_,_ = self.client.recv(pick=True,val=2)
        else:
            self.client = Client(self.player,port,ip)
            if self.client.connect() == "Can't connect":
                return "Connection ERROR!"
            else:
                self.hosting = False
                self.client.send("False")
                time.sleep(0.01) # delay sending more of the data
                data = {"loc":[0,0],"name":self.player_name}
                self.client.send(data,pick=True)
                pos = self.client.recv(pick=True,val=8)
                self.client.set_id(pos[1])
                self.player.set_pos(int(pos[0][0]),int(pos[0][1]))
                self.client.send("get")
                self.players,_,_ = self.client.recv(pick=True,val=8)
                
    def normal_play(self):
        self.game.display.fill((90,90,90))
        self.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        relative_pos = [int(pos[0]//2), int(pos[1]//2)]

        self.camera.update(self.player,self.game.display,10)
        
        scroll = [0,0]
        scroll[0] = self.camera.scroll[0]
        scroll[1] = self.camera.scroll[1]
        controller_input = self.handle_controller_input()
        
        tiles = []
        active_chunks = []
        angle = find_angle_from_points(relative_pos, self.player.get_center(), [0,0], False)
        for y in range(3):
            for x in range(4):
                chunk_x = x-1 + round(scroll[0]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_y = y-1 + round(scroll[1]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_id = f"{chunk_x}/{chunk_y}"
                active_chunks.append(chunk_id)

        for chunk_id in active_chunks:
            for layer in self.level:
                if layer != 'tiles':
                    if chunk_id in self.level[layer]:
                        for tile in self.level[layer][chunk_id]:
                            if tile[0] in self.tiles[self.zone]:
                                if tile[0] not in ['1','2','3']:
                                    self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                            if tile[0] in ['1','2','3']:
                                self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-2-scroll[1]))
                            if tile[0] in self.tile_data["collidable"]:
                                tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))
            
        self.player.draw(self.game.display, scroll)
        for chunk_id in active_chunks:
            if chunk_id in self.level["tiles"]:
                for tile in self.level["tiles"][chunk_id]:
                    if tile[0] in self.tiles[self.zone]:
                        if tile[0] not in ['1','2','3']:
                            self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                    if tile[0] in ['1','2','3']:
                        self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-2-scroll[1]))
                    if tile[0] in self.tile_data["collidable"]:
                        tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))

        self.player.movement(tiles)

        if controller_input["active"] == True:
            if controller_input["axis_val"][0] > 0.5:
                self.player.right = True
                self.right_pressed = True
            elif self.right_pressed == True:
                self.player.right = False
                self.right_pressed = False
            if controller_input["axis_val"][0] < -0.5:
                self.player.left = True
                self.left_pressed = True
            elif self.left_pressed == True:
                self.player.left = False
                self.left_pressed = False   
            if controller_input["buttons"]["jump"] == True and self.jumped == False:
                self.jumped = True
                if self.player.jump_count < 2:
                    self.player.vel_y = -self.player.jump
                    self.player.jump_count += 1
                if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                    self.player.wall_jump_true = True
                    self.player.jump_count = 1
            elif controller_input["buttons"]["jump"] == False and self.jumped == True:
                self.jumped = False

        for event in pygame.event.get():
            self.event = event
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_a:
                    self.player.left = True
                if event.key == K_d:
                    self.player.right = True
                if event.key == K_SPACE:
                    if self.player.jump_count < 2:
                        self.player.vel_y = -self.player.jump
                        self.player.jump_count += 1
                    if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                        self.player.wall_jump_true = True
                        self.player.jump_count = 1
                        
            if event.type == KEYUP:
                if event.key == K_a:
                    self.player.left = False
                if event.key == K_d:
                    self.player.right = False

        self.game.screen.blit(pygame.transform.scale(self.game.display, self.game.win_dims), (0,0))
        pygame.display.update()

    def update_mult_game(self,players,scroll):
        for p_id in players:
            p_pos = players[p_id]["loc"]
            player = Player(p_pos[0],p_pos[1],16,16,100,3,5,0.3)
            player.draw(self.game.display,scroll)

    def multi_play(self):
        self.game.display.fill((90,90,90))
        self.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        relative_pos = [int(pos[0]//2), int(pos[1]//2)]

        self.camera.update(self.player,self.game.display,10)
        
        scroll = [0,0]
        scroll[0] = self.camera.scroll[0]
        scroll[1] = self.camera.scroll[1]
        controller_input = self.handle_controller_input()
        
        tiles = []
        active_chunks = []
        angle = find_angle_from_points(relative_pos, self.player.get_center(), [0,0], False)
        for y in range(3):
            for x in range(4):
                chunk_x = x-1 + round(scroll[0]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_y = y-1 + round(scroll[1]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_id = f"{chunk_x}/{chunk_y}"
                active_chunks.append(chunk_id)

        for chunk_id in active_chunks:
            for layer in self.level:
                if layer != 'tiles':
                    if chunk_id in self.level[layer]:
                        for tile in self.level[layer][chunk_id]:
                            if tile[0] in self.tiles[self.zone]:
                                if tile[0] not in ['1','2','3']:
                                    self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                            if tile[0] in ['1','2','3']:
                                self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-2-scroll[1]))
                            if tile[0] in self.tile_data["collidable"]:
                                tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))
                                
        self.update_mult_game(self.players,scroll)
        
        for chunk_id in active_chunks:
            if chunk_id in self.level["tiles"]:
                for tile in self.level["tiles"][chunk_id]:
                    if tile[0] in self.tiles[self.zone]:
                        if tile[0] not in ['1','2','3']:
                            self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                    if tile[0] in ['1','2','3']:
                        self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-2-scroll[1]))
                    if tile[0] in self.tile_data["collidable"]:
                        tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))

        self.player.movement(tiles)

        if controller_input["active"] == True:
            if controller_input["axis_val"][0] > 0.5:
                self.player.right = True
                self.right_pressed = True
            elif self.right_pressed == True:
                self.player.right = False
                self.right_pressed = False
            if controller_input["axis_val"][0] < -0.5:
                self.player.left = True
                self.left_pressed = True
            elif self.left_pressed == True:
                self.player.left = False
                self.left_pressed = False   
            if controller_input["buttons"]["jump"] == True and self.jumped == False:
                self.jumped = True
                if self.player.jump_count < 2:
                    self.player.vel_y = -self.player.jump
                    self.player.jump_count += 1
                if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                    self.player.wall_jump_true = True
                    self.player.jump_count = 1
            elif controller_input["buttons"]["jump"] == False and self.jumped == True:
                self.jumped = False

        for event in pygame.event.get():
            self.event = event
            if event.type == pygame.QUIT:
                pygame.quit()
                self.client.send("quit")
                self.client.disconnect()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_a:
                    self.player.left = True
                if event.key == K_d:
                    self.player.right = True
                if event.key == K_SPACE:
                    if self.player.jump_count < 2:
                        self.player.vel_y = -self.player.jump
                        self.player.jump_count += 1
                    if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                        self.player.wall_jump_true = True
                        self.player.jump_count = 1
                        
            if event.type == KEYUP:
                if event.key == K_a:
                    self.player.left = False
                if event.key == K_d:
                    self.player.right = False

        command = f"move:{self.player.rect.x}:{self.player.rect.y}"

        self.client.send(command)
        self.players,_ = self.client.recv(pick=True,val=2)

        self.game.screen.blit(pygame.transform.scale(self.game.display, self.game.win_dims), (0,0))
        pygame.display.update()   

    def run(self):
        if self.play_type == "Singleplayer":
            self.normal_play()
        if self.play_type == "Multiplayer":
            self.multi_play()
