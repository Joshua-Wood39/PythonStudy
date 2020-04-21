import pygame
import tcod as libtcodpy

pygame.init()

# Game Sizes
GAME_WIDTH = 800
GAME_HEIGHT = 600
CELL_WIDTH = 32
CELL_HEIGHT = 32

# Map Vars
MAP_WIDTH = 30
MAP_HEIGHT = 30

# Color Definitions
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (100, 100, 100)

# Game Colors
COLOR_DEFAULT_BG = COLOR_GREY

# Sprites
S_PLAYER = pygame.image.load("assets/Python.png")
S_ENEMY = pygame.image.load("assets/Crab.png")
S_WALL = pygame.image.load("assets/Wall2.jpg")
S_FLOOR = pygame.image.load("assets/Floor.jpg")
S_FLOOREXPLORED = pygame.image.load("assets/FloorUnseen.png")
S_WALLEXPLORED = pygame.image.load("assets/WallUnseen.png")

# FOV Settings
FOV_ALGO = libtcodpy.FOV_BASIC
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10
