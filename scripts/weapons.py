#Weapons.py
#Holds all gun stuff
import pygame
import scripts
from . import *
import math,random

class Bullet:
    def __init__(self,game,x,y,speed,angle,color,dmg,owner,mult,lifetime,img=None,gravity=0):
        self.game = game
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.color = color
        self.dmg = dmg
        self.grav = gravity
        self.initial_vel_y = math.sin(self.angle)*self.speed
        self.owner = owner
        self.mult = mult
        self.lifetime = lifetime
        self.img = img
        self.id = random.randint(0,200000)
        if self.img != None:
            self.rect = pygame.Rect(self.x,self.y,self.img.get_width(),self.img.get_height())
        else:
            self.rect = pygame.Rect(self.x,self.y,5,5)

    def run(self,surf,scroll,dt,rects=None):
        self.x += math.cos(self.angle)*self.speed*dt*self.game.target_fps
        if self.grav == 0:
            self.y += math.sin(self.angle)*self.speed*dt*self.game.target_fps
        else:
            self.y += self.initial_vel_y*dt*self.game.target_fps
            self.initial_vel_y += self.grav*dt*self.game.target_fps
        self.lifetime -= 1*dt*self.game.target_fps
        if self.img != None:
            blit_center(surf,pygame.transform.rotate(self.img,math.degrees(-self.angle)),[self.rect.x-scroll[0],self.rect.y-scroll[1]])
            #pygame.draw.rect(surf,(0,255,0),(self.rect.x-scroll[0],self.rect.y-scroll[1],self.rect.width,self.rect.height),1)
        else:
            pygame.draw.line(surf,self.color,(self.x-scroll[0],self.y-scroll[1]),(self.x+math.cos(self.angle)*self.mult[0]-scroll[0],
                                                                                self.y+math.sin(self.angle)*self.mult[0]-scroll[1]),self.mult[1])
        self.rect.x,self.rect.y = self.x,self.y

        if rects != None:
            for rect in rects:
                if rect.colliderect(self.rect):
                    return "Collided"

