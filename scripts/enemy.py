import pygame
import scripts
import math


class Base_Enemy(scripts.Entity):
    def __init__(self,game,x,y,width,height,health,vel,jump,gravity,gravity_limit=6):
        super().__init__(x,y,width,height,vel,jump)

        self.game = game
        self.id = "Base_Enemy"
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

class Bad_Guy(Base_Enemy):
    def __init__(self,game,x,y,width,height,health,vel,jump,gravity,gravity_limit=6):
        super().__init__(game,x,y,width,height,health,vel,jump,gravity)

        self.vision = pygame.Rect(self.rect.x,self.rect.y,120,10)
        self.id = "Bad_Guy"
        
        #wall jump stuff
        self.wall_jump_true = False
        self.on_wall = False
        self.stick_on_wall = False
        self.stick_tick = 6
        self.jump_direction = 1
        self.wall_jump_tick = 7
        self.wall_jump_count = 0
        
        #gun stuff
        self.gun = None
        self.angle_to_target = 0

    def handle_ai(self,tiles,target,scroll):
        movement = [0,0]
        if self.right == True:
            movement[0] += self.vel
        if self.left == True:
            movement[0] += self.vel
        movement[1] += self.vel_y
        self.vel_y += self.gravity
        if self.vel_y > self.g_limit:
            self.vel_y = self.g_limit

        self.angle_to_target = scripts.find_angle_from_points(target.get_center(), self.get_center(), [0,0], [0,0], False)

        self.collisions = self.physics_obj.movement(movement,tiles)
        self.rect = self.physics_obj.rect
        self.x,self.y = self.rect.x,self.rect.y

        if self.collisions["bottom"] == True:
            self.vel_y = 1

    def shoot(self):
        pass

    def give_gun(self,gun): # util function so I can give the object a gun
        self.gun = gun
