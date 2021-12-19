#Library
import pygame
import os, xml.etree.ElementTree as ET
import json
import math
pygame.init()

#functions
def swap_color(img,old_c,new_c):
    img.set_colorkey(old_c)
    surf = img.copy()
    surf.fill(new_c)
    surf.blit(img,(0,0))
    surf.set_colorkey((0,0,0))
    return surf

def perfect_outline(img, surf, loc, color, colorkey=(0,0,0), colorkey2=(0,0,0)):
    img.set_colorkey(colorkey)
    mask = pygame.mask.from_surface(img)
    mask_surf = mask.to_surface(setcolor=color)
    mask_surf.set_colorkey((0,0,0))
    surf.blit(mask_surf,(loc[0]-1,loc[1]))
    surf.blit(mask_surf,(loc[0]+1,loc[1]))
    surf.blit(mask_surf,(loc[0],loc[1]-1))
    surf.blit(mask_surf,(loc[0],loc[1]+1))

def get_image(image,x,y,w,h,scale):
    surf = pygame.Surface((w,h))
    surf.set_colorkey((0,0,0))
    surf.blit(image, (0,0), (x,y,w,h))
    return pygame.transform.scale(surf, (int(w*scale), int(h*scale)))

def blit_center(surf,other_surf,pos):
    x = int(other_surf.get_width()/2)
    y = int(other_surf.get_height()/2)
    surf.blit(other_surf, (pos[0]-x,pos[1]-y))

#math stuff
def find_angle_from_points(point1,point2,scroll,offset,degrees):
    if degrees == False:
        return math.atan2(point1[1] - (int(point2[1])-scroll[1] + offset[1]), point1[0] - (int(point2[0])-scroll[0] + offset[0]))
    else:
        return math.degrees(math.atan2(point1[1] - (int(point2[1])-scroll[1] + offset[1]), point1[0] - (int(point2[0])-scroll[0] + offset[0])))

def normalize_vec(vec):
    # get the magnitude
    mag = math.sqrt( (vec[0])**2 + (vec[1])**2 )
    new_vec = [ vec[0]/mag, vec[1]/mag ]
    return new_vec

def line_to_line_vec_collide(start,end,origin,end2):
    P = pygame.math.Vector2(start)
    R = (pygame.math.Vector2(end)-P)
    Q = pygame.math.Vector2(origin)
    S = (pygame.math.Vector2(end2)-Q)
    d = R.dot((S.y, -S.x))
    if d == 0:
        return
    t = (Q-P).dot((S.y, -S.x))/d
    u = (Q-P).dot((R.y, -R.x))/d
    if 0 <= t <= 1 and 0 <= u <= 1:
        point = P+(R*t)
        return [point.x,point.y]
    return None

def line_to_rect_collide(start,end,rect):
    #Line points of the rect
    #Basically lines going around the border of the rect
    r_lines = {"L1":(rect.topleft,rect.bottomleft),"L2":(rect.topleft,rect.topright),"L3":(rect.topright, rect.bottomright),"L4":(rect.bottomleft,rect.bottomright)}
    for line in r_lines:
        point = line_to_line_vec_collide(start,end,r_lines[line][0],r_lines[line][1])
        if point != None:
            return [point,True]
    return [[0,0],False]
       

#Image manager
class Image_Manager:
    def __init__(self, valid_formats):
        self.valid_formats = valid_formats

    def load(self, path, colorkey=None):
        """
        load an image params:
        path -> path to the image being loaded
        colorkey -> If it is not None, sets a colorkey to the image
        """
        img = pygame.image.load(path).convert()
        if colorkey:
            img.set_colorkey(colorkey)
        return img

    def load_scaled_image(self,path,dims,colorkey=None):
        img = pygame.transform.scale(pygame.image.load(path), (dims[0], dims[1]))
        if colorkey:
            img.set_colorkey(colorkey)
        return img

    def get_image(self,image,x,y,w,h,scale):
        surf = pygame.Surface((w,h))
        surf.set_colorkey((0,0,0))
        surf.blit(image, (0,0), (x,y,w,h))
        return pygame.transform.scale(surf, (w*scale, h*scale))

    def load_folder(self, folder_path):
        folder_list = os.listdir(folder_path)
        img_list = []
        for file in folder_path:
            if file.split('.')[1] in self.valid_formats:
                img_list.append(pygame.image.load(f"{folder_path}.{file}"))

        return img_list

class XML_TREE:
    def __init__(self):
        self.id = "XML_TREE"
        self.files = {}

    def create_tree(self, xml_data, data_key):
        file = ET.parse(path)
        tree = file.getroot()
        self.files[data_key] = tree

    def get_attrib(self, data_key,tag_name):
        attrib_list = []
        for tag_data in self.files[data_key].iter(tag_name):
            attrib_list.append(tag_data.attribs)

        return attrib_list
    def get_text(self, data_key,tag_name):
        text_list = []
        for tag_data in self.files[data_key].iter(tag_name):
            text_list.append(tag_data.text)

        return text_list

    def get_tag(self, data_key, tag_name):
        tag_list = []
        for tag_data in self.files[data_key].iter(tag_name):
            tag_list.append(tag_data)

        return tag_list

