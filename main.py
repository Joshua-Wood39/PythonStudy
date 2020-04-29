# 3rd party modules
import constants
import pygame
import tcod as libtcodpy
import math


##############################################################################
# STRUCTURES
##############################################################################


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
        self.A_ENEMY1 = self.enemyspritesheet.get_animation(
            'k', 1, 16, 16, 2, (32, 32))
        self.A_ENEMY2 = self.enemyspritesheet.get_animation(
            'a', 5, 16, 16, 2, (32, 32))

        ## SPRITES ##
        self.S_WALL = pygame.image.load("assets/Wall2.jpg")
        self.S_FLOOR = pygame.image.load("assets/Floor.jpg")
        self.S_FLOOREXPLORED = pygame.image.load("assets/FloorUnseen.png")
        self.S_WALLEXPLORED = pygame.image.load("assets/WallUnseen.png")


##############################################################################
# OBJECTS
##############################################################################


class obj_Actor:
    def __init__(self, x, y, name_object, animation, animation_speed=.5, creature=None, ai=None, container=None, item=None):
        self.x = x  # map addresses
        self.y = y
        self.name_object = name_object
        self.animation = animation  # list of images
        self.animation_speed = animation_speed / 1.0  # in seconds

        # animation flicker speedd
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

        self.item = item
        if self.item:
            self.item.owner = self

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


##############################################################################
# COMPONENTS
##############################################################################


class com_Creature:
    '''Creatures have health, can damage other objects by attacking, and can die'''

    def __init__(self, name_instance, hp=10, death_function=None):
        self.name_instance = name_instance
        self.current_hp = hp
        self.max_hp = hp
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
        self.current_hp -= damage
        game_message(self.name_instance + "'s health is " +
                     str(self.current_hp) + "/" + str(self.max_hp), constants.COLOR_RED)

        if self.current_hp <= 0:

            if self.death_function is not None:
                self.death_function(self.owner)

    def heal(self, value):
        self.current_hp += value
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp


class com_Container:
    def __init__(self, volume=10.0, inventory=[]):
        self.inventory = inventory
        self.max_volume = volume

    # TODO Get names of everything in inventory

    # TODO Get the volume within container
    @property
    def volume(self):
        return 0.0
    # TODO Get the weight of everything in inventory


class com_Item:
    def __init__(self, weight=0.0, volume=0.0, use_function=None, value=None):
        self.weight = weight
        self.volume = volume
        self.use_function = use_function
        self.value = value

    def pick_up(self, actor):

        if actor.container:
            if actor.container.volume + self.volume > actor.container.max_volume:
                game_message("Not enough room to pick up!",
                             constants.COLOR_RED)

            else:
                game_message("Picking up", constants.COLOR_GREEN)
                actor.container.inventory.append(self.owner)
                GAME.current_objects.remove(self.owner)
                self.container = actor.container

    def drop(self, new_x, new_y):
        GAME.current_objects.append(self.owner)
        self.container.inventory.remove(self.owner)
        self.owner.x = new_x
        self.owner.y = new_y
        game_message("Item dropped", constants.COLOR_GREY)

    def use(self):
        '''Use the item by producing an effect and removing it'''
        if self.use_function:
            result = self.use_function(self.container.owner, self.value)

            if result is not None:
                print("use_function failed")

            else:
                self.container.inventory.remove(self.owner)


##############################################################################
# AI
##############################################################################


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


##############################################################################
# MAP
##############################################################################


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


def map_objects_at_coords(coords_x, coords_y):

    object_options = [
        obj for obj in GAME.current_objects if obj.x == coords_x and obj.y == coords_y]

    return object_options


def map_find_line(coords1, coords2):
    ''' Converts two x, y coords into a list of tiles.

    coords1 : (x1, y1)
    coords2 : (x2, y2)
    '''
    x1, y1 = coords1
    x2, y2 = coords2

    libtcodpy.line_init(x1, y1, x2, y2)

    calc_x, calc_y = libtcodpy.line_step()

    coord_list = []

    if x1 == x2 and y1 == y2:
        return [(x1, y1)]

    while (not calc_x is None):

        coord_list.append((calc_x, calc_y))

        calc_x, calc_y = libtcodpy.line_step()

    return coord_list


##############################################################################
# DRAW
##############################################################################


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
    # pygame.display.flip()


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
    draw_text(SURFACE_MAIN, "fps: " + str(int(CLOCK.get_fps())), constants.FONT_DEBUG_MESSAGE,
              (0, 0), constants.COLOR_WHITE, constants.COLOR_BLACK)


def draw_messages():

    if len(GAME.message_history) <= constants.NUM_MESSAGES:
        to_draw = GAME.message_history
    else:
        to_draw = GAME.message_history[-constants.NUM_MESSAGES:]

    text_height = helper_text_height(constants.FONT_MESSAGE_TEXT)

    start_y = (constants.MAP_HEIGHT * constants.CELL_HEIGHT -
               (constants.NUM_MESSAGES * text_height)) - 5

    i = 0

    for message, color in to_draw:

        draw_text(SURFACE_MAIN, message, constants.FONT_MESSAGE_TEXT, (0, start_y +
                                                                       (i * text_height)), color, constants.COLOR_BLACK)

        i += 1