class Gun:
    def __init__(self,game,gun,gun_info,FPS):
        self.game = game
        self.gun_info = gun_info
        self.name = gun
        self.FPS = FPS
        self.img = pygame.image.load(self.gun_info["image"]).convert()
        self.img.set_colorkey((255,255,255))
        self.weapon_group = ""
        if self.name in self.game.weapon_data["Shotguns"]:
            self.weapon_group = "Shotguns"
        if self.name in self.game.weapon_data["Pistols"]:
            self.weapon_group = "Pistols"
        if self.name in self.game.weapon_data["Rifles"]:
            self.weapon_group = "Rifles"
        if self.name in self.game.weapon_data["Snipers"]:
            self.weapon_group = "Snipers"
            
        if self.weapon_group == "Snipers":
            self.zoom_dis = self.gun_info["zoom_distances"]
        if self.weapon_group == "Shotguns":
            self.bullet_amount = self.gun_info["bullet_amount"]
            self.spread = self.gun_info["spread"]
            
        self.ammo = gun_info["ammo"]
        self.ammo_l = gun_info["ammo_loaded"]
        self.speed = gun_info["speed"]
        self.dmg = gun_info["damage"]
        self.crit_rate = gun_info["crit_rate"]
        self.shot = False
        self.reload_gun = False
        self.has_ammo = True
        self.flip = False
        self.crit_dmg = gun_info["crit_dmg"]

        # Rendering stuff
        #==========================================================================
        self.render_offset = gun_info["render_offset"]
        self.bullet_offset = gun_info["bullet_offset"]
        self.render_offset_copy = gun_info["render_offset"]
        self.bullet_offset_copy = gun_info["bullet_offset"]

        self.inv_render_offset = [-self.render_offset[0],self.render_offset[1]]
        self.inv_bullet_offset = [-self.bullet_offset[0],self.bullet_offset[1]]
        #==========================================================================

        self.bullet_size = gun_info["bullet_size"]
        self.pause = gun_info["pause"]*FPS
        self.reload_time = gun_info["reload_time"]*FPS
        if self.gun_info["bullet_image"] != None:
            self.bullet_img = self.load_bullet_img(self.gun_info["bullet_image"])
        else:
            self.bullet_img = None

    def shoot(self,bullet_list,owner,pos,angle,dt):
        if self.weapon_group != "Shotguns":
            if self.shot == False and self.reload_gun == False and self.has_ammo == True:
                dmg = self.dmg
                if random.random() <= self.crit_rate:
                    dmg = random.randint(self.crit_dmg[0],self.crit_dmg[1])

                if self.weapon_group != "Bows":
                    bullet_list.append(Bullet(self.game,pos[0]+self.bullet_offset[0],pos[1]+self.bullet_offset[1],self.speed,angle,(239,222,7),dmg,owner,self.bullet_size,self.gun_info["b_lifetime"],self.bullet_img))
                else:
                    bullet_list.append(Bullet(self.game,pos[0]+self.bullet_offset[0],pos[1]+self.bullet_offset[1],self.speed,angle,(239,222,7),dmg,owner,self.bullet_size,self.gun_info["b_lifetime"],self.bullet_img,self.gun_info["b_grav"]))
                    
                self.ammo_l -= 1
                self.shot = True

            if self.shot == True and self.has_ammo == True:
                self.pause -= 1*dt*self.game.target_fps
                if self.pause <= 0:
                    self.pause = self.gun_info["pause"]*self.FPS
                    self.shot = False
        else:
            if self.shot == False and self.reload_gun == False and self.has_ammo == True:
                for i in range(self.bullet_amount):
                    dmg = self.dmg
                    if random.random() <= self.crit_rate:
                        dmg = random.randint(self.crit_dmg[0],self.crit_dmg[1])

                    bullet_list.append(Bullet(self.game,pos[0]+self.render_offset[0],pos[1]+self.render_offset[1],self.speed,angle+random.uniform(self.spread[0],self.spread[1]),(239,222,7),dmg,owner,self.bullet_size,self.gun_info["b_lifetime"],self.bullet_img))
                    
                self.ammo_l -= 1
                self.shot = True

            if self.shot == True and self.has_ammo == True:
                self.pause -= 1*dt*self.game.target_fps
                if self.pause <= 0:
                    self.pause = self.gun_info["pause"]*self.FPS
                    self.shot = False

    def render(self,surf,scroll,pos,angle):
        if self.flip == True:
            self.render_offset = self.inv_render_offset
            self.bullet_offset = self.inv_bullet_offset
        else:
            self.render_offset = self.render_offset_copy
            self.bullet_offset = self.bullet_offset_copy

        blit_center(surf,pygame.transform.rotate(pygame.transform.flip(self.img, False, self.flip),angle),[(pos[0]+self.render_offset[0])-scroll[0],(pos[1]+self.render_offset[1])-scroll[1]])

    def load_bullet_img(self,name):
        img = pygame.image.load(name).convert()
        img.set_colorkey((255,255,255))
        return img

    def reload(self):
        self.reload_time = self.gun_info["reload_time"]*self.FPS
        if self.ammo_l == 0 and self.ammo_l != self.gun_info["ammo_loaded"]:
            self.ammo_l = self.gun_info["ammo_loaded"]
            self.ammo -= self.ammo_l
        else:
            if self.ammo != self.gun_info["ammo_loaded"]:
                ammo_dif = self.gun_info["ammo_loaded"]-self.ammo_l
                self.ammo -= ammo_dif
                self.ammo_l = self.gun_info["ammo_loaded"]
        if self.ammo < 0:
            self.ammo_l += self.ammo
            self.ammo = 0
        self.reload_gun = False

    def add_ammo(self,amount):
        self.ammo += amount
        if self.ammo > self.gun_info["ammo"]:
            self.ammo = self.gun_info["ammo"]

    def update(self,surf,scroll,pos,angle,dt,render=True):
        if render == True:
            self.render(surf,scroll,pos,angle)
        if self.ammo <= 0 and self.ammo_l <= 0:
            self.has_ammo = False
        
        if self.ammo_l <= 0 and self.has_ammo == True:
            self.reload_gun = True

        if self.reload_gun == True and self.has_ammo == True:
            self.reload_time -= 1*dt*self.game.target_fps
            if self.reload_time <= 0:
                self.reload()

class RPG(Gun):
    def __init__(self,game,rpg,FPS):
        super().__init__(game,rpg,game.weapon_info[rpg],FPS)
    
    

