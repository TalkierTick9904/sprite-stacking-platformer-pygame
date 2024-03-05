from settings import *
import math


# класс обычной сущности (по сути игрок)
class BaseEntity(pygame.sprite.Sprite):
    def __init__(self, app, name, character=False):
        self.app = app
        self.name = name
        self.group = app.main_group
        super().__init__(self.group)
        self.attrs = ENTITY_SPRITE_ATTRS[name]
        entity_cache = self.app.cache.entity_sprite_cache
        if character:
            self.images = entity_cache[name]["standing"]
        else:
            self.images = entity_cache[name]["images"]
        self.image = self.images[0]
        self.mask = entity_cache[name]["mask"]
        self.rect = self.image.get_rect()
        self.frame_index = 0

    # обновление кадра анимации
    def update(self):
        if self.app.anim_trigger:
            self.frame_index = (self.frame_index + 1) % len(self.images)
            self.image = self.images[self.frame_index]


# класс сущности (враги, дверь)
class Entity(BaseEntity):
    def __init__(self, app, name, pos, collision=False, character=False):
        super().__init__(app, name, character=character)
        if collision:
            self.app.collision_group.add(self)
        self.pos = vec2(pos) * TILE_SIZE
        self.player = app.player
        self.y_offset = vec2(0, self.attrs["y_offset"])
        self.screen_pos = vec2(0)

    def update(self):
        super().update()
        self.transform()
        self.set_rect()
        self.change_layer()

    # изменение позиции при перемещении игрока
    def transform(self):
        pos = self.pos - self.player.offset
        pos = pos.rotate_rad(self.player.angle)
        self.screen_pos = pos + CENTER

    # смена слоя при пересечении с объектами
    def change_layer(self):
        if self.group.has(self):
            self.group.change_layer(self, self.screen_pos.y)

    # изменение координат
    def set_rect(self):
        self.rect.center = self.screen_pos + self.y_offset

# класс взрыва
class Explosion(Entity):
    def __init__(self, app, pos):
        super().__init__(app, "explosion", pos)
        self.life_time_cycles = self.attrs["num_layers"]
        self.cycles = 0

    def update(self):
        super().update()
        self.check_life_time()

    # удаление спрайта после истечении срока жизни
    def check_life_time(self):
        if self.app.anim_trigger:
            self.cycles += 1
            if self.cycles >= self.life_time_cycles:
                self.kill()


