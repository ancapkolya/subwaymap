import random
import numpy as np
import datetime
import pygame


# Constants
COLOR_CONST = {
    '1-2': '#53991b',
    '3-5': '#5ecc04',
    '6-8': '#a6ff02',
    '9-11': '#d9ff02',
    '12-13': '#fff202',
    '14-16': '#ffb302',
    '17-19': '#ff7402',
    '20-100': '#ff1302',
    '101-10000': '#000000'
}

CELL_SIZE = 10


# Functions
def get_color(c):
    for i in COLOR_CONST:
        a, b = [int(j) for j in i.split('-')]
        if a <= c <= b:
            return COLOR_CONST[i]


# Geometry functions
get_length = lambda x, y, x1, y1: ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5


# Classes
class Map:
    def __init__(self, matrix=None, centers=None):
        if matrix is not None and centers is not None:
            self.map = np.array(matrix)
            self.centers = np.array(centers)
        else:
            self.map = np.random.randint(1, 5, (150, 75))
            self.centers = np.hstack([np.random.randint(6, 9, (50)), np.random.randint(10, 20, (10))])
            self.create_attractions(self.centers[0:9])
            self.create_attractions(self.centers[10:])

    def create_attractions(self, strength_array):
        for strength in strength_array:
            x = random.randint(15, 135)
            y = random.randint(15, 60)
            fragment_size = random.randint(8, 15)

            self.map[x, y] = strength

            max_diagonal = get_length(0, 0, fragment_size, fragment_size)
            start_x, start_y = x - fragment_size, y - fragment_size
            
            for k in range(start_y, start_y + fragment_size * 2):
                for m in range(start_x, start_x + fragment_size * 2):
                    self.map[m, k] += int(strength * abs((get_length(x, y, m, k) / max_diagonal) - 1) * random.randint(1, 10) / 10)

    def draw_map(self, surface, start_x=0, start_y=0):
        for i in range(self.map.shape[1]):
            for j in range(self.map.shape[0]):
                pygame.draw.rect(surface, get_color(self.map[j, i]),(j * CELL_SIZE + start_x, i * CELL_SIZE + start_y, (j + 1) * CELL_SIZE, (i + 1) * CELL_SIZE))


if __name__ == '__main__':
    import pygame

    pygame.init()
    size = width, height = 1500, 750
    screen = pygame.display.set_mode(size)
    running = True
    screen.fill('white')

    map = Map()

    def get_color(c):
        for i in COLOR_CONST:
            a, b = [int(j) for j in i.split('-')]
            if a <= c <= b:
                return COLOR_CONST[i]


    for i in range(map.map.shape[1]):
        for j in range(map.map.shape[0]):
            pygame.draw.rect(screen, get_color(map.map[j, i]), (j * CELL_SIZE, i * CELL_SIZE, (j + 1) * CELL_SIZE, (i + 1) * CELL_SIZE))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        pygame.display.flip()
    pygame.quit()