class Melee_Weapon:
    def __init__(self,game,weapon):
        self.game = game
        self.name = weapon
        self.weapon_info = self.game.weapon_data[self.name]
        self.weapon_group = "Melee"
        self.img = pygame.image.load(self.weapon_info["image"]).convert()
        self.img.set_colorkey((255,255,255))
        self.dmg = self.weapon_info["damage"]
        self.crit_dmg = self.weapon_info["crit_dmg"]
        self.crit_rate = self.weapon_info["crit_rate"]
        self.slash_speed = self.weapon_info["speed"]
        self.lifetime = self.weapon_info["lifetime"]
        self.flip = True
        self.attacked = False
        self.timer = Timer(self.weapon_info["attack_speed"])
        self.angle = 0
        self.rect = pygame.Rect(0,0,self.img.get_width()/2,self.img.get_height())
        self._render = True
        self.arc = scripts.Arc(15, 0, 1, 2, 1)

        self.render_offset = self.weapon_info["render_offset"]
        self.render_offset_copy = self.weapon_info["render_offset"]

        self.inv_render_offset = [-self.render_offset[0],self.render_offset[1]]
    
    def render(self,surf,scroll,pos,angle):
        if self.flip == True:
            self.render_offset = self.inv_render_offset
        else:
            self.render_offset = self.render_offset_copy

        if self._render == True:
            blit_center(surf,pygame.transform.rotate(pygame.transform.flip(self.img, False, self.flip),angle),[(pos[0]+self.render_offset[0])-scroll[0],(pos[1]+self.render_offset[1])-scroll[1]])
    
    def attack2(self, angle):
        if self.attacked == False:
            self.attacked = True
            self._render = False
            self.timer.make_var_false()
            self.timer.set_time()
            self.arc.start_angle = angle

    def update(self,surf,scroll,pos,angle):
        self.render(surf,scroll,pos,angle)
        self.timer.update()

        if self._render == False:
            self.arc.update()
            self.arc.render(surf, ((pos[0] + math.cos(math.radians(angle))*15)-scroll[0], (pos[1] + math.sin(math.radians(angle))*15)-scroll[1]), (190,190,190))

            if self.arc.time >= 190:
                self._render = True
                self.attacked = False

class Ammo:
    def __init__(self,game,ammo_type):
        self.game = game
        self.ammo_type = ammo_type
        self.value = self.game.ammo_data[ammo_type][0]
        self.weapon_group = self.game.ammo_data[ammo_type][1]

    def get_val(self):
        return self.value

    def get_group(self):
        return self.weapon_group



#==========================================================
#Throwables section
#Throwables are things the player can throw at enemies or any other players
#==========================================================
class Throwable(scripts.Entity):
    def __init__(self, game, x, y, width, height, vel):
        super().__init__(x, y, width, height, vel, 0)
        self.game = game


class Grenade(Throwable):
    def __init__(self, game, x, y, vel, angle):
        super().__init__(game, x, y, 5, 5, vel)

        self.image = pygame.image.load("data/images/weapons/grenade.png").convert()
        self.image.set_colorkey((255,255,255))

        #explosion animation
        self.anim = scripts.Animation()
        self.anim.load_anim("exp", "data/images/animations/explosion/exp", "png", [5,5,5,5,5],(0,0,0))

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect.width = self.width
        self.rect.height = self.height
        self.physics_obj.rect.width = self.width
        self.physics_obj.rect.height = self.height

        self.angle = angle
        self.vel_y = math.sin(self.angle)*self.vel
        self.gravity = 0.3
        self.vel_x = math.cos(self.angle)*self.vel
        self.blast_raduis = 0
        self.max_raduis = 55
        self.timer = 1*self.game.target_fps
        self.explode_lifetime = 16
        self.exploded = False
        self.dmg = 60

    def draw(self, surf, scroll):
        if self.exploded == True:
            img, frame = self.anim.animate("exp", True, True)
            self.explode_lifetime = 9
            surf.blit(img, (self.rect.x-(img.get_width()/2)-scroll[0], self.rect.y-(img.get_height()/2)-scroll[1]))
            if self.anim.frame_count == len(self.anim.frames['exp'])-1:
                self.explode_lifetime = 0
        else:
            surf.blit(self.image, (self.rect.x-scroll[0], self.rect.y-scroll[1]))

    def move(self, tiles, dt):
        movement = [0,0]

        movement[0] += self.vel_x * dt * self.game.target_fps
        movement[1] += self.vel_y * dt * self.game.target_fps
        self.vel_y += self.gravity * dt * self.game.target_fps

        if self.vel_y > 7:
            self.vel_y = 7

        if self.exploded == False:
            self.collisions = self.physics_obj.movement(movement, tiles)
            self.rect = self.physics_obj.rect
            self.x = self.rect.x
            self.y = self.rect.y

        if self.collisions["bottom"] == True:
            self.vel_x = (self.vel_x*0.5)
            self.vel_y = -(self.vel_y*0.3)
        
        if self.collisions["right"] == True or self.collisions["left"] == True:
            self.vel_x = -self.vel_x
        
        if self.collisions['top'] == True:
            self.vel_y = 1
        
        self.timer -= round(1 * dt * self.game.target_fps)
        if self.timer < 0:
            if self.exploded == False:
                self.explode(dt)
        
        if self.exploded == True:
            self.explode_lifetime -= round(1*dt*self.game.target_fps)
    
    def explode(self, dt):
        self.blast_raduis = self.max_raduis

        if self.blast_raduis >= self.max_raduis:
            self.blast_raduis = self.max_raduis
            self.exploded = True
    
    def get_explode_lifetime(self):
        return self.explode_lifetime



