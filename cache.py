from settings import *

# класс, отвечающий за кеширование спрайтов и анимаций
class Cache:
    def __init__(self):
        self.stacked_sprite_cache = {}
        self.entity_sprite_cache = {}
        # определение количества углов обзора сложенных спрайтов (stacked sprites)
        self.viewing_angle = 360 // NUM_ANGLES
        # толщина обводки сложенных спрайтов
        self.outline_thickness = 5
        # запись кеша в переменные
        self.get_stacked_sprite_cache()
        self.get_entity_sprite_cache()

    def get_entity_sprite_cache(self):
        # кеширование сушностей (просто анимированные спрайты)
        for sprite_name in ENTITY_SPRITE_ATTRS:
            self.entity_sprite_cache[sprite_name] = {}
            attrs = ENTITY_SPRITE_ATTRS[sprite_name]
            # обработка разных файлов анимаций
            if sprite_name in ("player", "enemy"):
                walking = self.get_layer_array(attrs, custom="walking")[::-1]
                dying = self.get_layer_array(attrs, custom="dying")[::-1]
                standing = self.get_layer_array(attrs, custom="standing")[::-1]
                attacking = self.get_layer_array(attrs, custom="attacking")[::-1]
                damaging = self.get_layer_array(attrs, custom="damaging")[::-1]
                self.entity_sprite_cache[sprite_name]["standing"] = standing
                self.entity_sprite_cache[sprite_name]["walking"] = walking
                self.entity_sprite_cache[sprite_name]["dying"] = dying
                self.entity_sprite_cache[sprite_name]["attacking"] = attacking
                self.entity_sprite_cache[sprite_name]["damaging"] = damaging
                if sprite_name == "player":
                    sprinting = self.get_layer_array(attrs, custom="sprinting")[::-1]
                    self.entity_sprite_cache[sprite_name]["sprinting"] = sprinting
                mask = self.get_entity_mask(attrs, standing)
            # обработка альтернативной картинки
            elif "alt" in attrs.keys():
                alt = self.get_layer_array(attrs)[::-1]
                images = self.get_layer_array(attrs, custom="alt")[::-1]
                self.entity_sprite_cache[sprite_name]["images"] = images
                self.entity_sprite_cache[sprite_name]["alt"] = alt
                mask = self.get_entity_mask(attrs, images)
            # обработка основной картинки
            else:
                images = self.get_layer_array(attrs)[::-1]
                self.entity_sprite_cache[sprite_name]["images"] = images
                mask = self.get_entity_mask(attrs, images)
            self.entity_sprite_cache[sprite_name]["mask"] = mask

    # получение или создание маски сущности
    def get_entity_mask(self, attrs, images):
        path = attrs.get("mask_path", False)
        if not path:
            return pygame.mask.from_surface(images[0])
        else:
            scale = attrs["scale"]
            mask_image = pygame.image.load(path).convert_alpha()
            mask_image = pygame.transform.scale(mask_image, vec2(mask_image.get_size()) * scale)
            return pygame.mask.from_surface(mask_image)

    # кеширование сложенных спрайтов
    def get_stacked_sprite_cache(self):
        for obj_name in STACKED_SPRITE_ATTRS:
            self.stacked_sprite_cache[obj_name] = {
                "rotated_sprites": {},
                "collision_masks": {}
            }
            attrs = STACKED_SPRITE_ATTRS[obj_name]
            layer_array = self.get_layer_array(attrs)
            self.run_prerender(obj_name, layer_array, attrs)

    # рендеринг всех слоев сложенного спрайта
    def run_prerender(self, obj_name, layer_array, attrs):
        outline = attrs.get("outline", True)
        mask_layer = attrs.get("mask_layer", attrs["num_layers"] // 2)
        # рендер с каждого угла
        for angle in range(NUM_ANGLES):
            surf = pygame.Surface(layer_array[0].get_size())
            surf = pygame.transform.rotate(surf, angle * self.viewing_angle)
            sprite_surf = pygame.Surface([surf.get_width(), surf.get_height() + attrs["num_layers"] * attrs["scale"]])
            sprite_surf.fill("khaki")
            sprite_surf.set_colorkey("khaki")
            for ind, layer in enumerate(layer_array):
                layer = pygame.transform.rotate(layer, angle * self.viewing_angle)
                sprite_surf.blit(layer, (0, ind * attrs["scale"]))
                if ind == mask_layer:
                    surf = pygame.transform.flip(sprite_surf, True, True)
                    mask = pygame.mask.from_surface(surf)
                    self.stacked_sprite_cache[obj_name]["collision_masks"][angle] = mask
            if outline:
                outline_coords = pygame.mask.from_surface(sprite_surf).outline()
                pygame.draw.polygon(sprite_surf, "black", outline_coords, self.outline_thickness)
            image = pygame.transform.flip(sprite_surf, True, True)
            self.stacked_sprite_cache[obj_name]["rotated_sprites"][angle] = image


    # разбивка одного изображения на список слоев
    def get_layer_array(self, attrs, custom=""):
        if custom:
            sprite_sheet = pygame.image.load(attrs[custom]).convert_alpha()
        else:
            sprite_sheet = pygame.image.load(attrs["path"]).convert_alpha()
        sprite_sheet = pygame.transform.scale(sprite_sheet, vec2(sprite_sheet.get_size()) * attrs["scale"])
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        sprite_height = sheet_height // attrs["num_layers"]
        sheet_height = sprite_height * attrs["num_layers"]
        layer_array = []
        for y in range(0, sheet_height, sprite_height):
            sprite = sprite_sheet.subsurface((0, y, sheet_width, sprite_height))
            layer_array.append(sprite)
        return layer_array[::-1]
