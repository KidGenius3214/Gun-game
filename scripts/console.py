#Console.py
#Console for:
#cheats
#server commands
#debugging


import pygame
import scripts
from pygame.locals import *


class Console:
    def __init__(self,game,size,server_mode=False):
        self.game = game
        self.x = 2

        self.server_mode = server_mode
        self.commands = []
        self.messages = []
        self.p_index = 0
        self.command_input = ""
        self.font = scripts.Text("data/images/font.png",2,2)
        self.extra_text = "|"
        self.extra_text_time = 32
        self.text_x = 0

        self.console_img = pygame.Surface(size)
        self.copy_img = pygame.Surface(size)
        self.console_img.fill((54,57,75))
        self.console_img.set_alpha(150)

        self.messages_img = pygame.Surface((size[0],size[1]*6))
        self.messages_img_c = pygame.Surface((size[0],size[1]*6))
        self.messages_img.fill((54,57,75))
        self.messages_img.set_alpha(150)
        
        self.base_y = self.messages_img.get_height()

    def render(self):
        self.copy_img.fill((0,0,0))
        self.copy_img.set_colorkey((0,0,0))
        self.messages_img_c.fill((0,0,0))
        self.messages_img_c.set_colorkey((0,0,0))

        self.game.display.blit(self.console_img,(self.x,self.game.display.get_height()-self.console_img.get_height()-4))
        self.game.display.blit(self.messages_img,(self.x,(self.game.display.get_height()-self.console_img.get_height()-5)-self.messages_img.get_height()))
        self.font.render(self.copy_img,self.command_input + self.extra_text,4-self.text_x,6,(255,255,255))
        
        self.game.display.blit(self.copy_img,(self.x,self.game.display.get_height()-self.console_img.get_height()-4))
        for i,message in enumerate(self.messages):
            self.base_y -= 17
            self.font.render(self.messages_img_c,message,1,self.base_y,(255,255,255))

        self.base_y = self.messages_img.get_height()

        self.game.display.blit(self.messages_img_c,(self.x,(self.game.display.get_height()-self.console_img.get_height()-5)-self.messages_img.get_height()))

        self.extra_text_time -= 1
        if self.extra_text_time <= 0:
            self.extra_text_time = 32
            if self.extra_text == " ":
                self.extra_text = '|'
            else:
                self.extra_text = " "

    def get_event(self,event):
        if event.type == KEYDOWN:
            if event.unicode not in ['\r','\x08','\x1b']:
                self.command_input += event.unicode
            if event.key == K_ESCAPE:
                self.command_input = ""
            if event.key == K_BACKSPACE:
                self.command_input = self.command_input[:-1]
            if event.key == K_RETURN:
                self.commands.insert(0,self.command_input)
                self.run_command(self.command_input)
                self.command_input = ""

    def run_command(self,command):
        if "spawn" in command:
            command = command.split(" ")
            if "gun" in command[1]:
                gun_spawn = command[1].split(":")
                try:
                    gun_spawn[1] = gun_spawn[1].replace('_', ' ')
                    Gun = scripts.Gun(self.game.game_manager,gun_spawn[1],self.game.gun_data[gun_spawn[1]],self.game.FPS)
                    if len(command) == 3:
                        pos = command[2].split(';')
                        item = scripts.Item(self.game.game_manager,int(pos[0]),int(pos[1]),gun_spawn[1],"Guns",self.game.FPS,Gun)
                    else:
                        scroll = self.game.game_manager.camera.scroll
                        pos = [int(pygame.mouse.get_pos()[0]/2)+scroll[0],int(pygame.mouse.get_pos()[1]/2)+scroll[1]]
                        item = scripts.Item(self.game.game_manager,pos[0],pos[1],gun_spawn[1],"Guns",self.game.FPS,Gun)

                    self.game.game_manager.items.append(item)
                    self.messages.insert(0,f"Spawned {gun_spawn[1]} at {pos}")
                except Exception as e:
                    print(e)
                    
            if "item" in command[1]:
                item_spawn = command[1].split(":")
                try:
                    item_spawn[1] = item_spawn[1].replace('_', ' ')
                    item_group = ""
                    ref_obj = None
                    if item_spawn[1] in self.game.item_info["Ammo"]:
                        item_group = "Ammo"
                        ref_obj = scripts.Ammo(self.game,item_spawn[1])
                    if len(command) == 3:
                        pos = command[2].split(';')
                        item = scripts.Item(self.game.game_manager,int(pos[0]),int(pos[1]),item_spawn[1],item_group,self.game.FPS,ref_obj)
                    else:
                        scroll = self.game.game_manager.camera.scroll
                        pos = [int(pygame.mouse.get_pos()[0]/2)+scroll[0],int(pygame.mouse.get_pos()[1]/2)+scroll[1]]
                        item = scripts.Item(self.game.game_manager,pos[0],pos[1],item_spawn[1],item_group,self.game.FPS,ref_obj)

                    self.game.game_manager.items.append(item)
                    self.messages.insert(0,f"Spawned {item_spawn[1]} at {pos}")
                except Exception as e:
                    print(e)

                    
    def change_size(self):
        pass
