import pygame
import scripts


class EntityManager:
    def __init__(self,game):
        self.game = game
        self.entities = []
        self.bullets = []
        self.items = []

    def add_entity(self,entity):
        self.entities.append(entity)

    def add_bullet(self,bullet):
        self.bullets.append(bullet)
    
    def add_item(self,item):
        self.items.append(item)
    
    def draw_all(self,surf,scroll,dt,active_chunks):
        self.draw_items(surf,scroll,dt,active_chunks)
        self.draw_bullets(surf,scroll,dt)

    def draw_items(self,surf,scroll,dt,active_chunks):
        for item in self.items:
            x = int(int(item.rect.x/self.game.TILESIZE)/self.game.CHUNKSIZE)
            y = int(int(item.rect.y/self.game.TILESIZE)/self.game.CHUNKSIZE)
            chunk_str = f"{x}/{y}"
            if chunk_str in active_chunks:
                item.pickup_cooldown -= 1
                if item.pickup_cooldown < 0:
                    item.pickup_cooldown = 0
                item.render(surf,scroll)
    
    def draw_bullets(self,surf,scroll,dt):
        for bullet in self.bullets:
            bullet.run(surf,scroll, dt)
            if bullet.lifetime <= 0:
                b_remove_list.append(n)
    
    def draw_entites(self,surf,scroll):
        pass
    
    def update_all(self,tiles):
        pass
    
    def update_items(self,tiles):
        pass
    
    def update_entities(self,tiles):
        pass
    
    def update_bullets(self,tiles):
        pass