# класс пули
class Bullet(BaseEntity):
    def __init__(self, app, pos, enemy=None):
        super().__init__(app, "bullet")
        self.pos = pos
        self.player = app.player
        self.y_offset = self.attrs["y_offset"]
        self.speed = 0.7
        self.bullet_direction = vec2(0, -self.speed)
        self.angle = self.player.angle
        self.life_time_cycles = 20
        self.cycles = 0
        self.enemy = enemy
        # если пулю выпустил враг, то изменяем направление
        if self.enemy:
            x_diff = self.player.offset.x - self.enemy.pos.x
            y_diff = self.player.offset.y - self.enemy.pos.y
            dist = math.sqrt(x_diff ** 2 + y_diff ** 2)
            self.bullet_direction = vec2(x_diff / dist * self.speed, y_diff / dist * self.speed)

    # проверка столкновений
    def check_collision(self):
        hits = pygame.sprite.spritecollide(self, self.app.collision_group, dokill=False, collided=pygame.sprite.collide_mask) # type: ignore
        if hits:
            if self.enemy and hits == [self.enemy]:
                return
            for sprite in hits:
                # разрушение коробки
                if sprite.name == "box":
                    self.app.boxes_destroyed += 1
                    pygame.mixer.Sound.play(SOUNDS["box"])
                    sprite.kill()
                # если сталкивается с врагом
                if not self.enemy and sprite.name == "enemy" and not sprite.dead:
                    sprite.hp -= 1
                    if sprite.hp == 0:
                        # смерть врага
                        self.app.enemies_killed += 1
                        CHANNELS["enemy_walking"].stop()
                        pygame.mixer.Sound.play(SOUNDS["death"])
                        sprite.dead = True
                    else:
                        # нанесение урона врагу
                        sprite.attacking = False
                        sprite.damaging = True
                        sprite.frame_index = 0
                        entity_cache = self.app.cache.entity_sprite_cache
                        sprite.images = entity_cache[sprite.name]["damaging"]
                        pygame.mixer.Sound.play(SOUNDS["damage"])
            pygame.mixer.Sound.play(SOUNDS["explosion"])
            # создание взрыва
            Explosion(self.app, self.pos / TILE_SIZE)
            self.kill()
        # если пуля от врага попадает в игрока
        if self.enemy:
            hit = pygame.sprite.collide_mask(self, self.player)
            if hit:
                if self.player.hp > 0:
                    self.player.hp -= 1
                if self.player.hp == 0:
                    # смерть игрока
                    CHANNELS["walking"].stop()
                    self.app.player.dead = True
                    pygame.mixer.Sound.play(SOUNDS["death"])
                elif not self.player.dead:
                    # нанесение урона игроку
                    self.app.player.damaging = True
                    self.app.player.attacking = False
                    entity_cache = self.app.cache.entity_sprite_cache
                    self.app.player.frame_index = 0
                    self.app.player.images = entity_cache[self.app.player.name]["damaging"]
                    pygame.mixer.Sound.play(SOUNDS["damage"])
                # создание взрыва
                pygame.mixer.Sound.play(SOUNDS["explosion"])
                Explosion(self.app, self.pos / TILE_SIZE)
                self.kill()

    # смена слоя
    def change_layer(self):
        if self.group.has(self):
            self.group.change_layer(self, self.rect.centery - self.y_offset)

    # проверка времени жизни
    def check_life_time(self):
        if self.app.anim_trigger:
            self.cycles += 1
            if self.cycles > self.life_time_cycles:
                self.kill()

    # поворот относительно игрока
    def rotate(self):
        pos = self.pos - self.player.offset
        pos = pos.rotate_rad(self.player.angle)
        self.rect.center = pos + CENTER + vec2(0, self.y_offset)

    # перемещение по траектории
    def run(self):
        bullet_direction = self.bullet_direction * self.app.speed
        if self.enemy:
            self.pos += bullet_direction
        else:
            self.pos += bullet_direction.rotate_rad(-self.angle)

    def update(self):
        self.run()
        self.rotate()
        self.change_layer()
        self.check_life_time()
        self.check_collision()


# класс сложенного спрайта (все объекты, которые кажутся трехмерными)
class StackedSprite(pygame.sprite.Sprite):
    def __init__(self, app, name, pos, rot, collision=True):
        self.app = app
        self.name = name
        self.pos = vec2(pos) * TILE_SIZE
        self.player = app.player
        self.group = app.main_group
        super().__init__(self.group)
        if collision:
            self.app.collision_group.add(self)
        self.attrs = STACKED_SPRITE_ATTRS[name]
        self.y_offset = vec2(0, self.attrs["y_offset"])
        self.cache = app.cache.stacked_sprite_cache
        self.viewing_angle = app.cache.viewing_angle
        self.rotated_sprites = self.cache[name]["rotated_sprites"]
        self.collision_masks = self.cache[name]["collision_masks"]
        self.angle = 0
        self.screen_pos = vec2(0)
        self.rot = (rot % 360) // self.viewing_angle
        self.image = self.rotated_sprites[self.angle]
        self.mask = self.collision_masks[self.angle]
        self.rect = self.image.get_rect()

    # смена слоя при пересечении c объектами
    def change_layer(self):
        if self.group.has(self):
            self.group.change_layer(self, self.screen_pos.y)

    # изменение положения относительно игрока
    def transform(self):
        pos = self.pos - self.player.offset
        pos = pos.rotate_rad(self.player.angle)
        self.screen_pos = pos + CENTER

    # получение угла относительно игрока
    def get_angle(self):
        self.angle = -math.degrees(self.player.angle) // self.viewing_angle + self.rot
        self.angle = int(self.angle % NUM_ANGLES)

    def update(self):
        self.transform()
        self.get_angle()
        self.get_image()
        self.change_layer()

    # получение изображения по углу
    def get_image(self):
        self.image = self.rotated_sprites[self.angle]
        self.mask = self.collision_masks[self.angle]
        self.rect = self.image.get_rect(center=self.screen_pos + self.y_offset)
