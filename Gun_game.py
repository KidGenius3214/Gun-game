#Main game
#By Kid Genius
import pygame
from pygame.locals import *
from scripts import *
import sys
pygame.init()

class Game:
    def __init__(self,win_dims,display_dims,FPS):
        self.win_dims = win_dims
        self.display_dims = display_dims
        self.FPS = FPS
        
        # Setup the screen and display
        self.json_h = JSON_Handler()
        self.controller_input = self.json_h.load("data/Game_data/controller_input.json", "controller_input")
        self.weapon_data = self.json_h.load("data/Game_data/weapons.json","gun_data")
        self.tile_data = self.json_h.load("data/Game_data/tile_data.json","tile_data")
        self.item_info = self.json_h.load("data/Game_data/item_info.json","item_data")
        self.ammo_data = self.json_h.load("data/Game_data/ammo_info.json","ammo_data")
        self.consumable_data = self.json_h.load("data/Game_data/consumables.json","consumable_data")
        self.key_inputs = self.json_h.load("data/Game_data/key_input.json","Key_Inputs")
        self.settings = self.json_h.load("data/Game_data/settings.json","settings")
        self.scale = self.settings['video_settings'][0]
        self.protocol = self.settings["networking"]["protocol"]
        self.fullscreen = False

        if self.settings['video_settings'][1] == False:
            self.screen = pygame.display.set_mode((int(self.win_dims[0]*self.scale),int(self.win_dims[1]*self.scale)))
        else:
            self.screen = pygame.display.set_mode((int(self.win_dims[0]*self.scale),int(self.win_dims[1]*self.scale)),pygame.FULLSCREEN)
            self.fullscreen = True
        self.display = pygame.Surface((self.display_dims))

        self.clock = pygame.time.Clock()
        self.version = "v2.0 alpha"
        pygame.display.set_caption(f"Gun Game {self.version}")
        self.state = "Menu"
        self.TILESIZE = 20
        self.CHUNKSIZE = 16
        self.img_m = Image_Manager(['.png','jpg'])

        #images
        # Zone 1 images
        self.zone1_tiles = {}
        tile_count = 0
        image = self.img_m.load("data/images/zone1_tileset/60_23.png",(255,255,255))
        for i in range(round(image.get_width()/self.TILESIZE)):
            tile_count = i+1
            self.zone1_tiles[str(tile_count)] = get_image(image,i*self.TILESIZE,0,self.TILESIZE,23,1)
        image = self.img_m.load("data/images/zone1_tileset/20_20.png",(255,255,255))
        for i in range(round(image.get_width()/self.TILESIZE)):
            tile_count = i+4
            self.zone1_tiles[str(tile_count)] = get_image(image,i*self.TILESIZE,0,self.TILESIZE,self.TILESIZE,1)
        image = self.img_m.load("data/images/zone1_tileset/plants.png",(255,255,255))
        for i in range(round(image.get_width()/self.TILESIZE)):
            tile_count = self.tile_data["plants"][i]
            self.zone1_tiles[str(tile_count)] = get_image(image,i*self.TILESIZE,0,self.TILESIZE,self.TILESIZE,1)
        image = self.img_m.load("data/images/zone1_tileset/trees.png",(255,255,255))
        for tree in self.tile_data["trees"]:
            tile_data = self.tile_data["trees"][tree]
            self.zone1_tiles[str(tree)] = get_image(image,tile_data[0],tile_data[1],tile_data[2],tile_data[3],1)
        self.zone1_tiles["park_bench"] = self.img_m.load("data/images/zone1_tileset/park_bench.png",(255,255,255))
            
        self.controller_cursor = self.img_m.load("data/images/cursor.png", (0,0,0))
        self.health_bar_img = self.img_m.load('data/images/Health_Bar.png',(255,255,255))

        self.tiles = {"zone1":self.zone1_tiles}
        self.menu_manager = Menu(self)

    def states_manager(self):
        if self.state == "Menu":
            self.main_menu()
        if self.state == "Play":
            self.play()
        if self.state == "Level_Editor":
            self.level_editor_mode()

    def create_game_manager(self,play_type):
        pygame.mouse.set_visible(False) #Hide mouse cursor
        self.game_manager = Game_manager(self,play_type)
    
    def create_menu_manager(self):
        pygame.mouse.set_visible(True) #Hide mouse cursor
        self.menu_manager = Menu(self)

    def create_Level_editor(self):
        self.level_editor = Level_Editor(self)
        self.level_editor.clicked = True

    def main_menu(self):
        self.menu_manager.run()

    def level_editor_mode(self):
        self.level_editor.run()

    def play(self):
        self.game_manager.run()

    def run(self):
        while True:
            self.states_manager()


Main_Game = Game([600,350], [600,350], 50)
Main_Game.run()
