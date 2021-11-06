#Weapons.py
#Holds all gun stuff
import pygame
from . import *
import math,random

class Bullet:
    def __init__(self,x,y,speed,angle,color,dmg,owner,mult,lifetime,img=None):
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.color = color
        self.dmg = dmg
        self.owner = owner
        self.mult = mult
        self.lifetime = lifetime
        self.img = img
        if self.img != None:
            self.rect = pygame.Rect(self.x,self.y,self.img.get_width(),self.img.get_height())
        else:
            self.rect = pygame.Rect(self.x,self.y,5,5)

    def run(self,surf,scroll,rects=None):
        self.x += math.cos(self.angle)*self.speed
        self.y += math.sin(self.angle)*self.speed
        self.lifetime -= 1
        if self.img != None:
            blit_center(surf,pygame.transform.rotate(self.img,-self.angle),[self.rect.x-scroll[0],self.rect.y-scroll[1]])
        else:
            pygame.draw.line(surf,self.color,(self.x-scroll[0],self.y-scroll[1]),(self.x+math.cos(self.angle)*self.mult[0]-scroll[0],
                                                                                    self.y+math.sin(self.angle)*self.mult[0]-scroll[1]),self.mult[1])
        self.rect.x,self.rect.y = self.x,self.y

        if rects != None:
            for rect in rects:
                if rect.colliderect(self.rect):
                    return "Collided"


class Gun:
    def __init__(self,gun,gun_info,FPS,is_shotgun=False):
        self.gun_info = gun_info
        self.gun = gun
        self.FPS = FPS
        self.gun_img = pygame.image.load(self.gun_info["image"]).convert()
        self.gun_img.set_colorkey((255,255,255))
        self.ammo = gun_info["ammo"]
        self.ammo_l = gun_info["ammo_loaded"]
        self.speed = gun_info["speed"]
        self.ammo -= self.ammo_l
        self.dmg = gun_info["damage"]
        self.crit_rate = gun_info["crit_rate"]
        self.shot = False
        self.reload_gun = False
        self.has_ammo = True
        self.flip = True
        self.is_shotgun = is_shotgun
        self.crit_dmg = gun_info["crit_dmg"]
        self.render_offset = gun_info["render_offset"]
        self.bullet_size = gun_info["bullet_size"]
        self.pause = gun_info["pause"]*FPS
        self.reload_time = gun_info["reload_time"]*FPS
        if self.gun_info["bullet_image"] != None:
            self.bullet_img = self.load_bullet_img(self.gun_info["bullet_image"])
        else:
            self.bullet_img = None

    def shoot(self,bullet_list,owner,pos,angle):
        if self.is_shotgun != True:
            if self.shot == False and self.reload_gun == False and self.has_ammo == True:
                dmg = random.randint(self.dmg[0],self.dmg[1])
                if random.randint(1,100) <= self.crit_rate:
                    dmg = random.randint(self.crit_dmg[0],self.crit_dmg[1])
                
                bullet_list.append(Bullet(pos[0],pos[1],self.speed,angle,(239,222,7),dmg,owner,self.bullet_size,self.gun_info["b_lifetime"],self.bullet_img))
                self.ammo_l -= 1
                self.shot = True

            if self.shot == True and self.has_ammo == True:
                self.pause -= 1
                if self.pause <= 0:
                    self.pause = self.gun_info["pause"]*self.FPS
                    self.shot = False
        else:
            if self.shot == False and self.reload_gun == False and self.has_ammo == True:
                for i in range(10):
                    dmg = random.randint(self.dmg[0],self.dmg[1])
                    if random.randint(1,100) <= self.crit_rate:
                        dmg = random.randint(self.crit_dmg[0],self.crit_dmg[1])
                    
                    bullet_list.append(Bullet(pos[0],pos[1],self.speed,angle+random.uniform(-0.2,0.2),(239,222,7),dmg,owner,self.bullet_size,self.gun_info["b_lifetime"],self.bullet_img))
                    
                self.ammo_l -= 1
                self.shot = True

            if self.shot == True and self.has_ammo == True:
                self.pause -= 1
                if self.pause <= 0:
                    self.pause = self.gun_info["pause"]*self.FPS
                    self.shot = False

    def render(self,surf,scroll,pos,angle):
        blit_center(surf,pygame.transform.rotate(pygame.transform.flip(self.gun_img, False, self.flip),angle),[(pos[0]+self.render_offset[0])-scroll[0],(pos[1]+self.render_offset[1])-scroll[1]])

    def load_bullet_img(name):
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

    def update(self,surf,scroll,pos,angle):
        self.render(surf,scroll,pos,angle)
        if self.ammo <= 0 and self.ammo_l == 0:
            self.has_ammo = False
        
        if self.ammo_l <= 0 and self.has_ammo == True:
            self.reload_gun = True

        if self.reload_gun == True and self.has_ammo == True:
            self.reload_time -= 1
            if self.reload_time <= 0:
                self.reload()
        