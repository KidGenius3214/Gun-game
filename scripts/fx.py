import pygame
from scripts.Engine import *

def advance(pos, angle, amt):
    pos[0] += math.cos(angle) * amt
    pos[1] += math.sin(angle) * amt
    return pos

class Arc:
    def __init__(self, spacing, start_angle, speed, curve_rate, scale):
        self.start_angle = start_angle
        self.speed = speed
        self.curve_rate = curve_rate
        self.scale = scale
        self.time = 0
        self.spacing = spacing
        self.width = 0.2
        self.max_width = 0
        self.max_height = 0

    def get_angle_points(self, t, curve_rate):
        p = advance([0,0], self.start_angle + (0.5 - t) * math.pi * 4 * self.width, self.spacing)
        p = advance(p, self.start_angle, (0.5 ** 2 - abs(0.5 - t) ** 2) * self.spacing * curve_rate)
        return p

    def calculate_points(self, start, end, curve_rate):
        base_point = advance([0,0], self.start_angle, self.spacing)
        point_count = 20
        arc_points = [self.get_angle_points(start + (i / point_count) * (end - start), curve_rate) for i in range(point_count + 1)]
        arc_points = [[p[0] * self.scale, p[1] * self.scale] for p in arc_points]
        return arc_points

    def update(self):
        self.time += 10
        self.time = self.time % 200

    def render(self, surf, pos, color):
        start = max(0,  min(1, self.time / 20 - 2))
        end = max(0, min(1, self.time / 20))
        points = self.calculate_points(start, end, self.curve_rate + self.time / 5) + self.calculate_points(start, end, (self.curve_rate * 0.5 + self.time / 3) * 0.4)[::-1]
        points = [[p[0] + pos[0], p[1] + pos[1]] for p in points]
        pygame.draw.polygon(surf, color, points)