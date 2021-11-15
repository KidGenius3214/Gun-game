#Player Class
import pygame
from pygame.locals import *
pygame.init()

import scripts

class Player(scripts.Entity):
    def __init__(self,game,x,y,w,h,health,vel,jump,gravity,g_limit=6):
        super().__init__(x,y,w,h,vel,jump)

        self.game = game

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
        self.dmg_timer = 5 #make sure player does not lose an excessive amount of health
        self.shield = 0
        self.max_shield = 150
        self.has_shield = self.shield > 0
        
        # wall_jump_stuff
        self.wall_jump_true = False
        self.on_wall = False
        self.stick_on_wall = False
        self.stick_tick = 6
        self.jump_direction = 1
        self.wall_jump_tick = 7
        self.wall_jump_count = 0

        # Gun stuff
        self.equipped_weapon = None
        self.weapon_index = 0
        self.alive = True

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

        if self.wall_jump_true == True and self.wall_jump_count < 4:
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
            self.wall_jump_count = 0

        if self.wall_jump_true == True:
            self.wall_jump_tick -= 1
            if self.wall_jump_tick <= 0:
                self.wall_jump_true = False
                self.wall_jump_tick = 7

    def damage(self,dealer,amount):
        if self.hurt == False:
            if self.has_shield != True:
                self.health -= amount
                self.hurt = True
                if self.health < 0:
                    self.health = 0
            else:
                self.shield -= amount
                self.hurt = True
                if self.shield < 0:
                    self.shield = 0

    def add_health(self,amount):
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def add_shield(self,amount):
        self.shield += amount
        if self.shield > self.max_shield:
            self.shield = self.max_shield # max value of the shield is 150

    def add_ammo(self,item,item_remove_list,index):
        value = item.ref_obj.get_val()
        a_type = item.ref_obj.ammo_type
        if self.equipped_weapon.gun_group == self.game.ammo_data[a_type][1]: # Firstly check if the equipped weapon is of this ammo type
            if self.equipped_weapon.ammo != self.equipped_weapon.gun_info['ammo']:
                self.equipped_weapon.add_ammo(value)
                item_remove_list.append(index)
        else: #If not,look through the inventory for this ammo type
            for i in range(3): # First 4 slots are where the weapons are in
                gun = self.inventory.inventory[i+1]
                if len(gun) != 0:
                    if gun[0].ref_obj.gun_group == self.game.ammo_data[a_type][1]:
                        if gun[0].ref_obj.ammo != gun[0].ref_obj.gun_info['ammo']:
                            gun[0].ref_obj.add_ammo(value)
                            item_remove_list.append(index)
                            break
            

    def update(self):
        if self.hurt == True:
            self.dmg_timer -= 1
            if self.dmg_timer < 0:
                self.dmg_timer = 5
                self.hurt = False

        self.has_shield = self.shield > 0

        if self.health <= 0 :
            self.alive = False
            
