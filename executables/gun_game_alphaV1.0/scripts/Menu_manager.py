# Menu manager
import pygame
pygame.init()
from . import *
import sys

class Menu:
    def __init__(self, game):
        self.state = "Menu"
        self.game = game
        self.clicked = False
        self.click_tick = 50

        #Main menu screen
        self.play_button = Button(30, 35, 2, "SinglePlayer", 4,"Big", True)
        self.multiplayer_btn = Button(30, 90, 2, "Multiplayer", 4, "Big",True)
        self.level_btn = Button(30, 145, 2, "Level Editor", 4, "Big",True)
        
        #Multiplayer screen
        self.LAN_btn = Button(45,70,3,"LAN Game",5,"Big",True)
        self.Online_btn = Button(275,70,3,"Online",5,"Big",True)
        self.Host_btn = Button(45,70,3,"Host",5,"small",True)
        self.Join_btn = Button(275,70,3,"Join",5,"small",True)
        self.real_join = Button(45,70,3,"Join",5,"small",True)
        self.ip_addr = Text_Input(15,20,3,1,20)
        self.port_num = Text_Input(15,45,3,1,10)
        self.clock = pygame.time.Clock()
        
    def run(self):
        self.game.display.fill((90,90,90))
        self.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        pos = [int(pos[0]//2), int(pos[1]//2)]

        for event in pygame.event.get():
            if self.state == "Join_screen":
                self.ip_addr.get_event(event)
                self.port_num.get_event(event)
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
                self.game.game_manager.setup_mult(True,5555,"0", ["Classic",12,[[0,0],[100,20]]] )
                self.game.state = "Play"
                self.clicked = True
            if self.Join_btn.clicked == True and self.clicked == False:
                self.game.create_game_manager("Multiplayer")
                self.state = 'Join_screen'
                self.clicked = True
                
        if self.state == "Join_screen":
            self.ip_addr.update(self.game.display,pos)
            self.port_num.update(self.game.display,pos)
            self.real_join.update(self.game.display,pos)

            ip = self.ip_addr.text

            if self.real_join.clicked == True and self.clicked == False:
                self.game.game_manager.setup_mult(False,int(self.port_num.text),ip)
                self.game.state = "Play"

        if self.clicked == True:
            self.click_tick -= 1
            if self.click_tick <= 0:
                self.clicked = False
                self.click_tick = 50

        self.game.screen.blit(pygame.transform.scale(self.game.display, self.game.win_dims), (0,0))
        pygame.display.update()
