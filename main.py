# 3rd party modules
import pygame
import tcod as libtcodpy

# game files
import constants


# STRUCT

class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path


# OBJECTS

class obj_Actor:
    def __init__(self, x, y, name_object, sprite, creature=None, ai=None):
        self.x = x  # map addresses
        self.y = y
        self.sprite = sprite

        self.creature = creature
        if creature:
            creature.owner = self

        self.ai = ai
        if ai:
            ai.owner = self

    def draw(self):
        SURFACE_MAIN.blit(
            self.sprite, (self.x * constants.CELL_WIDTH, self.y * constants.CELL_HEIGHT))


# COMPONENTS

class com_Creature:
    '''Creatures have health, can damage other objects by attacking, and can die'''

    def __init__(self, name_instance, hp=10, death_function=None):
        self.name_instance = name_instance
        self.hp = hp
        self.maxhp = hp
        self.death_function = death_function

    def move(self, dx, dy):

        tile_is_wall = (GAME_MAP[self.owner.x + dx]
                        [self.owner.y + dy].block_path == True)
        target = map_check_for_creatures(
            self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            self.attack(target, 3)

        if not tile_is_wall:
            self.owner.x += dx
            self.owner.y += dy

    def attack(self, target, damage):
        print(self.name_instance + " attacks " +
              target.creature.name_instance + " for " + str(damage) + " damage!")
        target.creature.take_damage(damage)

    def take_damage(self, damage):
        self.hp -= damage
        print(self.name_instance + "'s health is " +
              str(self.hp) + "/" + str(self.maxhp))

        if self.hp <= 0:

            if self.death_function is not None:
                self.death_function(self.owner)

# TODO class com_Item:


# TODO class com_Container:

    # MAP


# AI

class ai_Test:
    '''Once per turn, execute'''

    def take_turn(self):
        self.owner.creature.move(libtcodpy.random_get_int(0, -1, 1),
                                 libtcodpy.random_get_int(0, -1, 1))


def death_monster(monster):
    '''On death, most monsters stop moving'''

    print(monster.creature.name_instance + " is dead!")
    monster.creature = None
    monster.ai = None

# MAP


def map_create():
    new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)]
               for x in range(0, constants.MAP_WIDTH)]

    new_map[10][10].block_path = True
    new_map[10][15].block_path = True

    for x in range(constants.MAP_WIDTH):
        new_map[x][0].block_path = True
        new_map[x][constants.MAP_HEIGHT - 1].block_path = True

    for y in range(constants.MAP_HEIGHT):
        new_map[0][y].block_path = True
        new_map[constants.MAP_WIDTH - 1][y].block_path = True

    return new_map


def map_check_for_creatures(x, y, exclude_object=None):

    target = None

    if exclude_object:
        # check object list to find creature at location that isn't excluded
        for object in GAME_OBJECTS:
            if (object is not exclude_object and object.x == x and object.y == y and object.creature):
                target = object

            if target:
                return target

    else:
        # check object list to find any creature at that location
        for object in GAME_OBJECTS:
            if(object.x == x and object.y == y and object.creature):
                target = object

            if target:
                return target

# DRAWING


def draw_game():
    global SURFACE_MAIN

    # clear the surface
    SURFACE_MAIN.fill(constants.COLOR_DEFAULT_BG)

    # draw the map
    draw_map(GAME_MAP)

    # draw all objects
    for obj in GAME_OBJECTS:
        obj.draw()

    # update the display
    pygame.display.flip()


def draw_map(map_to_draw):
    for x in range(0, constants.MAP_WIDTH):
        for y in range(0, constants.MAP_HEIGHT):
            if map_to_draw[x][y].block_path == True:
                # draw wall
                SURFACE_MAIN.blit(
                    constants.S_WALL, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
            else:
                # draw floor
                SURFACE_MAIN.blit(
                    constants.S_FLOOR, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))


# GAME

def game_main_loop():
    '''In this function we loop the main game'''
    game_quit = False

    # player action definition
    player_action = "no-action"

    while not game_quit:

        # handle player input
        player_action = game_handle_keys()

        if player_action == "QUIT":
            game_quit = True

        elif player_action != "no-action":
            for obj in GAME_OBJECTS:
                if obj.ai:
                    obj.ai.take_turn()

        # draw the game
        draw_game()

    pygame.quit()
    exit()


def game_initialize():
    '''This function initializes the main window, and pygame'''

    global SURFACE_MAIN, GAME_MAP, PLAYER, ENEMY, GAME_OBJECTS
    # initialize pygame
    pygame.init()

    SURFACE_MAIN = pygame.display.set_mode(
        (constants.MAP_WIDTH * constants.CELL_WIDTH, constants.MAP_HEIGHT * constants.CELL_HEIGHT))

    GAME_MAP = map_create()

    creature_com1 = com_Creature("greg")
    PLAYER = obj_Actor(1, 1, "python", constants.S_PLAYER, creature_com1)

    creature_com2 = com_Creature("jackie", death_function=death_monster)
    ai_com = ai_Test()
    ENEMY = obj_Actor(10, 13, "crab", constants.S_ENEMY,
                      creature_com2, ai_com)

    GAME_OBJECTS = [PLAYER, ENEMY]


def game_handle_keys():
    # get player input
    event_list = pygame.event.get()

    # process input
    for event in event_list:
        if event.type == pygame.QUIT:
            return "QUIT"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                PLAYER.creature.move(0, -1)
                return "player-moved"
            if event.key == pygame.K_DOWN:
                PLAYER.creature.move(0, 1)
                return "player-moved"
            if event.key == pygame.K_LEFT:
                PLAYER.creature.move(-1, 0)
                return "player-moved"
            if event.key == pygame.K_RIGHT:
                PLAYER.creature.move(1, 0)
                return "player-moved"

    return "no-action"


if __name__ == '__main__':
    game_initialize()
    game_main_loop()
