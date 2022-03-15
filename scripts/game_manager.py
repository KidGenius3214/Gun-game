#Game manager
#It's basically where whole gameplay stuff is 
import pygame
from pygame.locals import *
pygame.init()
import scripts
import sys, math, random,time,base64
import json,pickle,subprocess,threading
from copy import deepcopy

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

def rotate(point, angle, origin, Round = False):
        x = point[0] - origin[0]
        y = point[1] - origin[1]
        
        Cos = math.cos(math.radians(angle))
        Sin = math.sin(math.radians(angle))

        if Round == True:
            xPrime = (round(x * Cos)) - (round(y * Sin))
            yPrime = (round(x * Sin)) + (round(y * Cos))
        else:
            xPrime = (x * Cos) - (y * Sin)
            yPrime = (x * Sin) + (y * Cos)
            
        xPrime += origin[0]
        yPrime += origin[1]
        newPoint = [xPrime, yPrime]
        return newPoint

class GameManager:
    def __init__(self,game,play_type):
        self.game = game
        self.target_fps = self.game.target_fps
        self.play_type = play_type
        self.player = scripts.Player(self,0, 0, 16, 16, 100, 3, 6, 0.3)
        self.event = None
        self.console = scripts.Console(self.game,(self.game.display.get_width()-4,25))
        self.current_level = 'Debug_level_0'
        self.bullets = []
        self.particles = []
        self.items = []
        self.entities = []
        self.entities.append(scripts.Bad_Guy(self,2*self.game.TILESIZE,0,self.game.TILESIZE,self.game.TILESIZE,100,0.1,6,0.3))
        self.enemy_ids = ["Bad Guy"]
        self.level = None
        self.tiles = self.game.tiles
        self.scroll = [0,0]
        self.alt_key = False
        self.shift = False
        self.ctrl = False
        self.show_console = False
        self.zoom = 1 # Change the view of the display
        self.zoom_index = 0 # Index for zooming in snipers
        self.tile_data = self.game.tile_data
        self.weapon_data = self.game.weapon_data
        self.consumable_data = self.game.consumable_data
        self.ammo_data = self.game.ammo_data
        self.item_data = self.game.item_info
        self.key_inputs = self.game.key_inputs
        self.camera = scripts.Camera()
        self.show_fps = False
        self.EntityManager = scripts.EntityManager(game)

        #Delta time calculation
        self.time_passed = time.time()
        self.dt = 1


        #Fonts
        self.font1 = scripts.Text("data/images/font.png",1,3)
        self.font1_x1_5 = scripts.Text("data/images/font.png", round(1*1.5), round(3*1.5))

        self.font2 = scripts.Text("data/images/font.png",1,2)
        self.font2_x1_5 = scripts.Text("data/images/font.png", round(1*1.5), round(2*1.5))

        self.font3 = scripts.Text("data/images/font.png",1,1)
        self.font3_x1_5 = scripts.Text("data/images/font.png", round(1*1.5), round(1*1.5))

        self.fonts = {"font_1": [self.font1, self.font1_x1_5], "font_2":[self.font2, self.font2_x1_5], "font_3":[self.font3, self.font3_x1_5]}
        
        #controller stuff
        self.controller_input = self.game.json_h.files["controller_input"]
        self.right_pressed = False
        self.left_pressed = False
        self.jumped = False
        self.joystick = None
        self.controller_pos = [0,0]
        self.moving_aim_axis = False
        self.c_sensitivity = self.controller_input["sensitivity"]
        self.reload_controller()
    
        #Multiplayer stuff
        self.hosting = False
        self.host_server = None
        self.players = {}
        self.client = None
        self.ip = ""
        self.port = 1

        #Inventory rendering stuff
        self.position = 25
        self.size = 1

        self.grenade = None
        self.reset_level(self.current_level)

    def reload_controller(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        joy_count = pygame.joystick.get_count()
        if joy_count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

    def change_dims(self):
        self.console.change_size([round(self.game.display_dims[0]*self.zoom)-round(4*self.zoom),round(25*self.zoom)],2+round(self.zoom))
        # Change size of display
        self.game.display = pygame.transform.scale(self.game.display,(round(self.game.display_dims[0]*self.zoom),round(self.game.display_dims[1]*self.zoom)))
        self.camera.update(self.player,self.game.display,1) # Make sure the camera is on the player when changing the dimensions

    def reset_level(self,level):
        self.items = []
        self.reload_controller()
        with open(f"data/maps/{level}.level", "rb") as file:
            data = pickle.load(file)
            file.close()
            self.level = data["data"]
            self.zone = data["zone"]
            del data

        for spawn in self.level["spawnpoints"]:
            if spawn[0] == "spawn":
                self.player.set_pos(spawn[1][0]*self.game.TILESIZE,spawn[1][1]*self.game.TILESIZE)
                self.camera.update(self.player,self.game.display,1)

        for item_id in self.level["items"]:
            if item_id[0] in self.item_data["Guns"]:
                gun = scripts.Gun(self,item_id[0],self.weapon_data[item_id[0]],self.target_fps)
                item = scripts.Item(self,item_id[1][0]*self.game.TILESIZE,item_id[1][1]*self.game.TILESIZE,item_id[0],"Guns",self.target_fps,gun)
                self.EntityManager.add_item(item)
                self.items.append(item)
            if item_id[0] in self.item_data["Melee"]:
                melee = scripts.Melee_Weapon(self,item_id[0])
                item = scripts.Item(self,item_id[1][0]*self.game.TILESIZE,item_id[1][1]*self.game.TILESIZE,item_id[0],"Melee",self.target_fps,melee)
                self.EntityManager.add_item(item)
                self.items.append(item)
            if item_id[0] in self.item_data["Ammo"]:
                ref_obj = scripts.Ammo(self.game,item_id[0])
                item = scripts.Item(self,item_id[1][0]*self.game.TILESIZE,item_id[1][1]*self.game.TILESIZE,item_id[0],"Ammo",self.target_fps,ref_obj)
                self.EntityManager.add_item(item)
                self.items.append(item)
            if item_id[0] in self.item_data["Consumables"]:
                item = scripts.Consumable(self,int(item_id[1][0]*self.game.TILESIZE),int(item_id[1][1]*self.game.TILESIZE),item_id[0])
                self.EntityManager.add_item(item)
                self.items.append(item)

        self.current_level = level
            
    def handle_controller_input(self):
        controller_states = {
            "active":False,
            "axis_val":[0,0],
            "buttons":{"jump":False,"change_gun":[False,0],"shoot":False,"right":False,"left":False,"up":False,"down":False}
        }
        if self.joystick != None:
            controller_states["active"] = True
            if self.controller_input[self.joystick.get_name()] != {}:
                for axis in range(self.joystick.get_numaxes()):

                    if axis in self.controller_input[self.joystick.get_name()]["axes"]:
                        if axis == self.controller_input[self.joystick.get_name()]["aim_x"]: #Aiming in the x axis
                            self.controller_pos[0] += self.joystick.get_axis(axis)*self.c_sensitivity
                            if self.joystick.get_axis(axis) > 0.6 or self.joystick.get_axis(axis) < -0.6:
                                self.moving_aim_axis = True
                            if self.controller_pos[0] < 0:
                                self.controller_pos[0] = 0
                            if self.controller_pos[0] > self.game.display.get_width()-1:
                                self.controller_pos[0] = self.game.display.get_width()-1
                                
                        if axis == self.controller_input[self.joystick.get_name()]["aim_y"]: # Aiming in the y axis
                            self.controller_pos[1] += self.joystick.get_axis(axis)*self.c_sensitivity
                            if self.joystick.get_axis(axis) > 0.6 or self.joystick.get_axis(axis) < -0.6:
                                self.moving_aim_axis = True
                            if self.controller_pos[1] < 0:
                                self.controller_pos[1] = 0
                            if self.controller_pos[1] > self.game.display.get_height()-1:
                                self.controller_pos[1] = self.game.display.get_height()-1
                                
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
                                
                for hat in range(self.joystick.get_numhats()):
                    if hat in self.controller_input[self.joystick.get_name()]["hats"]:
                        hat_val = self.joystick.get_hat(hat)
                        if hat_val[0] != 0:
                            controller_states["buttons"]["change_gun"] = [True,hat_val[0]]
                
                for button in range(self.joystick.get_numbuttons()):
                    if button in self.controller_input[self.joystick.get_name()]["buttons"]:
                        if button == self.controller_input[self.joystick.get_name()]["jump"]:
                            if self.joystick.get_button(button):
                                if controller_states["buttons"]["jump"] == False:
                                    controller_states["buttons"]["jump"] = True
                                else:
                                    controller_states["buttons"]["jump"] = False

                        if button == self.controller_input[self.joystick.get_name()]["shoot"]:
                            if self.joystick.get_button(button):
                                if controller_states["buttons"]["shoot"] == False:
                                    controller_states["buttons"]["shoot"] = True
                                else:
                                    controller_states["buttons"]["shoot"] = False

        return controller_states
    
    def find_min_and_max(self, rect, angle, axis, normal):
        a = (pygame.math.Vector2(rotate(rect.topleft, angle, rect.center))).dot(normal)
        b = (pygame.math.Vector2(rotate(rect.topright, angle, rect.center))).dot(normal)
        c = (pygame.math.Vector2(rotate(rect.bottomleft, angle, rect.center))).dot(normal)
        d = (pygame.math.Vector2(rotate(rect.bottomright, angle, rect.center))).dot(normal)

        projections = [a,b,c,d]

        Min = projections[0]
        for proj in projections:
            if proj < Min:
                Min = proj
        
        Max = projections[0]
        for proj in projections:
            if proj > Max:
                Max = proj
        
        return [Min, Max]
                

    def SAT_Collision(self, A, B, rotA, rotB):
        #X axis
        Axis1 = rotate([1,0], rotA, [0,0])
        Axis2 = rotate([1,0], rotB, [0,0])

        #Y axis
        Axis3 = rotate([0,1], rotA, [0,0])
        Axis4 = rotate([0,1], rotB, [0,0])

        x_axis = [Axis1, Axis2]
        y_axis = [Axis3, Axis4]

        axis_check = [False,False,False,False]
        #check x-axis
        for i, axis in enumerate(x_axis):
            Amin, Amax = self.find_min_and_max(A, rotA, 'x', axis)
            Bmin, Bmax = self.find_min_and_max(B, rotB, 'x', axis)

            if Bmin < Amax and Bmax > Amin:
                axis_check[i] = True
        
        #check y-axis
        for i, axis in enumerate(y_axis):
            j = i + 2

            Amin, Amax = self.find_min_and_max(A, rotA, 'y', axis)
            Bmin, Bmax = self.find_min_and_max(B, rotB, 'y', axis)

            if Bmin < Amax and Bmax > Amin:
                axis_check[j] = True
        
        collision = (axis_check == [True,True,True,True])
        return collision

    def melee_attack_logic(self,weapon):
        angle = -weapon.angle
        rect = weapon.rect
        if self.player.flip == True:
            rect = pygame.Rect(rect.x-rect.width, rect.y, rect.width, rect.height)
        for enemy in self.entities:
            #Get All axis for the rect and enemy rect
            if self.SAT_Collision(rect, enemy.rect, angle, 0) == True:
                print("sliced")
                enemy.damage("player", weapon.dmg)
                print(enemy.health)


    def singleplayer_game(self):
        self.game.display.fill((90,90,90))
        self.game.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        size_dif = float(self.game.screen.get_width()/self.game.display.get_width())
        self.relative_pos = [int(pos[0]/size_dif), int(pos[1]/size_dif)]

        #print( self.SAT_Collision(pygame.Rect(200, 300, 50, 50), pygame.Rect(200, 300, 50, 50), 5, 0) )

        #Delta Time calculation
        now = time.time()
        self.dt = now - self.time_passed
        self.time_passed = now
        self.game.display = pygame.transform.scale(self.game.display,(round(self.game.display_dims[0]*self.zoom),round(self.game.display_dims[1]*self.zoom)))

        self.camera.update(self.player,self.game.display,10)
        
        scroll = [0,0]
        scroll[0] = self.camera.scroll[0]
        scroll[1] = self.camera.scroll[1]
        controller_input = self.handle_controller_input()
        
        tiles = []
        active_chunks = []
        angle = scripts.find_angle_from_points(self.relative_pos,self.player.get_center(),scroll,[0,0],False)

        if self.moving_aim_axis == True:
            angle = scripts.find_angle_from_points(self.controller_pos,self.player.get_center(),scroll,[0,0],False)

        chunk_num = self.game.CHUNKSIZE*self.game.TILESIZE
        chunk_seen_width = round(self.game.display.get_width()/chunk_num)+2
        chunk_seen_height = round(self.game.display.get_height()/chunk_num)+2
        
        for y in range(chunk_seen_height):
            for x in range(chunk_seen_width):
                chunk_x = x-1 + round(scroll[0]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_y = y-1 + round(scroll[1]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_id = f"{chunk_x}/{chunk_y}"
                active_chunks.append(chunk_id)

        for chunk_id in active_chunks:
            for layer in self.level:
                if layer not in ['tiles','spawnpoints','items']:
                    if chunk_id in self.level[layer]:
                        for tile in self.level[layer][chunk_id]:
                            if tile[0] in self.tiles[self.zone]:
                                if tile[0] not in ['1','2','3']:
                                    self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                            if tile[0] in ['1','2','3']:
                                self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-3-scroll[1]))
                            if tile[0] in self.tile_data["collidable"]:
                                tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))

        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.pickup_cooldown -= 1
                if item.pickup_cooldown < 0:
                    item.pickup_cooldown = 0
                item.render(self.game.display,scroll)
        
        b_remove_list = []
        n = 0
        for bullet in self.bullets:
            bullet.run(self.game.display,scroll, self.dt)
            if bullet.lifetime <= 0:
                b_remove_list.append(n)
            n += 1
        b_remove_list.sort(reverse=True)
        for bullet in b_remove_list:
            self.bullets.pop(bullet)

        enemy_remove_list = []
        n = 0
        for enemy in self.entities:
            if enemy.id == "Base_Enemy":
                if enemy.alive == True:
                    enemy.draw(self.game.display,scroll)
                else:
                    enemy_remove_list.append(n)
                enemy.update()
            if enemy.id == "Bad_Guy":
                if enemy.alive == True:
                    enemy.draw(self.game.display,scroll)
                else:
                    enemy_remove_list.append(n)
                enemy.update()
            n += 1
        enemy_remove_list.sort(reverse=True)
        for enemy in enemy_remove_list:
            self.entities.pop(enemy)

        self.player.draw(self.game.display, scroll)

        for chunk_id in active_chunks:
            if chunk_id in self.level["tiles"]:
                for tile in self.level["tiles"][chunk_id]:
                    if tile[0] in self.tiles[self.zone]:
                        if tile[0] not in ['1','2','3']:
                            self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                    if tile[0] in ['1','2','3']:
                        self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-3-scroll[1]))
                    if tile[0] in self.tile_data["collidable"]:
                        tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))

        if self.player.equipped_weapon != None:
            x = self.relative_pos[0]+scroll[0]
            if self.player.equipped_weapon.weapon_group != "Melee":
                if x < self.player.get_center()[0]:
                    self.player.equipped_weapon.flip = True
                    self.player.flip = True
                else:
                    self.player.equipped_weapon.flip = False
                    self.player.flip = False
                self.player.equipped_weapon.update(self.game.display,scroll,self.player.get_center(),math.degrees(-angle),self.dt)
                if pygame.mouse.get_pressed()[0] == True:
                    self.player.equipped_weapon.shoot(self.bullets,"player",self.player.get_center(),angle,self.dt)
                if controller_input["active"] == True:
                    x = self.controller_pos[0]+scroll[0]
                    if x < self.player.get_center()[0]:
                        self.player.equipped_weapon.flip = True
                        self.player.flip = True
                    else:
                        self.player.equipped_weapon.flip = False
                        self.player.flip = False
                    if controller_input["buttons"]["shoot"] == True:
                        self.player.equipped_weapon.shoot(self.bullets,"player",self.player.get_center(),angle,self.dt)
            if self.player.equipped_weapon.weapon_group == "Melee":
                if x < self.player.get_center()[0]:
                    self.player.equipped_weapon.flip = True
                    self.player.flip = True
                else:
                    self.player.equipped_weapon.flip = False
                    self.player.flip = False
                self.player.equipped_weapon.update(self.game.display,scroll,[self.player.get_center()[0],self.player.get_center()[1]],math.degrees(-angle))
                if pygame.mouse.get_pressed()[0] == True and self.player.melee_attacked == False:
                    self.player.melee_attacked = True
                    self.player.equipped_weapon.attack(angle,[self.player.get_center()[0],self.player.get_center()[1]])
                    self.melee_attack_logic(self.player.equipped_weapon)
                if controller_input["active"] == True:
                    x = self.controller_pos[0]+scroll[0]
                    if x < self.player.get_center()[0]:
                        self.player.equipped_weapon.flip = True
                        self.player.flip = True
                    else:
                        self.player.equipped_weapon.flip = False
                        self.player.flip = False

        b_remove_list = []
        n = 0
        for bullet in self.bullets:
            for enemy in self.entities:
                if bullet.rect.colliderect(enemy.rect):
                    if bullet.owner in ["player"]:
                        enemy.damage(bullet.owner,bullet.dmg)
                        b_remove_list.append(n)

            if bullet.rect.colliderect(self.player.rect):
                if bullet.owner in self.enemy_ids:
                    self.player.damage(bullet.owner,bullet.dmg)
                    b_remove_list.append(n)
            
            for tile in tiles:
                if tile.colliderect(bullet.rect):
                    b_remove_list.append(n)
                    
            n += 1
        b_remove_list.sort(reverse=True)
        for bullet in b_remove_list:
            try:
                self.bullets.pop(bullet)
            except:
                pass

        p_remove_list = []
        n = 0
        for particle in self.particles:
            particle.render(self.game.display,[0,0])
            if particle.size <= 0:
                p_remove_list.append(n)
            n += 1
        p_remove_list.sort(reverse=True)
        for particle in p_remove_list:
            self.particles.pop(particle)

        for enemy in self.entities:
            if enemy.id == "Base_Enemy":
                enemy.movement(tiles)
            if enemy.id == "Bad_Guy":
                enemy.handle_ai(tiles,self.player,scroll)


        item_remove_list = []
        n = 0
        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.move(tiles,self.dt)
            if item.rect.colliderect(self.player.rect):
                if item.pickup_cooldown <= 0:
                    if isinstance(item, scripts.Item):
                        if item.item_group in ["Guns","Melee"]:
                            if self.player.no_space == False:
                                tooltip = scripts.Tooltip(self.player.rect.topright[0]+5,self.player.rect.y+1,1,1,"E to pickup",(235,235,235))
                                tooltip.draw(self.game.display,scroll)
                            if item.dropped == False:
                                if self.player.equipped_weapon != None:
                                    if item.ref_obj.name == self.player.equipped_weapon.name and item.item_group != "Melee":
                                        if self.player.add_weapon_item(item) == True:
                                            item_remove_list.append(n)
                                            self.player.equip_weapon()
                                if pygame.key.get_pressed()[self.key_inputs["equip"]] == True:
                                    if self.player.add_weapon_item(item) == True:
                                        item_remove_list.append(n)
                                        self.player.equip_weapon()
                                elif pygame.key.get_pressed()[self.key_inputs["change"]] == True: 
                                    if self.player.swap_weapon(item) == True:
                                        item_remove_list.append(n)
                                        self.player.equip_weapon()
                        if item.item_group == "Ammo":
                            self.player.add_ammo(item,item_remove_list,n)
                    if isinstance(item,scripts.Consumable):
                        if item.is_shield == False:
                            if self.player.health != self.player.max_health:
                                self.player.add_health(item.value)
                                item_remove_list.append(n)
                        else:
                            if self.player.shield != self.player.max_shield:
                                self.player.add_shield(item.value)
                                item_remove_list.append(n)
            n += 1
        item_remove_list.sort(reverse=True)
        for item in item_remove_list:
            self.items.pop(item)

        self.player.movement(tiles, self.dt)

        if self.show_console == True:
            self.console.render()

        self.player.update()

        self.game.display.blit(pygame.transform.scale(self.game.health_bar_img,(round((self.game.health_bar_img.get_width()*2)*self.zoom),
                                                                                round((self.game.health_bar_img.get_height()*2)*self.zoom))),(2,2))
        health_calc = ((self.player.health*168)/self.player.max_health)
        pygame.draw.rect(self.game.display,(0,255,0),(4,4,round(health_calc*self.zoom),round(16*self.zoom)))

        self.fonts["font_1"][0].render(self.game.display,f"{self.player.shield}",(self.game.health_bar_img.get_width()*2)+6,2,(127,127,127))

        #Show ammo and gun name
        if self.player.equipped_weapon != None:
            color = (255,255,255)
            if self.player.equipped_weapon.weapon_group != "Melee":
                ammo_text = f"{self.player.equipped_weapon.ammo}/{self.player.equipped_weapon.ammo_l}"
            else:
                ammo_text = "\x00/\x00"
            if self.player.equipped_weapon.weapon_group != "Melee":
                if self.player.equipped_weapon.ammo <= 0 and self.player.equipped_weapon.ammo_l <= 0:
                    color = (255,0,0)
                
            self.fonts["font_1"][0].render(self.game.display,ammo_text,2,(self.game.health_bar_img.get_height()*2)+7,color)


        #Render the inventory of the player
        inventory_data = self.player.inventory.get_all_items()
        self.position = 10
        for i,weapon_id in sorted(enumerate(inventory_data), reverse=True):
            weapon = inventory_data[weapon_id]
            if len(weapon) != 0:
                weapon = weapon[0].ref_obj
                if weapon != self.player.equipped_weapon:
                    surf = pygame.mask.from_surface(weapon.img)
                    img = surf.to_surface(setcolor=(240,240,240))
                    img = pygame.transform.scale(img,(img.get_width(),img.get_height()))
                    img.set_colorkey((0,0,0))
                    if weapon.weapon_group == "Melee":
                        img = scripts.get_image(img,int(img.get_width()/2),0,int(img.get_width()/2),img.get_height(),1)
                    self.game.display.blit(img, (self.game.display.get_width()-(img.get_width()+self.position), 10))
                    pygame.draw.line(self.game.display,(240,240,240),(self.game.display.get_width()-(img.get_width()+self.position),1), ((self.game.display.get_width()-(img.get_width()+self.position))+(img.get_width()-2),1),2)
                    self.position += img.get_width()+20
                else:
                    surf = pygame.mask.from_surface(weapon.img)
                    img = surf.to_surface(setcolor=(255,255,255))
                    img = pygame.transform.scale(img,(round(img.get_width()*1.5),round(img.get_height()*1.5)))
                    img.set_colorkey((0,0,0))
                    if weapon.weapon_group == "Melee":
                        img = scripts.get_image(img,int(img.get_width()/2),0,int(img.get_width()/2),img.get_height(),1)
                    self.game.display.blit(img, (self.game.display.get_width()-(img.get_width()+self.position), 10))
                    pygame.draw.line(self.game.display,(255,255,255),(self.game.display.get_width()-(img.get_width()+self.position+3),1), ((self.game.display.get_width()-(img.get_width()+self.position))+(img.get_width()-3),1),2)
                    self.position += img.get_width()+20
        
        if self.player.weapon_count >= 4:
            self.player.no_space = True

        if self.show_fps == True:
            size = (self.font1.get_size(f"FPS: {int(self.game.clock.get_fps())}"))
            self.font1.render(self.game.display, f"FPS: {int(self.game.clock.get_fps())}", self.game.display.get_width()-(size[0]+5), self.game.display.get_height()-(size[1]+1), (255,255,255))
        else:
            pass

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

            if controller_input["buttons"]["change_gun"][0] == True:
                self.player.weapon_index += controller_input["buttons"]["change_gun"][1]
                if self.player.weapon_index < 0:
                    self.player.weapon_index = 0
                if self.player.weapon_index > 2:
                    self.player.weapon_index = 2
                self.player.equip_weapon()

        if self.moving_aim_axis == True:
            scripts.blit_center(self.game.display,self.game.controller_cursor,self.controller_pos)
        else:
            scripts.blit_center(self.game.display,self.game.controller_cursor,self.relative_pos)

        for event in pygame.event.get():
            self.event = event
            if self.show_console == True:
                self.console.get_event(event)
                
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.show_console = False
                    
                if self.show_console == False:
                    if event.key == self.key_inputs["left"]:
                        self.player.left = True
                    if event.key == self.key_inputs["right"]:
                        self.player.right = True
                    if event.key == self.key_inputs["reload"]:
                        if self.player.equipped_weapon != None:
                            if self.player.equipped_weapon.reload_gun == False:
                                self.player.equipped_weapon.reload_gun = True
                    if event.key == K_LALT:
                        self.alt_key = True
                    if event.key == K_RALT:
                        self.alt_key = True
                    if event.key == K_c:
                        if self.alt_key == True:
                            self.show_console = True
                    if event.key == self.key_inputs["drop"]:
                        movement = [0,0]
                        if self.player.flip == True:
                            movement = [-6,-2]
                        else:
                            movement = [4,-2]
                        self.player.drop_weapon(movement)
                            
                    if event.key == self.key_inputs["sniper_zoom"]:
                        if self.player.equipped_weapon != None:
                            if self.player.equipped_weapon.weapon_group == "Snipers":
                                if self.zoom_index < len(self.player.equipped_weapon.zoom_dis):
                                    self.zoom = self.player.equipped_weapon.zoom_dis[self.zoom_index]
                                self.zoom_index += 1
                                if self.zoom_index > len(self.player.equipped_weapon.zoom_dis):
                                    self.zoom = 1
                                    self.zoom_index = 0
                                self.change_dims()
                                
                    if event.key == self.key_inputs["jump"]:
                        if self.player.jump_count < 2 and self.player.on_wall == False:
                            self.player.vel_y = -self.player.jump
                            self.player.jump_count += 1
                        if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                            self.player.wall_jump_true = True
                            self.player.jump_count = 1
                    
                    if event.key == self.key_inputs["throwables"]:
                        print("Thrown")
                    
                    if event.key == K_F1:
                        self.show_fps = not self.show_fps
                    
                    if event.key == K_F11:
                        if self.game.fullscreen != True:
                            self.game.screen = pygame.display.set_mode((int(self.game.win_dims[0]*self.game.scale),int(self.game.win_dims[1]*self.game.scale)),pygame.FULLSCREEN)
                            self.game.fullscreen = True
                        else:
                            self.game.screen = pygame.display.set_mode((int(self.game.win_dims[0]*self.game.scale),int(self.game.win_dims[1]*self.game.scale)),pygame.RESIZABLE)
                            self.game.fullscreen = False

                    #Gun changing                      
                    if event.key == K_1:
                        self.player.change_weapon(0)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()
                        
                    if event.key == K_2:
                       self.player.change_weapon(1)
                       if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                           self.zoom = 1
                           self.zoom_index = 0
                           self.change_dims()
                           
                    if event.key == K_3:
                        self.player.change_weapon(2)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()
                            
                    if event.key == K_4:
                        self.player.change_weapon(3)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()
            
            if event.type == KEYUP:
                if self.show_console == False:
                    if event.key == K_a:
                        self.player.left = False
                    if event.key == K_d:
                        self.player.right = False
                    if event.key == K_LALT:
                        self.alt_key = False
                    if event.key == K_RALT:
                        self.alt_key = False
            
            if event.type == JOYDEVICEADDED:
                self.reload_controllers()
            
            if event.type == JOYDEVICEREMOVED:
                self.reload_controllers()

            if event.type == MOUSEMOTION:
                self.controller_pos = list(self.relative_pos)
                self.moving_aim_axis = False

            if event.type == MOUSEBUTTONDOWN:
                if self.show_console == False:
                    if event.button == 4:
                        self.player.change_weapon(0,decrease=True)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()
                    if event.button == 5:
                        self.player.change_weapon(0,increase=True)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    if self.player.equipped_weapon != None:
                        if self.player.equipped_weapon.weapon_group == 'Melee':
                            self.player.melee_attacked = False
                        
        self.game.screen.blit(pygame.transform.scale(self.game.display, (self.game.screen.get_width(),self.game.screen.get_height())), (0,0))
        pygame.display.update()

    # Multiplayer setup,managing and gameplay goes here
    # Setup
    def setup_mult(self,host,port,ip,game_info=[]):
        if self.game.protocol == "UDP":
            if host == True:
                self.client = scripts.UDPClient(port,get_wifi_ip())
                if self.client.connect() == "Connection_ERROR":
                    return "Connection ERROR!"
                else:
                    self.hosting = True
                    data = {"loc":[0,0],"name":self.player.name, "health":self.player.health,"shield":self.player.shield,"equipped_weapon":{},"angle":0, "is_host": True, "addr":"0", "no_send_time":0}
                    msg = f"CREATE_PLAYER;{json.dumps(data)};{json.dumps(game_info)}"
                    self.client.send(msg,json_encode=True)
                    pos = self.client.recv(json_encode=True,val=8)
                    self.client.set_id(pos[1])
                    self.player.set_pos(int(pos[0][0])*self.game.TILESIZE,int(pos[0][1])*self.game.TILESIZE)
                    self.client.send(f"get:{self.client.id}")
                    self.players,_,items,self.entites,map_type,_ = self.client.recv(json_encode=True,val=15)

                    self.console = scripts.Console(self.game,(self.game.display.get_width()-4,25),client=self.client)

                    if map_type[0] == "Custom":
                        self.client.send(f"send_map:{map_type[1]}")

                        size = int(self.client.recv())
                        self.level = self.client.recv(json_encode=True,val=int(size+(size*0.5)))
                    else:
                        self.reset_multiplayer_level(map_type[1],items)

            else:
                self.client = scripts.UDPClient(port,ip)
                if self.client.connect() == "Connection_ERROR":
                    self.game.state = "Menu"
                else:
                    self.hosting = False
                    data = {"loc":[0,0],"name":self.player.name, "health":self.player.health,"shield":self.player.shield,"equipped_weapon":{},"angle":0, "is_host": False, "addr":"0", "no_send_time":0}
                    msg = f"CREATE_PLAYER;{json.dumps(data)};{json.dumps(game_info)}"
                    self.client.send(msg,json_encode=True)
                    pos = self.client.recv(json_encode=True,val=8)
                    self.client.set_id(pos[1])
                    self.player.set_pos(int(pos[0][0]),int(pos[0][1]))
                    self.client.send(f"get:{self.client.id}")
                    self.players,_,items,entites,map_type,_ = self.client.recv(json_encode=True,val=15)
                    
                    if map_type[0] == "Custom":
                        self.client.send(f"send_map:{map_type[1]}")

                        size = int(self.client.recv())
                        self.level = self.client.recv(json_encode=True,val=int(size+(size*0.5)))
                    else:
                        self.reset_multiplayer_level(map_type[1],items)
        elif self.game.protocol == "TCP":
            if host == True:
                self.client = scripts.TCPClient(port,get_wifi_ip())
                if self.client.connect() == "Connection_ERROR":
                    return "Connection ERROR!"
                else:
                    self.hosting = True
                    data = {"loc":[0,0],"name":self.player.name, "health":self.player.health,"shield":self.player.shield,"equipped_weapon":{},"angle":0, "is_host": True, "addr":"0", "no_send_time":0}
                    msg = f"{json.dumps(data)};{json.dumps(game_info)}"
                    self.client.send(msg)
                    pos = self.client.recv(json_encode=True,val=8)
                    self.client.set_id(pos[1])
                    self.player.set_pos(int(pos[0][0])*self.game.TILESIZE,int(pos[0][1])*self.game.TILESIZE)
                    self.client.send(f"get")
                    self.players,_,items,self.entites,map_type,_ = self.client.recv(json_encode=True,val=15)

                    self.console = scripts.Console(self.game,(self.game.display.get_width()-4,25),client=self.client)

                    if map_type[0] == "Custom":
                        self.client.send(f"send_map:{map_type[1]}")

                        size = int(self.client.recv())
                        self.level = self.client.recv(json_encode=True,val=int(size+(size*0.5)))
                    else:
                        self.reset_multiplayer_level(map_type[1],items)

            else:
                self.client = scripts.TCPClient(port,ip)
                if self.client.connect() == "Connection_ERROR":
                    self.game.state = "Menu"
                else:
                    self.hosting = False
                    data = {"loc":[0,0],"name":self.player.name, "health":self.player.health,"shield":self.player.shield,"equipped_weapon":{},"angle":0, "is_host": False, "addr":"0", "no_send_time":0}
                    msg = f"{json.dumps(data)};{json.dumps(game_info)}"
                    self.client.send(msg)
                    pos = self.client.recv(json_encode=True,val=8)
                    self.client.set_id(pos[1])
                    self.player.set_pos(int(pos[0][0]),int(pos[0][1]))
                    self.client.send(f"get")
                    self.players,_,items,entites,map_type,_ = self.client.recv(json_encode=True,val=15)
                    
                    if map_type[0] == "Custom":
                        self.client.send(f"send_map:{map_type[1]}")

                        size = int(self.client.recv())
                        self.level = self.client.recv(json_encode=True,val=int(size+(size*0.5)))
                    else:
                        self.reset_multiplayer_level(map_type[1],items)
    
    #Managing
    def reset_multiplayer_level(self,level,items):
        self.items = []
        self.reload_controller()
        with open(f"data/maps/{level}.level", "rb") as file:
            data = pickle.load(file)
            file.close()
            self.level = data["data"]
            self.zone = data["zone"]
            del data
        
        for item_id in items:
            if item_id[0] in self.item_data["Guns"]:
                gun = scripts.Gun(self,item_id[0],self.weapon_data[item_id[0]],self.target_fps)
                item = scripts.Item(self,item_id[1][0],item_id[1][1],item_id[0],"Guns",self.target_fps,gun)
                item.id = item_id[4]
                item.update_pos = True
                self.items.append(item)
            if item_id[0] in self.item_data["Melee"]:
                melee = scripts.Melee_Weapon(self,item_id[0])
                item = scripts.Item(self,item_id[1][0],item_id[1][1],item_id[0],"Melee",self.target_fps,melee)
                item.id = item_id[4]
                item.update_pos = True
                self.items.append(item)
            if item_id[0] in self.item_data["Ammo"]:
                ref_obj = scripts.Ammo(self.game,item_id[0])
                item = scripts.Item(self,item_id[1][0],item_id[1][1],item_id[0],"Ammo",self.target_fps,ref_obj)
                item.id = item_id[4]
                item.update_pos = True
                self.items.append(item)
            if item_id[0] in self.item_data["Consumables"]:
                item = scripts.Consumable(self,item_id[1][0],item_id[1][1],item_id[0])
                item.id = item_id[4]
                item.update_pos = True
                self.items.append(item)

        self.player.health = self.players[str(self.client.id)]["health"]
        self.player.max_health = self.player.health
        self.current_level = level
    
    def render_game(self,scroll,active_chunks,dt):
        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.pickup_cooldown -= 1
                if item.pickup_cooldown < 0:
                    item.pickup_cooldown = 0
                item.render(self.game.display,scroll)

        for bullet in self.bullets:
            bullet.run(self.game.display,scroll,dt)
            if bullet.lifetime <= 0:
                msg = "bullet_life_ended:"+str(bullet.id)
                self.client.send(msg)

        for player_id in self.players:
            player_data = self.players[player_id]
            player = scripts.Player(self,int(player_data["loc"][0]),int(player_data["loc"][1]),16,16,player_data["health"],3,6,0.3)
            if player.health > 0:
                player.draw(self.game.display,scroll)

    def create_weapon(self,weapon_data):
        if weapon_data != {}:
            if weapon_data["type"] == "Gun":
                gun = scripts.Gun(self,weapon_data["name"],self.weapon_data[weapon_data["name"]],self.target_fps)
                gun.flip = weapon_data["is_flipped"]
                return gun
            if weapon_data["type"] == "Melee":
                melee = scripts.Melee_Weapon(self,weapon_data["name"])
                melee.is_flipped = weapon_data["is_flipped"]
                return melee
    
    def can_create_items(self,items):
        item_list = []
        item_r = []
        item_r_ids = []
        item_obj_r = []

        for item in self.items:
            item_list.append(item.id)

        for i in range(len(items)):
            item = items[i]
            if item[4] in item_list:
                item_r.append(item)
                item_r_ids.append(item[4])
        
        for item in self.items:
            if item.id not in item_r_ids:
                item_obj_r.append(item)

        for item in item_r:
            items.remove(item)
        
        for item in item_obj_r:
            self.items.remove(item)

    def create_items(self,items):
        for item_id in items:
            if item_id[0] in self.item_data["Guns"]:
                gun = scripts.Gun(self,item_id[0],self.weapon_data[item_id[0]],self.target_fps)
                if len(item_id[-1]) != 0:
                    gun.ammo = item_id[-1][0]
                    gun.ammo_l = item_id[-1][1]
                item = scripts.Item(self,item_id[1][0],item_id[1][1],item_id[0],"Guns",self.target_fps,gun)
                if item_id[3] == "dropped":
                    item.dropped = True
                item.movement[0] = item_id[2][0]
                item.movement[1] = item_id[2][1]
                item.id = item_id[4]
                item.update_pos = True
                self.items.append(item)
            if item_id[0] in self.item_data["Melee"]:
                melee = scripts.Melee_Weapon(self,item_id[0])
                if item_id[-1] != []:
                    pass
                item = scripts.Item(self,item_id[1][0],item_id[1][1],item_id[0],"Melee",self.target_fps,melee)
                if item_id[3] == "dropped":
                    item.dropped = True
                item.movement[0] = item_id[2][0]
                item.movement[1] = item_id[2][1]
                item.update_pos = True
                item.id = item_id[4]
                self.items.append(item)
            if item_id[0] in self.item_data["Ammo"]:
                ref_obj = scripts.Ammo(self.game,item_id[0])
                item = scripts.Item(self,item_id[1][0],item_id[1][1],item_id[0],"Ammo",self.target_fps,ref_obj)
                if item_id[3] == "dropped":
                    item.dropped = True
                item.movement[0] = item_id[2][0]
                item.movement[1] = item_id[2][1]
                item.update_pos = True
                item.id = item_id[4]
                self.items.append(item)
            if item_id[0] in self.item_data["Consumables"]:
                item = scripts.Consumable(self,int(item_id[1][0]),int(item_id[1][1]),item_id[0])
                if item_id[3] == "dropped":
                    item.dropped = True
                item.item_obj.movement[0] = item_id[2][0]
                item.item_obj.movement[1] = item_id[2][1]
                item.update_pos = True
                item.id = item_id[4]
                self.items.append(item)
    
    def can_create_bullets(self,bullets):
        bullet_list = []
        bullet_r = []
        bullet_r_ids = []
        bullet_obj_r = []

        for bullet in self.bullets:
            bullet_list.append(bullet.id)

        for i in range(len(bullets)):
            bullet = bullets[i]
            if bullet[-1] in bullet_list:
                bullet_r.append(bullet)
                bullet_r_ids.append(bullet[-1])
        
        for bullet in self.bullets:
            if bullet.id not in bullet_r_ids:
                bullet_obj_r.append(bullet)

        for bullet in bullet_r:
            bullets.remove(bullet)
        
        for bullet in bullet_obj_r:
            self.bullets.remove(bullet)

    def create_bullets(self,bullets):
        for bullet_data in bullets:
            if bullet_data[10] != None:
                img = self.game.img_m.load(bullet[10],(255,255,255))
            else:
                img = None
            bullet = scripts.Bullet(self, bullet_data[0],bullet_data[1],bullet_data[2],bullet_data[3],bullet_data[4],bullet_data[5],bullet_data[7],
                                    bullet_data[8],bullet_data[9],img,bullet_data[6])
            bullet.id = bullet_data[-1]
            self.bullets.append(bullet)
    
    def update_game(self,tiles,scroll,active_chunks,dt):
        player = scripts.Player(self,self.players[str(self.client.id)]["loc"][0], self.players[str(self.client.id)]["loc"][1],self.player.rect.width,self.player.rect.height,0,0,0,0)
        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.move(tiles, dt)
            if item.rect.colliderect(player.rect):
                if item.pickup_cooldown <= 0:
                    if isinstance(item, scripts.Item):
                        if item.item_group in ["Guns","Melee"]:
                            if self.player.no_space == False:
                                tooltip = scripts.Tooltip(player.rect.topright[0]+5,player.rect.y+1,1,1,"E to pickup",(235,235,235))
                                tooltip.draw(self.game.display,scroll)
                            if item.dropped == False:
                                if self.player.equipped_weapon != None:
                                    if item.ref_obj.name == self.player.equipped_weapon.name and item.item_group != "Melee":
                                        if self.player.add_weapon_item(item) == True:
                                            self.player.equip_weapon()
                                            self.client.send(f"remove_item:{item.id}")
                                if pygame.key.get_pressed()[self.key_inputs["equip"]] == True:
                                    if self.player.add_weapon_item(item) == True:
                                        self.player.equip_weapon()
                                        self.client.send(f"remove_item:{item.id}")
                                if pygame.key.get_pressed()[self.key_inputs["change"]] == True:
                                    if item.dropped != True:
                                        if self.player.swap_weapon(item) == True:
                                            self.player.equip_weapon()

                        if item.item_group == "Ammo":
                            self.player.add_ammo(item,item_remove_list,n)
                    if isinstance(item,scripts.Consumable):
                        if item.is_shield == False:
                            if self.player.health != self.player.max_health:
                                self.player.add_health(item.value)
                        else:
                            if self.player.shield != self.player.max_shield:
                                self.player.add_shield(item.value)
        
        player = scripts.Player(self,self.players[str(self.client.id)]["loc"][0], self.players[str(self.client.id)]["loc"][1],self.player.rect.width,self.player.rect.height,0,0,0,0) 
        player_names = []
        for player_id in self.players:
            if self.players[player_id]["name"] != self.players[str(self.client.id)]["name"]:
                player_names.append(self.players[player_id]["name"])
        for bullet in self.bullets:
            if bullet.rect.colliderect(player.rect):
                if self.players[str(bullet.owner)]["name"] in player_names:
                    self.player.damage(self.players[str(bullet.owner)]["name"],bullet.dmg)
                    msg = "bullet_collide:"+str(bullet.id)
                    self.client.send(msg)
            for tile in tiles:
                if tile.colliderect(bullet.rect):
                    msg = "bullet_collide:"+str(bullet.id)
                    self.client.send(msg)

        for player_id in self.players:
            player_data = self.players[player_id]
            player = scripts.Player(self,int(player_data["loc"][0]),int(player_data["loc"][1]),16,16,100,3,6,0.3)
            e_weapon = self.create_weapon(player_data["equipped_weapon"])
            if e_weapon != None:
                if isinstance(e_weapon,scripts.Gun):
                    e_weapon.update(self.game.display,scroll,[player.get_center()[0]+e_weapon.render_offset[0], player.get_center()[1]+e_weapon.render_offset[1]],math.degrees(-player_data["angle"]), dt)
                if isinstance(e_weapon,scripts.Melee_Weapon):
                    e_weapon.update(self.game.display,scroll,[player.get_center()[0], player.get_center()[1]],math.degrees(-player_data["angle"]))

    # Gameplay
    def multiplayer_game(self):
        self.game.display.fill((90,90,90))
        self.game.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        size_dif = float(self.game.screen.get_width()/self.game.display.get_width())
        self.relative_pos = [int(pos[0]/size_dif), int(pos[1]/size_dif)]

        #Delta Time calculation
        now = time.time()
        self.dt = now - self.time_passed
        self.time_passed = now

        player = scripts.Player(self,self.players[str(self.client.id)]["loc"][0], self.players[str(self.client.id)]["loc"][1],self.player.rect.width,self.player.rect.height,self.players[str(self.client.id)]["health"],0,0,0)

        self.camera.update(player,self.game.display,10)
        scroll = [0,0]
        scroll[0] = self.camera.scroll[0]
        scroll[1] = self.camera.scroll[1]
        controller_input = self.handle_controller_input()
        
        tiles = []
        active_chunks = []
        angle = scripts.find_angle_from_points(self.relative_pos,self.player.get_center(),scroll,[0,0],False)

        if self.moving_aim_axis == True:
            angle = scripts.find_angle_from_points(self.controller_pos,self.player.get_center(),scroll,[0,0],False)

        chunk_num = self.game.CHUNKSIZE*self.game.TILESIZE
        chunk_seen_width = round(self.game.display.get_width()/chunk_num)+2
        chunk_seen_height = round(self.game.display.get_height()/chunk_num)+2
        
        for y in range(chunk_seen_height):
            for x in range(chunk_seen_width):
                chunk_x = x-1 + round(scroll[0]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_y = y-1 + round(scroll[1]/(self.game.CHUNKSIZE*self.game.TILESIZE))
                chunk_id = f"{chunk_x}/{chunk_y}"
                active_chunks.append(chunk_id)

        for chunk_id in active_chunks:
            for layer in self.level:
                if layer not in ['tiles','spawnpoints','items']:
                    if chunk_id in self.level[layer]:
                        for tile in self.level[layer][chunk_id]:
                            if tile[0] in self.tiles[self.zone]:
                                if tile[0] not in ['1','2','3']:
                                    self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                            if tile[0] in ['1','2','3']:
                                self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-3-scroll[1]))
                            if tile[0] in self.tile_data["collidable"]:
                                tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))

        self.render_game(scroll,active_chunks,self.dt)

        for chunk_id in active_chunks:
            if chunk_id in self.level["tiles"]:
                for tile in self.level["tiles"][chunk_id]:
                    if tile[0] in self.tiles[self.zone]:
                        if tile[0] not in ['1','2','3']:
                            self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-scroll[1]))
                    if tile[0] in ['1','2','3']:
                        self.game.display.blit(self.tiles[self.zone][tile[0]], (tile[1][0]*self.game.TILESIZE-scroll[0], tile[1][1]*self.game.TILESIZE-3-scroll[1]))
                    if tile[0] in self.tile_data["collidable"]:
                        tiles.append(pygame.Rect(tile[1][0]*self.game.TILESIZE, tile[1][1]*self.game.TILESIZE,self.game.TILESIZE,self.game.TILESIZE))
        
        self.player.movement(tiles, self.dt)
        self.update_game(tiles,scroll,active_chunks, self.dt)
        self.player.update()

        if self.player.equipped_weapon != None:
            x = self.relative_pos[0]+scroll[0]
            if self.player.equipped_weapon.weapon_group != "Melee":
                if x < self.player.get_center()[0]:
                    self.player.equipped_weapon.flip = True
                    self.player.flip = True
                else:
                    self.player.equipped_weapon.flip = False
                    self.player.flip = False
                
                bullets = []
                bullet_data = []
                self.player.equipped_weapon.update(self.game.display,scroll,self.player.get_center(),angle, self.dt,render=False)
                if pygame.mouse.get_pressed()[0] == True: #Shoot the bullet
                    self.player.equipped_weapon.shoot(bullets,self.client.id,player.get_center(),self.players[str(self.client.id)]["angle"], self.dt)

                    if len(bullets) != 0:
                        if self.player.equipped_weapon.weapon_group != "Shotguns":
                            bullet = bullets[0]
                            bullet_data = [bullet.x,bullet.y,bullet.speed,bullet.angle,bullet.color,bullet.dmg,bullet.grav,bullet.owner,bullet.mult,bullet.lifetime,self.player.equipped_weapon.gun_info["bullet_image"], bullet.id]
                            del bullet
                        else:
                            for bullet in bullets:
                                bullet_data = [bullet.x,bullet.y,bullet.speed,bullet.angle,bullet.color,bullet.dmg,bullet.grav,bullet.owner,bullet.mult,bullet.lifetime,self.player.equipped_weapon.gun_info["bullet_image"], bullet.id]
                                msg = "bullet;"+json.dumps(bullet_data)
                                self.client.send(msg)

                if bullet_data != [] and self.player.equipped_weapon.weapon_group != "Shotguns":
                    self.client.send("bullet;"+json.dumps(bullet_data))

        if self.show_console == True:
            self.console.render()
        

        self.game.display.blit(pygame.transform.scale(self.game.health_bar_img,(round((self.game.health_bar_img.get_width()*2)*self.zoom),
                                                                                round((self.game.health_bar_img.get_height()*2)*self.zoom))),(2,2))
        health_calc = ((player.health*168)/self.player.max_health)
        pygame.draw.rect(self.game.display,(0,255,0),(4,4,round(health_calc*self.zoom),round(16*self.zoom)))

        self.fonts["font_1"][0].render(self.game.display,f"{self.player.shield}",(self.game.health_bar_img.get_width()*2)+6,2,(127,127,127))

        #Show ammo and gun name
        if self.player.equipped_weapon != None:
            color = (255,255,255)
            if self.player.equipped_weapon.weapon_group != "Melee":
                ammo_text = f"{self.player.equipped_weapon.ammo}/{self.player.equipped_weapon.ammo_l}"
            else:
                ammo_text = "\x00/\x00"
            if self.player.equipped_weapon.weapon_group != "Melee":
                if self.player.equipped_weapon.ammo <= 0 and self.player.equipped_weapon.ammo_l <= 0:
                    color = (255,0,0)
                
            self.fonts["font_1"][0].render(self.game.display,ammo_text,2,(self.game.health_bar_img.get_height()*2)+7,color)


        #Render the inventory of the player
        inventory_data = self.player.inventory.get_all_items()
        self.position = 10
        for i,weapon_id in enumerate(inventory_data):
            weapon = inventory_data[weapon_id]
            if len(weapon) != 0:
                weapon = weapon[0].ref_obj
                if weapon != self.player.equipped_weapon:
                    surf = pygame.mask.from_surface(weapon.img)
                    img = surf.to_surface(setcolor=(240,240,240))
                    img = pygame.transform.scale(img,(img.get_width(),img.get_height()))
                    img.set_colorkey((0,0,0))
                    if weapon.weapon_group == "Melee":
                        img = scripts.get_image(img,int(img.get_width()/2),0,int(img.get_width()/2),img.get_height(),1)
                    self.game.display.blit(img, (self.game.display.get_width()-(img.get_width()+self.position), 10))
                    pygame.draw.line(self.game.display,(240,240,240),(self.game.display.get_width()-(img.get_width()+self.position),1), ((self.game.display.get_width()-(img.get_width()+self.position))+(img.get_width()-2),1),2)
                    self.position += img.get_width()+20
                else:
                    surf = pygame.mask.from_surface(weapon.img)
                    img = surf.to_surface(setcolor=(255,255,255))
                    img = pygame.transform.scale(img,(round(img.get_width()*1.5),round(img.get_height()*1.5)))
                    img.set_colorkey((0,0,0))
                    if weapon.weapon_group == "Melee":
                        img = scripts.get_image(img,int(img.get_width()/2),0,int(img.get_width()/2),img.get_height(),1)
                    self.game.display.blit(img, (self.game.display.get_width()-(img.get_width()+self.position), 10))
                    pygame.draw.line(self.game.display,(255,255,255),(self.game.display.get_width()-(img.get_width()+self.position+3),1), ((self.game.display.get_width()-(img.get_width()+self.position))+(img.get_width()-3),1),2)
                    self.position += img.get_width()+20
        
        if self.player.weapon_count >= 4:
            self.player.no_space = True

        if self.moving_aim_axis == True:
            scripts.blit_center(self.game.display,self.game.controller_cursor,self.controller_pos)
        else:
            scripts.blit_center(self.game.display,self.game.controller_cursor,self.relative_pos)

        for event in pygame.event.get():
            self.event = event
            if self.show_console == True:
                self.console.get_event(event)
                
            if event.type == pygame.QUIT:
                self.client.send(f"DISCONNECT:{self.client.id}")
                if self.hosting == True:
                    self.client.send("CLOSE_SERVER")
                self.client.disconnect()
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.show_console = False
                    
                if self.show_console == False:
                    if self.player.alive == True:
                        if event.key == self.key_inputs["left"]:
                            self.player.left = True
                        if event.key == self.key_inputs["right"]:
                            self.player.right = True
                        if event.key == self.key_inputs["jump"]:
                            if self.player.jump_count < 2 and self.player.on_wall == False:
                                self.player.vel_y = -self.player.jump*self.dt*self.target_fps
                                self.player.jump_count += 1
                            if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                                self.player.wall_jump_true = True
                                self.player.jump_count = 1
                        if event.key == self.key_inputs["drop"]:
                            movement = [0,0]
                            if self.player.flip == True:
                                movement = [-6,-2]
                            else:
                                movement = [4,-2]
                            result = self.player.drop_weapon(movement)
                            if result == True:
                                item = self.items.pop(-1)
                                if isinstance(item.ref_obj, scripts.Gun):
                                    ref_obj = item.ref_obj
                                    weapon_data = [ref_obj.ammo,ref_obj.ammo_l]
                                else:
                                    weapon_data = []
                                item_data = [item.item_name,[int(item.rect.x),int(item.rect.y)], [item.movement[0],item.movement[1]], "dropped", item.id, weapon_data] # Items have a name,pos,movement
                                self.client.send('add_item;'+json.dumps(item_data))
                        if event.key == self.key_inputs["reload"]:
                            if self.player.equipped_weapon != None:
                                if self.player.equipped_weapon.reload_gun == False:
                                    self.player.equipped_weapon.reload_gun = True
                        if event.key == self.key_inputs["sniper_zoom"]:
                            if self.player.equipped_weapon != None:
                                if self.player.equipped_weapon.weapon_group == "Snipers":
                                    if self.zoom_index < len(self.player.equipped_weapon.zoom_dis):
                                        self.zoom = self.player.equipped_weapon.zoom_dis[self.zoom_index]
                                    self.zoom_index += 1
                                    if self.zoom_index > len(self.player.equipped_weapon.zoom_dis):
                                        self.zoom = 1
                                        self.zoom_index = 0
                                    self.change_dims()
                        
                        #Gun changing                      
                        if event.key == K_1:
                            self.player.change_weapon(0)
                            if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                                self.zoom = 1
                                self.zoom_index = 0
                                self.change_dims()
                            
                        if event.key == K_2:
                            self.player.change_weapon(1)
                            if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                                self.zoom = 1
                                self.zoom_index = 0
                                self.change_dims()
                            
                        if event.key == K_3:
                            self.player.change_weapon(2)
                            if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                                self.zoom = 1
                                self.zoom_index = 0
                                self.change_dims()
                                
                        if event.key == K_4:
                            self.player.change_weapon(3)
                            if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                                self.zoom = 1
                                self.zoom_index = 0
                                self.change_dims()

                    if event.key == K_LALT:
                        self.alt_key = True
                    if event.key == K_RALT:
                        self.alt_key = True
                    if event.key == K_c:
                        if self.alt_key == True:
                            self.show_console = True
                    
                    if event.key == K_F11:
                        if self.game.fullscreen != True:
                            self.game.screen = pygame.display.set_mode((int(self.game.win_dims[0]*self.game.scale),int(self.game.win_dims[1]*self.game.scale)),pygame.FULLSCREEN)
                            self.game.fullscreen = True
                        else:
                            self.game.screen = pygame.display.set_mode((int(self.game.win_dims[0]*self.game.scale),int(self.game.win_dims[1]*self.game.scale)),pygame.RESIZABLE)
                            self.game.fullscreen = False
                        
            if event.type == KEYUP:
                if self.show_console == False:
                    if event.key == K_a:
                        self.player.left = False
                    if event.key == K_d:
                        self.player.right = False
                    if event.key == K_LALT:
                        self.alt_key = False
                    if event.key == K_RALT:
                        self.alt_key = False
            
            if event.type == JOYDEVICEADDED:
                self.reload_controllers()
            
            if event.type == JOYDEVICEREMOVED:
                self.reload_controllers()
            
            if event.type == MOUSEMOTION:
                self.controller_pos = list(self.relative_pos)
                self.moving_aim_axis = False

            if event.type == MOUSEBUTTONDOWN:
                if self.show_console == False:
                    if event.button == 5:
                        self.player.change_weapon(0,decrease=True)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()
                    if event.button == 4:
                        self.player.change_weapon(0,increase=True)
                        if self.zoom > 1 and self.player.equipped_weapon.weapon_group != "Snipers":
                            self.zoom = 1
                            self.zoom_index = 0
                            self.change_dims()

        if self.client.connected == True:
            if isinstance(self.client, scripts.UDPClient):
                if self.player.alive == False:
                    movements = [[3,-2],[-4,-2],[-4,-3.7],[3,-3.7]]
                    w_count = self.player.weapon_count
                    self.player.drop_all_weapons(movements)
                    for i in range(w_count):
                        item = self.items.pop(-1)
                        if isinstance(item.ref_obj, scripts.Gun):
                            ref_obj = item.ref_obj
                            weapon_data = [ref_obj.ammo,ref_obj.ammo_l]
                        else:
                            weapon_data = []
                        item_data = [item.item_name,[int(item.rect.x),int(item.rect.y)], [item.movement[0],item.movement[1]], "dropped", item.id, []] # Items have a name,pos,movement
                        self.client.send("add_item;"+json.dumps(item_data))
                if self.player.equipped_weapon != None:
                    if self.player.equipped_weapon.weapon_group != "Melee":
                        equipped_weapon = {"type": "Gun", "name":self.player.equipped_weapon.name,"is_flipped":self.player.equipped_weapon.flip}
                    else:
                        equipped_weapon = {"type":"Melee", "name":self.player.equipped_weapon.name,"is_flipped":self.player.equipped_weapon.flip}
                else:
                    equipped_weapon = {}
                command = f"update;{self.player.rect.x};{self.player.rect.y};{angle};{json.dumps(equipped_weapon)};{self.player.health};{self.player.shield};{self.client.id}" # update has position,angle,equipped_weapon and the client id
                self.client.send(command)
                data = self.client.recv(json_encode=True,val=20)
                if data not in ["No data","Server is closed!"]:
                    self.players = data[0]
                    items = data[1]
                    bullets = data[2]
                    self.can_create_items(items)
                    self.can_create_bullets(bullets)
                    self.create_items(items)
                    self.create_bullets(bullets)
                else:
                    if data == "Server is closed!":
                        self.game.create_menu_manager()
                        self.game.state = "Menu"
            if isinstance(self.client,scripts.TCPClient):
                if self.player.alive == False:
                    movements = [[3,-2],[-4,-2],[-4,-3.7],[3,-3.7]]
                    w_count = self.player.weapon_count
                    self.player.drop_all_weapons(movements)
                    for i in range(w_count):
                        item = self.items.pop(-1)
                        if isinstance(item.ref_obj, scripts.Gun):
                            ref_obj = item.ref_obj
                            weapon_data = [ref_obj.ammo,ref_obj.ammo_l]
                        else:
                            weapon_data = []
                        item_data = [item.item_name,[int(item.rect.x),int(item.rect.y)], [item.movement[0],item.movement[1]], "dropped", item.id, weapon_data] # Items have a name,pos,movement
                        self.client.send("add_item;"+json.dumps(item_data))
                if self.player.equipped_weapon != None:
                    if self.player.equipped_weapon.weapon_group != "Melee":
                        equipped_weapon = {"type": "Gun", "name":self.player.equipped_weapon.name,"is_flipped":self.player.equipped_weapon.flip}
                    else:
                        equipped_weapon = {"type":"Melee", "name":self.player.equipped_weapon.name,"is_flipped":self.player.equipped_weapon.flip}
                else:
                    equipped_weapon = {}
                command = f"update;{self.player.rect.x};{self.player.rect.y};{angle};{json.dumps(equipped_weapon)};{self.player.health};{self.player.shield}" # update has position,angle,equipped_weapon and the client id
                self.client.send(command)
                data = self.client.recv(json_encode=True,val=20)
                if data not in ["No data","Server is closed!"]:
                    self.players = data[0]
                    items = data[1]
                    bullets = data[2]
                    self.can_create_items(items)
                    self.can_create_bullets(bullets)
                    self.create_items(items)
                    self.create_bullets(bullets)
                else:
                    if data == "Server is closed!":
                        self.game.create_menu_manager()
                        self.game.state = "Menu"
        else:
            self.game.create_menu_manager()
            self.game.state = "Menu"

            
        self.game.screen.blit(pygame.transform.scale(self.game.display, (self.game.screen.get_width(),self.game.screen.get_height())), (0,0))
        pygame.display.update()

    def run(self):
        if self.play_type == "Singleplayer":
            self.singleplayer_game()
        if self.play_type == "Multiplayer":
            self.multiplayer_game()
