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
        self.screen = pygame.display.set_mode(self.win_dims)
        self.display = pygame.Surface((self.display_dims))
        self.version = "v2.0 alpha"
        pygame.display.set_caption(f"Gun Game {self.version}")
        self.state = "Menu"
        self.TILESIZE = 20
        self.CHUNKSIZE = 16
        self.img_m = Image_Manager(['.png','jpg'])
        self.json_h = JSON_Handler()
        self.controller_input = self.json_h.load("data/Game_data/controller_input.json", "controller_input")
        self.gun_data = self.json_h.load("data/Game_data/guns.json","gun_data")
        self.tile_data = self.json_h.load("data/Game_data/tile_data.json","tile_data")

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
        self.zone1_tiles["park_bench"] = self.img_m.load("data/images/zone1_tileset/park_bench.png",(255,255,255))
            
        self.controller_cursor = self.img_m.load("data/images/cursor.png", (255,255,255))

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
        self.game_manager = Game_manager(self,play_type)

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
        self.states_manager()


Main_Game = Game([1200,700], [600,350], 50)
while True:
    Main_Game.run()