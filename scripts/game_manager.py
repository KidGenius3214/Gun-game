#Game manager
#It's basically where whole gameplay stuff is 
import pygame
from pygame.locals import *
pygame.init()
import scripts
import sys, math, random,json,time
import json,pickle

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
    def __init__(self,game,play_type):
        self.game = game
        self.play_type = play_type
        self.player = scripts.Player(self,0, 0, 16, 16, 100, 3, 6, 0.3)
        self.event = None
        self.console = scripts.Console(self.game,(self.game.display.get_width()-4,25))
        self.current_level = 'Debug_level_0'
        self.bullets = []
        self.particles = []
        self.items = []
        self.entities = []
        self.entities.append(scripts.Bad_Guy(self,5*self.game.TILESIZE,0,self.game.TILESIZE,self.game.TILESIZE,100,0.1,6,0.3))
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
                gun = scripts.Gun(self,item_id[0],self.weapon_data[item_id[0]],self.game.FPS)
                item = scripts.Item(self,item_id[1][0]*self.game.TILESIZE,item_id[1][1]*self.game.TILESIZE,item_id[0],"Guns",self.game.FPS,gun)
                self.items.append(item)
            if item_id[0] in self.item_data["Ammo"]:
                ref_obj = scripts.Ammo(self.game,item_id[0])
                item = scripts.Item(self,item_id[1][0]*self.game.TILESIZE,item_id[1][1]*self.game.TILESIZE,item_id[0],"Ammo",self.game.FPS,ref_obj)
                self.items.append(item)
            if item_id[0] in self.item_data["Consumables"]:
                item = scripts.Consumable(self,int(item_id[1][0]*self.game.TILESIZE),int(item_id[1][1]*self.game.TILESIZE),item_id[0])
                self.items.append(item)
        
        self.sword = scripts.Melee_Weapon(self,"Sword")
        item = scripts.Item(self,500,-600,"Sword","Melee",self.game.FPS,self.sword)
        self.items.append(item)
            
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

    def setup_mult(self,host,port,ip,game_info=[]):
        if host == True:
            self.client = scripts.Client(self.player,port,get_wifi_ip())
            if self.client.connect() == "Connection_ERROR":
                return "Connection ERROR!"
            else:
                self.hosting = True
                self.client.send(str(self.hosting))
                send_data = self.client.recv()
                if send_data == "Send game info":
                    time.sleep(0.01) # delay sending more of the data
                    self.client.send(game_info,json_encode=True)
                    
                data = {"loc":[0,0],"name":self.player_name, "health":0,"shield":0,"equipped_gun":{},"inventory":{},"angle":0}
                self.client.send(data,json_encode=True)
                pos = self.client.recv(json_encode=True,val=8)
                self.client.set_id(pos[1])
                self.player.set_pos(int(pos[0][0])*self.game.TILESIZE,int(pos[0][1])*self.game.TILESIZE)
                self.client.send("get")
                self.players,_,items,self.entites,map_type,_ = self.client.recv(json_encode=True,val=15)

                self.console = scripts.Console(self.game,(self.game.display.get_width()-4,25),client=self.client)

                time.sleep(0.01)
                if map_type[0] == "Custom":
                    self.client.send(f"send_map:{map_type[1]}")

                    size = int(self.client.recv())
                    self.level = self.client.recv(json_encode=True,val=int(size+(size*0.5)))
                else:
                    self.reset_mult_level(map_type[1],items)

        else:
            self.client = scripts.Client(self.player,port,ip)
            if self.client.connect() == "Can't connect":
                return "Connection ERROR!"
            else:
                self.hosting = False
                self.client.send("False")
                time.sleep(0.2) # delay sending more of the data
                data = {"loc":[0,0],"name":self.player_name, "health":0,"shield":0,"equipped_gun":None,"inventory":None,"angle":0}
                self.client.send(data,json_encode=True)
                pos = self.client.recv(json_encode=True,val=8)
                self.client.set_id(pos[1])
                self.player.set_pos(int(pos[0][0]),int(pos[0][1]))
                self.client.send("get")
                self.players,_,items,entites,map_type,_ = self.client.recv(json_encode=True,val=15)
                time.sleep(0.01)
                
                if map_type[0] == "Custom":
                    self.client.send(f"send_map:{map_type[1]}")

                    size = int(self.client.recv())
                    self.level = self.client.recv(json_encode=True,val=int(size+(size*0.5)))
                else:
                    self.reset_mult_level(map_type[1],items)

    def normal_play(self):
        self.game.display.fill((90,90,90))
        self.game.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        size_dif = float(self.game.win_dims[0]/self.game.display.get_width())
        self.relative_pos = [int(pos[0]/size_dif), int(pos[1]/size_dif)]

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
                if layer not in ['tiles','spawnpoints','guns']:
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
            bullet.run(self.game.display,scroll)
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
                self.player.equipped_weapon.update(self.game.display,scroll,[self.player.get_center()[0],self.player.get_center()[1]],math.degrees(-angle))
                if pygame.mouse.get_pressed()[0] == True:
                    self.player.equipped_weapon.shoot(self.bullets,"player",[self.player.get_center()[0]+self.player.equipped_weapon.bullet_offset[0],self.player.get_center()[1]+self.player.equipped_weapon.bullet_offset[1]],angle)
                if controller_input["active"] == True:
                    x = self.controller_pos[0]+scroll[0]
                    if x < self.player.get_center()[0]:
                        self.player.equipped_weapon.flip = True
                        self.player.flip = True
                    else:
                        self.player.equipped_weapon.flip = False
                        self.player.flip = False
                    if controller_input["buttons"]["shoot"] == True:
                        self.player.equipped_weapon.shoot(self.bullets,"player",[self.player.get_center()[0]+self.player.equipped_weapon.render_offset[0],self.player.get_center()[1]+self.player.equipped_weapon.render_offset[1]],angle)
            if self.player.equipped_weapon.weapon_group == "Melee":
                if x < self.player.get_center()[0]:
                    self.player.equipped_weapon.flip = True
                    self.player.flip = True
                else:
                    self.player.equipped_weapon.flip = False
                    self.player.flip = False
                self.player.equipped_weapon.render(self.game.display,scroll,[self.player.get_center()[0],self.player.get_center()[1]],math.degrees(-angle))
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
            particle.render(self.game.display,scroll)
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
                item.move(tiles)
            if item.rect.colliderect(self.player.rect):
                if item.pickup_cooldown <= 0:
                    if isinstance(item, scripts.Item):
                        if item.item_group in ["Guns","Melee"]:
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

        self.player.movement(tiles)

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
                        self.player.drop_weapon()
                            
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
                        
        self.game.screen.blit(pygame.transform.scale(self.game.display, self.game.win_dims), (0,0))
        pygame.display.update()

    def run(self):
        if self.play_type == "Singleplayer":
            self.normal_play()