def draw_text(display_surface, text_to_display, font, T_coords, text_color, back_color=None):
    '''This function takes in some text, and displays it on the referenced surface'''

    text_surf, text_rect = helper_text_objects(
        text_to_display, font, text_color, back_color)

    text_rect.topleft = T_coords

    display_surface.blit(text_surf, text_rect)


def draw_tile_rect(coords):

    x, y = coords

    new_x = x * constants.CELL_WIDTH
    new_y = y * constants.CELL_HEIGHT

    new_surface = pygame.Surface((constants.CELL_WIDTH, constants.CELL_HEIGHT))

    new_surface.fill(constants.COLOR_WHITE)

    new_surface.set_alpha(200)  # setting opacity

    SURFACE_MAIN.blit(new_surface, (new_x, new_y))


##############################################################################
# HELPER FUNCTIONS
##############################################################################


def helper_text_objects(incoming_text, incoming_font, incoming_color, incoming_bg):
    if incoming_bg:

        Text_surface = incoming_font.render(
            incoming_text, False, incoming_color, incoming_bg)

    else:
        Text_surface = incoming_font.render(
            incoming_text, False, incoming_color)

    return Text_surface, Text_surface.get_rect()


def helper_text_height(font):

    font_object = font.render('a', False, (0, 0, 0))
    font_rect = font_object.get_rect()
    return font_rect.height


def helper_text_width(font):

    font_object = font.render('a', False, (0, 0, 0))
    font_rect = font_object.get_rect()
    return font_rect.width


##############################################################################
# MAGIC
##############################################################################


def cast_heal(target, value):
    if target.creature.current_hp == target.creature.max_hp:
        game_message(target.creature.name_instance + " the " +
                     target.name_object + " is already at full health!")
        return "canceled"
    else:
        game_message(target.creature.name_instance + " the " + target.name_object +
                     " healed for " + str(value) + " health!")
        target.creature.heal(value)
        print(target.creature.current_hp)
    return None


def cast_lightning(damage):

    player_location = (PLAYER.x, PLAYER.y)
    # Prompt player for a tile
    point_selected = menu_tile_select(
        coords_origin=player_location, max_range=5)

    # Convert that tile into a list of tiles between A --> B
    list_of_tiles = map_find_line(player_location, point_selected)

    # Cycle through list, damage everything found
    for i, (x, y) in enumerate(list_of_tiles):

        target = map_check_for_creatures(x, y)

        if target and i != 0:
            target.creature.take_damage(damage)


##############################################################################
# MENUS
##############################################################################


def menu_pause():
    ''' This menu pauses the game and displays a simple message '''
    menu_close = False

    window_width = constants.MAP_WIDTH * constants.CELL_WIDTH
    window_height = constants.MAP_HEIGHT * constants.CELL_HEIGHT

    menu_text = "PAUSED"
    menu_font = constants.FONT_DEBUG_MESSAGE

    text_height = helper_text_height(menu_font)
    text_width = len(menu_text) * helper_text_width(menu_font)

    while not menu_close:

        events_list = pygame.event.get()

        for event in events_list:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_p:
                    menu_close = True

        draw_text(SURFACE_MAIN, menu_text, constants.FONT_DEBUG_MESSAGE, ((window_width /
                                                                           2) - (text_width / 2), (window_height / 2) - (text_height / 2)), constants.COLOR_WHITE, constants.COLOR_BLACK)

        CLOCK.tick(constants.GAME_FPS)

        pygame.display.flip()


def menu_inventory():

    menu_close = False
    menu_width = 200
    menu_height = 200

    window_width = constants.MAP_WIDTH * constants.CELL_WIDTH
    window_height = constants.MAP_HEIGHT * constants.CELL_HEIGHT

    menu_x = (window_width / 2) - (menu_width / 2)
    menu_y = (window_height / 2) - (menu_height / 2)

    menu_text_font = constants.FONT_MESSAGE_TEXT

    menu_text_height = helper_text_height(menu_text_font)
    menu_text_color = constants.COLOR_WHITE

    local_inventory_surface = pygame.Surface((menu_width, menu_height))

    while not menu_close:

        # Clear the menu
        local_inventory_surface.fill(constants.COLOR_BLACK)

        # Register changes

        print_list = [obj.name_object for obj in PLAYER.container.inventory]

        events_list = pygame.event.get()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Setting coords for in-menu mouse location
        mouse_x_rel = mouse_x - menu_x
        mouse_y_rel = mouse_y - menu_y

        mouse_in_window = (mouse_x_rel > 0 and
                           mouse_y_rel > 0 and
                           mouse_x_rel < menu_width and
                           mouse_y_rel < menu_height)

        mouse_line_selection = math.floor(mouse_y_rel / menu_text_height)

        for event in events_list:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_i:
                    menu_close = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if (mouse_in_window and
                            mouse_line_selection <= len(print_list) - 1):
                        PLAYER.container.inventory[mouse_line_selection].item.use(
                        )

        # Draw the list

        for line, (name) in enumerate(print_list):

            if line == mouse_line_selection and mouse_in_window:
                draw_text(local_inventory_surface,
                          name,
                          menu_text_font,
                          (0, 0 + (line * menu_text_height)),
                          menu_text_color,
                          constants.COLOR_GREY)
            else:
                draw_text(local_inventory_surface,
                          name,
                          menu_text_font,
                          (0, 0 + (line * menu_text_height)),
                          menu_text_color)

        # Display Menu
        SURFACE_MAIN.blit(local_inventory_surface,
                          (menu_x, menu_y))

        CLOCK.tick(constants.GAME_FPS)

        pygame.display.flip()