class Molotov(Throwable):
    def __init__(self, game, x, y, vel, angle):
        super().__init__(game, x, y-8, 5, 5, vel)
        
        self.image = pygame.image.load("data/images/weapons/molotov.png").convert()
        self.image.set_colorkey((255,255,255))

        #Flame animation
        self.anim = scripts.Animation()
        self.anim.load_anim("burn", "data/images/animations/flame/burn", "png", [7,7,7,7,7,7,7,7],(255,255,255))

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect.width = self.width
        self.rect.height = self.height
        self.physics_obj.rect.width = self.width
        self.physics_obj.rect.height = self.height

        self.angle = angle
        self.vel_y = math.sin(self.angle)*self.vel
        self.gravity = 0.3
        self.vel_x = math.cos(self.angle)*self.vel
        self.burn_lifetime = 120
        self.burning = False
        self.burned = False
        self.burn_distance = (-40, 40)
        self.flames = []
        self.dmg = 9

    def draw(self,surf,scroll):
        if self.burning == True:
            self.anim.animate("burn")
            for flame in self.flames:
                surf.blit(self.anim.image, (flame.x-(self.anim.image.get_width()/2)-scroll[0], flame.y-scroll[1]))
        else:
            surf.blit(self.image, (self.rect.x-scroll[0], self.rect.y-scroll[1]))


    def move(self,tiles,dt):
        movement = [0,0]

        movement[0] += self.vel_x * dt * self.game.target_fps
        movement[1] += self.vel_y * dt * self.game.target_fps
        self.vel_y += self.gravity * dt * self.game.target_fps

        if self.vel_y > 7:
            self.vel_y = 7

        if self.burning == False:
            self.collisions = self.physics_obj.movement(movement, tiles)
            self.rect = self.physics_obj.rect
            self.x = self.rect.x
            self.y = self.rect.y

        if self.collisions["bottom"] == True:
            self.vel_x = (self.vel_x*0.5)
            self.burning = True
            flame_count = random.randint(6,12)
            for i in range(flame_count):
                x = self.rect.x + random.randint(self.burn_distance[0], self.burn_distance[1])
                y = self.rect.bottom - 11
                if len(self.flames) < flame_count:
                    self.flames.append(pygame.Rect(x, y, 9, 11))
        
        if self.collisions["right"] == True or self.collisions["left"] == True:
            self.vel_x = -self.vel_x
        
        if self.collisions['top'] == True:
            self.vel_y = 1

        if self.burning == True:
            self.burn_lifetime -= 1*dt*self.game.target_fps
            if self.burn_lifetime <= 0:
                self.burning = False
                self.burned = True


