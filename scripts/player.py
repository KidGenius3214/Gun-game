#Player Class
import pygame
from pygame.locals import *
pygame.init()

import scripts

class Player(scripts.Entity):
    def __init__(self,game,x,y,w,h,health,vel,jump,gravity,g_limit=6):
        super().__init__(x,y,w,h,vel,jump)

        self.state = "Idle"
        self.gravity = gravity
        self.g_limit = g_limit
        self.has_jumped = False
        self.jump_count = 0
        self.flip = False

        #Health management
        self.health = health
        self.max_health = health
        self.hurt = False
        self.dmg_timer = 10 #make sure player does not lose an excessive amount of health
        self.shield = 0
        
        # wall_jump_stuff
        self.wall_jump_true = False
        self.on_wall = False
        self.stick_on_wall = False
        self.stick_tick = 6
        self.jump_direction = 1
        self.wall_jump_tick = 7
        self.wall_jump_cooldown = 14

        # Gun stuff
        self.equipped_weapon = None
        self.weapon_index = 0

        # Inventory stuff
        # First 4 slots are where the weapons are stored
        self.inventory = scripts.Inventory(7) 

    def add_weapon_item(self,item): #add weapons
        free_slots = self.inventory.free_slots()
        if len(free_slots) != 0:
            if free_slots[0] <= 3:
                return self.inventory.add_item(item,free_slots[0],True)
            else:
                return False
        else:
            return False

    def equip_weapon(self):
        self.equipped_weapon = self.inventory.get_item(self.weapon_index)[0].ref_obj

    def movement(self,tiles):
        movement = [0,0]
        if self.left == True:
            movement[0] -= self.vel
            self.flip = True
        if self.right == True:
            movement[0] += self.vel
            self.flip = False
        movement[1] += self.vel_y
        self.vel_y += self.gravity
        if self.vel_y > self.g_limit:
            self.vel_y = self.g_limit

        if self.wall_jump_true == True:
            movement[1] = -4
            movement[0] = 8*self.jump_direction
            self.vel_y = -4

        self.collisions = self.physics_obj.movement(movement,tiles)
        self.rect = self.physics_obj.rect
        self.x = self.rect.x
        self.y = self.rect.y

        self.on_wall = False

        if self.collisions["top"] == True:
            self.vel_y += 1.2

        if self.collisions["right"] == True or self.collisions["left"] == True:
            self.on_wall = True
            self.wall_jump_true = False
            if movement[1] > 0:
                self.vel_y = 1.5
            if self.collisions["right"] == True:
                self.jump_direction = -1
            else:
                self.jump_direction = 1
        else:
            self.on_wall = False
            self.wall_up_time = 4
        
        if self.collisions["bottom"] == True:
            self.vel_y = 1
            self.jump_count = 0

        if self.wall_jump_true == True:
            self.wall_jump_tick -= 1
            if self.wall_jump_tick <= 0:
                self.wall_jump_true = False
                self.wall_jump_tick = 7

    def hurt(self,dealer,amount):
        if self.hurt == False:
            self.health -= amount
            if self.health < 0:
                self.health = 0

    def add_health(self,amount):
        self.health += amount
        if self.health > self.max_health:
            self.heath = self.max_health

    def add_shield(self,amount):
        self.shield += amount
        if self.shield > 150:
            self.shield = 150 # max value of the shield is 150
            
