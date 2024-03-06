import os
import re
import sys
import pygame
from pathlib import Path

# в этом файле все переменные, которые используются в разных файлах проекта
pygame.init()
vec2 = pygame.math.Vector2
info = pygame.display.Info()
RES = WIDTH, HEIGHT = vec2(info.current_w, info.current_h)
CENTER = H_WIDTH, H_HEIGHT = RES // 2
TILE_SIZE = 250
PLAYER_SPEED = 0.4
PLAYER_ROT_SPEED = 0.002
BG_COLOR = (106, 145, 35)
MENU_COLOR = (244, 243, 215)
MENU_ALT_COLOR = (11, 11, 11)
NUM_ANGLES = 180  # multiple of 360 -> 24, 30, 36, 40, 45, 60, 72, 90, 120, 180
PLAYER_HP, ENEMY_HP = 5, 3
MUSIC_VOLUME = 50
SFX_VOLUME = 50
# загрузка настроек из файла и создание такого, если его нет
if not os.path.isdir("data"):
    os.mkdir("data")
if os.path.isfile(Path("data/settings.txt")):
    with open(Path("data/settings.txt"), "r") as file:
        for line in file.readlines():
            key, val = line.split()
            if key == "MUSIC_VOLUME":
                MUSIC_VOLUME = int(val)
            elif key == "SFX_VOLUME":
                SFX_VOLUME = int(val)
else:
    with open(Path("data/settings.txt"), "w") as file:
        file.write(f"MUSIC_VOLUME {MUSIC_VOLUME}\nSFX_VOLUME {SFX_VOLUME}\n")
# все звуки в игре
SOUNDS = {
    "shot": pygame.mixer.Sound(Path("assets/sounds/shot.ogg")),
    "explosion": pygame.mixer.Sound(Path("assets/sounds/explosion.wav")),
    "walking": pygame.mixer.Sound(Path("assets/sounds/walking.wav")),
    "sprinting": pygame.mixer.Sound(Path("assets/sounds/sprinting.wav")),
    "door": pygame.mixer.Sound(Path("assets/sounds/door.wav")),
    "box": pygame.mixer.Sound(Path("assets/sounds/box.wav")),
    "coin": pygame.mixer.Sound(Path("assets/sounds/coin.wav")),
    "damage": pygame.mixer.Sound(Path("assets/sounds/damage.ogg")),
    "death": pygame.mixer.Sound(Path("assets/sounds/death.wav")),
    "heal": pygame.mixer.Sound(Path("assets/sounds/heal.wav")),
}
for name, sound in SOUNDS.items():
    sound.set_volume(SFX_VOLUME / 100)
