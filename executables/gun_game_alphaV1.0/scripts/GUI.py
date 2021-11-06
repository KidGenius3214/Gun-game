#Gui file
import pygame
from.Engine import *
pygame.init()

buttons_image = pygame.image.load("data/images/buttons.png")

class Button:
    def __init__(self,x,y,font_size,text,btn_size,btn_type,hover=False):
        self.x = x
        self.y = y
        self.clicked = False
        self.hover = hover
        self.text = text
        self.font = Text("data/images/font.png", 1,font_size)
        self.disabled = False
        self.btn_size = btn_size
        self.btn_type = btn_type
        if self.btn_type == 'Big':
            self.normal = get_image(buttons_image,0,0,34,12,btn_size)
            self.hovered = get_image(buttons_image,34,0,34,12,btn_size)
        if self.btn_type == 'small':
            self.normal = get_image(buttons_image,68,0,28,12,btn_size)
            self.hovered = get_image(buttons_image,96,0,28,12,btn_size)
        self.image = self.normal
        self.rect = pygame.Rect(self.x,self.y,self.image.get_width(), self.image.get_height())

    def update(self,surf,pos,scroll=None):
        if self.rect.collidepoint(pos) and self.disabled == False:
            if self.hover == True:
                self.image = self.hovered
            if pygame.mouse.get_pressed()[0]:
                self.clicked = True
            else:
                self.clicked = False
        else:
            self.image = self.normal
            self.clicked = False

        if self.disabled == True:
            self.normal = get_image(buttons_image,0,12,34,12,self.btn_size)

        surf.blit(self.image, (self.rect.x, self.rect.y))
        size = self.font.get_size(self.text)
        if self.btn_type == 'Big':
            text_pos = [(self.rect.x+int(self.rect.width/2))-int(size[0]/2)+3, (self.rect.y+int(self.rect.height/2))-int(size[1]/2)]
        else:
            text_pos = [(self.rect.x+int(self.rect.width/2))-int(size[0]/2), (self.rect.y+int(self.rect.height/2))-int(size[1]/2)]
        self.font.render(surf, self.text, text_pos[0], text_pos[1], (255,255,255))


class Text_Input:
    def __init__(self,x,y,font_scale,spacing,text_limit):
        self.x = x
        self.y = y
        self.font = Text("data/images/font.png", spacing, font_scale)
        height = self.font.get_size("TEXT")[1]+4
        self.rect = pygame.Rect(self.x,self.y, 56, height) #the rect width can be adjusted
        self.text = ""
        self.text_limit = text_limit
        self.text_index = -1
        self.backspace = False
        self.selected =  False
        self.backspace_tick = 20
        self.clicked = False
        self.click_tick = 20
        self.removed = False
        self.removed_tick = 90

    def get_event(self,event):
        if self.selected == True:
            if event.type == pygame.KEYDOWN:
                if len(self.text) < self.text_limit:
                    self.text += event.unicode
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-2]
                    self.backspace = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    self.backspace = False

    def update(self,surf,pos):
        if self.font.get_size(self.text)[0] > 56+4:
            self.rect.width = self.font.get_size(self.text)[0] + 8
        else:
            self.rect.width = 56

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == True and self.clicked == False:
                self.selected = True
                self.clicked = True
        if self.rect.collidepoint(pos) == False:
            if pygame.mouse.get_pressed()[0] == True and self.clicked == False:
                self.selected = False
                self.clicked = True

        if self.backspace == True:
            self.backspace_tick -= 1
            if self.backspace_tick < 0 and self.removed == False:
                self.text = self.text[:-2]
                self.removed = True
        else:
            self.backspace_tick = 20
        
        if self.selected == False:
            pygame.draw.rect(surf,(50,50,50), self.rect, 1)
        else:
            pygame.draw.rect(surf,(160,160,160), self.rect, 1)

        self.font.render(surf, self.text, self.rect.x+4, self.rect.y+2, (255,255,255))

        if self.clicked == True:
            self.click_tick -= 1
            if self.click_tick < 0:
                self.click_tick = 20
                self.clicked = False

        if self.removed == True:
            self.removed_tick -= 1
            if self.removed_tick < 0:
                self.removed_tick = 90
                self.removed = False

        
