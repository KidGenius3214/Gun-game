#In game level editor for the game
# Players can make their own levels
import pygame
pygame.init()
from . import *
from copy import deepcopy
from .GUI import *
import sys
import queue
import pickle
import os
import json

class Level_Editor:
    def __init__(self,game):
        self.game = game
        self.img_m = Image_Manager(['.png','jpg'])
        self.font = Text("data/images/font.png", 1, 2)
        self.current_map = "zone1"
        self.current_tile = '1'
        self.current_layer = "tiles"
        self.scroll = [0,0]
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.shift = False
        self.ctrl = False
        self.clicked = False
        self.click_tick = 60
        self.load_map = False
        self.does_not_exist = False
        self.erase = False
        self.copy_mode = False
        self.alert_tick = 360
        self.speed = 2
        self.save_button = Button(440, 10, 1, "Save",2,"small",True)
        self.load_button = Button(500, 10, 1, "Load",2,"small",True)
        self.map_name = Text_Input(15, self.game.display.get_height()-30,2,1,16)
        self.load_name = Text_Input(25, (self.game.display.get_height()//2)-12,3,1,16)
        self.load_btn = Button(76, (self.game.display.get_height()//2)-12, 1, "Load",2,"small",True)
        self.cancel_btn = Button(76, (self.game.display.get_height()//2)-12, 1, "Cancel",2,"small",True)
        self.exit_btn = Button(440, 38, 1, "Exit",2,"small",True)
        self.alert_font = Text("data/images/font.png", 1, 3)
        self.font = Text("data/images/font.png", 1, 2)
        self.level_num = 0
        self.map_copy = {}
        self.move = False
        self.select = False
        self.select_done = False
        self.og_pos = [0,0]
        self.select_rect = pygame.Rect(0,0,0,0)
        self.prompt_timer = 150
        self.prompt = ""
        self.prompt_on = False
        self.saved = False
        self.exit_prompt = False
        self.exit_save_button = Button(200,(self.game.display.get_height()//2)-10,1,"Save&Exit", 2, "small",True)
        self.exit_button = Button(260,(self.game.display.get_height()//2)-10,1,"Exit", 2, "small",True)
        self.cancel_button = Button(320,(self.game.display.get_height()//2)-10,1,"Cancel", 2, "small",True)
        self.exit_save_button.disabled = True
        self.exit_button.disabled = True
        self.cancel_button.disabled = True
        self.log = []
        self.log_num = 0
        self.logged = False
        self.tilesets = {}
        self.tile_data = self.game.tile_data
    
        # Zone 1 images
        self.zone1_tiles = {}
        tile_count = 0
        spawn_image = self.img_m.load("data/images/spawn.png",(255,255,255))
        spawn_image2 = self.img_m.load("data/images/spawn_mult.png",(255,255,255))
        self.map_size = [self.game.CHUNKSIZE,self.game.CHUNKSIZE]
        self.map = {"plants":[],"decor":[],"tiles":[]}
        image = self.img_m.load("data/images/zone1_tileset/60_23.png",(255,255,255))
        for i in range(round(image.get_width()/self.game.TILESIZE)):
            tile_count = i+1
            self.zone1_tiles[str(tile_count)] = get_image(image,i*self.game.TILESIZE,0,self.game.TILESIZE,23,1)
        image = self.img_m.load("data/images/zone1_tileset/20_20.png",(255,255,255))
        for i in range(round(image.get_width()/self.game.TILESIZE)):
            tile_count = i+4
            self.zone1_tiles[str(tile_count)] = get_image(image,i*self.game.TILESIZE,0,self.game.TILESIZE,self.game.TILESIZE,1)
        image = self.img_m.load("data/images/zone1_tileset/plants.png",(255,255,255))
        for i in range(round(image.get_width()/self.game.TILESIZE)):
            tile_id = self.tile_data["plants"][i]
            self.zone1_tiles[str(tile_id)] = get_image(image,i*self.game.TILESIZE,0,self.game.TILESIZE,self.game.TILESIZE,1)
            
        self.zone1_tiles["spawn"] = spawn_image
        self.zone1_tiles["spawn_mult"] = spawn_image2
        image = self.img_m.load("data/images/gun_tiles.png")
        for i in range(round(image.get_width()/self.game.TILESIZE)):
            tile_id = self.tile_data["guns"][i]
            self.zone1_tiles[str(tile_id)] = get_image(image,i*self.game.TILESIZE,0,self.game.TILESIZE,self.game.TILESIZE,1)

        self.zone1_tiles["park_bench"] = self.img_m.load("data/images/zone1_tileset/park_bench.png",(255,255,255))

        self.tilesets["zone1"] = self.zone1_tiles
                
        self.buttons = {}
        button_col = 0
        button_row = 0
        for tile in self.tilesets[self.current_map]:
            image = self.zone1_tiles[tile]
            tile_id = tile
            self.buttons[tile] = [image,tile_id,pygame.Rect((button_col*22)+440,button_row*24+70,image.get_width(),image.get_height())]
            button_col += 1
            if button_col > 6:
                button_row += 1
                button_col = 0
            
        self.chunk_size = self.game.CHUNKSIZE
        for i in range(self.map_size[1]):
            self.map["tiles"].append([])
            for j in range(self.map_size[0]):
                self.map["tiles"][i].append('0')
                
        self.map["plants"] = deepcopy(self.map["tiles"])
        self.map["decor"] = deepcopy(self.map["tiles"])

        self.maps = [self.map,self.buttons]

    def save(self,game_map,map_name):
        #chunkify the data
        if map_name == '':
            map_name = 'new_level'
        final_map = self.chunkify(game_map)
        data = {"data":final_map, "zone":self.current_map, "normal_map":game_map, "spawnpoints":[]}
        self.prompt = "Map Saved"
        self.prompt_on = True
        with open(f"data/maps/{map_name}.level", "wb") as file:
            pickle.dump(data, file)
            file.close()

    def extend_map(self,x,y):
        if x >= self.map_size[0] or y >= self.map_size[1]:
            temp = self.maps[0]
            x = int(x/self.chunk_size)
            y = int(y/self.chunk_size)
            width = int(len(temp["tiles"][0])/self.chunk_size)
            height = int(len(temp["tiles"])/self.chunk_size)
            increase_x = 0
            increase_y = 0

            if x <= 0:
                increase_x = 0
            elif  x - width == 0:
                increase_x = 1
            elif x == width:
                increase_x = 1
            elif x < width:
                increase_x = 0
            else:
                increase_x = x - width
                if increase_x < 0:
                    increase_x = -(increase_x)

            if y <= 0:
                increase_y = 0
            elif  y - height == 0:
                increase_y = 1
            elif y == height:
                increase_y = 1
            elif y < height:
                increase_y = 0
            else:
                increase_y = y - width
                if increase_y < 0:
                    increase_y = -(increase_y)

            increase_x *= self.chunk_size
            increase_y *= self.chunk_size
            self.maps[0] = {}
            for layer in temp:
                self.maps[0][layer] = []
            self.map_size[0] += increase_x
            self.map_size[1] += increase_y

            for layer in temp:
                for i in range(self.map_size[1]):
                    self.maps[0][layer].append([])
                    for j in range(self.map_size[0]):
                        self.maps[0][layer][i].append('0')

                for i in range(len(temp[layer])):
                    for j in range(len(temp[layer][0])):
                        self.maps[0][layer][i][j] = temp[layer][i][j]

    def load(self,name):
        with open(f"data/maps/{name}.level", "rb") as file:
            data = pickle.load(file)
            file.close()
        norm_data = data["normal_map"]
        del data
        return norm_data

    def del_selected(self):
        map_pos = [int(self.select_rect.x/self.game.TILESIZE), int(self.select_rect.y/self.game.TILESIZE)]
        width = int(self.select_rect.width/self.game.TILESIZE)
        height = int(self.select_rect.height/self.game.TILESIZE)

        for layer in self.maps[0]:
            for i in range(height):
                for j in range(width):
                    try:
                        self.maps[0][layer][i+map_pos[1]][j+map_pos[0]] = '0'
                    except:
                        pass

    def copy_map(self):
        map_pos = [int(self.select_rect.x/self.game.TILESIZE), int(self.select_rect.y/self.game.TILESIZE)]
        width = int(self.select_rect.width/self.game.TILESIZE)
        height = int(self.select_rect.height/self.game.TILESIZE)

        for layer in self.maps[0]:
            self.map_copy[layer] = []
            for i in range(height):
                self.map_copy[layer].append([])
                for j in range(width):
                    self.map_copy[layer][i].append(self.maps[0][layer][i+map_pos[1]][j+map_pos[0]])

    def paste(self,x,y):
        width = len(self.map_copy["tiles"][0])
        height = len(self.map_copy["tiles"])
        
        for layer in self.map_copy:
            for i in range(height):
                for j in range(width):
                    self.extend_map(j+x, i+y)
                    try:
                        self.maps[0][layer][i+y][j+x] = self.map_copy[layer][i][j]
                    except:
                        pass
        
    def get_chunk_str(self, x, y):
        chunk_x = int(x/self.chunk_size)
        chunk_y = int(y/self.chunk_size)
        chunk_str = f"{chunk_x}/{chunk_y}"
        return chunk_str

    def chunkify(self,data):
        chunk_data = []
        final_map = {"spawnpoints":[],"guns":[]}
        mult_x = 0
        mult_y = 0
        for layer in data:
            mult_x = 0
            mult_y = 0
            world_w = round(len(data[layer][0])/self.chunk_size)
            world_h = round(len(data[layer])/self.chunk_size)
            final_map[layer] = {}
            chunk_data = []
            for i in range(world_h):
                for j in range(world_w):
                    for y_pos in range(self.chunk_size):
                        for x_pos in range(self.chunk_size):
                            target_x = j * self.chunk_size + x_pos
                            target_y = i * self.chunk_size + y_pos
                            tile_coord = [target_x, target_y]
                            tile_x = mult_x + x_pos
                            tile_y = mult_y + y_pos
                            chunk_str = self.get_chunk_str(target_x, target_y)
                            try:
                                if data[layer][tile_y][tile_x] in ["spawn","spawn_mult"]:
                                    spawn_id = data[layer][tile_y][tile_x]
                                    final_map["spawnpoints"].append([spawn_id,tile_coord])
                                if data[layer][tile_y][tile_x] in self.tile_data["guns"]:
                                    gun_id = data[layer][tile_y][tile_x]
                                    final_map["guns"].append([gun_id, tile_coord])

                                offset = [0,0]
                                if data[layer][tile_y][tile_x] in self.tile_data["Level_Editor_offsets"]:
                                    offset = self.tile_data["Level_Editor_offsets"][data[layer][tile_y][tile_x]]
                                    tile_coord[0] += offset[0]
                                    tile_coord[1] += offset[1]
                                    
                                chunk_data.append([data[layer][tile_y][tile_x], tile_coord]) # so it does not crash
                            except:
                                pass
                            final_map[layer][chunk_str] = chunk_data
                            if len(chunk_data) == self.chunk_size**2: # makes sure the size of a chunk is equal to the chunk size because each tile is in a row
                                chunk_data = []
                            
                    mult_x += self.chunk_size
                    if mult_x >= self.chunk_size*world_w:
                        mult_x = 0
                        
                mult_y += self.chunk_size
                        
        return final_map

    def flood_fill(self, map_data, x, y, new_val):
        world_w = len(map_data[0])
        world_h = len(map_data)
        old_val = map_data[y][x]
        if old_val == new_val:
            return
        Queue = queue.Queue()
        Queue.put((y, x))
        while not Queue.empty():
            y, x = Queue.get()
            if x < 0 or x >= world_w or y < 0 or y >= world_h or map_data[y][x] != old_val:
                continue
            else:
                map_data[y][x] = new_val
                Queue.put((y+1, x))
                Queue.put((y-1, x))
                Queue.put((y, x+1))
                Queue.put((y, x-1))

    def log_state(self):
        if self.logged == True:
            self.log = self.log[:self.log_num]
        self.log.append(pickle.dumps(self.maps[0]))
        self.log_num += 1
        self.logged = False

    def undo(self):
        if self.log_num > 0:
            self.log_num -= 1
        data = self.log[self.log_num]
        return pickle.loads(data)

    def redo(self):
        if self.log_num < len(self.log):
            self.log_num += 1
        if self.log_num == len(self.log):
            self.log_num  = len(self.log)-1
        data = self.log[self.log_num]
        return pickle.loads(data)

    def run(self):
        self.game.display.fill((90,90,90))
        pos = pygame.mouse.get_pos()
        pos = [int(pos[0]//2),int(pos[1]//2)]   

        game_map = self.maps[0]
        buttons = self.maps[1]

        if self.shift == True:
            speed = 7

        if self.load_map == False and self.exit_prompt == False:
            if self.left == True:
                self.scroll[0] -= self.speed
            if self.right == True:
                self.scroll[0] += self.speed
            if self.up == True:
                self.scroll[1] -= self.speed
            if self.down == True:
                self.scroll[1] += self.speed

        pygame.draw.rect(self.game.display, (0,100,230), (0-self.scroll[0],0-self.scroll[1], len(game_map[self.current_layer][0])*self.game.TILESIZE, len(game_map[self.current_layer])*self.game.TILESIZE),1)

        for layer in game_map:
            for i, row in enumerate(game_map[layer]):
                for j, tile in enumerate(row):
                    if tile in self.zone1_tiles and tile not in ['1','2','3']:
                        offset = [0,0]
                        if tile in self.tile_data["Level_Editor_offsets"]:
                            offset = self.tile_data["Level_Editor_offsets"][tile]
                        self.game.display.blit(self.zone1_tiles[tile], ((j+offset[0])*self.game.TILESIZE-self.scroll[0],(i+offset[1])*self.game.TILESIZE-self.scroll[1]))
                    if tile in self.zone1_tiles and tile in ['1','2','3']:
                        self.game.display.blit(self.zone1_tiles[tile], (j*self.game.TILESIZE-self.scroll[0],i*self.game.TILESIZE-2-self.scroll[1]))

        if self.select == True and self.select_done == False and self.load_map == False and self.exit_prompt == False:
            self.select_rect.x = self.og_pos[0]*self.game.TILESIZE
            self.select_rect.y = self.og_pos[1]*self.game.TILESIZE
            self.select_rect.width = -(self.og_pos[0]-int((pos[0]+self.scroll[0])/self.game.TILESIZE)-1)*self.game.TILESIZE
            self.select_rect.height = -(self.og_pos[1]-int((pos[1]+self.scroll[1])/self.game.TILESIZE)-1)*self.game.TILESIZE
            pygame.draw.rect(self.game.display,(255,0,0),(self.select_rect.x-self.scroll[0], self.select_rect.y-self.scroll[1],
                                                          self.select_rect.width, self.select_rect.height),1)
        else:
            self.og_pos[0] = int((pos[0]+self.scroll[0])/self.game.TILESIZE)
            self.og_pos[1] = int((pos[1]+self.scroll[1])/self.game.TILESIZE)

        if self.select_done == True:
            pygame.draw.rect(self.game.display,(255,0,0),(self.select_rect.x-self.scroll[0], self.select_rect.y-self.scroll[1],
                                                          self.select_rect.width, self.select_rect.height),1)

        pygame.draw.rect(self.game.display, (50,50,100), (self.game.display.get_width()-170,0,170,self.game.display.get_height()))

        x = int((pos[0]+self.scroll[0])/self.game.TILESIZE)
        y = int((pos[1]+self.scroll[1])/self.game.TILESIZE)
        place = (self.save_button.rect.collidepoint(pos) == False and self.load_button.rect.collidepoint(pos) == False and self.map_name.rect.collidepoint(pos) == False)
        if self.load_map == False and self.exit_prompt == False and self.clicked == False:
            if pygame.mouse.get_pressed()[0] and x > -1 and y > -1 and pos[0] < self.game.display.get_width()-170\
               and place == True:
                self.extend_map(x,y)
                try:
                    if self.erase == False:
                        self.maps[0][self.current_layer][y][x] = self.current_tile
                    if self.erase == True:
                        self.maps[0][self.current_layer][y][x] = '0'
                except Exception as e:
                    print(e)
                self.select = False
            if pygame.mouse.get_pressed()[2] == True and x > -1 and y > -1 and pos[0] < self.game.display.get_width()-170:
                self.select = True
                self.select_done = False
                
        
        for button in buttons:
            self.game.display.blit(buttons[button][0], buttons[button][2])
            if buttons[button][2].collidepoint(pos):
                if self.load_map == False and self.exit_prompt == False:
                    if pygame.mouse.get_pressed()[0] == True:
                        self.current_tile = buttons[button][1]
            pygame.draw.rect(self.game.display, (255,0,0), buttons[self.current_tile][2],1)

        self.map_name.update(self.game.display,pos)
        self.save_button.update(self.game.display,pos)
        self.load_button.update(self.game.display,pos)
        self.exit_btn.update(self.game.display,pos)

        if self.save_button.clicked == True and self.clicked == False and self.saved == False and self.load_map == False and self.exit_prompt == False:
            self.save(game_map, self.map_name.text+f"_{self.level_num}")
            self.clicked = True
            self.saved = True
        if self.load_button.clicked == True and self.clicked == False and self.load_map == False and self.exit_prompt == False:
            self.load_map = True
        if self.exit_btn.clicked == True and self.clicked == False and self.exit_prompt == False and self.load_map == False:
            self.exit_prompt = True
            self.exit_save_button.disabled = False
            self.exit_button.disabled = False
            self.cancel_button.disabled = False

        if self.load_map == True:
            self.load_name.update(self.game.display, pos)
            self.load_btn.rect.x = self.load_name.rect.right+8
            self.load_btn.update(self.game.display,pos)

            self.cancel_btn.rect.x = self.load_btn.rect.right+4
            self.cancel_btn.update(self.game.display,pos)

            if self.load_btn.clicked == True:
                if os.path.exists(f"data/maps/{self.load_name.text}.level"):
                    self.maps[0] = self.load(self.load_name.text)
                    self.prompt = f"Loaded {self.load_name.text}"
                    self.map_size = [len(self.maps[0]["tiles"][0]), len(self.maps[0]["tiles"])]
                    self.load_map = False
                    self.map_name.text = self.load_name.text[:-2]
                    self.load_name.text = ''
                    self.prompt_on = True
                    self.clicked = True
                else:
                    self.does_not_exist = True

            if self.cancel_btn.clicked == True:
                self.load_map = False
                self.load_name.text = ''
                self.clicked = True

        if self.exit_prompt == True:
            self.exit_save_button.update(self.game.display,pos)
            self.exit_button.update(self.game.display,pos)
            self.cancel_button.update(self.game.display,pos)

            self.font.render(self.game.display,"Are you sure you want to leave?",(self.game.display.get_width()//2)-(self.font.get_size("Are you sure you want to leave?")[0]//2)
                             ,(self.game.display.get_height()//2)-28,(255,255,255))

            if self.exit_save_button.clicked == True and self.clicked == False:
                self.save(game_map, self.map_name.text + f"_{self.level_num}")
                self.game.state = "Menu"
                
            if self.exit_button.clicked == True and self.clicked == False:
                self.game.state = "Menu"

            if self.cancel_button.clicked == True and self.clicked == False:
                self.exit_prompt = False
                self.exit_save_button.disabled = True
                self.exit_button.disabled = True
                self.cancel_button.disabled = True
                self.clicked = True

        self.font.render(self.game.display, f"Level: {self.level_num}", 15, self.game.display.get_height()-46, (255,255,255))
        self.font.render(self.game.display, f"Layer: {self.current_layer}", 15, self.game.display.get_height()-63, (255,255,255))
        if self.erase == False:
            text = "Paint"
        elif self.erase == True:
            text = "Erase"
        self.font.render(self.game.display, f"Mode: {text}", 15, self.game.display.get_height()-80, (255,255,255))

        if self.does_not_exist == True:
            self.alert_tick -= 1
            if self.alert_tick > 0:
                self.alert_font.render(self.game.display, "The map does not exist",self.load_name.rect.x, self.load_name.rect.bottom+4, (255,0,0))
            else:
                self.alert_tick = 120
                self.does_not_exist = False

        for event in pygame.event.get():
            if self.load_map == False and self.exit_prompt ==  False:
                self.map_name.get_event(event)
            if self.load_map == True:
                self.load_name.get_event(event)
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    self.left = True
                    if self.select == True:
                        self.select_done = True
                    self.select = False
                if event.key == 127:
                    if self.select == True or self.select_done == True:
                        self.log_state()
                        self.del_selected()
                        self.select = False
                        self.select_done = False
                if event.key == K_c:
                    if self.ctrl == True:
                        self.log_state()
                        self.copy_map()
                        self.select = False
                        self.select_done = False
                if event.key == K_v:
                    if self.ctrl == True:
                        self.log_state()
                        self.paste(x,y)
                        self.select = False
                        self.select_done = False
                if event.key == K_RIGHT:
                    self.right = True
                    if self.select == True:
                        self.select_done = True
                    self.select = False
                if event.key == K_UP:
                    self.up = True
                    if self.select == True:
                        self.select_done = True
                    self.select = False
                if event.key == K_DOWN:
                    self.down = True
                    if self.select == True:
                        self.select_done = True
                    self.select = False
                if self.load_name.selected == False and self.map_name.selected == False:
                    if event.key == K_w:
                        self.level_num += 1
                    if event.key == K_s:
                        if self.level_num > 0:
                            self.level_num -= 1
                if event.key == K_LSHIFT:
                    self.shift = True
                if event.key == K_RSHIFT:
                    self.shift = True
                if event.key == K_LCTRL:
                    self.ctrl = True
                if event.key == K_RCTRL:
                    self.ctrl = True
                if event.key == K_e and self.load_map == False and self.map_name.selected == False:
                    self.erase = True
                if event.key == K_b and self.load_map == False and self.map_name.selected == False:
                    self.erase = False
                if event.key == K_f:
                    if self.shift == True:
                        self.flood_fill(self.maps[0][self.current_layer], x, y, self.current_tile)
                        self.log_state()
                    if self.ctrl == True:
                        self.flood_fill(self.maps[0][self.current_layer], x, y, '0')
                        self.log_state()
                if event.key == K_1:
                    self.current_layer = "tiles"
                if event.key == K_2:
                    self.current_layer = "plants"
                if event.key == K_3:
                    self.current_layer = "decor"
                if event.key == K_z:
                    if self.ctrl == True:
                        self.logged = True
                        self.maps[0] = self.undo()
                        self.map_size = [len(self.maps[0]["tiles"][0]), len(self.maps[0]["tiles"])]
                if event.key == K_y:
                    if self.ctrl == True:
                        self.maps[0] = self.redo()
                        self.map_size = [len(self.maps[0]["tiles"][0]), len(self.maps[0]["tiles"])]
                        
            if event.type == KEYUP:
                if event.key == K_LEFT:
                    self.left = False
                if event.key == K_RIGHT:
                    self.right = False
                if event.key == K_UP:
                    self.up = False
                if event.key == K_DOWN:
                    self.down = False
                if event.key == K_LSHIFT:
                    self.shift = False
                if event.key == K_RSHIFT:
                    self.shift = False
                if event.key == K_LCTRL:
                    self.ctrl = False
                if event.key == K_RCTRL:
                    self.ctrl = False

            if event.type == MOUSEBUTTONUP:
                if event.button == 3:
                    self.select_done = True
                if event.button == 1:
                    if x > -1 and y > -1 and pos[0] < self.game.display.get_width()-170:
                        self.log_state()

        if self.clicked == True:
            self.click_tick -= 1
            if self.click_tick <= 0:
                self.clicked = False
                self.click_tick = 60
                self.saved = False

        if self.prompt_on == True:
            self.prompt_timer -= 1
            self.font.render(self.game.display, self.prompt, 15, self.game.display.get_height()-97, (255,255,255))
            if self.prompt_timer <= 0:
                self.prompt_timer = 150
                self.prompt = ""
                self.prompt_on = False
        
        self.game.screen.blit(pygame.transform.scale(self.game.display, self.game.win_dims), (0,0))
        pygame.display.update()

        
