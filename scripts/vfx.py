import pygame
from scripts.Engine import *

class Slash:
    def __init__(self, pos, raduis, start_angle, s_end_angle, end_angle,  slash_rate, curve_rate, spacing, direction, width, width_decrease, duration, color, speed, width_can_shrink = False):
        # Setup Slash effect
        self.pos = pos # position of the slash/arc, which is the center of the circle
        self.size = raduis # how large the circle is
        self.s_angle = start_angle # starting angle to create arc
        self.s_end_angle = s_end_angle # this angle will be changed for the slash animation
        self.end_angle = end_angle # the angle where the arc will end
        self.slash_rate = slash_rate # how much the starting end angle will be changed by
        self.curve_rate = curve_rate # how the arc curves, i am not really sure
        self.spacing = spacing # spacing/jumps between the points on the arc
        self.h_stretch = 1 # how the circle is stretched on the horizontal axis
        self.v_stretch = 1 # how the circle is stretched on the vertical axis
        self.angle = direction # angle where slash will face
        self.width = width # width of the arc
        self.width_decrease = width_decrease # the amount the arc will decrease by
        self.width_can_shrink = width_can_shrink # if the width is allowed to be decreased
        self.duration = Timer(duration) # how long the arc can last
        self.duration.set_time()
        self.duration.make_var_false()
        self.color = color # color of the arc
        self.speed = speed
        # Surface that is going to be used for pixel perfect collision
        self.surface = pygame.Surface((self.size*4, self.size*4)) 

    def create_points(self, h_stretch, v_stretch, scroll):
        points = [] # points list

        for i in range(self.s_angle, self.s_end_angle):

            if i+self.spacing > self.end_angle: #  break out of the loop when the angle is higher than the end angle
                break
            
            # This is to create points that go around in a circle (Well, this math makes a circle)
            x = math.cos(math.radians(i+self.spacing)) * self.size 
            y = math.sin(math.radians(i+self.spacing)) * self.size

            # Create the points
            # Add the position to the (x, y) from above and apply the stretching effect on them
            points.append([self.pos[0] + (x*h_stretch), self.pos[1] + (y*v_stretch)])

        for i in range(len(points)):
            newP = rotate(points[i], self.angle, self.pos, True) # Rotate the points using self.angle
            points[i] = [newP[0]-scroll[0], newP[1]-scroll[1]]
        
        return points

    def still_active(self):
        return self.duration.get_var()

    def render(self, surf, scroll, polygon=False):
        p1 = self.create_points(self.h_stretch, self.v_stretch, scroll)
        w = 0
        for p in p1:
            if p[0] > w:
                w = p[0]
        p2 = self.create_points(self.h_stretch * self.width, self.v_stretch, scroll)
        p3 = (self.create_points(self.h_stretch, self.v_stretch, scroll) + self.create_points(self.h_stretch * self.width, self.v_stretch, scroll)[::-1])

        self.h_stretch += self.curve_rate
        self.pos[0] += math.cos(math.radians(self.angle)) * self.speed
        self.pos[1] += math.sin(math.radians(self.angle)) * self.speed

        self.s_end_angle += self.slash_rate
        if self.s_end_angle == self.end_angle:
            self.s_end_angle = self.end_angle

        if polygon == True:
            pygame.draw.polygon(surf, self.color, p3)
        else:
            pygame.draw.lines(surf, self.color, False, p1)
            pygame.draw.lines(surf, self.color, False, p2)
        
        self.duration.update()


class VFX:
    def __init__(self, game):
        self.game = game
    
    def render_arc(self):
        pass


        