from random import uniform
from characters import Enemy
from objects import *
from settings import *


# класс основной сцены игры
class Scene:
    def __init__(self, app):
        self.app = app
        self.map = [[]]
        self.load_level()
        self.rotating_objects = []
        self.load_scene()

    # загрузка сцены
    def load_scene(self):
        coins = 0
        for i, row in enumerate(self.map):
            for j, name in enumerate(row):
                pos = vec2(j + 0.5, i + 0.5)
                # расстановка объектов из файла с уровнем по экрану
                if name not in OBJECTS.keys():
                    continue
                name = OBJECTS[name]
                if name == "player":
                    self.app.player.offset = pos * TILE_SIZE
                elif name == "enemy":
                    Enemy(self.app, pos, ENEMY_HP)
                elif name == "door":
                    Entity(self.app, name, pos, collision=True)
                elif name == "grass":
                    StackedSprite(self.app, name, pos + vec2(uniform(-0.25, 0.25)), uniform(0, 360), collision=False)
                elif name == "box":
                    StackedSprite(self.app, name, pos, uniform(0, 360))
                elif name == "coin":
                    coins += 1
                    obj = StackedSprite(self.app, name, pos + vec2(uniform(-0.25, 0.25)), uniform(0, 360))
                    self.rotating_objects.append(obj)
                elif name == "medkit":
                    obj = StackedSprite(self.app, name, pos + vec2(uniform(-0.25, 0.25)), uniform(0, 360))
                    self.rotating_objects.append(obj)
                elif name == "wall":
                    if i == 0:
                        StackedSprite(self.app, name, pos, 90)
                    elif i == len(self.map) - 1:
                        StackedSprite(self.app, name, pos, 90)
                    else:
                        StackedSprite(self.app, name, pos, 0)
                elif name == "tower":
                    if i == 0:
                        if j == 0:
                            StackedSprite(self.app, name, pos, 0)
                        else:
                            StackedSprite(self.app, name, pos, 270)
                    else:
                        if j == 0:
                            StackedSprite(self.app, name, pos, 90)
                        else:
                            StackedSprite(self.app, name, pos, 180)
                else:
                    StackedSprite(self.app, name, pos + vec2(uniform(-0.25, 0.25)), uniform(0, 360))
            self.app.coins_level = coins

    # загрузка значений из следующего уровня
    def load_level(self):
        self.map = LEVELS[self.app.level_number-1]

    # поворот сцены относительно игрока
    def rotate(self):
        for obj in self.rotating_objects:
            obj.rot = 30 * self.app.time

    # загрузка следующего уровня
    def next_level(self):
        if len(LEVELS) <= self.app.level_number:
            return True
        self.app.to_save = {
            "hp": self.app.player.hp_on_start,
            "level_number": self.app.level_number + 1,
            "coins_collected": self.app.coins_collected,
            "enemies_killed": self.app.enemies_killed,
            "bullets_shot": self.app.bullets_shot,
            "boxes_destroyed": self.app.boxes_destroyed,
            "hp_healed": self.app.hp_healed,
        }
        self.app.level_number += 1
        for sprite in self.app.main_group:
            if sprite.name == "player":
                sprite.angle = 0
                continue
            sprite.kill()
        self.load_level()
        self.rotating_objects = []
        self.load_scene()
        return False

    def update(self):
        self.rotate()
