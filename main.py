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
        self.environmentsheet = obj_Spritesheet("assets/DungeonStarter.png")
        self.itemsheet = obj_Spritesheet("assets/pngguru.com.png")

        ## ANIMATIONS ##
        self.A_PLAYER = self.charspritesheet.get_animation(
            'o', 5, 16, 16, 2, (32, 32))
        self.A_ENEMY1 = self.enemyspritesheet.get_animation(
            'k', 1, 16, 16, 2, (32, 32))
        self.A_ENEMY2 = self.enemyspritesheet.get_animation(
            'a', 5, 16, 16, 2, (32, 32))

        ## SPRITES ##
        self.S_WALL = pygame.image.load("assets/Wall2.jpg")
        self.S_FLOOR = self.environmentsheet.get_image(
            'a', 16, 16, 16, (32, 32))[0]
        self.S_FLOOREXPLORED = self.environmentsheet.get_image(
            'a', 1, 16, 16, (32, 32))[0]
        self.S_WALLEXPLORED = pygame.image.load("assets/WallUnseen.png")
        self.S_SKULL = [pygame.image.load("assets/Skull.png")]

        ## ITEMS ##
        self.S_SWORD = [pygame.transform.scale(
            pygame.image.load("assets/Sword.png"), (constants.CELL_WIDTH, constants.CELL_HEIGHT))]
        self.S_SHIELD = [pygame.transform.scale(pygame.image.load(
            "assets/Shield.png"), (constants.CELL_WIDTH, constants.CELL_HEIGHT))]
        self.S_SCROLL_01 = pygame.image.load("assets/Scroll.png")
        self.S_SCROLL_02 = pygame.image.load("assets/Scroll.png")
        self.S_SCROLL_03 = pygame.image.load("assets/Scroll.png")


##############################################################################
# OBJECTS
##############################################################################


