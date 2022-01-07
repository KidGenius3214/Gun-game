import pygame
import scripts
from pygame.locals import *


class Consumable:
    def __init__(self,game,x,y,name):
        self.game = game
        self.x = x
        self.y = y
        self.name = name
        self.value = self.game.consumable_data[self.name][0]
        self.is_shield = self.game.consumable_data[self.name][1]
        self.item_obj = scripts.Item(self.game,self.x,self.y,self.name,"Consumables",self.game.game.FPS,self)
        self.pickup_cooldown = self.item_obj.pickup_cooldown
        self.rect = self.item_obj.rect

    def render(self,surf,scroll):
        self.item_obj.render(surf,scroll)

    def move(self,tiles):
        self.item_obj.move(tiles)
        self.rect = self.item_obj.rect

        
        
