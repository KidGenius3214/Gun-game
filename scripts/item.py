import pygame
import scripts
import json

with open("data/Game_data/item_info.json","r") as file:
    item_info = json.load(file)
    file.close()

class Item:
    def __init__(self,game,x,y,item_name,item_group,FPS,reference_obj=None):
        self.x = x
        self.y = y
        self.item_name = item_name
        self.item_group = item_group
        self.animate = item_info[item_group][item_name][3]
        if item_group not in ["Melee"]:
            if self.animate == True:
                self.animations = scripts.Animation()
                path = item_info[item_group][item_name][0]
                self.animations.load_anim("idle",f"data/images/animations/{path}/idle","png",item_info[item_group][item_name][4],(255,255,255))
                self.img = self.animations.image
            else:
                self.img = pygame.image.load(item_info[item_group][item_name][0]).convert()

        if item_group in ["Melee"]:
            if self.animate == True:
                self.animations = scripts.Animation()
                path = item_info[item_group][item_name][1]
                self.animations.load_anim("idle",f"data/images/animations/{path}/idle","png",item_info[item_group][item_name][5],(255,255,255))
                for i in range(len(item_info[item_group][item_name][5])):
                    width = int(self.animations.anim_database["idle"]["idle"+"_"+i].get_width()/2)
                    height = self.animations.anim_database["idle"]["idle"+"_"+i].get_height()
                    self.animations.anim_database["idle"]["idle"+"_"+i] = scripts.get_image(self.animations.anim_database["idle"]["idle"+"_"+i],width,0,width,height,1)
                self.animations.image = self.animations.anim_database["idle"]["idle_0"]
                self.img = self.animations.image
            else:
                self.img = pygame.image.load(item_info[item_group][item_name][0]).convert()
                self.img = scripts.get_image(self.img,int(self.img.get_width()/2),0,int(self.img.get_width()/2),self.img.get_height(),1)

        self.img.set_colorkey((255,255,255))
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.rect = pygame.Rect(self.x,self.y,self.width,self.height)
        self.ref_obj = reference_obj
        self.grounded = False
        self.collisions = {"right":False,"left":False,"top":False,"bottom":False}
        self.physics_obj = scripts.Physics(self.rect.x,self.rect.y,self.rect.width,self.rect.height+2)
        self.vel_y = 0
        self.grav = 0.15
        self.timer = 45
        self.step = 1
        self.FPS = FPS
        self.movement = [0,0]
        self.dropped = False
        self.drop_timer = 45
        self.pickup_cooldown = 0
        #light/line streak animation
        self.s_count = 0
        self.index = 0
        self.streak_time = item_info[item_group][item_name][1]*self.FPS # time light streak lasts

    def set_ref_obj(self,obj):
        self.ref_obj = obj

    def del_ref_obj(self,obj):
        self.ref_obj = None

    def move(self,tiles):
        if self.dropped != True:
            self.movement = [0,0]

        self.movement[1] += self.vel_y
        self.vel_y += self.grav
            
        if self.vel_y > 15:
            self.vel_y = 15
        
        self.collisions = self.physics_obj.movement(self.movement,tiles)
        self.rect = self.physics_obj.rect
        self.x = self.rect.x
        self.y = self.rect.y

        if self.collisions["bottom"] == True:
            self.vel_y = -(self.vel_y*0.4)
            if self.vel_y > -0.6:
                self.vel_y = 0
            self.vel_y = round(self.vel_y)
            self.grounded = True
            self.dropped = False

        if self.collisions["top"] == True:
            self.vel_y = 2
            self.movement[1] += 0.3

        if (self.collisions['right'] == True) or (self.collisions['left']):
            self.movement[0] = -(self.movement[0]*0.5)
        

    def render(self,surf,scroll):
        if self.animate == True:
            self.img = self.animations.animate('idle',True)
        
        scripts.perfect_outline(self.img,surf,[self.rect.x-scroll[0],self.rect.y-scroll[1]],(255,255,255),(255,255,255)) #outline the item
        
        surf.blit(self.img,(self.rect.x-scroll[0],self.rect.y-scroll[1]))
        

        # light/line streak animation on the item
        blank_surf = pygame.Surface((self.rect.width,self.rect.height)) # blank surface
        blank_surf.fill((0,0,0))
        mask_array = pygame.PixelArray(blank_surf) # array to handle pixels in an organised way
        overlay_array = [] # spots to modify pixels(will match the color of the outline color)
        offset = 0
        for i in range(blank_surf.get_height()):
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

    def set_pos(self,pos):
        self.rect.x,self.rect.y = pos
        self.physics_obj.x,self.physics_obj.y = pos

    def get_center(self):
        center_x = self.rect.x+int(self.rect.width/2)
        center_y = self.rect.y+int(self.rect.height/2)
        return [center_x, center_y]

    def update(self,surf,scroll,tiles):
        self.movement(tiles)
        self.render(surf,scroll)
