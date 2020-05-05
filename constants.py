import tcod as libtcodpy
import pygame
pygame.init()
pygame.font.init()


# Game Sizes
GAME_WIDTH = 800
GAME_HEIGHT = 600
CELL_WIDTH = 32
CELL_HEIGHT = 32

# FPS
GAME_FPS = 60

# Map Limitations
MAP_WIDTH = 30
MAP_HEIGHT = 30
MAP_MAX_NUM_ROOMS = 10

# Room Limitations
ROOM_MAX_WIDTH = 5
ROOM_MAX_HEIGHT = 7
ROOM_MIN_WIDTH = 3
ROOM_MIN_HEIGHT = 3

# Color Definitions
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (100, 100, 100)
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
FONT_DEBUG_MESSAGE = pygame.font.SysFont("comicsans", 36)
FONT_MESSAGE_TEXT = pygame.font.SysFont("comicsans", 30)
FONT_CURSOR_TEXT = pygame.font.SysFont("comicsans", CELL_HEIGHT)