class JSON_Handler:
    def __init__(self):
        self.files = {}

    def load(self, file_path, file_key):
        with open(file_path) as file:
            info = json.load(file)
            self.files[file_key] = info
        return info

    def write(self, data,file_path):
        with open(file_path, "r") as file:
            json.dump(data,file_path)
            file.close()

    def get_data(self,file_key):
        return self.files[file_key]

    def del_file(self,file_key,return_data=False):
        if return_data == False:
            del self.files[file_key]
        else:
            data = self.files[file_key]
            del self.files[file_key]
            return data

#Physics and collisions
def collision_test(rect,rect_group):
    hit_list = []
    for other_rect in rect_group:
        if rect.colliderect(other_rect):
            hit_list.append(other_rect)

    return hit_list

class Physics:
    def __init__(self,x,y,w,h):
        self.rect = pygame.Rect(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def movement(self,movement,tiles):
        #x-axis(tiles)
        self.x += movement[0]
        self.rect.x = int(self.x)
        collision_types = {"right":False,"left":False,"top":False,"bottom":False}
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.left
                collision_types["right"] = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                collision_types["left"] = True
            self.x = self.rect.x
            
        #y-axis(tiles)
        self.y += movement[1]
        self.rect.y = int(self.y)
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types["bottom"] = True
            if movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types["top"] = True
            self.y = self.rect.y

        return collision_types

    def sprite_collision(self, sprite, walls, movement, constants=None):
        collision_types = {"right": False, "left": False, "top":False, "bottom":False}
        hit_list = pygame.sprite.collide(sprite, walls, False, collide_hit_rect)
        
        if constants == None:
            if hit_list:
                if movement.x > 0:
                    sprite.rect.x = hit_list[0].topleft[0] - sprite.rect.width
                    collision_types["right"] = True
                if movement.x < 0:
                    sprite.rect.x = hit_list[0].topleft[0] + sprite.rect.width
                    collision_types["left"] = True
        else:
            if hit_list:
                if movement.x > 0:
                    sprite.rect.x = hit_list[0].topleft[0] - constants[0]
                    collision_types["right"] = True
                if movement.x < 0:
                    sprite.rect.x = hit_list[0].topleft[0] + constants[1]
                    collision_types["left"] = True

        hit_list = pygame.sprite.collide(sprite, walls, False, collide_hit_rect)
        if constants == None:
            if hit_list:
                if movement.y > 0:
                    sprite.rect.y = hit_list[0].topleft[1] - sprite.rect.height
                    collision_types["bottom"] = True
                if movement.y < 0:
                    sprite.rect.y = hit_list[0].topleft[1] + sprite.rect.height
                    collision_types["top"] = True
        else:
            if hit_list:
                if movement.y > 0:
                    sprite.rect.y = hit_list[0].topleft[1] - constants[3]
                    collision_types["bottom"] = True
                if movement.y < 0:
                    sprite.rect.y = hit_list[0].topleft[1] + constants[4]
                    collision_types["bottom"] = True
        return collision_types

    def change_rect(self,rect):
        self.rect = rect

class Entity:
    def __init__(self,x,y,width,height,vel,jump):
        # Rect setup
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.id = ''
        self.rect = pygame.Rect(self.x,self.y,self.w,self.h)
        self.physics_obj = Physics(self.rect.x,self.rect.y,self.rect.width,self.rect.height)
        self.collisions = {"top":False,"bottom":False,"right":False,"left":False}
        #movement vars
        self.vel = vel
        self.vec = pygame.math.Vector2()
        self.jump = jump
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        self.gravity = 0.4
        self.vel_y = 0

        #States and animation management
        self.state = ""
        self.image = pygame.Surface((self.rect.width,self.rect.height))
        self.image.fill((0,0,255))
        self.entity_frame_count = 0

    def draw(self, surf, scroll):
        surf.blit(self.image, (self.rect.x-scroll[0],self.rect.y-scroll[1]))

    def get_center(self):
        center_x = self.rect.x+int(self.rect.width/2)
        center_y = self.rect.y+int(self.rect.height/2)
        return [center_x, center_y]

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y
        self.physics_obj.x = x
        self.physics_obj.y = y

class Particle:
    def __init__(self, x, y, size,shape_type,color,motion,size_decrease=1,grav=None,outline=None):
        self.x = x
        self.y = y
        self.size = size
        self.shape_type = shape_type
        self.color = color
        self.size_decrease = size_decrease
        self.motion = motion
        self.grav = grav
        self.outline = outline

    def render(self, surf,scroll):
        if self.shape_type == "circle":
            pygame.draw.circle(surf, self.color, (self.x-scroll[0], self.y-scroll[1]), self.size)
            if self.outline != None:
                if self.outline[1] > self.outline[2]:
                    pygame.draw.circle(surf, self.outline[0], (self.x-scroll[0], self.y-scroll[1]), self.size,self.outline[1])
                self.outline[1] -= self.size_decrease
            self.size -= self.size_decrease
            self.x += self.motion[0]
            self.y += self.motion[1]
            if self.grav != None:
                self.motion[1] -= self.grav

        if self.shape_type == 'square':
            pygame.draw.rect(surf, self.color, (self.x-scroll[0],self.y-scroll[1],self.size,self.size))
            if self.outline != None:
                if self.outline[1] > self.outline[2]:
                    pygame.draw.rect(surf, self.outline[0], (self.x-scroll[0],self.y-scroll[1],self.size,self.size), self.outline[1])
                self.outline[1] -= self.size_decrease
            self.size -= self.size_decrease
            self.x += self.motion[0]
            self.y += self.motion[1]
            if self.grav != None:
                self.motion[1] -= self.grav

        if self.size <= 0:
            del self
class Camera:
    def __init__(self):
        self.true_scroll = [0,0]
        self.scroll = [0,0]

    def update(self,target,surf,diviser):
        self.scroll = [0,0]
        self.true_scroll[0] += (target.rect.x-surf.get_width()/2-self.true_scroll[0])/diviser
        self.true_scroll[1] += (target.rect.y-surf.get_height()/2-self.true_scroll[1])/diviser
        self.scroll[0] = int(self.true_scroll[0])
        self.scroll[1] = int(self.true_scroll[1])
        

class Text:
    def __init__(self, font_path, spacing,scale):
        self.font_image = font_path
        self.spacing = spacing
        self.font = {}
        self.scale = scale
        self.img_m = Image_Manager(["png", "jpg"])
        self.y_size = 0
        self.load_font()

    def load_font(self):
        Font_Order = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','.','-',',',':','+','\'','!','?','0','1','2','3','4','5','6','7','8','9','(',')','/','_','=','\\','[',']','*','"','<','>',';','|', '%', '&','\x00']
        font_image = pygame.image.load(self.font_image).convert()
        character_count = 0
        current_char_width = 0
        for x in range(font_image.get_width()):
            c = font_image.get_at((x, 0))
            if c[0] == 127:
                char_img = get_image(font_image, x - current_char_width, 0, current_char_width, font_image.get_height(), self.scale)
                self.font[Font_Order[character_count]] = char_img
                character_count += 1
                current_char_width = 0
            else:
                current_char_width += 1
        self.y_size = font_image.get_height()

    def render(self,surf, text, x, y, color=None):
        spacing = 0
        y_offset = 0
        for index,char in enumerate(text):
            if color != None:
                if char not in [' ','\n']:
                    char_img = swap_color(self.font[char], (255,0,0), color)
            else:
                if char not in [' ','\n']:
                    char_img = self.font[char]

            if char not in [' ','\n']:
                surf.blit(char_img, (x+spacing, y+y_offset))
            if char not in [' ','\n']:
                spacing += self.font[char].get_width() + self.spacing
            else:
                spacing += self.font['A'].get_width()
            
            if char == '\n':
                y_offset += self.font['A'].get_height()+1
                spacing = 0
            

    def get_size(self,text):
        width = 0
        height = self.font['A'].get_height()
        for char in text:
            if char not in [' ','\n']:
                width += self.font[char].get_width()
            else:
                width += self.font['A'].get_width()

            if char == '\n':
                height += self.font['A'].get_height()+1
                width = 0

        width += (len(text)-1)*self.spacing
        return [width, height]

class Animation:
    def __init__(self):
        self.anim_database = {}
        self.frames = {}
        self.frame_count = 0
        self.image = None
        self.states = []

    def load_anim(self, anim_key, folder, ext, frame_duration,colorkey=None):
        img_id = folder.split('/')[-1]
        self.anim_database[anim_key] = {}
        self.frames[anim_key] = []
        self.states.append(anim_key)
        for i in range(len(frame_duration)):
            path = f"{folder}/{img_id}_{i}.{ext}"
            img = pygame.image.load(path).convert()
            if colorkey != None:
                img.set_colorkey(colorkey)
                self.anim_database[anim_key][path.split('/')[-1].split('.')[0]] = img
            for i in range(frame_duration[i]):
                self.frames[anim_key].append(path.split('/')[-1].split('.')[0])

        frame = self.frames[self.states[0]][0]
        self.image = self.anim_database[self.states[0]][frame]

        
    def animate(self,state,return_img=False):
        self.frame_count += 1
        if self.frame_count >= len(self.frames[state]):
            self.frame_count = 0
        frame_name = self.frames[state][self.frame_count]
        self.image = self.anim_database[state][frame_name]
        if return_img != False:
            return self.image
        
