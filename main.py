# 3rd party modules
import pygame
import tcod as libtcodpy

# game files
import constants


def draw_game():
    global SURFACE_MAIN
    # TODO clear the surface

    # TODO draw the map

    # TODO draw the character


def game_main_loop():
    '''In this function we loop the main game'''
    game_quit = False

    while not game_quit:

        # get player input
        event_list = pygame.event.get()

        # TODO process input
        for event in event_list:
            if event.type == pygame.QUIT:
                game_quit = True

        # TODO draw the game

    pygame.quit()
    exit()


def game_initialize():
    '''This function initializes the main window, and pygame'''

    global SURFACE_MAIN
    # initialize pygame
    pygame.init()

    SURFACE_MAIN = pygame.display.set_mode(
        (constants.GAME_WIDTH, constants.GAME_HEIGHT))


if __name__ == '__main__':
    game_initialize()
    game_main_loop()
