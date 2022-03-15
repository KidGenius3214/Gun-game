#Player Class
import pygame
from pygame.locals import *
pygame.init()

import scripts

class Player(scripts.Entity):
    def __init__(self,game,x,y,w,h,health,vel,jump,gravity,g_limit=6):
        super().__init__(x,y,w,h,vel,jump)

        self.game = game

        self.name = "Player"

        self.state = "Idle"
        self.gravity = gravity
        self.g_limit = g_limit
        self.has_jumped = False
        self.jump_count = 0
        self.flip = False
        self.id = 'Player'
        self.alive = True

        #Health management
        self.health = health
        self.max_health = health
        self.hurt = False
        self.dmg_timer = 0 #make sure player does not lose an excessive amount of health
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

        # weapon stuff
        self.equipped_weapon = None
        self.WEAPON_LIMIT = 4
        self.weapon_index = 0
        self.weapon_count = 0
        self.alive = True
        self.no_space = False
        self.melee_attacked = False

        # Inventory stuff
        # First 4 slots are where the weapons are stored
        self.inventory = scripts.Inventory(7)

        #Effects
        self.effect = "None"
        self.effect_count = 10
        self.effect_time = 0

    def add_weapon_item(self,item): #add weapons
        free_slots = self.inventory.free_slots()
        if len(free_slots) != 0:
            if free_slots[0] < self.WEAPON_LIMIT:
                for i in range(self.WEAPON_LIMIT): # First 4 slots are where the weapons are in
                    weapon = self.inventory.inventory[i]
                    if len(weapon) != 0:
                        if weapon[0].item_group != "Melee":
                            if weapon[0].item_name == item.item_name:
                                if weapon[0].ref_obj.ammo != weapon[0].ref_obj.gun_info['ammo']:
                                    weapon[0].ref_obj.add_ammo(item.ref_obj.ammo)
                                    return True
                                else:
                                    return False
                self.weapon_count += 1
                return self.inventory.add_item(item,free_slots[0],True)
            else:
                return False
        else:
            return False

    def equip_weapon(self):
        item_valid = len(self.inventory.get_item(self.weapon_index)) != 0
        if item_valid == True:
            self.equipped_weapon = self.inventory.get_item(self.weapon_index)[0].ref_obj
        else:
            return False

    def change_weapon(self,index,increase=False,decrease=False):
        if increase == False and decrease == False:
            old_index = self.weapon_index
            self.weapon_index = index
            if self.equip_weapon() == False:
                self.weapon_index = old_index
        elif increase == True and decrease == False:
            old_index = self.weapon_index 
            if self.weapon_index < self.WEAPON_LIMIT:
                self.weapon_index += 1
                if self.equip_weapon() == False:
                    self.weapon_index = old_index
        elif increase == False and decrease == True:
            old_index = self.weapon_index
            self.weapon_index -= 1
            if self.weapon_index < 0:
                self.weapon_index = 0
            if self.equip_weapon() == False:
                self.weapon_index = old_index
    
    def drop_weapon(self,movement,sort_weapons=True):
        if self.equipped_weapon != None:
            self.weapon_count -= 1
            item = self.inventory.remove_item(self.weapon_index,return_item=True)[0]
            item.pickup_cooldown = 15
            item.vel_y = 0
            item.dropped = True
            pos = self.get_center()
            pos[1] -= item.rect.width//2
            item.set_pos(pos)
            item.movement = movement
            self.game.items.append(item)
            self.equipped_weapon = None
            if sort_weapons == True:
                self.sort_weapons()
            if self.weapon_index == self.weapon_count:
                self.weapon_index -= 1
                if self.weapon_index < 0:
                    self.weapon_index = 0
            self.equip_weapon()
            self.no_space = False
            return True
        else:
            return False

    def swap_weapon(self,item):
        if item != None:
            if self.flip == True:
                movement = [-6,-2]
            else:
                movement = [4,-2]
            self.drop_weapon(movement,False)
            return self.add_weapon_item(item)
        else:
            return False
    
    def sort_weapons(self):
        if self.weapon_index != 3:
            if self.weapon_index == 0:
                for i in range(3):
                    temp = self.inventory.remove_item(i+1,True)
                    if len(temp) != 0:
                        self.inventory.add_item(temp[0],i,True)
            if self.weapon_index == 1:
                for i in range(2):
                    temp = self.inventory.remove_item(self.weapon_index+(1+i),True)
                    if len(temp) != 0:
                        self.inventory.add_item(temp[0],i+1,True)
            if self.weapon_index == 2:
                for i in range(1):
                    temp = self.inventory.remove_item(self.weapon_index+1,True)
                    if len(temp) != 0:
                        self.inventory.add_item(temp[0],i+2,True)
    
    def drop_all_weapons(self,movement_list):
        self.weapon_index = 0
        if self.weapon_count < 0:
            return False
        for i in range(self.weapon_count):
            self.drop_weapon(movement_list[i])
        return True
    
    def add_ammo(self,item,item_remove_list,index):
        value = item.ref_obj.get_val()
        a_type = item.ref_obj.ammo_type
        if self.equipped_weapon != None:
            if self.equipped_weapon.weapon_group == self.game.ammo_data[a_type][1]: # Firstly check if the equipped weapon is of this ammo type
                if self.equipped_weapon.ammo != self.equipped_weapon.gun_info['ammo']:
                    self.equipped_weapon.add_ammo(value)
                    item_remove_list.append(index)
            else: #If not,look through the inventory for this ammo type
                for i in range(3): # First 4 slots are where the weapons are in
                    gun = self.inventory.inventory[i+1]
                    if len(gun) != 0:
                        if gun[0].ref_obj.weapon_group == self.game.ammo_data[a_type][1]:
                            if gun[0].ref_obj.ammo != gun[0].ref_obj.gun_info['ammo']:
                                gun[0].ref_obj.add_ammo(value)
                                item_remove_list.append(index)
                                break
        else: #If not,look through the inventory for this ammo type
            for i in range(3): # First 4 slots are where the weapons are in
                gun = self.inventory.inventory[i+1]
                if len(gun) != 0:
                    if gun[0].ref_obj.weapon_group == self.game.ammo_data[a_type][1]:
                        if gun[0].ref_obj.ammo != gun[0].ref_obj.gun_info['ammo']:
                            gun[0].ref_obj.add_ammo(value)
                            item_remove_list.append(index)
                            break

    def movement(self,tiles, dt):
        #delta time is to make sure that the player moves the same amount nevery second
        movement = [0,0]
        if self.left == True:
            movement[0] -= self.vel * dt * self.game.target_fps
        if self.right == True:
            movement[0] += self.vel * dt * self.game.target_fps
        movement[1] += self.vel_y * dt * self.game.target_fps
        self.vel_y += self.gravity * dt * self.game.target_fps
        if self.vel_y > self.g_limit:
            self.vel_y = self.g_limit

        if self.wall_jump_true == True:
            movement[1] = -4*dt*self.game.target_fps
            movement[0] = (8*dt*self.game.target_fps)*self.jump_direction
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
                self.vel_y = 1.2
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
            self.wall_jump_tick -= 1*dt*self.game.target_fps
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


    def manage_effects(self):
        if self.effect == "burning":
            count = self.effect_count
            self.damage('burn',1)
            self.effect_time += 1

            if self.effect_time >= 20:
                self.effect_time = 0
                self.effect = "None"

    def update(self):
        self.manage_effects()

        if self.hurt == True:
            self.dmg_timer -= 1
            if self.dmg_timer < 0:
                self.dmg_timer = 0
                self.hurt = False

        self.has_shield = self.shield > 0

        if self.health <= 0 :
            self.alive = False
            
