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
    def __init__(self,game,play_type,p_name="Player"):
        self.game = game
        self.play_type = play_type
        self.player = scripts.Player(self,0, 0, 16, 16, 100, 3, 6, 0.3)
        self.player_name = p_name
        self.event = None
        self.clock = pygame.time.Clock()
        self.console = scripts.Console(self.game,(self.game.display.get_width()-4,25))
        self.current_level = 'Debug_level_0'
        self.bullets = []
        self.particles = []
        self.items = []
        self.entities = []
        self.enemy_ids = ["Bad Guy"]
        self.level = None
        self.tiles = self.game.tiles
        self.scroll = [0,0]
        self.alt_key = False
        self.shift = False
        self.ctrl = False
        self.show_console = False
        self.zoom = 1
        self.zoom_index = 0
        self.tile_data = self.game.tile_data
        self.gun_data = self.game.gun_data
        self.consumable_data = self.game.consumable_data
        
        #controller stuff
        self.controller_input = self.game.json_h.files["controller_input"]
        self.right_pressed = False
        self.left_pressed = False
        self.jumped = False
        self.ip = ""
        self.port = 1
        self.font1 = scripts.Text("data/images/font.png",1,3)
        self.font2 = scripts.Text("data/images/font.png",1,2)
        self.ammo_data = self.game.ammo_data
    
        #Multiplayer stuff
        self.hosting = False
        self.host_server = None
        self.players = {}
        self.client = None
        self.test_gun = None
        
        self.camera = scripts.Camera()
        self.joystick = None
        self.controller_pos = [0,0]
        self.moving_aim_axis = False
        self.c_sensitivity = self.controller_input["sensitivity"]
        self.reload_controller()

        self.reset_level(self.current_level)

    def reload_controller(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        joy_count = pygame.joystick.get_count()
        if joy_count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

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
        for gun_pos in self.level["guns"]:
            gun = scripts.Gun(self,gun_pos[0],self.gun_data[gun_pos[0]],self.game.FPS)
            item = scripts.Item(self,gun_pos[1][0]*self.game.TILESIZE,gun_pos[1][1]*self.game.TILESIZE,gun_pos[0],"Guns",self.game.FPS,gun)
            self.items.append(item)

    def reset_mult_level(self,level,items):
        self.reload_controller()
        self.items = []

        for i,item_info in enumerate(items):
            if item_info[1] == "Guns":
                gun = scripts.Gun(self,item_info[0][0],self.gun_data[item_info[0][0]],self.game.FPS)
                item = scripts.Item(self,item_info[0][1][0]*self.game.TILESIZE,item_info[0][1][1]*self.game.TILESIZE,item_info[0][0],"Guns",self.game.FPS,gun)
                item.id = i
                self.items.append(item)

        with open(f"data/maps/{level}.level","rb") as file:
            data = pickle.load(file)
            file.close()
            self.level = data["data"]
            self.zone = data["zone"]
            del data

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
        self.clock.tick(self.game.FPS)
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

        item_remove_list = []
        n = 0
        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.render(self.game.display,scroll)
            if item.rect.colliderect(self.player.rect):
                if isinstance(item, scripts.Item):
                    if item.item_group in ["Guns"]:
                        if self.player.add_weapon_item(item) == True:
                            item_remove_list.append(n)
                            if self.player.weapon_count == 0:
                                self.player.weapon_index = 0
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
                    enemy.gun.update(self.game.display,scroll,enemy.get_center(),math.degrees(-enemy.angle_to_target))
                    enemy.gun.shoot(self.bullets,"Bad Guy",enemy.get_center(),enemy.angle_to_target)
                else:
                    enemy_remove_list.append(n)
                enemy.update()
            n += 1
        enemy_remove_list.sort(reverse=True)
        for enemy in enemy_remove_list:
            self.entities.pop(enemy)

        self.player.draw(self.game.display, scroll)

        if self.player.equipped_weapon != None:
            x = self.relative_pos[0]+scroll[0]
            if x < self.player.get_center()[0]:
                self.player.equipped_weapon.flip = True
            else:
                self.player.equipped_weapon.flip = False
            self.player.equipped_weapon.update(self.game.display,scroll,[self.player.get_center()[0],self.player.get_center()[1]],math.degrees(-angle))
            if pygame.mouse.get_pressed()[0] == True:
                self.player.equipped_weapon.shoot(self.bullets,"player",[self.player.get_center()[0],self.player.get_center()[1]],angle)
            if controller_input["active"] == True:
                if controller_input["buttons"]["shoot"] == True:
                    self.player.equipped_weapon.shoot(self.bullets,"player",[self.player.get_center()[0],self.player.get_center()[1]],angle)

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

        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.move(tiles)

        self.player.movement(tiles)

        if self.show_console == True:
            self.console.render()

        self.player.update()

        self.game.display.blit(pygame.transform.scale(self.game.health_bar_img,(round((self.game.health_bar_img.get_width()*2)*self.zoom),
                                                                                round((self.game.health_bar_img.get_height()*2)*self.zoom))),(2,2))
        health_calc = ((self.player.health*168)/self.player.max_health)
        pygame.draw.rect(self.game.display,(0,255,0),(3+round(self.zoom),3+round(self.zoom),round(health_calc*self.zoom),round(16*self.zoom)))

        self.font1.render(self.game.display,f"{self.player.shield}",(self.game.health_bar_img.get_width()*2)+6,2,(127,127,127))

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
            pygame.mouse.set_visible(False)
            blit_center(self.game.display,self.game.controller_cursor,self.controller_pos)

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
                    if event.key == K_a:
                        self.player.left = True
                    if event.key == K_d:
                        self.player.right = True
                    if event.key == K_r:
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
                    if event.key == K_z:
                        if self.player.equipped_weapon != None:
                            if self.player.equipped_weapon.gun_group == "Snipers":
                                if self.zoom_index < len(self.player.equipped_weapon.zoom_dis):
                                    self.zoom = self.player.equipped_weapon.zoom_dis[self.zoom_index]
                                self.zoom_index += 1
                                if self.zoom_index > len(self.player.equipped_weapon.zoom_dis):
                                    self.zoom = 1
                                    self.zoom_index = 0

                                self.console.change_size([round(self.game.display_dims[0]*self.zoom)-round(4*self.zoom),round(25*self.zoom)],2+round(self.zoom+0.1))

                                self.game.display = pygame.transform.scale(self.game.display,(round(self.game.display_dims[0]*self.zoom),round(self.game.display_dims[1]*self.zoom)))
                                self.camera.update(self.player,self.game.display,1)
                                
                    if event.key == K_SPACE:
                        if self.player.jump_count < 2 and self.player.on_wall == False:
                            self.player.vel_y = -self.player.jump
                            self.player.jump_count += 1
                        if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                            self.player.wall_jump_true = True
                            self.player.jump_count = 1
                            self.player.wall_jump_count += 1
                        
                    if event.key == K_0:
                        before_i = self.player.weapon_index
                        self.player.weapon_index = 0
                        if self.player.equip_weapon() == False:
                            self.player.weapon_index = before_i
                    if event.key == K_1:
                       before_i = self.player.weapon_index
                       self.player.weapon_index = 1
                       if self.player.equip_weapon() == False:
                           self.player.weapon_index = before_i
                    if event.key == K_2:
                        before_i = self.player.weapon_index
                        self.player.weapon_index = 2
                        if self.player.equip_weapon() == False:
                            self.player.weapon_index = before_i
                    if event.key == K_3:
                        before_i = self.player.weapon_index
                        self.player.weapon_index = 3
                        if self.player.equip_weapon() == False:
                            self.player.weapon_index = before_i

            if event.type == MOUSEMOTION:
                self.controller_pos = list(self.relative_pos)
                self.moving_aim_axis = False
                pygame.mouse.set_visible(True)
                        
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

    # Multiplayer game and data handling
    def render_mult_game(self,active_chunks,scroll):   
        item_remove_list = []
        n = 0
        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.render(self.game.display,scroll)
        
        for bullet in self.bullets:
            bullet_data = bullets[bullet]
            bullet_obj = scripts.Bullet(bullet_data["loc"][0],bullet_data["loc"][1],bullet_data["speed"],bullet_data["angle"],bullet_data["color"],bullet_data["dmg"],bullet_data["owner"],
                                        bullet_data["size"],bullet_data["lifetime"])
            bullet_obj.run(self.game.display,scroll)
            
            mod_data = {"loc":[bullet_obj.rect.x,bullet_obj.rect.y], "speed":bullet_data["speed"], "angle":bullet_data["angle"],"color":bullet_data["color"],"dmg":bullet_data["dmg"],
                        "owner":bullet_data["owner"],"size":bullet_data["size"],"lifetime":bullet_obj.lifetime}
            
            data = ["b_move",bullet,mod_data]
            self.client.send(data,json_encode=True)

        for p_id in self.players:
            p_pos = self.players[p_id]["loc"]
            player = Player(self,p_pos[0],p_pos[1],16,16,100,3,5,0.3)
            player.draw(self.game.display,scroll)

        

    def update_mult_game(self,tiles,active_chunks,scroll):
        for bullet in self.bullets:
            bullet_data = bullets[bullet]
            bullet_obj = scripts.Bullet(bullet_data["loc"][0],bullet_data["loc"][1],bullet_data["speed"],bullet_data["angle"],bullet_data["color"],bullet_data["dmg"],bullet_data["owner"],
                                        bullet_data["size"],bullet_data["lifetime"])
            
            for tile in tiles:
                if tile.colliderect(bullet_obj.rect):
                    command = f"b_collide:{bullet}"
                    self.client.send(command)

        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.movement(tiles)
                if item.rect.colliderect(self.player.rect):
                    if item.item_group in ["Guns"]:
                        if self.player.add_weapon_item(item) == True:
                            p_invent_data = self.create_invent_data(self.player)
                            command = ["item_collide",[self.client.id,item.id],p_invent_data]
                            self.client.send(command,json_encode=True)
                            data = self.client.recv(json_encode=True,val=2)
                            self.create_item_from_data(data)

                            
    def create_item_from_data(self,items):
        self.items = []
        for i,item_info in enumerate(items):
            if item_info[1] == "Guns":
                gun = scripts.Gun(self,item_info[0][0],self.gun_data[item_info[0][0]],self.game.FPS)
                item = scripts.Item(self,item_info[0][1][0]*self.game.TILESIZE,item_info[0][1][1]*self.game.TILESIZE,item_info[0][0],"Guns",self.game.FPS,gun)
                item.id = i
                self.items.append(item)

    def create_invent_data(self,player):
        inventory_data = player.inventory.get_all_items()
        sendable_data = []

        #Gun_data
        for i in range(4):
            item = inventory_data[i]
            if len(item) != 0:
                gun = item[0].ref_obj
                data = {}
                data["name"] = gun.gun
                data["ammo"] = gun.ammo
                data["ammo_l"] = gun.ammo_l
                sendable_data.append(data)

        return sendable_data

    def multi_play(self):
        self.game.display.fill((90,90,90))
        self.clock.tick(self.game.FPS)
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
        angle = find_angle_from_points(self.relative_pos,self.player.get_center(),scroll,[0,0],False)

        if self.moving_aim_axis == True:
            angle = find_angle_from_points(self.controller_pos,self.player.get_center(),scroll,[0,0],False)

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

##        item_remove_list = []
##        n = 0
##        for item in self.items:
##            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
##            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
##            chunk_str = f"{x}/{y}"
##            if chunk_str in active_chunks:
##                item.render(self.game.display,scroll)
##            if item.rect.colliderect(self.player.rect):
##                if item.item_group in ["Guns"]:
##                    if self.player.add_weapon_item(item) == True:
##                        item_remove_list.append(n)
##                if item.item_group == "Ammo":
##                    value = item.ref_obj.get_val()
##                    a_type = item.ref_obj.ammo_type
##                    if self.player.equipped_weapon.gun_group == self.ammo_data[a_type][1]: # Firstly check if the equipped weapon is of this ammo type
##                        self.player.equipped_weapon.add_ammo(value)
##                        item_remove_list.append(n)
##                    else: #If not,look through the inventory for this ammo type
##                        for i in range(4): # First 4 slots are where the weapons are in
##                            gun = self.player.inventory.inventory[i]
##                            if len(gun) != 0:
##                                if gun[0].ref_obj.gun_group == self.ammo_data[a_type][1]:
##                                    gun[0].ref_obj.add_ammo(value)
##                                    item_remove_list.append(n)
##                                    break                                    
##            n += 1
##
##        enemy_remove_list = []
##        n = 0
##        for enemy in self.entities:
##            if enemy.id == "Base_Enemy":
##                if enemy.alive == True:
##                    enemy.draw(self.game.display,scroll)
##                else:
##                    enemy_remove_list.append(n)
##                enemy.update()
##            if enemy.id == "Bad_Guy":
##                if enemy.alive == True:
##                    enemy.draw(self.game.display,scroll)
##                    enemy.gun.update(self.game.display,scroll,enemy.get_center(),math.degrees(-enemy.angle_to_target))
##                    enemy.gun.shoot(self.bullets,"Bad Guy",enemy.get_center(),enemy.angle_to_target)
##                else:
##                    enemy_remove_list.append(n)
##                enemy.update()
##            n += 1
##        enemy_remove_list.sort(reverse=True)
##        for enemy in enemy_remove_list:
##            self.entities.pop(enemy)

        self.render_mult_game(active_chunks,scroll)

##        if self.player.equipped_weapon != None:
##            self.player.equipped_weapon.update(self.game.display,scroll,[self.player.get_center()[0],self.player.get_center()[1]],math.degrees(-angle))
##            if pygame.mouse.get_pressed()[0] == True:
##                self.player.equipped_weapon.shoot(self.bullets,"player",[self.player.get_center()[0],self.player.get_center()[1]],angle)
##            if controller_input["active"] == True:
##                if controller_input["buttons"]["shoot"] == True:
##                    self.player.equipped_weapon.shoot(self.bullets,"player",[self.player.get_center()[0],self.player.get_center()[1]],angle)

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

##
##        p_remove_list = []
##        n = 0
##        for particle in self.particles:
##            particle.render(self.game.display,scroll)
##            if particle.size <= 0:
##                p_remove_list.append(n)
##            n += 1
##        p_remove_list.sort(reverse=True)
##        for particle in p_remove_list:
##            self.particles.pop(particle)
##
##        for enemy in self.entities:
##            if enemy.id == "Base_Enemy":
##                enemy.movement(tiles)
##            if enemy.id == "Bad_Guy":
##                enemy.handle_ai(tiles,self.player,scroll)
##

        self.player.movement(tiles)
        self.update_mult_game(tiles,active_chunks,scroll)

        if self.show_console == True:
            self.console.render()

        self.player.update()

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
            pygame.mouse.set_visible(False)
            blit_center(self.game.display,self.game.controller_cursor,self.controller_pos)

        command = f"move:{self.player.rect.x}:{self.player.rect.y}"

        self.client.send(command)
        data = self.client.recv(json_encode=True,val=2)
        if data != "Bad Data":
            self.players,bullets,items,self.entities = data

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
                    if event.key == K_a:
                        self.player.left = True
                    if event.key == K_d:
                        self.player.right = True
                    if event.key == K_r:
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
                    if event.key == K_z:
                        if self.player.equipped_weapon != None:
                            if self.player.equipped_weapon.gun_group == "Snipers":
                                if self.zoom_index < len(self.player.equipped_weapon.zoom_dis):
                                    self.zoom = self.player.equipped_weapon.zoom_dis[self.zoom_index]
                                self.zoom_index += 1
                                if self.zoom_index > len(self.player.equipped_weapon.zoom_dis):
                                    self.zoom = 1
                                    self.zoom_index = 0

                                self.console.change_size([round(self.game.display_dims[0]*self.zoom)-round(4*self.zoom),round(25*self.zoom)],2+round(self.zoom+0.1))

                                self.game.display = pygame.transform.scale(self.game.display,(round(self.game.display_dims[0]*self.zoom),round(self.game.display_dims[1]*self.zoom)))
                                self.camera.update(self.player,self.game.display,1)
                                
                    if event.key == K_SPACE:
                        if self.player.jump_count < 2 and self.player.on_wall == False:
                            self.player.vel_y = -self.player.jump
                            self.player.jump_count += 1
                        if self.player.on_wall == True and self.player.collisions["bottom"] == False:
                            self.player.wall_jump_true = True
                            self.player.jump_count = 1
                            self.player.wall_jump_count += 1
                        
##                    if event.key == K_0:
##                        self.player.weapon_index = 0
##                        self.player.equip_weapon()
##                    if event.key == K_1:
##                        self.player.weapon_index = 1
##                        self.player.equip_weapon()
##                    if event.key == K_2:
##                        self.player.weapon_index = 2
##                        self.player.equip_weapon()

            if event.type == MOUSEMOTION:
                self.controller_pos = list(self.relative_pos)
                self.moving_aim_axis = False
                pygame.mouse.set_visible(True)
                        
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
        if self.play_type == "Multiplayer":
            self.multi_play()
