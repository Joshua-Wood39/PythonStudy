import constants
import pygame
import tcod as libtcodpy
import math
import pickle
import gzip
import random
import sys
import datetime
import os

##############################################################################
# STRUCTURES
##############################################################################


class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False


class struc_Preferences:
    def __init__(self):
        self.vol_sound = 0.5
        self.vol_music = 0.5


##############################################################################
# OBJECTS
##############################################################################


class obj_Actor:
    def __init__(self, x, y,
                 name_object,
                 animation_key,
                 animation_speed=.5,
                 creature=None,
                 ai=None,
                 container=None,
                 item=None,
                 equipment=None,
                 stairs=None,
                 state=None,
                 exitportal=None,
                 depth=0):
        self.x = x  # map addresses
        self.y = y
        self.name_object = name_object
        self.animation_key = animation_key
        self.state = state
        self.depth = depth

        # list of images
        self.animation = ASSETS.animation_dict[self.animation_key]
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

        self.stairs = stairs
        if self.stairs:
            self.stairs.owner = self

        self.exitportal = exitportal
        if self.exitportal:
            self.exitportal.owner = self

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
                SURFACE_MAP.blit(
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

                SURFACE_MAP.blit(
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

    def move_away(self, other):
        dx = self.x - other.x
        dy = self.y - other.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        self.creature.move(dx, dy)

    def animation_destroy(self):
        self.animation = None

    def animation_init(self):
        self.animation = ASSETS.animation_dict[self.animation_key]


class obj_Game:
    def __init__(self):
        self.current_objects = []
        self.message_history = []
        self.maps_previous = []
        self.maps_next = []

        self.current_map, self.current_rooms = map_create()

    def transition_next(self):

        global FOV_CALCULATE

        FOV_CALCULATE = True

        self.maps_previous.append((PLAYER.x,
                                   PLAYER.y,
                                   self.current_map,
                                   self.current_rooms,
                                   self.current_objects))

        for obj in self.current_objects:
            obj.animation_destroy()

        if len(self.maps_next) == 0:

            # Clear the previous items and enemies
            self.current_objects = [PLAYER]

            PLAYER.animation_init()

            self.current_map, self.current_rooms = map_create()
            map_place_objects(self.current_rooms)

        else:
            (PLAYER.x, PLAYER.y, self.current_map, self.current_rooms,
             self.current_objects) = self.maps_next[-1]

            for obj in self.current_objects:
                obj.animation_init()

            map_make_fov(self.current_map)
            FOV_CALCULATE = True

            # Stack method of removal
            del self.maps_next[-1]

    def transition_previous(self):
        global FOV_CALCULATE

        if len(self.maps_previous) != 0:

            for obj in self.current_objects:
                obj.animation_destroy()

            self.maps_next.append((PLAYER.x,
                                   PLAYER.y,
                                   self.current_map,
                                   self.current_rooms,
                                   self.current_objects))

            (PLAYER.x, PLAYER.y, self.current_map, self.current_rooms,
             self.current_objects) = self.maps_previous[-1]

            for obj in self.current_objects:
                obj.animation_init()

            map_make_fov(self.current_map)
            FOV_CALCULATE = True

            del self.maps_previous[-1]


class obj_Spritesheet:
    '''Class used to grab images out of a sprite sheet'''

    def __init__(self, file_name):
        # Load the sprite sheet.
        self.sprite_sheet = pygame.image.load(file_name).convert()
        self.tiledict = {'aa': 0, 'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7,
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


class obj_Room:
    ''' This is a rectangle that lives on the map '''

    def __init__(self, coords, size):

        self.x1, self.y1 = coords
        self.w, self.h = size

        self.x2 = self.x1 + self.w
        self.y2 = self.y1 + self.h

    @property
    def center(self):
        center_x = math.floor((self.x1 + self.x2) / 2)
        center_y = math.floor((self.y1 + self.y2) / 2)

        return (center_x, center_y)

    def intersect(self, other):
        # Return true if other object intercepts this one
        objects_intersect = (self.x1 <= other.x2 and self.x2 >=
                             other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1)
        return objects_intersect


class obj_Camera:

    def __init__(self):
        self.width = constants.CAMERA_WIDTH
        self.height = constants.CAMERA_HEIGHT
        self.x, self.y = (0, 0)

    def update(self):

        target_x = PLAYER.x * constants.CELL_WIDTH + (constants.CELL_WIDTH/2)
        target_y = PLAYER.y * constants.CELL_HEIGHT + (constants.CELL_HEIGHT/2)

        distance_x, distance_y = self.map_dist((target_x, target_y))

        self.x += int(distance_x)
        self.y += int(distance_y)

    def win_to_map(self, coords):
        tar_x, tar_y = coords
        # Convert window coords to distance from camera
        cam_d_x, cam_d_y = self.cam_dist((tar_x, tar_y))

        # Distance from camera --> map coord
        map_p_x = self.x + cam_d_x
        map_p_y = self.y + cam_d_y

        return (map_p_x, map_p_y)

    def map_dist(self, coords):
        new_x, new_y = coords

        dist_x = new_x - self.x
        dist_y = new_y - self.y

        return (dist_x, dist_y)

    def cam_dist(self, coords):
        win_x, win_y = coords

        dist_x = win_x - (self.width / 2)
        dist_y = win_y - (self.height / 2)

        return (dist_x, dist_y)

    @property
    def rectangle(self):
        pos_rect = pygame.Rect(
            (0, 0), (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))
        pos_rect.center = (self.x, self.y)
        return pos_rect

    @property
    def map_address(self):
        map_x = self.x / constants.CELL_WIDTH
        map_y = self.y / constants.CELL_HEIGHT

        return (map_x, map_y)


class obj_Assets:
    def __init__(self):
        self.load_assets()
        self.volume_adjust()

    def load_assets(self):
        #######
        # ART
        #######

        ## SPRITESHEETS ##
        self.charspritesheet = obj_Spritesheet("assets/Reptiles.png")
        self.enemyspritesheet = obj_Spritesheet("assets/Aquatic.png")
        self.environmentsheet = obj_Spritesheet("assets/DungeonStarter.png")
        self.itemsheet = obj_Spritesheet("assets/pngguru.com.png")
        self.mousesheet = obj_Spritesheet("assets/Mouse.png")

        ## ANIMATIONS ##
        self.A_PLAYER = self.charspritesheet.get_animation(
            'o', 5, 16, 16, 2, (32, 32))
        self.A_ENEMY1 = self.enemyspritesheet.get_animation(
            'k', 1, 16, 16, 2, (32, 32))
        self.A_ENEMY2 = self.enemyspritesheet.get_animation(
            'a', 5, 16, 16, 2, (32, 32))
        self.A_MOUSE = self.mousesheet.get_animation(
            'aa', 0, 32, 32, 2, (32, 32))

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
        self.S_LAMP = pygame.image.load("assets/Lamp.png")

        ## SPECIAL ##
        self.S_UPSTAIRS = [pygame.image.load("assets/Upstairs.png")]
        self.S_DOWNSTAIRS = [pygame.image.load("assets/Downstairs.png")]
        self.MAIN_MENU_BG = pygame.image.load("assets/Live Python.jpg")
        self.S_DOOR_OPEN = [pygame.image.load("assets/DoorOpen.png")]
        self.S_DOOR_CLOSE = [pygame.image.load("assets/DoorClose.png")]
        # self.MAIN_MENU_BG = pygame.transform.scale(
        # self.MAIN_MENU_BG, (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))

        self.animation_dict = {
            ## ANIMATIONS ##
            "A_PLAYER": self.A_PLAYER,
            "A_ENEMY1": self.A_ENEMY1,
            "A_ENEMY2": self.A_ENEMY2,
            "A_MOUSE": self.A_MOUSE,

            ## SPRITES ##
            "S_SKULL": self.S_SKULL,

            ## ITEMS ##
            "S_SWORD": self.S_SWORD,
            "S_SHIELD": self.S_SHIELD,
            "S_SCROLL_01": [self.S_SCROLL_01],
            "S_SCROLL_02": [self.S_SCROLL_02],
            "S_SCROLL_03": [self.S_SCROLL_03],
            "S_LAMP": [self.S_LAMP],

            ## SPECIAL ##
            "S_STAIRS_UP": self.S_UPSTAIRS,
            "S_STAIRS_DOWN": self.S_DOWNSTAIRS,
            "S_DOOR_OPEN": self.S_DOOR_OPEN,
            "S_DOOR_CLOSE": self.S_DOOR_CLOSE

        }

        #########
        # AUDIO
        #########

        # Complete Sound List
        self.snd_list = []

        # Loaded Sound Assets
        self.music_background = "audio/African Safari Loop.wav"
        self.sound_hit_1 = self.sound_add("audio/Real_Punch.wav")
        self.sound_hit_2 = self.sound_add("audio/Strong_Punch.wav")

        # Sounds for Player strike
        self.snd_list_hit = [self.sound_hit_1, self.sound_hit_2]

    def sound_add(self, file_address):

        new_sound = pygame.mixer.Sound(file_address)

        self.snd_list.append(new_sound)

        return new_sound

    def volume_adjust(self):

        for sound in self.snd_list:
            sound.set_volume(PREFERENCES.vol_sound)

        pygame.mixer.music.set_volume(PREFERENCES.vol_music)


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

        if damage_dealt > 0 and self.owner is PLAYER:
            pygame.mixer.Sound.play(RANDOM_ENGINE.choice(ASSETS.snd_list_hit))

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
    def __init__(self, volume=10.0, inventory=None):
        self.inventory = inventory
        self.max_volume = volume
        if inventory:
            self.inventory = inventory
        else:
            self.inventory = []

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

                self.owner.animation_destroy()

                GAME.current_objects.remove(self.owner)
                self.current_container = actor.container

    def drop(self, new_x, new_y):
        GAME.current_objects.append(self.owner)

        self.owner.animation_init()

        self.current_container.inventory.remove(self.owner)
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


class com_Stairs:

    def __init__(self, downwards=True):

        self.downwards = downwards

    def use(self):
        if self.downwards:
            GAME.transition_next()
        else:
            GAME.transition_previous()


class com_ExitPortal:
    def __init__(self):
        self.OPEN = "S_DOOR_OPEN"
        self.CLOSE = "S_DOOR_CLOSE"

    def update(self):
        # Flag initialization
        found_lamp = False

        # Check condition
        portal_open = self.owner.state == "OPEN"

        for obj in PLAYER.container.inventory:
            if obj.name_object is "THE LAMP":
                found_lamp = True

        if found_lamp and not portal_open:
            self.owner.state = "OPEN"
            self.owner.animation_key = "S_DOOR_OPEN"
            self.owner.animation_init()

        if not found_lamp and portal_open:
            self.owner.state = "CLOSED"
            self.owner.animation_key = "S_DOOR_CLOSE"
            self.owner.animation_init()

    def use(self):

        if self.owner.state == "OPEN":

            PLAYER.state = "STATUS_WIN"

            SURFACE_MAIN.fill(constants.COLOR_WHITE)

            screen_center = (constants.CAMERA_WIDTH/2,
                             constants.CAMERA_HEIGHT/2)

            draw_text(SURFACE_MAIN, "YOU WON!", constants.FONT_TITLE_SCREEN,
                      screen_center, constants.COLOR_BLACK, center=True)

            pygame.display.update()

            filename = ("savedata/win_" + PLAYER.creature.name_instance + "." +
                        datetime.date.today().strftime("%Y%B%d") + ".txt")

            file_exists = os.path.isfile(filename)
            save_exists = os.path.isfile("assets/savegame")

            if file_exists:
                os.remove(filename)
            if save_exists:
                os.remove("assets/savegame")

            # 'a+' will append an existing file, or create one if it doesn't exist
            legacy_file = open(filename, 'a+')

            for message, color in GAME.message_history:
                legacy_file.write(message + "\n")

            pygame.time.wait(4000)


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


class ai_Flee:

    def take_turn(self):
        monster = self.owner

        if libtcodpy.map_is_in_fov(FOV_MAP, monster.x, monster.y):

            self.owner.move_away(PLAYER)


##############################################################################
# DEATH
##############################################################################


def death_monster(monster):
    '''On death, most monsters stop moving'''

    game_message(monster.creature.name_instance +
                 " is dead!", constants.COLOR_GREY)

    monster.animation = ASSETS.S_SKULL
    monster.animation_key = "S_SKULL"
    monster.depth = constants.DEPTH_CORPSE
    monster.creature = None
    monster.ai = None


def death_mouse(mouse):
    game_message(mouse.creature.name_instance +
                 " is dead! Eat him!", constants.COLOR_GREEN)

    mouse.animation = ASSETS.S_SKULL
    mouse.animation_key = "S_SKULL"
    mouse.creature = None
    mouse.ai = None


def death_player(player):
    player.state = "STATUS_DEAD"

    SURFACE_MAIN.fill(constants.COLOR_BLACK)

    screen_center = (constants.CAMERA_WIDTH/2, constants.CAMERA_HEIGHT/2)

    draw_text(SURFACE_MAIN, "YOU DIED!", constants.FONT_TITLE_SCREEN,
              screen_center, constants.COLOR_WHITE, center=True)

    pygame.display.update()

    filename = ("savedata/legacy_" + PLAYER.creature.name_instance + "." +
                datetime.date.today().strftime("%Y%B%d") + ".txt")

    file_exists = os.path.isfile(filename)
    save_exists = os.path.isfile("assets/savegame")

    if file_exists:
        os.remove(filename)
    if save_exists:
        os.remove("assets/savegame")

    # 'a+' will append an existing file, or create one if it doesn't exist
    legacy_file = open(filename, 'a+')

    for message, color in GAME.message_history:
        legacy_file.write(message + "\n")

    pygame.time.wait(4000)


##############################################################################
# MAP
##############################################################################


def map_create():
    # Generate a map full of walls
    new_map = [[struc_Tile(True) for y in range(0, constants.MAP_HEIGHT)]
               for x in range(0, constants.MAP_WIDTH)]
    # Generate new room
    list_of_rooms = []

    for i in range(constants.MAP_MAX_NUM_ROOMS):

        w = libtcodpy.random_get_int(
            0, constants.ROOM_MIN_WIDTH, constants.ROOM_MAX_WIDTH)
        h = libtcodpy.random_get_int(
            0, constants.ROOM_MIN_HEIGHT, constants.ROOM_MAX_HEIGHT)

        x = libtcodpy.random_get_int(0, 2, constants.MAP_WIDTH - w - 2)
        y = libtcodpy.random_get_int(0, 2, constants.MAP_HEIGHT - h - 2)

        # Create the room
        new_room = obj_Room((x, y), (w, h))

        failed = False

        # Check for intersect
        for other_room in list_of_rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            # Place the room
            map_create_room(new_map, new_room)
            current_center = new_room.center

            if len(list_of_rooms) != 0:
                previous_center = list_of_rooms[-1].center

                # Dig the tunnels
                map_create_tunnels(current_center, previous_center, new_map)

            list_of_rooms.append(new_room)

    map_make_fov(new_map)

    return (new_map, list_of_rooms)


def map_place_objects(room_list):

    current_level = len(GAME.maps_previous) + 1

    top_level = (current_level == 1)

    final_level = (current_level == constants.MAP_NUM_LEVELS)

    for room in room_list:

        first_room = (room == room_list[0])
        last_room = (room == room_list[-1])

        if first_room:
            PLAYER.x, PLAYER.y = room.center

        if first_room and top_level:
            gen_portal(room.center)

        if first_room and not top_level:
            gen_stairs((PLAYER.x, PLAYER.y), downwards=False)

        if last_room:
            if final_level:
                gen_LAMP(room.center)
            else:
                gen_stairs(room.center)

        x = libtcodpy.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcodpy.random_get_int(0, room.y1 + 1, room.y2 - 1)

        gen_enemy((x, y))

        x = libtcodpy.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcodpy.random_get_int(0, room.y1 + 1, room.y2 - 1)

        gen_item((x, y))


def map_create_room(new_map, new_room):

    for x in range(new_room.x1, new_room.x2):
        for y in range(new_room.y1, new_room.y2):
            new_map[x][y].block_path = False


def map_create_tunnels(coords1, coords2, new_map):
    x1, y1 = coords1
    x2, y2 = coords2

    coin_flip = (libtcodpy.random_get_int(0, 0, 1) == 1)

    if coin_flip:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            new_map[x][y1].block_path = False
        for y in range(min(y1, y2), max(y1, y2) + 1):
            new_map[x2][y].block_path = False
    else:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            new_map[x1][y].block_path = False
        for x in range(min(x1, x2), max(x1, x2) + 1):
            new_map[x][y2].block_path = False


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
    SURFACE_MAP.fill(constants.COLOR_DEFAULT_BG)

    CAMERA.update()

    # draw the map
    draw_map(GAME.current_map)

    # draw all objects ---removed key=lambda obj: obj.depth
    for obj in sorted(GAME.current_objects, key=lambda obj: obj.depth, reverse=True):
        obj.draw()

    SURFACE_MAIN.blit(SURFACE_MAP, (0, 0), CAMERA.rectangle)

    draw_debug()
    draw_messages()


def draw_map(map_to_draw):

    cam_x, cam_y = CAMERA.map_address
    display_map_w = constants.CAMERA_WIDTH / constants.CELL_WIDTH
    display_map_h = constants.CAMERA_HEIGHT / constants.CELL_HEIGHT

    render_w_min = math.floor(cam_x - (display_map_w / 2))
    render_h_min = math.floor(cam_y - (display_map_h / 2))
    render_w_max = math.floor(cam_x + (display_map_w / 2))
    render_h_max = math.floor(cam_y + (display_map_h / 2))

    if render_w_min < 0:
        render_w_min = 0
    if render_h_min < 0:
        render_h_min = 0

    if render_w_max > constants.MAP_WIDTH:
        render_w_max = constants.MAP_WIDTH
    if render_h_max > constants.MAP_HEIGHT:
        render_h_max = constants.MAP_HEIGHT

    for x in range(render_w_min, render_w_max):
        for y in range(render_h_min, render_h_max):

            is_visible = libtcodpy.map_is_in_fov(FOV_MAP, x, y)

            if is_visible:

                map_to_draw[x][y].explored = True

                if map_to_draw[x][y].block_path == True:
                    # draw wall
                    SURFACE_MAP.blit(
                        ASSETS.S_WALL, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    # draw floor
                    SURFACE_MAP.blit(
                        ASSETS.S_FLOOR, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))

            elif map_to_draw[x][y].explored:

                if map_to_draw[x][y].block_path == True:
                    SURFACE_MAP.blit(
                        ASSETS.S_WALLEXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    SURFACE_MAP.blit(
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

    start_y = (constants.CAMERA_HEIGHT -
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

    SURFACE_MAP.blit(new_surface, (new_x, new_y))


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

    caster_location = (caster.x, caster.y)

    # Get target tile
    point_selected = menu_tile_select(
        coords_origin=caster_location, max_range=max_r, penetrate_walls=False, pierce_creature=False, radius=local_radius)

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
# UI
##############################################################################


class ui_Button:

    def __init__(self, surface, button_text, size, center_coords,
                 color_box_mouseover=constants.COLOR_RED,
                 color_box_default=constants.COLOR_GREEN,
                 color_text_mouseover=constants.COLOR_GREY,
                 color_text_default=constants.COLOR_GREY):

        self.surface = surface
        self.button_text = button_text
        self.size = size
        self.center_coords = center_coords

        self.c_box_mo = color_box_mouseover
        self.c_box_default = color_box_default
        self.c_text_mo = color_text_mouseover
        self.c_text_default = color_text_default
        self.current_c_box = color_box_default
        self.current_c_text = color_text_default

        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = center_coords

    def update(self, player_input):

        mouse_clicked = False

        local_events, local_mousepos = player_input
        mouse_x, mouse_y = local_mousepos

        mouse_over = (mouse_x >= self.rect.left
                      and mouse_x <= self.rect.right
                      and mouse_y >= self.rect.top
                      and mouse_y <= self.rect.bottom)

        for event in local_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_clicked = True

        if mouse_over and mouse_clicked:
            return True

        if mouse_over:
            self.current_c_box = self.c_box_mo
            self.current_c_text = self.c_text_mo
        else:
            self.current_c_box = self.c_box_default
            self.current_c_text = self.c_text_default

    def draw(self):

        pygame.draw.rect(self.surface, self.current_c_box, self.rect)
        draw_text(self.surface, self.button_text, constants.FONT_DEBUG_MESSAGE,
                  self.center_coords, self.current_c_text, center=True)


class ui_Slider:
    def __init__(self, surface, size, center_coords, bg_color, fg_color, parameter_value):

        self.surface = surface
        self.size = size
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.current_val = parameter_value

        self.bg_rect = pygame.Rect((0, 0), size)
        self.bg_rect.center = center_coords
        self.fg_rect = pygame.Rect(
            (0, 0), (self.bg_rect.width * self.current_val, self.bg_rect.height))
        self.fg_rect.topleft = self.bg_rect.topleft

        self.grip_tab = pygame.Rect((0, 0), (20, self.bg_rect.height + 4))
        self.grip_tab.center = (
            self.fg_rect.right, self.bg_rect.centery)

    def update(self, player_input):

        # Will be '1' if the left mouse button is held down
        mouse_down = pygame.mouse.get_pressed()[0]  # Returns a tuple (0,0,0)

        local_events, local_mousepos = player_input
        mouse_x, mouse_y = local_mousepos

        mouse_over = (mouse_x >= self.bg_rect.left
                      and mouse_x <= self.bg_rect.right
                      and mouse_y >= self.bg_rect.top
                      and mouse_y <= self.bg_rect.bottom)

        if mouse_down and mouse_over:
            self.current_val = (mouse_x - self.bg_rect.left)/self.bg_rect.width

            self.fg_rect.width = self.bg_rect.width * self.current_val

            self.grip_tab.center = (self.fg_rect.right, self.bg_rect.centery)

    def draw(self):
        # Draw bg rect ~ RED
        pygame.draw.rect(self.surface, self.bg_color, self.bg_rect)

        # Draw fg rect ~ GREEN
        pygame.draw.rect(self.surface, self.fg_color, self.fg_rect)

        # Draw the grip tab ~ BLACK
        pygame.draw.rect(self.surface, constants.COLOR_BLACK, self.grip_tab)


##############################################################################
# MENUS
##############################################################################


def menu_main():

    game_initialize()

    menu_running = True

    title_x = constants.CAMERA_WIDTH/2
    title_y = constants.CAMERA_HEIGHT/2 - 40
    title_text = "Kick-Ass Snickety Snake Game"

    # Button Addresses
    continue_button_y = title_y + 40
    new_button_y = continue_button_y + 40
    options_button_y = new_button_y + 40
    quit_button_y = options_button_y + 40

    continue_game_button = ui_Button(SURFACE_MAIN, "Continue", (150, 35),
                                     (title_x, continue_button_y))

    new_game_button = ui_Button(SURFACE_MAIN, "New Game", (150, 35),
                                (title_x, new_button_y))

    options_button = ui_Button(SURFACE_MAIN, "Options", (150, 35),
                               (title_x, options_button_y))

    quit_button = ui_Button(SURFACE_MAIN, "Quit", (150, 35),
                            (title_x, quit_button_y))

    pygame.mixer.music.load(ASSETS.music_background)
    pygame.mixer.music.play()

    while menu_running:

        list_of_events = pygame.event.get()
        mouse_position = pygame.mouse.get_pos()

        game_input = (list_of_events, mouse_position)

        # Handle Menu Events
        for event in list_of_events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Button updates
        if continue_game_button.update(game_input):
            pygame.mixer.music.stop()

            try:
                game_load()
            except:
                game_new()

            game_main_loop()
            game_initialize()

        if new_game_button.update(game_input):
            pygame.mixer.music.stop()
            game_new()
            game_main_loop()
            game_initialize()

        if options_button.update(game_input):
            menu_main_options()

        if quit_button.update(game_input):
            pygame.quit()
            sys.exit()

        SURFACE_MAIN.blit(ASSETS.MAIN_MENU_BG, (0, 0))

        draw_text(SURFACE_MAIN, title_text, constants.FONT_TITLE_SCREEN,
                  (title_x, title_y), constants.COLOR_RED, back_color=constants.COLOR_BLACK, center=True)

        # Draw menu
        continue_game_button.draw()
        new_game_button.draw()
        options_button.draw()
        quit_button.draw()

        # Update menu
        pygame.display.update()


def menu_main_options():

    # Menu Vars
    settings_menu_w = 200
    settings_menu_h = 200
    settings_menu_bgcolor = constants.COLOR_GREY

    # Slider Vars
    slider_x = constants.CAMERA_WIDTH/2
    sound_effect_slider_y = constants.CAMERA_HEIGHT/2 - 60
    sound_effect_vol = 0.5  # Sound is on a scale of 0.0 -> 1.0 in pygame.mixer
    music_effect_slider_y = constants.CAMERA_HEIGHT/2 - 10

    # Text Vars
    text_y_offset = 20
    sound_text_y = sound_effect_slider_y - text_y_offset
    music_text_y = music_effect_slider_y - text_y_offset

    # Button Vars
    button_save_y = music_effect_slider_y + 50

    window_center = (constants.CAMERA_WIDTH/2, constants.CAMERA_HEIGHT/2)

    settings_menu_surface = pygame.Surface((settings_menu_w, settings_menu_h))

    settings_menu_rect = pygame.Rect(0, 0, settings_menu_w, settings_menu_h)

    settings_menu_rect.center = window_center

    menu_close = False

    sound_effect_slider = ui_Slider(SURFACE_MAIN, (125, 15), (
        slider_x, sound_effect_slider_y), constants.COLOR_RED, constants.COLOR_GREEN, PREFERENCES.vol_sound)

    music_effect_slider = ui_Slider(SURFACE_MAIN, (125, 15), (
        slider_x, music_effect_slider_y), constants.COLOR_RED, constants.COLOR_GREEN, PREFERENCES.vol_music)

    save_button = ui_Button(SURFACE_MAIN,
                            "Save",
                            (100, 30),
                            (slider_x, button_save_y),
                            constants.COLOR_D_GREY,
                            constants.COLOR_GREEN,
                            constants.COLOR_BLACK,
                            constants.COLOR_BLACK)

    while not menu_close:

        list_of_events = pygame.event.get()
        mouse_position = pygame.mouse.get_pos()

        game_input = (list_of_events, mouse_position)

        # Handle Menu Events
        for event in list_of_events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_close = True

        current_sound_vol = PREFERENCES.vol_sound
        current_music_vol = PREFERENCES.vol_music

        sound_effect_slider.update(game_input)
        music_effect_slider.update(game_input)

        if current_sound_vol is not sound_effect_slider.current_val:
            PREFERENCES.vol_sound = sound_effect_slider.current_val
            ASSETS.volume_adjust()

        if current_music_vol is not music_effect_slider.current_val:
            PREFERENCES.vol_music = music_effect_slider.current_val
            ASSETS.volume_adjust()

        if save_button.update(game_input):
            preferences_save()
            menu_close = True

        # Draw the Menu
        settings_menu_surface.fill(settings_menu_bgcolor)
        SURFACE_MAIN.blit(settings_menu_surface, settings_menu_rect.topleft)
        draw_text(SURFACE_MAIN, "SOUND FX", constants.FONT_DEBUG_MESSAGE,
                  (slider_x, sound_text_y), constants.COLOR_BLACK, center=True)
        draw_text(SURFACE_MAIN, "MUSIC", constants.FONT_DEBUG_MESSAGE,
                  (slider_x, music_text_y), constants.COLOR_BLACK, center=True)
        sound_effect_slider.draw()
        music_effect_slider.draw()
        save_button.draw()

        pygame.display.update()


def menu_pause():
    ''' This menu pauses the game and displays a simple message '''
    menu_close = False

    window_width = constants.CAMERA_WIDTH
    window_height = constants.CAMERA_HEIGHT

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

    window_width = constants.CAMERA_WIDTH
    window_height = constants.CAMERA_HEIGHT

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
        mapx_pixel, mapy_pixel = CAMERA.win_to_map((mouse_x, mouse_y))

        map_coord_x = math.floor(mapx_pixel/constants.CELL_WIDTH)
        map_coord_y = math.floor(mapy_pixel/constants.CELL_HEIGHT)

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
        SURFACE_MAIN.fill(constants.COLOR_DEFAULT_BG)
        SURFACE_MAP.fill(constants.COLOR_BLACK)

        CAMERA.update()

        draw_map(GAME.current_map)

        for obj in GAME.current_objects:
            obj.draw()

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

        SURFACE_MAIN.blit(SURFACE_MAP, (0, 0), CAMERA.rectangle)

        draw_debug()
        draw_messages()

        # Update the display
        pygame.display.flip()

        # Tick the CLOCK
        CLOCK.tick(constants.GAME_FPS)


##############################################################################
# GENERATORS
##############################################################################


# PLAYER
def gen_player(coords):
    global PLAYER
    x, y = coords
    container_com = com_Container()
    creature_com = com_Creature(
        "Snicky", base_atk=4, hp=25, death_function=death_player)
    PLAYER = obj_Actor(x, y, "Python", "A_PLAYER",
                       animation_speed=1, creature=creature_com, container=container_com, depth=constants.DEPTH_PLAYER)
    GAME.current_objects.append(PLAYER)


# SPECIAL
def gen_stairs(coords, downwards=True):

    x, y = coords

    if downwards:
        stairs_com = com_Stairs()
        stairs = obj_Actor(
            x, y, "stairs", animation_key="S_STAIRS_DOWN", stairs=stairs_com)
    else:
        stairs_com = com_Stairs(downwards)
        stairs = obj_Actor(
            x, y, "stairs", animation_key="S_STAIRS_UP", stairs=stairs_com)

    GAME.current_objects.append(stairs)


def gen_portal(coords):

    x, y = coords

    port_com = com_ExitPortal()
    portal = obj_Actor(x, y, "exit portal",
                       animation_key="S_DOOR_CLOSE", exitportal=port_com)

    GAME.current_objects.append(portal)


def gen_LAMP(coords):
    x, y = coords

    item_com = com_Item()

    return_object = obj_Actor(
        x, y, "THE LAMP", animation_key="S_LAMP", item=item_com, depth=constants.DEPTH_ITEM)

    GAME.current_objects.append(return_object)


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
                              animation_key="S_SCROLL_01", item=item_com, depth=constants.DEPTH_ITEM)

    return return_object


def gen_scroll_fireball(coords):

    x, y = coords

    damage = libtcodpy.random_get_int(0, 2, 4)
    radius = 1
    m_range = libtcodpy.random_get_int(0, 9, 12)

    item_com = com_Item(use_function=cast_fireball,
                        value=(damage, radius, m_range))

    return_object = obj_Actor(x, y, "fireball scroll",
                              animation_key="S_SCROLL_02", item=item_com, depth=constants.DEPTH_ITEM)

    return return_object


def gen_scroll_confusion(coords):

    x, y = coords

    effect_length = libtcodpy.random_get_int(0, 5, 10)

    item_com = com_Item(use_function=cast_confusion,
                        value=effect_length)

    return_object = obj_Actor(x, y, "confusion scroll",
                              animation_key="S_SCROLL_03", item=item_com, depth=constants.DEPTH_ITEM)

    return return_object


def gen_weapon_sword(coords):

    x, y = coords

    bonus = libtcodpy.random_get_int(0, 1, 2)

    equipment_com = com_Equipment(attack_bonus=bonus)

    return_object = obj_Actor(
        x, y, "Short Sword", animation_key="S_SWORD", equipment=equipment_com, depth=constants.DEPTH_ITEM)

    return return_object


def gen_armor_shield(coords):

    x, y = coords

    bonus = libtcodpy.random_get_int(0, 1, 2)

    equipment_com = com_Equipment(defense_bonus=bonus)

    return_object = obj_Actor(
        x, y, "Small Shield", animation_key="S_SHIELD", equipment=equipment_com, depth=constants.DEPTH_ITEM)

    return return_object


# ENEMIES
def gen_enemy(coords):
    random_num = libtcodpy.random_get_int(0, 1, 100)

    if random_num <= 15:
        new_enemy = gen_aquatic_squid(coords)
    elif random_num <= 70:
        new_enemy = gen_mouse(coords)
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
    enemy = obj_Actor(x, y, "Rock Lobster", animation_key="A_ENEMY1",
                      animation_speed=1, creature=creature_com, ai=ai_com, item=item_com, depth=constants.DEPTH_ENEMY)
    return enemy


def gen_aquatic_squid(coords):

    x, y = coords

    max_health = libtcodpy.random_get_int(0, 12, 15)
    base_attack = libtcodpy.random_get_int(0, 3, 6)

    item_com = com_Item(use_function=cast_heal, value=5)
    creature_com = com_Creature(
        "Poots", base_atk=base_attack, hp=max_health, death_function=death_monster)
    ai_com = ai_Chase()
    enemy = obj_Actor(x, y, "Fugly Squid", animation_key="A_ENEMY2", animation_speed=1,
                      creature=creature_com, ai=ai_com, item=item_com, depth=constants.DEPTH_ENEMY)
    return enemy


def gen_mouse(coords):

    x, y = coords

    base_attack = 0

    max_health = 1

    creature_name = "Mousy"

    creature_com = com_Creature(
        creature_name, base_atk=base_attack, hp=max_health, death_function=death_mouse)

    ai_com = ai_Flee()

    item_com = com_Item(use_function=cast_heal, value=5)

    mouse = obj_Actor(x, y, "Mouse", animation_key="A_MOUSE",
                      animation_speed=1, creature=creature_com, item=item_com, ai=ai_com, depth=constants.DEPTH_ENEMY)

    return mouse


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
            game_exit()

        for obj in GAME.current_objects:
            if obj.ai:
                if player_action != "no-action":
                    obj.ai.take_turn()
            if obj.exitportal:
                obj.exitportal.update()

        if (PLAYER.state == "STATUS_DEAD" or PLAYER.state == "STATUS_WIN"):
            game_quit = True

        # draw the game
        draw_game()

        # update the game
        pygame.display.flip()

        # tick the CLOCK
        CLOCK.tick(constants.GAME_FPS)


def game_initialize():
    '''This function initializes the main window, and pygame'''

    global SURFACE_MAIN, SURFACE_MAP
    global CLOCK, FOV_CALCULATE, ASSETS, CAMERA, RANDOM_ENGINE
    global PREFERENCES
    # initialize pygame
    pygame.init()

    pygame.key.set_repeat(200, 70)  # first delay, 200ms, then 70ms after

    pygame.font.init()

    # Initialize Preferences
    try:
        preferences_load()
    except:
        PREFERENCES = struc_Preferences()

    SURFACE_MAIN = pygame.display.set_mode(
        (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))

    SURFACE_MAP = pygame.Surface(
        (constants.MAP_WIDTH * constants.CELL_WIDTH, constants.MAP_HEIGHT * constants.CELL_HEIGHT))

    CAMERA = obj_Camera()

    ASSETS = obj_Assets()

    CLOCK = pygame.time.Clock()

    # Random Number Engine
    RANDOM_ENGINE = random.SystemRandom()

    FOV_CALCULATE = True


def game_handle_keys():
    global FOV_CALCULATE
    # get player input
    keys_list = pygame.key.get_pressed()
    event_list = pygame.event.get()

    # Check for mod key
    MOD_KEY = (keys_list[pygame.K_RSHIFT] or keys_list[pygame.K_LSHIFT])

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

            if MOD_KEY and event.key == pygame.K_PERIOD:
                list_of_objects = map_objects_at_coords(PLAYER.x, PLAYER.y)
                for obj in list_of_objects:
                    if obj.stairs:
                        obj.stairs.use()
                    if obj.exitportal:
                        obj.exitportal.use()

    return "no-action"


def game_message(game_msg, msg_color=constants.COLOR_GREY):

    GAME.message_history.append((game_msg, msg_color))


def game_new():
    global GAME

    GAME = obj_Game()

    gen_player((0, 0))

    map_place_objects(GAME.current_rooms)


def game_exit():

    game_save()

    # Quit the game
    pygame.quit()
    sys.exit()


def game_save():
    for obj in GAME.current_objects:
        obj.animation_destroy()

    with gzip.open('savedata/savegame', 'wb') as file:
        pickle.dump([GAME, PLAYER], file)


def game_load():

    global GAME, PLAYER

    with gzip.open('savedata/savegame', 'rb') as file:
        GAME, PLAYER = pickle.load(file)

    for obj in GAME.current_objects:
        obj.animation_init()

    map_make_fov(GAME.current_map)


def game_continue():

    # Starts the game, or loads a saved game
    try:
        game_load()
    except:
        game_new()

    game_main_loop()


def preferences_save():
    with gzip.open('savedata/prefs', 'wb') as file:
        pickle.dump(PREFERENCES, file)


def preferences_load():
    global PREFERENCES

    with gzip.open('savedata/prefs', 'rb') as file:
        PREFERENCES = pickle.load(file)


if __name__ == '__main__':
    menu_main()
