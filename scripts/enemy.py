import pygame
import scripts
import math


class Base_Enemy(scripts.Entity):
    def __init__(self,x,y,width,height,health,vel,jump,gravity,gravity_limit=6):
        super().__init__(x,y,width,height,vel,jump)

        self.gravity = gravity
        self.g_limit = gravity_limit

        #Health management
        self.health = health
        self.hurt = False
        self.dmg_timer = 4
        self.alive = self.health > 0

        self.state = "Idle"
        self.action = "Stand"

        self.image.fill((255,0,0))

    def movement(self,tiles):
        movement = [0,0]
        if self.right == True:
            movement[0] += self.vel
        if self.left == True:
            movement[0] += self.vel
        movement[1] += self.vel_y
        self.vel_y += self.gravity
        if self.vel_y > self.g_limit:
            self.vel_y = self.g_limit

        self.collisions = self.physics_obj.movement(movement,tiles)
        self.rect = self.physics_obj.rect
        self.x,self.y = self.rect.x,self.rect.y

        if self.collisions["bottom"] == True:
            self.vel_y = 1

    def damage(self,dealer,amount):
        if self.hurt == False:
            self.health -= amount
            self.hurt = True
            if self.health <= 0:
                self.health = 0
                
    def update(self):
        #update some stuff in the class
        if self.hurt == True:
            self.dmg_timer -= 1
            if self.dmg_timer <= 0:
                self.dmg_timer = 4
                self.hurt = 0

        if self.health <= 0:
            self.alive = False
