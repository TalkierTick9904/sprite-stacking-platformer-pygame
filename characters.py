from settings import *
from objects import BaseEntity, Entity, Bullet
import math
import random


# класс игрока
class Player(BaseEntity):
    def __init__(self, app, hp):
        super().__init__(app, "player", character=True)
        # перемещение игрока в центр
        self.group.change_layer(self, CENTER.y)
        self.rect = self.image.get_rect(center=CENTER)
        # переменные с говорящими названиями
        self.offset = vec2(0)
        self.inc = vec2(0)
        self.prev_inc = vec2(0)
        self.angle = 0
        self.moving = False
        self.sprinting = False
        self.sprintinglock = False
        self.shooting = True
        self.dead = False
        self.deadlock = False
        self.attacking = False
        self.damaging = False
        self.dead_cycles = 0
        self.reload_cycles = 20
        self.sprint_cycles = 30.0
        self.max_hp = hp
        self.hp = hp
        self.hp_on_start = hp

    # расчет изменения положения игрока
    def control(self):
        self.inc = vec2(0)
        speed = PLAYER_SPEED * self.app.speed
        rot_speed = PLAYER_ROT_SPEED * self.app.speed
        key_state = pygame.key.get_pressed()
        if key_state[pygame.K_LSHIFT] or key_state[pygame.K_RSHIFT]:
            # начало спринта при нажатом shift
            self.sprinting = True
            speed *= 1.5
        if self.sprinting and self.sprint_cycles < 1:
            self.sprinting = False
            speed /= 1.5
        # изменение угла обзора
        if key_state[pygame.K_q]:
            self.angle += rot_speed
        if key_state[pygame.K_e]:
            self.angle -= rot_speed
        # изменение положения
        if key_state[pygame.K_w]:
            self.inc += vec2(0, -speed)
        if key_state[pygame.K_s]:
            self.inc += vec2(0, speed)
        if key_state[pygame.K_a]:
            self.inc += vec2(-speed, 0)
        if key_state[pygame.K_d]:
            self.inc += vec2(speed, 0)
        # если перемещение по двум осям, то скорость регулируется
        if self.inc.x and self.inc.y:
            self.inc *= 1 / math.sqrt(2)
        # начало спринта
        if self.sprinting and self.moving and not (self.attacking or self.damaging) and not self.sprintinglock and self.sprint_cycles >= 1:
            self.sprintinglock = True
            # смена анимации
            self.frame_index = 0
            entity_cache = self.app.cache.entity_sprite_cache
            self.images = entity_cache[self.name]["sprinting"]
            CHANNELS["walking"].stop()
            CHANNELS["sprinting"].play(SOUNDS["sprinting"], -1)
        # начало остановки
        if self.inc == vec2(0) and self.moving and not (self.attacking or self.damaging):
            self.moving = False
            self.sprintinglock = False
            # смена анимации
            self.frame_index = 0
            entity_cache = self.app.cache.entity_sprite_cache
            self.images = entity_cache[self.name]["standing"]
            CHANNELS["walking"].stop()
            CHANNELS["sprinting"].stop()
        # начало движения
        elif self.inc != vec2(0) and not self.moving and not (self.attacking or self.damaging) and not self.sprintinglock:
            self.moving = True
            self.frame_index = 0
            entity_cache = self.app.cache.entity_sprite_cache
            self.images = entity_cache[self.name]["walking"]
            CHANNELS["walking"].play(SOUNDS["walking"], -1)
        # прекращение спринта
        if not self.sprinting and self.sprintinglock and self.moving:
            self.sprintinglock = False
            # смена анимации
            self.frame_index = 0
            entity_cache = self.app.cache.entity_sprite_cache
            self.images = entity_cache[self.name]["walking"]
            CHANNELS["sprinting"].stop()
            CHANNELS["walking"].play(SOUNDS["walking"], -1)
        self.sprinting = False
        self.inc.rotate_ip_rad(-self.angle)

    # обработка ивента стрельбы
    def shoot(self):
        if self.shooting:
            self.app.bullets_shot += 1
            self.reload_cycles = 0
            self.shooting = False
            entity_cache = self.app.cache.entity_sprite_cache
            self.attacking = True
            self.damaging = False
            self.frame_index = 0
            self.images = entity_cache[self.name]["attacking"]
            pygame.mixer.Sound.play(SOUNDS["shot"])
            # спавн пули
            Bullet(self.app, self.offset[:])

    # проверка коллизии
    def check_collision(self):
        hits = pygame.sprite.spritecollide(self, self.app.collision_group, dokill=False, collided=pygame.sprite.collide_mask) # type: ignore
        if not hits:
            # откат движения
            if self.inc.x or self.inc.y:
                self.prev_inc = self.inc
        else:
            for sprite in hits:
                # сбор монетки
                if sprite.name == "coin":
                    pygame.mixer.Sound.play(SOUNDS["coin"])
                    self.app.coins_level_collected += 1
                    sprite.kill()
                # обработка перехода на новый уровень
                if sprite.name == "door" and self.app.level_completed:
                    self.app.coins_collected += self.app.coins_level
                    self.app.coins_level_collected = 0
                    self.app.coins_level = 0
                    self.app.level_completed = False
                    self.hp_on_start = self.hp
                    self.app.won = self.app.scene.next_level()
                    break
                # восстановление здоровья
                if sprite.name == "medkit":
                    pygame.mixer.Sound.play(SOUNDS["heal"])
                    self.app.hp_healed += PLAYER_HP - self.hp
                    self.hp = PLAYER_HP
                    sprite.kill()
            # замена спрайта двери
            if self.app.coins_level_collected == self.app.coins_level and not self.app.level_completed and not self.app.won and not self.app.lost:
                for sprite in self.app.main_group:
                    if sprite.name == "door":
                        entity_cache = self.app.cache.entity_sprite_cache
                        sprite.images = entity_cache[sprite.name]["alt"]
                        pygame.mixer.Sound.play(SOUNDS["door"])
                self.app.level_completed = True
            self.inc = -self.prev_inc

    # движение игрока
    def move(self):
        self.offset += self.inc

    def update(self):
        # смена анимации при смерти
        if self.dead and not self.deadlock:
            entity_cache = self.app.cache.entity_sprite_cache
            images = entity_cache[self.name]["dying"]
            self.images = images
            self.frame_index = 0
            self.deadlock = True
            self.dead_cycles = 0
            return
        # задержка для проигрывания анимации смерти
        elif self.dead:
            entity_cache = self.app.cache.entity_sprite_cache
            images = entity_cache[self.name]["dying"]
            self.images = images
            if self.frame_index == len(images) - 1:
                self.frame_index = len(images) - 2
                self.images = [images[-1]]
            super().update()
            if self.app.anim_trigger:
                self.dead_cycles += 1
                if self.dead_cycles > 5:
                    self.app.lost = True
                return
        super().update()
        # откат анимации после атаки
        if self.frame_index == 3 and self.attacking:
            self.attacking = False
            entity_cache = self.app.cache.entity_sprite_cache
            self.frame_index = 0
            if self.sprintinglock:
                self.images = entity_cache[self.name]["sprinting"]
            elif self.moving:
                self.images = entity_cache[self.name]["walking"]
            else:
                self.images = entity_cache[self.name]["standing"]
        # откат анимации после получения урона
        if self.frame_index == 3 and self.damaging:
            self.damaging = False
            entity_cache = self.app.cache.entity_sprite_cache
            self.frame_index = 0
            if self.sprintinglock:
                self.images = entity_cache[self.name]["sprinting"]
            elif self.moving:
                self.images = entity_cache[self.name]["walking"]
            else:
                self.images = entity_cache[self.name]["standing"]
        self.control()
        self.check_collision()
        self.move()
        # обработка перезарядок
        if self.app.anim_trigger:
            if self.sprintinglock and self.sprint_cycles >= 1:
                self.sprint_cycles = round(self.sprint_cycles - 1.0, 1)
            elif self.sprintinglock:
                self.sprint_cycles = 0
            elif self.sprint_cycles < 30:
                self.sprint_cycles = round(self.sprint_cycles + 0.2, 1)
            if self.reload_cycles < 20:
                self.reload_cycles += 1
            elif self.reload_cycles == 20:
                self.shooting = True


