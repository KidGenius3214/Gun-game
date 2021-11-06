#Player Class
import pygame
from pygame.locals import *
pygame.init()

from . import *

class Player(Entity):
    def __init__(self,x,y,w,h,health,vel,jump,gravity):
        super().__init__(x,y,w,h,vel,jump)


        self.health = health
        self.state = "Idle"
        self.gravity = gravity
        self.has_jumped = False
        self.jump_count = 0
        
        #wall_jump_stuff
        self.wall_jump_true = False
        self.on_wall = False
        self.stick_on_wall = False
        self.stick_tick = 6
        self.jump_direction = 1
        self.wall_jump_tick = 7
        self.wall_jump_cooldown = 14

    def movement(self,tiles):
        movement = [0,0]
        if self.left == True:
            movement[0] -= self.vel
        if self.right == True:
            movement[0] += self.vel
        movement[1] += self.vel_y
        self.vel_y += self.gravity
        if self.vel_y > 6:
            self.vel_y = 6

        if self.wall_jump_true == True:
            movement[1] = -4
            movement[0] = 8*self.jump_direction
            self.vel_y = -4

        self.collisions = self.physics_obj.movement(movement,tiles)
        self.rect = self.physics_obj.rect

        self.on_wall = False

        if self.collisions["top"] == True:
            self.vel_y += 1.2

        if self.collisions["right"] == True or self.collisions["left"] == True:
            self.on_wall = True
            self.wall_jump_true = False
            if movement[1] > 0:
                self.vel_y = 1.5
            if self.collisions["right"] == True:
                self.jump_direction = -1
            else:
                self.jump_direction = 1
        else:
            self.on_wall = False
            self.wall_up_time = 4
        
        if self.collisions["bottom"] == True:
            self.vel_y = 1
            self.jump_count = 0

        if self.wall_jump_true == True:
            self.wall_jump_tick -= 1
            if self.wall_jump_tick <= 0:
                self.wall_jump_true = False
                self.wall_jump_tick = 7
            
