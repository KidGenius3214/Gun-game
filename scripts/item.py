import pygame
import scripts
import json
import pytweening as tween

with open("data/Game_data/item_info.json","r") as file:
    item_info = json.load(file)
    file.close()

class Item:
    def __init__(self,game,x,y,item_name,item_group,FPS,reference_obj=None):
        self.x = x
        self.y = y
        self.item_name = item_name
        self.item_group = item_group
        self.img = pygame.image.load(item_info[item_group][item_name][0]).convert()
        self.img.set_colorkey((255,255,255))
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.rect = pygame.Rect(self.x,self.y,self.width,self.height+4)
        self.ref_obj = reference_obj
        self.grounded = False
        self.collisions = {"right":False,"left":False,"top":False,"bottom":False}
        self.physics_obj = scripts.Physics(self.rect.x,self.rect.y,self.rect.width,self.rect.height)
        self.timer = 45
        self.hover = 45
        self.gravity = 1
        self.direction = 0.13
        self.step = 1
        self.FPS = FPS
        #light/line streak animation
        self.s_count = 0
        self.index = 0
        self.streak_time = item_info[item_group][item_name][1]*self.FPS # time light streak lasts

    def set_ref_obj(self,obj):
        self.ref_obj = obj

    def del_ref_obj(self,obj):
        self.ref_obj = None

    def bobbing(self,movement):
        self.hover -= 1
        if self.hover < 0:
            self.direction = -self.direction
            self.hover = 45
        movement[1] = self.direction

    def movement(self,tiles):
        movement = [0,self.gravity]

        self.gravity += 0.01
        if self.gravity > 4.5:
            self.gravity = 4.5

        if self.grounded == False:
            if self.collisions["top"] == True or self.collisions["bottom"] == True:
                self.grounded = True

        if self.grounded == True:
            self.bobbing(movement)
        
        self.collisions = self.physics_obj.movement(movement,tiles)
        self.rect = self.physics_obj.rect
        self.x = self.rect.x
        self.y = self.rect.y

    def render(self,surf,scroll):
        scripts.perfect_outline(self.img,surf,[self.rect.x-scroll[0],self.rect.y-scroll[1]],(255,255,255),(255,255,255)) #outline the item
        
        surf.blit(self.img,(self.rect.x-scroll[0],self.rect.y-scroll[1]))

        # light/line streak animation on the item
        blank_surf = pygame.Surface((self.rect.width,self.rect.height)) # blank surface
        blank_surf.fill((0,0,0))
        mask_array = pygame.PixelArray(blank_surf) # array to handle pixels in an organised way
        overlay_array = [] # spots to modify pixels(will match the color of the outline color)
        offset = 0
        for i in range(blank_surf.get_width()):
            for j in range(item_info[self.item_group][self.item_name][2]):
                loc = [((j+self.index)+offset)+self.s_count,i] # calculate light streak spot
                overlay_array.append(loc)
            offset -= 0
        self.index += 1
        self.s_count += 0

        mask_array[:] = (0,0,0)
        for pixel in overlay_array:
            try:
                if self.img.get_at((pixel[0],pixel[1])) != (255,255,255,255): #check if the pixel is not equal to the colorkey,which in our case is white/we use the actual image
                    mask_array[pixel[0],pixel[1]] = (255,255,255) #set the pixel needed to the light streak color
            except Exception as e:
                pass
            
        # overlay image
        new_img = mask_array.make_surface()
        new_img.set_colorkey((0,0,0)) #the background is black by default
        surf.blit(new_img,(self.rect.x-scroll[0],self.rect.y-scroll[1]))

        self.streak_time -= 1
        if self.streak_time <= 0:
            self.count = 0
            self.index = 0
            self.streak_time = item_info[self.item_group][self.item_name][1]*self.FPS

    def update(self,surf,scroll,tiles):
        self.movement(tiles)
        self.render(surf,scroll)