class obj_Actor:
    def __init__(self, x, y,
                 name_object,
                 animation,
                 animation_speed=.5,
                 creature=None,
                 ai=None,
                 container=None,
                 item=None,
                 equipment=None):
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

        self.equipment = equipment
        if self.equipment:
            self.equipment.owner = self

            self.item = com_Item()
            self.item.owner = self

    @property  # Can call the method as a property
    def display_name(self):
        if self.creature:
            return (self.creature.name_instance + " the " + self.name_object)

        if self.item:
            if self.equipment and self.equipment.equipped:
                return (self.name_object + " (equipped)")
            else:
                return (self.name_object)

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

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y

        return math.sqrt(dx ** 2 + dy ** 2)

    def move_towards(self, other):
        dx = other.x - self.x
        dy = other.y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        self.creature.move(dx, dy)


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

    def __init__(self, name_instance, base_atk=2, base_def=0, hp=10, death_function=None):
        self.name_instance = name_instance
        self.base_atk = base_atk
        self.base_def = base_def
        self.current_hp = hp
        self.max_hp = hp
        self.death_function = death_function

    def move(self, dx, dy):

        tile_is_wall = (GAME.current_map[self.owner.x + dx]
                        [self.owner.y + dy].block_path == True)
        target = map_check_for_creatures(
            self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            self.attack(target)

        if not tile_is_wall and not target:
            self.owner.x += dx
            self.owner.y += dy

    def attack(self, target):
        damage_dealt = self.power - target.creature.defense

        game_message(self.name_instance + " attacks " +
                     target.creature.name_instance + " for " + str(damage_dealt) + " damage!", constants.COLOR_WHITE)
        target.creature.take_damage(damage_dealt)

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

    @property
    def power(self):

        total_power = self.base_atk

        if self.owner.container:
            object_bonuses = [
                obj.equipment.attack_bonus for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                if bonus:
                    total_power += bonus

        return total_power

    @property
    def defense(self):

        total_defense = self.base_def

        if self.owner.container:
            object_bonuses = [
                obj.equipment.defense_bonus for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                if bonus:
                    total_defense += bonus

        return total_defense


class com_Container:
    def __init__(self, volume=10.0, inventory=[]):
        self.inventory = inventory
        self.max_volume = volume

    # TODO Get names of everything in inventory

    # TODO Get the volume within container
    @property
    def volume(self):
        return 0.0

    @property
    def equipped_items(self):
        list_of_equipped_items = [
            obj for obj in self.inventory if obj.equipment and obj.equipment.equipped]

        return list_of_equipped_items

    # TODO Get the weight of everything in inventory


class com_Item:
    def __init__(self, weight=0.0, volume=0.0,
                 use_function=None,
                 value=None):
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
                self.current_container = actor.container

    def drop(self, new_x, new_y):
        GAME.current_objects.append(self.owner)
        self.container.inventory.remove(self.owner)
        self.owner.x = new_x
        self.owner.y = new_y
        game_message("Item dropped", constants.COLOR_GREY)

    def use(self):
        '''Use the item by producing an effect and removing it'''
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return

        if self.use_function:
            result = self.use_function(
                self.current_container.owner, self.value)

            if result is not None:
                print("use_function failed")

            else:
                self.current_container.inventory.remove(self.owner)


class com_Equipment:
    def __init__(self, attack_bonus=None, defense_bonus=None, slot=None):
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.slot = slot

        self.equipped = False

    def toggle_equip(self):
        if self.equipped:
            self.unequip()
        else:
            self.equip()

    def equip(self):

        # Check for equipment in slot

        all_equipped_items = self.owner.item.current_container.equipped_items
        if all_equipped_items:
            for item in all_equipped_items:
                if item.equipment.slot and item.equipment.slot == self.slot:
                    game_message("Equipment slot is occupied",
                                 constants.COLOR_RED)
                    return

        self.equipped = True
        game_message("Item equipped")

    def unequip(self):

        # Toggle self.equipped
        self.equipped = False
        game_message("Item unequipped")


##############################################################################
# AI
##############################################################################


class ai_Confuse:
    '''Once per turn, execute'''

    def __init__(self, old_ai, num_turns):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):

        if self.num_turns > 0:
            self.owner.creature.move(libtcodpy.random_get_int(0, -1, 1),
                                     libtcodpy.random_get_int(0, -1, 1))

            self.num_turns -= 1

        else:
            self.owner.ai = self.old_ai

            game_message(self.owner.display_name +
                         " has broken free!", constants.COLOR_RED)


class ai_Chase:
    ''' A basic monster ai which chases and tries to harm player.'''

    def take_turn(self):
        monster = self.owner

        if libtcodpy.map_is_in_fov(FOV_MAP, monster.x, monster.y):

            # TODO Move towards the player if far away
            if monster.distance_to(PLAYER) >= 2:
                self.owner.move_towards(PLAYER)

            # TODO If close enough, attack player
            elif PLAYER.creature.current_hp > 0:
                monster.creature.attack(PLAYER)


def death_monster(monster):
    '''On death, most monsters stop moving'''

    game_message(monster.creature.name_instance +
                 " is dead!", constants.COLOR_GREY)

    monster.animation = ASSETS.S_SKULL
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


def map_find_radius(coords, radius):
    center_x, center_y = coords

    tile_list = []
    start_x = (center_x - radius)
    end_x = (center_x + radius + 1)
    start_y = (center_y - radius)
    end_y = (center_y + radius + 1)

    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            tile_list.append((x, y))

    return tile_list


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


def draw_text(display_surface, text_to_display, font, T_coords, text_color, back_color=None, center=False):
    '''This function takes in some text, and displays it on the referenced surface'''

    text_surf, text_rect = helper_text_objects(
        text_to_display, font, text_color, back_color)

    if not center:
        text_rect.topleft = T_coords
    else:
        text_rect.center = T_coords

    display_surface.blit(text_surf, text_rect)


def draw_tile_rect(coords, tile_color=None, tile_alpha=None, mark=None):

    x, y = coords

    # Default colors
    if tile_color:
        local_color = tile_color
    else:
        local_color = constants.COLOR_WHITE

    # Default alpha
    if tile_alpha:
        local_alpha = tile_alpha
    else:
        local_alpha = 200

    new_x = x * constants.CELL_WIDTH
    new_y = y * constants.CELL_HEIGHT

    new_surface = pygame.Surface((constants.CELL_WIDTH, constants.CELL_HEIGHT))

    new_surface.fill(local_color)

    new_surface.set_alpha(local_alpha)  # setting opacity

    if mark:
        draw_text(new_surface, mark, font=constants.FONT_CURSOR_TEXT, T_coords=(
            constants.CELL_WIDTH/2, constants.CELL_HEIGHT/2), text_color=constants.COLOR_BLACK, center=True)

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


def cast_lightning(caster, T_damage_maxrange):

    damage, m_range = T_damage_maxrange

    player_location = (caster.x, caster.y)
    # Prompt player for a tile
    point_selected = menu_tile_select(
        coords_origin=player_location, max_range=m_range, penetrate_walls=False)

    # Convert that tile into a list of tiles between A --> B
    if point_selected:
        list_of_tiles = map_find_line(player_location, point_selected)

        # Cycle through list, damage everything found

        for i, (x, y) in enumerate(list_of_tiles):

            target = map_check_for_creatures(x, y)

            if target:
                target.creature.take_damage(damage)


def cast_fireball(caster, T_damage_radius_range):

    # defs
    damage, local_radius, max_r = T_damage_radius_range

    player_location = (caster.x, caster.y)

    # Get target tile
    point_selected = menu_tile_select(
        coords_origin=player_location, max_range=max_r, penetrate_walls=False, pierce_creature=False, radius=local_radius)

    if point_selected:
        # Get sequence of tiles
        tiles_to_damage = map_find_radius(point_selected, local_radius)

        creature_hit = False

        # Damage all creatures in tiles
        for (x, y) in tiles_to_damage:
            creatures_to_damage = map_check_for_creatures(x, y)

            if creatures_to_damage:
                creatures_to_damage.creature.take_damage(damage)

                if creatures_to_damage is not PLAYER:
                    creature_hit = True

        if creature_hit:
            game_message("The monster howls out in pain.", constants.COLOR_RED)


def cast_confusion(caster, effect_length):

    # Select tile
    point_selected = menu_tile_select()

    # Get target
    if point_selected:
        tile_x, tile_y = point_selected
        target = map_check_for_creatures(tile_x, tile_y)

    # Temporarily confuse the target
        if target:
            oldai = target.ai
            target.ai = ai_Confuse(old_ai=oldai, num_turns=effect_length)
            target.ai.owner = target

            game_message("The creature's eyes glaze over",
                         constants.COLOR_GREEN)


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

        # Collect list of item names
        print_list = [obj.display_name for obj in PLAYER.container.inventory]

        # Get list of input events
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
                        menu_close = True

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

        # RENDER GAME #
        draw_game()

        # Display Menu
        SURFACE_MAIN.blit(local_inventory_surface,
                          (menu_x, menu_y))

        CLOCK.tick(constants.GAME_FPS)

        pygame.display.flip()


def menu_tile_select(coords_origin=None, max_range=None, penetrate_walls=True, pierce_creature=True, radius=None):
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

                # Stop at max range
                if max_range and i == max_range - 1:
                    break

                # Stop at wall
                if not penetrate_walls and GAME.current_map[x][y].block_path:
                    break

                # Stop at creature
                if not pierce_creature and map_check_for_creatures(x, y):
                    break

        else:
            valid_tiles = [(map_coord_x, map_coord_y)]

        # Return map coords when presses left mouse-button
        for event in events_list:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_l:
                    menu_close = True
                if event.key == pygame.K_f:
                    menu_close = True
                if event.key == pygame.K_c:
                    menu_close = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Returns coord selected
                    return(valid_tiles[-1])

        # Draw game first
        draw_game()

        # Draw rectangle at mouse position on top of game
        for (tile_x, tile_y) in valid_tiles:

            if (tile_x, tile_y) == valid_tiles[-1]:
                draw_tile_rect(coords=(tile_x, tile_y), mark="X")
            else:
                draw_tile_rect(coords=(tile_x, tile_y))

        if radius:
            area_effect = map_find_radius(valid_tiles[-1], radius)

            for (tile_x, tile_y) in area_effect:
                draw_tile_rect(coords=(tile_x, tile_y),
                               tile_color=constants.COLOR_RED, tile_alpha=150)

        # Update the display
        pygame.display.flip()

        # Tick the CLOCK
        CLOCK.tick(constants.GAME_FPS)


##############################################################################
# GENERATORS
##############################################################################


# PLAYER
def gen_player(coords):
    x, y = coords
    container_com = com_Container()
    creature_com = com_Creature("Snicky", base_atk=4)
    player = obj_Actor(x, y, "Python", ASSETS.A_PLAYER,
                       animation_speed=1, creature=creature_com, container=container_com)
    return player


# ITEMS
def gen_item(coords):

    random_num = libtcodpy.random_get_int(0, 1, 5)

    if random_num == 1:
        new_item = gen_scroll_lightning(coords)
    elif random_num == 2:
        new_item = gen_scroll_fireball(coords)
    elif random_num == 3:
        new_item = gen_scroll_confusion(coords)
    elif random_num == 4:
        new_item = gen_weapon_sword(coords)
    elif random_num == 5:
        new_item = gen_armor_shield(coords)

    GAME.current_objects.append(new_item)


def gen_scroll_lightning(coords):

    x, y = coords

    damage = libtcodpy.random_get_int(0, 5, 7)
    m_range = libtcodpy.random_get_int(0, 7, 8)

    item_com = com_Item(use_function=cast_lightning, value=(damage, m_range))

    return_object = obj_Actor(x, y, "lightning scroll",
                              animation=[ASSETS.S_SCROLL_01], item=item_com)

    return return_object


def gen_scroll_fireball(coords):

    x, y = coords

    damage = libtcodpy.random_get_int(0, 2, 4)
    radius = 1
    m_range = libtcodpy.random_get_int(0, 9, 12)

    item_com = com_Item(use_function=cast_fireball,
                        value=(damage, radius, m_range))

    return_object = obj_Actor(x, y, "fireball scroll",
                              animation=[ASSETS.S_SCROLL_02], item=item_com)

    return return_object


def gen_scroll_confusion(coords):

    x, y = coords

    effect_length = libtcodpy.random_get_int(0, 5, 10)

    item_com = com_Item(use_function=cast_confusion,
                        value=effect_length)

    return_object = obj_Actor(x, y, "confusion scroll",
                              animation=[ASSETS.S_SCROLL_03], item=item_com)

    return return_object


def gen_weapon_sword(coords):

    x, y = coords

    bonus = libtcodpy.random_get_int(0, 1, 2)

    equipment_com = com_Equipment(attack_bonus=bonus)

    return_object = obj_Actor(
        x, y, "Short Sword", animation=ASSETS.S_SWORD, equipment=equipment_com)

    return return_object


def gen_armor_shield(coords):

    x, y = coords

    bonus = libtcodpy.random_get_int(0, 1, 2)

    equipment_com = com_Equipment(defense_bonus=bonus)

    return_object = obj_Actor(
        x, y, "Small Shield", animation=ASSETS.S_SHIELD, equipment=equipment_com)

    return return_object


# ENEMIES
def gen_enemy(coords):
    random_num = libtcodpy.random_get_int(0, 1, 100)

    if random_num <= 15:
        new_enemy = gen_aquatic_squid(coords)
    else:
        new_enemy = gen_aquatic_lobster(coords)

    GAME.current_objects.append(new_enemy)


def gen_aquatic_lobster(coords):

    x, y = coords

    max_health = libtcodpy.random_get_int(0, 5, 10)
    base_attack = libtcodpy.random_get_int(0, 1, 3)

    item_com = com_Item(use_function=cast_heal, value=4)
    creature_com = com_Creature(
        "Flippy", base_atk=base_attack, hp=max_health, death_function=death_monster)
    ai_com = ai_Chase()
    enemy = obj_Actor(x, y, "Rock Lobster", ASSETS.A_ENEMY1,
                      animation_speed=1, creature=creature_com, ai=ai_com, item=item_com)
    return enemy


def gen_aquatic_squid(coords):

    x, y = coords

    max_health = libtcodpy.random_get_int(0, 12, 15)
    base_attack = libtcodpy.random_get_int(0, 3, 6)

    item_com = com_Item(use_function=cast_heal, value=5)
    creature_com = com_Creature(
        "Poots", base_atk=base_attack, hp=max_health, death_function=death_monster)
    ai_com = ai_Chase()
    enemy = obj_Actor(x, y, "Fugly Squid", ASSETS.A_ENEMY2, animation_speed=1,
                      creature=creature_com, ai=ai_com, item=item_com)
    return enemy


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

    # Create items
    gen_item((2, 2))
    gen_item((2, 3))
    gen_item((2, 4))

    # Create 2 enemies
    gen_enemy((15, 15))
    gen_enemy((15, 18))

    PLAYER = gen_player((1, 1))

    GAME.current_objects.append(PLAYER)


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

            if event.key == pygame.K_f:
                cast_fireball()

            if event.key == pygame.K_c:
                cast_confusion()

    return "no-action"


def game_message(game_msg, msg_color=constants.COLOR_GREY):

    GAME.message_history.append((game_msg, msg_color))


if __name__ == '__main__':
    game_initialize()
    game_main_loop()
