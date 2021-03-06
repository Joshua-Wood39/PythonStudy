import tcod as libtcodpy
import pygame
pygame.init()
pygame.font.init()


# Game Sizes
CAMERA_WIDTH = 800
CAMERA_HEIGHT = 600
CELL_WIDTH = 32
CELL_HEIGHT = 32

# FPS
GAME_FPS = 60

# Map Limitations
MAP_WIDTH = 100
MAP_HEIGHT = 100
MAP_MAX_NUM_ROOMS = 10
MAP_NUM_LEVELS = 1

# Room Limitations
ROOM_MAX_WIDTH = 5
ROOM_MAX_HEIGHT = 7
ROOM_MIN_WIDTH = 3
ROOM_MIN_HEIGHT = 3

# Color Definitions
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (100, 100, 100)
COLOR_D_GREY = (50, 50, 50)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)

# Game Colors
COLOR_DEFAULT_BG = COLOR_GREY


# FOV Settings
FOV_ALGO = libtcodpy.FOV_BASIC
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10


# Message Defaults
NUM_MESSAGES = 4


# Fonts
FONT_TITLE_SCREEN = pygame.font.SysFont("comicsans", 50)
FONT_DEBUG_MESSAGE = pygame.font.SysFont("comicsans", 36)
FONT_MESSAGE_TEXT = pygame.font.SysFont("comicsans", 30)
FONT_CURSOR_TEXT = pygame.font.SysFont("comicsans", CELL_HEIGHT)

# Depth
DEPTH_PLAYER = -100
DEPTH_ENEMY = 1
DEPTH_ITEM = 2
DEPTH_CORPSE = 3