def menu_tile_select(coords_origin=None, max_range=None, penetrate_walls=True):
    ''' This menu lets the player select a tile. 
    This function pauses the game, produces an on-screen rectangle
    and when the player presses the left mouse-button, will return
    (message for now) the map address
    '''
    menu_close = False

    while not menu_close:

        # Get mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Get button clicks
        events_list = pygame.event.get()

        # Mouse map selection
        map_coord_x = math.floor(mouse_x/constants.CELL_WIDTH)
        map_coord_y = math.floor(mouse_y/constants.CELL_HEIGHT)

        valid_tiles = []

        if coords_origin:
            full_list_tiles = map_find_line(
                coords_origin, (map_coord_x, map_coord_y))

            for i, (x, y) in enumerate(full_list_tiles):
                valid_tiles.append((x, y))
                if max_range and i == max_range:
                    break

        else:
            valid_tiles = [(map_coord_x, map_coord_y)]

        # Return map coords when presses left mouse-button
        for event in events_list:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_l:
                    menu_close = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Returns coord selected
                    return(valid_tiles[-1])

        # Draw game first
        draw_game()

        # Draw rectangle at mouse position on top of game
        for (tile_x, tile_y) in valid_tiles:
            draw_tile_rect((tile_x, tile_y))

        # Update the display
        pygame.display.flip()

        # Tick the CLOCK
        CLOCK.tick(constants.GAME_FPS)


##############################################################################
# GAME
##############################################################################


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

        # update the game
        pygame.display.flip()

        # tick the CLOCK
        CLOCK.tick(constants.GAME_FPS)

    pygame.quit()
    exit()


def game_initialize():
    '''This function initializes the main window, and pygame'''

    global SURFACE_MAIN, GAME, CLOCK, FOV_CALCULATE, PLAYER, ENEMY, ENEMY2, ASSETS
    # initialize pygame
    pygame.init()

    pygame.key.set_repeat(200, 70)  # first delay, 200ms, then 70ms after

    pygame.font.init()

    SURFACE_MAIN = pygame.display.set_mode(
        (constants.MAP_WIDTH * constants.CELL_WIDTH, constants.MAP_HEIGHT * constants.CELL_HEIGHT))

    GAME = obj_Game()

    CLOCK = pygame.time.Clock()

    FOV_CALCULATE = True

    ASSETS = struc_Assets()

    container_com1 = com_Container()
    creature_com1 = com_Creature("greg")
    PLAYER = obj_Actor(1, 1, "python", ASSETS.A_PLAYER,
                       animation_speed=1, creature=creature_com1, container=container_com1)

    item_com1 = com_Item(use_function=cast_heal, value=4)
    creature_com2 = com_Creature("jackie", death_function=death_monster)
    ai_com1 = ai_Test()
    ENEMY = obj_Actor(10, 13, "rock lobster", ASSETS.A_ENEMY1, animation_speed=1,
                      creature=creature_com2, ai=ai_com1, item=item_com1)

    item_com2 = com_Item(use_function=cast_heal, value=5)
    creature_com3 = com_Creature("bob", death_function=death_monster)
    ai_com2 = ai_Test()
    ENEMY2 = obj_Actor(10, 18, "ugly squid", ASSETS.A_ENEMY2, animation_speed=1,
                       creature=creature_com3, ai=ai_com2, item=item_com2)

    GAME.current_objects = [PLAYER, ENEMY, ENEMY2]


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

            if event.key == pygame.K_g:
                objects_at_player = map_objects_at_coords(PLAYER.x, PLAYER.y)

                for obj in objects_at_player:
                    if obj.item:
                        obj.item.pick_up(PLAYER)

            if event.key == pygame.K_d:
                if len(PLAYER.container.inventory) > 0:
                    PLAYER.container.inventory[-1].item.drop(
                        PLAYER.x, PLAYER.y)

            if event.key == pygame.K_p:
                menu_pause()

            if event.key == pygame.K_i:
                menu_inventory()

            # key 'l' --> turn on tile selection
            if event.key == pygame.K_l:
                cast_lightning(10)

    return "no-action"


def game_message(game_msg, msg_color=constants.COLOR_GREY):

    GAME.message_history.append((game_msg, msg_color))


if __name__ == '__main__':
    game_initialize()
    game_main_loop()
