# 3rd party modules
import constants
import pygame
import tcod as libtcodpy


# game files


#  _______ _________ _______           _______ _________
# (  ____ \\__   __/(  ____ )|\     /|(  ____ \\__   __/
# | (    \/   ) (   | (    )|| )   ( || (    \/   ) (
# | (_____    | |   | (____)|| |   | || |         | |
# (_____  )   | |   |     __)| |   | || |         | |
#       ) |   | |   | (\ (   | |   | || |         | |
# /\____) |   | |   | ) \ \__| (___) || (____/\   | |
# \_______)   )_(   |/   \__/(_______)(_______/   )_(

class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False


class struc_Assets:
    def __init__(self):
        ## SPRITESHEETS ##
        self.charspritesheet = obj_Spritesheet("assets/Reptiles.png")
        self.enemyspritesheet = obj_Spritesheet("assets/Aquatic.png")

        ## ANIMATIONS ##
        self.A_PLAYER = self.charspritesheet.get_animation(
            'o', 5, 16, 16, 2, (32, 32))
        self.A_ENEMY = self.enemyspritesheet.get_animation(
            'k', 1, 16, 16, 2, (32, 32))

        ## SPRITES ##
        self.S_WALL = pygame.image.load("assets/Wall2.jpg")
        self.S_FLOOR = pygame.image.load("assets/Floor.jpg")
        self.S_FLOOREXPLORED = pygame.image.load("assets/FloorUnseen.png")
        self.S_WALLEXPLORED = pygame.image.load("assets/WallUnseen.png")

        ## FONTS ##
        self.FONT_DEBUG_MESSAGE = pygame.font.SysFont("comicsans", 36)
        self.FONT_MESSAGE_TEXT = pygame.font.SysFont("comicsans", 30)


#  _______  ______  _________ _______  _______ _________ _______
# (  ___  )(  ___ \ \__    _/(  ____ \(  ____ \\__   __/(  ____ \
# | (   ) || (   ) )   )  (  | (    \/| (    \/   ) (   | (    \/
# | |   | || (__/ /    |  |  | (__    | |         | |   | (_____
# | |   | ||  __ (     |  |  |  __)   | |         | |   (_____  )
# | |   | || (  \ \    |  |  | (      | |         | |         ) |
# | (___) || )___) )|\_)  )  | (____/\| (____/\   | |   /\____) |
# (_______)|/ \___/ (____/   (_______/(_______/   )_(   \_______)


class obj_Actor:
    def __init__(self, x, y, name_object, animation, animation_speed=.5, creature=None, ai=None, container=None):
        self.x = x  # map addresses
        self.y = y
        self.animation = animation  # list of images
        self.animation_speed = animation_speed / 1.0  # in seconds

        # animation flicker speed
        self.flicker_speed = self.animation_speed / len(self.animation)
        self.flicker_timer = 0.0
        self.sprite_image = 0

        self.creature = creature
        if self.creature:
            self.creature.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.container = container
        if self.container:
            self.container.owner = self

    def draw(self):
        is_visible = libtcodpy.map_is_in_fov(FOV_MAP, self.x, self.y)

        if is_visible:
            if len(self.animation) == 1:
                SURFACE_MAIN.blit(
                    self.animation[0], (self.x * constants.CELL_WIDTH, self.y * constants.CELL_HEIGHT))

            elif len(self.animation) > 1:
                if CLOCK.get_fps() > 0.0:
                    self.flicker_timer += 1 / CLOCK.get_fps()

                if self.flicker_timer >= self.flicker_speed:
                    self.flicker_timer = 0.0

                    if self.sprite_image >= len(self.animation) - 1:
                        self.sprite_image = 0

                    else:
                        self.sprite_image += 1

                SURFACE_MAIN.blit(
                    self.animation[self.sprite_image], (self.x * constants.CELL_WIDTH, self.y * constants.CELL_HEIGHT))


class obj_Game:
    def __init__(self):

        self.current_map = map_create()
        self.current_objects = []

        self.message_history = []