class SmokeGrenade(Throwable):
    def __init__(self, game, x, y, vel, angle):
        super().__init__(game, x, y-8, 5, 5, vel)

        self.image = pygame.image.load("data/images/weapons/SmokeGrenade.png").convert()
        self.image.set_colorkey((255,255,255))

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect.width = self.width
        self.rect.height = self.height
        self.physics_obj.rect.width = self.width
        self.physics_obj.rect.height = self.height

        self.angle = angle
        self.vel_y = math.sin(self.angle)*self.vel
        self.gravity = 0.3
        self.vel_x = math.cos(self.angle)*self.vel
        self.particles = []
        self.timer = scripts.Timer(1000)
        self.timer.make_var_false()
        self.timer.set_time()
        self.exploded = False
        self.smoke_lifetime = scripts.Timer(6500)
        self.done_smoking = False
    
    def draw(self, surf, scroll):
        if self.exploded == True:

            for i in range(3):
                self.particles.append(scripts.Particle(self.rect.x+random.randint(-40,40), self.rect.y-5, random.randint(30,40),"square", random.choice([(190,190,190), (180,180,180), (140,140,140), (210,210,210)]),[random.randint(0,6)-4, random.randint(-9,-6)+3],size_decrease=0.46, grav=-0.2))

            n = 0
            p_remove_list = []
            for p in self.particles:
                p.render(surf, scroll)
                if p.size <= 0:
                    p_remove_list.append(n)
                
                n += 1
            p_remove_list.sort(reverse=True)
            for p in p_remove_list:
                try:
                    p_remove_list.pop(p)
                except:
                    pass

            surf.blit(self.image, (self.rect.x-scroll[0], self.rect.y-scroll[1]))

        else:
            surf.blit(self.image, (self.rect.x-scroll[0], self.rect.y-scroll[1]))
    
    def move(self, tiles, dt):
        movement = [0,0]

        movement[0] += self.vel_x * dt * self.game.target_fps
        movement[1] += self.vel_y * dt * self.game.target_fps
        self.vel_y += self.gravity * dt * self.game.target_fps

        if self.vel_y > 7:
            self.vel_y = 7

        self.collisions = self.physics_obj.movement(movement, tiles)
        self.rect = self.physics_obj.rect
        self.x = self.rect.x
        self.y = self.rect.y
        
        if self.collisions["bottom"] == True:
            self.vel_x = (self.vel_x*0.5)
            self.vel_y = -(self.vel_y*0.3)

        if self.collisions["right"] == True or self.collisions["left"] == True:
            self.vel_x = -self.vel_x
        
        if self.collisions['top'] == True:
            self.vel_y = 1

        self.timer.update()
        if self.timer.get_var() == True:
            if self.exploded == False:
                self.exploded = True
        
        if self.exploded == True:
            if self.smoke_lifetime.get_var() == True:
                self.smoke_lifetime.make_var_false()
                self.smoke_lifetime.set_time()

            self.smoke_lifetime.update()
            self.done_smoking = self.smoke_lifetime.get_var()
        

class FlashBang(Throwable):
    def __init__(self, game, x, y, vel, angle):
        super().__init__(game, x, y-8, 5, 5, vel)

        self.image = pygame.image.load("data/images/weapons/FlashBang.png").convert()
        self.image.set_colorkey((255,255,255))

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect.width = self.width
        self.rect.height = self.height
        self.physics_obj.rect.width = self.width
        self.physics_obj.rect.height = self.height

        self.angle = angle
        self.vel_y = math.sin(self.angle)*self.vel
        self.gravity = 0.3
        self.vel_x = math.cos(self.angle)*self.vel
        self.timer = scripts.Timer(1000)
        self.timer.make_var_false()
        self.timer.set_time()
        self.exploded = False
        self.raduis = 100
        self.surf = pygame.Surface(self.game.game.display.get_size())
        self.surf.fill((255,255,255))
        self.surf.set_alpha(255)
    
    def draw(self, surf, scroll):
        if self.exploded == True:
            pass
        else:
            surf.blit(self.image, (self.rect.x-scroll[0], self.rect.y-scroll[1]))
    
    def move(self, tiles, dt):
        movement = [0,0]

        movement[0] += self.vel_x * dt * self.game.target_fps
        movement[1] += self.vel_y * dt * self.game.target_fps
        self.vel_y += self.gravity * dt * self.game.target_fps

        if self.vel_y > 7:
            self.vel_y = 7

        if self.exploded != True:
            self.collisions = self.physics_obj.movement(movement, tiles)
            self.rect = self.physics_obj.rect
            self.x = self.rect.x
            self.y = self.rect.y
        
        if self.collisions["bottom"] == True:
            self.vel_x = (self.vel_x*0.5)
            self.vel_y = -(self.vel_y*0.3)

        if self.collisions["right"] == True or self.collisions["left"] == True:
            self.vel_x = -self.vel_x
        
        if self.collisions['top'] == True:
            self.vel_y = 1

        self.timer.update()
        if self.timer.get_var() == True:
            if self.exploded == False:
                self.exploded = True
        
        if self.exploded == True:
            surf_opacity = round(self.surf.get_alpha()-(1))
            self.surf.set_alpha(surf_opacity)