pygame.mixer.music.set_volume(MUSIC_VOLUME / 100)
# каналы со звуками ходьбы и спринта
CHANNELS = {
    "walking": pygame.mixer.Channel(2),
    "sprinting": pygame.mixer.Channel(3),
    "enemy_walking": pygame.mixer.Channel(4),
}
# анимации в меню
MENU_ANIMATIONS_ATTRS = {
    "main_menu": {
        "path": Path("assets/menu_animations/main_menu.png"),
        "num_layers": 8,
        "scale": 20,
    },
    "pause_menu": {
        "path": Path("assets/menu_animations/pause_menu.png"),
        "num_layers": 4,
        "scale": 15,
    },
    "win_menu": {
        "path": Path("assets/menu_animations/win_menu.png"),
        "num_layers": 4,
        "scale": 20,
    },
    "lose_menu": {
        "path": Path("assets/menu_animations/lose_menu.png"),
        "num_layers": 4,
        "scale": 20,
    },
}
# иконки
ICONS = {
    "health": Path("assets/icons/health.png"),
    "coins": Path("assets/icons/coins.png"),
    "level": Path("assets/icons/level.png"),
    "reloading": Path("assets/icons/reloading.png"),
    "sprinting": Path("assets/icons/sprinting.png"),
}
# сущности
ENTITY_SPRITE_ATTRS = {
    "player": {
        "walking": Path("assets/entities/player/player_walking.png"),
        "standing": Path("assets/entities/player/player_standing.png"),
        "dying": Path("assets/entities/player/player_dying.png"),
        "attacking": Path("assets/entities/player/player_attacking.png"),
        "damaging": Path("assets/entities/player/player_damaging.png"),
        "sprinting": Path("assets/entities/player/player_sprinting.png"),
        "mask_path": Path("assets/entities/player/mask.png"),
        "num_layers": 4,
        "scale": 8,
        "y_offset": 0,
    },
    "enemy": {
        "walking": Path("assets/entities/enemy/enemy_walking.png"),
        "standing": Path("assets/entities/enemy/enemy_standing.png"),
        "dying": Path("assets/entities/enemy/enemy_dying.png"),
        "attacking": Path("assets/entities/enemy/enemy_attacking.png"),
        "damaging": Path("assets/entities/enemy/enemy_damaging.png"),
        "mask_path": Path("assets/entities/enemy/mask.png"),
        "num_layers": 4,
        "scale": 8,
        "y_offset": 0,
    },
    "explosion": {
        "num_layers": 7,
        "scale": 1,
        "path": Path("assets/entities/explosion/explosion.png"),
        "y_offset": 50,
    },
    "bullet": {
        "num_layers": 1,
        "scale": 0.4,
        "path": Path("assets/entities/bullet/bullet.png"),
        "y_offset": 50,
    },
    "door": {
        "num_layers": 1,
        "scale": 4,
        "path": Path("assets/entities/door/door_closed.png"),
        "alt": Path("assets/entities/door/door_open.png"),
        "mask_path": Path("assets/entities/door/mask.png"),
        "y_offset": -30,
    },
}
# сложенные спрайты
STACKED_SPRITE_ATTRS = {
    "coin": {
        "path": Path("assets/stacked_sprites/coin.png"),
        "num_layers": 18,
        "scale": 5,
        "y_offset": 0,
    },
    "medkit": {
        "path": Path("assets/stacked_sprites/medkit.png"),
        "num_layers": 24,
        "scale": 3.5,
        "y_offset": 0
    },
    "box": {
        "path": Path("assets/stacked_sprites/box.png"),
        "num_layers": 12,
        "scale": 8,
        "y_offset": 10,
    },
    "grass": {
        "path": Path("assets/stacked_sprites/grass.png"),
        "num_layers": 12,
        "scale": 7,
        "y_offset": 20,
        "outline": False,
    },
    "tree": {
        "path": Path("assets/stacked_sprites/tree.png"),
        "num_layers": 43,
        "scale": 8,
        "y_offset": -130,
        "transparency": True,
        "mask_layer": 3,
    },
    "wall": {
        "path": Path("assets/stacked_sprites/wall.png"),
        "num_layers": 21,
        "scale": 10,
        "y_offset": 10,
    },
    "tower": {
        "path": Path("assets/stacked_sprites/tower.png"),
        "num_layers": 21,
        "scale": 11,
        "y_offset": 10,
    },
}
# все объекты
OBJECTS = {"P": "player", "E": "enemy", "D": "door", "R": "tree", "G": "grass",
           "B": "box", "W": "wall", "T": "tower", "C": "coin", "M": "medkit"}
# загрузка уровней из папки
LEVELS = []
level_path = Path("assets/levels")
path_list = []
for path in os.listdir(level_path):
    path = os.path.join(level_path, path)
    if os.path.isfile(path) and re.match("^level_[0-9]+\.txt$", os.path.split(path)[1]): # type: ignore
        path_list.append(path)
path_list = sorted(path_list, key=lambda x: int(os.path.split(x)[1].split("_")[-1].strip(".txt")))
for path in path_list:
    with open(path, "r") as file:
        level = [line.strip().split() for line in file]
    if level:
        LEVELS.append(level)
if not LEVELS:
    print("No levels in folder")
    sys.exit(1)
# загрузка сейвов из папки
SAVES = dict()
save_path = Path("data/saves")
path_list = []
if os.path.isdir(save_path):
    for path in os.listdir(save_path):
        path = os.path.join(save_path, path)
        if os.path.isfile(path) and re.match("^.+\.txt$", os.path.split(path)[1]): # type: ignore
            SAVES[os.path.split(path)[1][:-4]] = path
else:
    os.mkdir(save_path)