class obj_Spritesheet:
    '''Class used to grab images out of a sprite sheet'''

    def __init__(self, file_name):
        # Load the sprite sheet.
        self.sprite_sheet = pygame.image.load(file_name).convert()
        self.tiledict = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7,
                         'h': 8, 'i': 9, 'j': 10, 'k': 11, 'l': 12, 'm': 13, 'n': 14, 'o': 15, 'p': 16}

    def get_image(self, column, row, width=constants.CELL_WIDTH, height=constants.CELL_HEIGHT, scale=None):
        image_list = []

        image = pygame.Surface([width, height]).convert()

        image.blit(self.sprite_sheet, (0, 0), (
            self.tiledict[column] * width, row * height, width, height))

        image.set_colorkey(constants.COLOR_BLACK)  # addresses transparency

        if scale:
            (new_w, new_h) = scale
            image = pygame.transform.scale(image, (new_w, new_h))

        image_list.append(image)

        return image_list

    def get_animation(self, column, row, width=constants.CELL_WIDTH, height=constants.CELL_HEIGHT, num_sprites=1, scale=None):
        image_list = []

        for i in range(num_sprites):
            # Create blank surface
            image = pygame.Surface([width, height]).convert()

            # Copy image to surface
            image.blit(self.sprite_sheet, (0, 0), (
                self.tiledict[column] * width + (width * i), row * height, width, height))

            # Set transparency key to black
            image.set_colorkey(constants.COLOR_BLACK)

            if scale:
                (new_w, new_h) = scale
                image = pygame.transform.scale(image, (new_w, new_h))

            image_list.append(image)

        return image_list


#  _______  _______  _______  _______  _______  _        _______  _       _________
# (  ____ \(  ___  )(       )(  ____ )(  ___  )( (    /|(  ____ \( (    /|\__   __/
# | (    \/| (   ) || () () || (    )|| (   ) ||  \  ( || (    \/|  \  ( |   ) (
# | |      | |   | || || || || (____)|| |   | ||   \ | || (__    |   \ | |   | |
# | |      | |   | || |(_)| ||  _____)| |   | || (\ \) ||  __)   | (\ \) |   | |
# | |      | |   | || |   | || (      | |   | || | \   || (      | | \   |   | |
# | (____/\| (___) || )   ( || )      | (___) || )  \  || (____/\| )  \  |   | |
# (_______/(_______)|/     \||/       (_______)|/    )_)(_______/|/    )_)   )_(