# класс игрока
class Enemy(Entity):
    def __init__(self, app, pos, hp):
        super().__init__(app, "enemy", pos, collision=True, character=True)
        self.inc = vec2(0)
        self.prev_inc = vec2(0)
        self.moving = False
        self.attacking = False
        self.dead = False
        self.deadlock = False
        self.damaging = False
        self.shoot_cycles = 0
        self.hp = hp

    # обработка движения
    def calculate(self):
        self.inc = vec2(0)
        speed, radius = PLAYER_SPEED / 2 * self.app.speed, 200
        # приближение к игроку на окружность с определенным радиусом
        x_diff = self.app.player.offset.x - self.pos.x
        y_diff = self.app.player.offset.y - self.pos.y
        dist = math.sqrt(x_diff ** 2 + y_diff ** 2)
        if dist > radius:
            self.inc += vec2(x_diff / dist * speed, y_diff / dist * speed)
        # начало остановки 
        if self.inc == vec2(0) and self.moving:
            self.moving = False
            # смена анимации
            entity_cache = self.app.cache.entity_sprite_cache
            self.images = entity_cache[self.name]["standing"]
            CHANNELS["enemy_walking"].stop()
        # начало движения
        elif self.inc != vec2(0) and not self.moving:
            self.moving = True
            # смена анимации
            entity_cache = self.app.cache.entity_sprite_cache
            self.images = entity_cache[self.name]["walking"]
            CHANNELS["enemy_walking"].play(SOUNDS["walking"], -1)

    # обработка ивента стрельбы
    def shoot(self):
        if self.app.anim_trigger and not self.app.player.dead:
            if self.shoot_cycles < 20:
                self.shoot_cycles += 1
            elif self.shoot_cycles == 20:
                shoots = random.randint(-10, 10)
                if shoots <= 0:
                    return
                self.shoot_cycles = 0
                self.frame_index = 0
                self.attacking = True
                self.damaging = False
                entity_cache = self.app.cache.entity_sprite_cache
                self.images = entity_cache[self.name]["attacking"]
                pygame.mixer.Sound.play(SOUNDS["shot"])
                # спавн пули
                Bullet(self.app, self.pos[:], enemy=self)

    # проверка столкновений
    def check_collision(self):
        hits = pygame.sprite.spritecollide(self, self.app.collision_group, dokill=False, collided=pygame.sprite.collide_mask) # type: ignore
        if hits == [self]:
            if self.inc.x or self.inc.y:
                self.prev_inc = self.inc
        else:
            self.inc = -self.prev_inc

    # передвижение
    def move(self):
        self.pos += self.inc

    def update(self):
        # смена анимации при смерти
        if self.dead and not self.deadlock:
            entity_cache = self.app.cache.entity_sprite_cache
            images = entity_cache[self.name]["dying"]
            self.images = images
            self.frame_index = 0
            self.deadlock = True
            return
        # задержка для проигрывания анимации смерти
        elif self.dead:
            entity_cache = self.app.cache.entity_sprite_cache
            images = entity_cache[self.name]["dying"]
            self.images = images
            if self.frame_index == len(images) - 1:
                self.frame_index = len(images) - 2
                self.images = [images[-1]]
            super().update()
            return
        super().update()
        # откат анимации после атаки
        if self.frame_index == 3 and self.attacking:
            self.attacking = False
            entity_cache = self.app.cache.entity_sprite_cache
            self.frame_index = 0
            if self.moving:
                self.images = entity_cache[self.name]["walking"]
            else:
                self.images = entity_cache[self.name]["standing"]
        # откат анимации после получения урона
        if self.frame_index == 3 and self.damaging:
            self.damaging = False
            entity_cache = self.app.cache.entity_sprite_cache
            self.frame_index = 0
            if self.moving:
                self.images = entity_cache[self.name]["walking"]
            else:
                self.images = entity_cache[self.name]["standing"]
        self.shoot()
        self.calculate()
        self.check_collision()
        self.move()