class com_Creature:
    '''Creatures have health, can damage other objects by attacking, and can die'''

    def __init__(self, name_instance, hp=10, death_function=None):
        self.name_instance = name_instance
        self.hp = hp
        self.maxhp = hp
        self.death_function = death_function

    def move(self, dx, dy):

        tile_is_wall = (GAME.current_map[self.owner.x + dx]
                        [self.owner.y + dy].block_path == True)
        target = map_check_for_creatures(
            self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            self.attack(target, 3)

        if not tile_is_wall:
            self.owner.x += dx
            self.owner.y += dy

    def attack(self, target, damage):
        game_message(self.name_instance + " attacks " +
                     target.creature.name_instance + " for " + str(damage) + " damage!", constants.COLOR_WHITE)
        target.creature.take_damage(damage)

    def take_damage(self, damage):
        self.hp -= damage
        game_message(self.name_instance + "'s health is " +
                     str(self.hp) + "/" + str(self.maxhp), constants.COLOR_RED)

        if self.hp <= 0:

            if self.death_function is not None:
                self.death_function(self.owner)


class com_Container:
    def _init__(self, volume=10.0, inventory=[]):
        self.inventory = inventory
        self.max_volume = volume

    # TODO Get names of everything in inventory

    # TODO Get the volume within container

    # TODO Get the weight of everything in inventory


class com_Item:
    def __init__(self, weight=0.0, volume=0.0):
        self.weight = weight
        self.volume = volume

    # TODO Pick up this item
    def pick_up(self, actor):

        if actor.container:
            if actor.container.volume + self.volume > actor.container.max_volume:
                game_message("Not enough room to pick up!",
                             constants.COLOR_RED)

            else:
                game_message("Picking up", constants.COLOR_GREEN)
                actor.container.inventory.append(self.owner)
                GAME.current_objects.remove(self.owner)
                self.current_container = actor.container

    # TODO Drop this item

    def drop(self):
        GAME.current_objects.append(self.owner)
        self.current_container.inventory.remove(self.owner)
        game_message("Item dropped", constants.COLOR_GREY)

    # TODO Use the item ~ item effect

#  _______ _________
# (  ___  )\__   __/
# | (   ) |   ) (
# | (___) |   | |
# |  ___  |   | |
# | (   ) |   | |
# | )   ( |___) (___
# |/     \|\_______/


class ai_Test:
    '''Once per turn, execute'''

    def take_turn(self):
        self.owner.creature.move(libtcodpy.random_get_int(0, -1, 1),
                                 libtcodpy.random_get_int(0, -1, 1))


def death_monster(monster):
    '''On death, most monsters stop moving'''

    game_message(monster.creature.name_instance +
                 " is dead!", constants.COLOR_GREY)
    monster.creature = None
    monster.ai = None

#  _______  _______  _______
# (       )(  ___  )(  ____ )
# | () () || (   ) || (    )|
# | || || || (___) || (____)|
# | |(_)| ||  ___  ||  _____)
# | |   | || (   ) || (
# | )   ( || )   ( || )
# |/     \||/     \||/


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

    map_make_fov(new_map)

    return new_map


def map_check_for_creatures(x, y, exclude_object=None):

    target = None

    if exclude_object:
        # check object list to find creature at location that isn't excluded
        for object in GAME.current_objects:
            if (object is not exclude_object and object.x == x and object.y == y and object.creature):
                target = object

            if target:
                return target

    else:
        # check object list to find any creature at that location
        for object in GAME.current_objects:
            if(object.x == x and object.y == y and object.creature):
                target = object

            if target:
                return target


def map_make_fov(incoming_map):
    global FOV_MAP

    FOV_MAP = libtcodpy.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    for y in range(constants.MAP_HEIGHT):
        for x in range(constants.MAP_WIDTH):
            libtcodpy.map_set_properties(FOV_MAP, x, y,
                                         not incoming_map[x][y].block_path, not incoming_map[x][y].block_path)


def map_calculate_fov():
    global FOV_CALCULATE

    if FOV_CALCULATE:
        FOV_CALCULATE = False
        libtcodpy.map_compute_fov(
            FOV_MAP, PLAYER.x, PLAYER.y, constants.TORCH_RADIUS, constants.FOV_LIGHT_WALLS, constants.FOV_ALGO)


#  ______   _______  _______
# (  __  \ (  ____ )(  ___  )|\     /|
# | (  \  )| (    )|| (   ) || )   ( |
# | |   ) || (____)|| (___) || | _ | |
# | |   | ||     __)|  ___  || |( )| |
# | |   ) || (\ (   | (   ) || || || |
# | (__/  )| ) \ \__| )   ( || () () |
# (______/ |/   \__/|/     \|(_______)


def draw_game():
    global SURFACE_MAIN

    # clear the surface
    SURFACE_MAIN.fill(constants.COLOR_DEFAULT_BG)

    # draw the map
    draw_map(GAME.current_map)

    # draw all objects
    for obj in GAME.current_objects:
        obj.draw()

    draw_debug()
    draw_messages()

    # update the display
    pygame.display.flip()


def draw_map(map_to_draw):
    for x in range(0, constants.MAP_WIDTH):
        for y in range(0, constants.MAP_HEIGHT):

            is_visible = libtcodpy.map_is_in_fov(FOV_MAP, x, y)

            if is_visible:

                map_to_draw[x][y].explored = True

                if map_to_draw[x][y].block_path == True:
                    # draw wall
                    SURFACE_MAIN.blit(
                        ASSETS.S_WALL, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    # draw floor
                    SURFACE_MAIN.blit(
                        ASSETS.S_FLOOR, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))

            elif map_to_draw[x][y].explored:

                if map_to_draw[x][y].block_path == True:
                    SURFACE_MAIN.blit(
                        ASSETS.S_WALLEXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    SURFACE_MAIN.blit(
                        ASSETS.S_FLOOREXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))


def draw_debug():
    draw_text(SURFACE_MAIN, "fps: " + str(int(CLOCK.get_fps())),
              (0, 0), constants.COLOR_WHITE, constants.COLOR_BLACK)


def draw_messages():

    if len(GAME.message_history) <= constants.NUM_MESSAGES:
        to_draw = GAME.message_history
    else:
        to_draw = GAME.message_history[-constants.NUM_MESSAGES:]

    text_height = helper_text_height(ASSETS.FONT_MESSAGE_TEXT)

    start_y = (constants.MAP_HEIGHT * constants.CELL_HEIGHT -
               (constants.NUM_MESSAGES * text_height)) - 5

    i = 0

    for message, color in to_draw:

        draw_text(SURFACE_MAIN, message, (0, start_y +
                                          (i * text_height)), color, constants.COLOR_BLACK)

        i += 1


def draw_text(display_surface, text_to_display, T_coords, text_color, back_color=None):
    '''This function takes in some text, and displays it on the referenced surface'''

    text_surf, text_rect = helper_text_objects(
        text_to_display, text_color, back_color)

    text_rect.topleft = T_coords

    display_surface.blit(text_surf, text_rect)


#           _______  _        _______  _______  _______
# |\     /|(  ____ \( \      (  ____ )(  ____ \(  ____ )
# | )   ( || (    \/| (      | (    )|| (    \/| (    )|
# | (___) || (__    | |      | (____)|| (__    | (____)|
# |  ___  ||  __)   | |      |  _____)|  __)   |     __)
# | (   ) || (      | |      | (      | (      | (\ (
# | )   ( || (____/\| (____/\| )      | (____/\| ) \ \__
# |/     \|(_______/(_______/|/       (_______/|/   \__/


def helper_text_objects(incoming_text, incoming_color, incoming_bg):
    if incoming_bg:

        Text_surface = ASSETS.FONT_DEBUG_MESSAGE.render(
            incoming_text, False, incoming_color, incoming_bg)

    else:
        Text_surface = ASSETS.FONT_DEBUG_MESSAGE.render(
            incoming_text, False, incoming_color)

    return Text_surface, Text_surface.get_rect()


def helper_text_height(font):

    font_object = font.render('a', False, (0, 0, 0))
    font_rect = font_object.get_rect()
    return font_rect.height


#  _______  _______  _______  _______
# (  ____ \(  ___  )(       )(  ____ \
# | (    \/| (   ) || () () || (    \/
# | |      | (___) || || || || (__
# | | ____ |  ___  || |(_)| ||  __)
# | | \_  )| (   ) || |   | || (
# | (___) || )   ( || )   ( || (____/\
# (_______)|/     \||/     \|(_______/


def game_main_loop():
    '''In this function we loop the main game'''
    game_quit = False

    # player action definition
    player_action = "no-action"

    while not game_quit:

        # handle player input
        player_action = game_handle_keys()

        map_calculate_fov()

        if player_action == "QUIT":
            game_quit = True

        elif player_action != "no-action":
            for obj in GAME.current_objects:
                if obj.ai:
                    obj.ai.take_turn()

        # draw the game
        draw_game()

        CLOCK.tick(constants.GAME_FPS)

    pygame.quit()
    exit()


def game_initialize():
    '''This function initializes the main window, and pygame'''

    global SURFACE_MAIN, GAME, CLOCK, FOV_CALCULATE, PLAYER, ENEMY, ASSETS
    # initialize pygame
    pygame.init()
    pygame.font.init()

    SURFACE_MAIN = pygame.display.set_mode(
        (constants.MAP_WIDTH * constants.CELL_WIDTH, constants.MAP_HEIGHT * constants.CELL_HEIGHT))

    GAME = obj_Game()

    CLOCK = pygame.time.Clock()

    FOV_CALCULATE = True

    ASSETS = struc_Assets()

    creature_com1 = com_Creature("greg")
    PLAYER = obj_Actor(1, 1, "python", ASSETS.A_PLAYER,
                       animation_speed=1, creature=creature_com1)

    creature_com2 = com_Creature("jackie", death_function=death_monster)
    ai_com = ai_Test()
    ENEMY = obj_Actor(10, 13, "crab", ASSETS.A_ENEMY, animation_speed=1,
                      creature=creature_com2, ai=ai_com)

    GAME.current_objects = [PLAYER, ENEMY]


def game_handle_keys():
    global FOV_CALCULATE
    # get player input
    event_list = pygame.event.get()

    # process input
    for event in event_list:
        if event.type == pygame.QUIT:
            return "QUIT"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                PLAYER.creature.move(0, -1)
                FOV_CALCULATE = True
                return "player-moved"
            if event.key == pygame.K_DOWN:
                PLAYER.creature.move(0, 1)
                FOV_CALCULATE = True
                return "player-moved"
            if event.key == pygame.K_LEFT:
                PLAYER.creature.move(-1, 0)
                FOV_CALCULATE = True
                return "player-moved"
            if event.key == pygame.K_RIGHT:
                PLAYER.creature.move(1, 0)
                FOV_CALCULATE = True
                return "player-moved"

    return "no-action"


def game_message(game_msg, msg_color):

    GAME.message_history.append((game_msg, msg_color))


if __name__ == '__main__':
    game_initialize()
    game_main_loop()
