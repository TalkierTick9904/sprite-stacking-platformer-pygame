from settings import *


# класс меню паузы
class PauseMenu:
    def __init__(self, screen, font, app=None):
        self.app = app
        self.screen = screen
        self.font = font
        self.big_font = pygame.font.Font(pygame.font.get_default_font(), 60)
        self.width = WIDTH // 4
        self.height = HEIGHT // 2
        self.gap_between = 5
        self.gap_borders = 10
        self.active_input = False
        self.input_text = ""
        # переменные для анимации
        self.anim_trigger = False
        self.frame_index = 0
        self.stop_animation = True
        attrs = MENU_ANIMATIONS_ATTRS["pause_menu"]
        self.images = self.get_layer_array(attrs)[::-1]
        self.image = self.images[0]
        self.pos = ((WIDTH - self.width) // 2, (HEIGHT - self.height) // 2 + (HEIGHT - self.height) // 4)
        self.anim_rect = pygame.Rect(self.pos[0], self.app.icons["health"].get_height() + 40, self.width, self.pos[1] - self.app.icons["health"].get_height()) # type: ignore
        # кнопки в меню
        buttons = {"resume": pygame.Rect(0, 0, 0, 0), "save": pygame.Rect(0, 0, 0, 0),
                   "load": pygame.Rect(0, 0, 0, 0), "settings": pygame.Rect(0, 0, 0, 0),
                   "main menu": pygame.Rect(0, 0, 0, 0)}
        self.set_ui("Game paused", buttons)

    # вычисление положения и запись значений в словари у элементов интерфейса
    def set_ui(self, text, buttons, slider_attrs=dict(), caption=None, multiline=False):
        self.buttons = buttons
        self.sliders = dict()
        self.slider_attrs = slider_attrs
        self.text, self.text_rect, self.caption, self.caption_rect = None, None, None, None
        text_height = 0
        if text:
            self.text = self.big_font.render(text, True, MENU_ALT_COLOR)
            text_height = self.height * 0.3 + self.gap_between
            text_center = pygame.Rect(self.pos[0] + self.gap_borders, self.pos[1] + self.gap_borders,
                                      self.width - 2 * self.gap_borders, text_height - self.gap_between).center
            self.text_rect = self.text.get_rect(center=text_center)
            if caption and not multiline:
                self.caption = self.font.render(caption, True, MENU_ALT_COLOR)
                caption_height = self.caption.get_height() + self.gap_between * 3
                caption_center = pygame.Rect(self.pos[0] + self.gap_borders, self.pos[1] + self.gap_borders + text_height,
                                             self.width - 2 * self.gap_borders, caption_height - self.gap_between).center
                self.caption_rect = self.caption.get_rect(center=caption_center)
                text_height += caption_height
            elif caption and multiline:
                self.caption = self.create_multiline_text(self.font, caption, MENU_ALT_COLOR)
                caption_height = self.caption.get_height() + self.gap_between * 3
                caption_center = pygame.Rect(self.pos[0] + self.gap_borders, self.pos[1] + self.gap_borders + text_height,
                                             self.width - 2 * self.gap_borders, caption_height - self.gap_between).center
                self.caption_rect = self.caption.get_rect(center=caption_center)
                text_height += caption_height
        button_height = (self.height - text_height - self.gap_between * (len(self.buttons.keys()) - 1) - self.gap_borders * 2) / len(self.buttons.keys())
        for i, button in enumerate(self.buttons.keys()):
            self.buttons[button].x = int(self.pos[0] + self.gap_borders)
            self.buttons[button].y = int(self.pos[1] + text_height + self.gap_borders + i * (self.gap_between + button_height))
            self.buttons[button].width = int(self.width - self.gap_borders * 2)
            self.buttons[button].height = int(button_height)
            if len(button) > 2 and button[-2:] == "_s":
                self.buttons[button].y += int(self.gap_between + button_height / 2)
                self.buttons[button].height = int(button_height / 2 - self.gap_between)
                if slider_attrs[button][1] - 1 == slider_attrs[button][0]:
                    self.sliders[button] = self.buttons[button].width
                else:
                    self.sliders[button] = self.buttons[button].width / slider_attrs[button][1] * slider_attrs[button][0]
            if len(button) > 2 and button[-2:] == "_i":
                self.buttons[button].y += int(self.gap_between + button_height / 2)
                self.buttons[button].height = int(button_height / 2 - self.gap_between)

    # рендер интерфейса
    def render(self, mousepos, outline=False):
        if self.sliders:
            self.update_sliders(mousepos)
        pygame.draw.rect(self.screen, MENU_COLOR, ((self.pos[0], self.pos[1]), (self.width, self.height)), border_radius=5)
        if outline:
            pygame.draw.rect(self.screen, MENU_ALT_COLOR, ((self.pos[0] - 2, self.pos[1] - 2), (self.width + 4, self.height + 4)), border_radius=5, width=2)
        if self.text:
            self.screen.blit(self.text, self.text_rect)
        if self.caption:
            self.screen.blit(self.caption, self.caption_rect)
        for text, rect in self.buttons.items():
            if len(text) > 2 and text[-2:] == "_s":
                slider_rect = pygame.Rect(rect.x, rect.y, self.sliders[text], rect.height)
                pygame.draw.rect(self.screen, MENU_ALT_COLOR, rect, width=2, border_radius=5)
                pygame.draw.rect(self.screen, MENU_ALT_COLOR, slider_rect, border_radius=5)
                text = self.font.render(text[:-2], True, MENU_ALT_COLOR)
                text_rect = pygame.Rect(rect.x, rect.y - rect.height - self.gap_between, rect.width, rect.height)
                text_rect = text.get_rect(center=text_rect.center)
            elif len(text) > 2 and text[-2:] == "_i":
                if self.active_input:
                    pygame.draw.rect(self.screen, MENU_ALT_COLOR, rect, width=2, border_radius=5)
                else:
                    pygame.draw.rect(self.screen, MENU_COLOR, rect, width=2, border_radius=5)
                text = self.font.render("name of the save", True, MENU_ALT_COLOR)
                text_rect = pygame.Rect(rect.x, rect.y - rect.height - self.gap_between, rect.width, rect.height)
                text_rect = text.get_rect(center=text_rect.center)
                self.screen.blit(text, text_rect)
                text = self.font.render(self.input_text, True, MENU_ALT_COLOR)
                text_rect = text.get_rect(center=rect.center)
            elif rect.collidepoint(mousepos[0], mousepos[1]):
                pygame.draw.rect(self.screen, MENU_COLOR, rect, border_radius=5)
                text = self.font.render(text, True, MENU_ALT_COLOR)
                text_rect = text.get_rect(center=rect.center)
            else:
                pygame.draw.rect(self.screen, MENU_ALT_COLOR, rect, border_radius=5)
                text = self.font.render(text, True, MENU_COLOR)
                text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
        self.screen.blit(self.image, self.image.get_rect(center=self.anim_rect.center))
        self.update_animation()

    # создание поверхности с несколькими линиями текста
    def create_multiline_text(self, font, text, text_color):
        lines = dict()
        text = text.splitlines()
        width, height = 0, 0
        for line in text:
            line_surface = font.render(line, True, text_color)
            lines[line_surface] = height
            if line_surface.get_width() > width:
                width = line_surface.get_width()
            height += line_surface.get_height()
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for line, height in lines.items():
            rect = pygame.Rect(0, height, width, line.get_height())
            rect = line.get_rect(center=rect.center)
            surface.blit(line, rect)
        return surface

    # разбивка картинки на кадры анимации
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

    # переключение кадров анимации
    def update_animation(self):
        if self.anim_trigger:
            self.frame_index = (self.frame_index + 1) % len(self.images)
            self.image = self.images[self.frame_index]
            if self.stop_animation:
                if self.frame_index == len(self.images) - 1:
                    self.images = [self.images[-1]]
            self.anim_trigger = False

    # обработка клика
    def check_click(self, mousepos):
        self.active_input = False
        for text, rect in self.buttons.items():
            if rect.collidepoint(mousepos[0], mousepos[1]):
                return self.process_button(text)
        return False, ""

    # обработка ввода при активном поле ввода
    def process_input(self, event):
        if event.key == pygame.K_RETURN:
            self.active_input = False
        elif event.key == pygame.K_BACKSPACE:
            if self.input_text:
                self.input_text = self.input_text[:-1]
        elif not any(ord(x) > 127 for x in event.unicode):
            if len(self.input_text) < 15:
                self.input_text += event.unicode

    # обновление положения слайдеров
    def update_sliders(self, mousepos):
        for text, rect in self.buttons.items():
            if len(text) > 2 and text[-2:] == "_s" and rect.collidepoint(mousepos[0], mousepos[1]) and pygame.mouse.get_pressed()[0]:
                self.sliders[text] = mousepos[0] - rect.x
                if self.sliders[text] < 1:
                    self.sliders[text] = 0
                if self.sliders[text] > rect.width:
                    self.slider_width = rect.width

    # действия при нажатии на кнопку по названию
    def process_button(self, text):
        global MUSIC_VOLUME, SFX_VOLUME
        if text in ("resume", "ok") and not "input_i" in self.buttons.keys():
            return True, text
        elif text == "ok" and self.input_text:
            buttons = {"resume": pygame.Rect(0, 0, 0, 0), "save": pygame.Rect(0, 0, 0, 0),
                       "load": pygame.Rect(0, 0, 0, 0), "settings": pygame.Rect(0, 0, 0, 0),
                       "main menu": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Game paused", buttons)
            return False, self.input_text + "_s"
        elif text == "main menu":
            buttons = {"ok": pygame.Rect(0, 0, 0, 0), "cancel": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Exit", buttons, caption="Unsaved progress will be lost")
        elif text == "load":
            buttons = dict()
            for save in SAVES.keys():
                buttons[save] = pygame.Rect(0, 0, 0, 0)
            buttons["cancel"] = pygame.Rect(0, 0, 0, 0)
            self.set_ui("Load save", buttons)
        elif text == "settings":
            slider_attrs = {"music volume_s": (MUSIC_VOLUME, 101), "sfx volume_s": (SFX_VOLUME, 101)}
            buttons = {"music volume_s": pygame.Rect(0, 0, 0, 0), "sfx volume_s": pygame.Rect(0, 0, 0, 0),
                       "save": pygame.Rect(0, 0, 0, 0), "cancel": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Settings", buttons, slider_attrs)
        elif text == "cancel":
            buttons = {"resume": pygame.Rect(0, 0, 0, 0), "save": pygame.Rect(0, 0, 0, 0),
                       "load": pygame.Rect(0, 0, 0, 0), "settings": pygame.Rect(0, 0, 0, 0),
                       "main menu": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Game paused", buttons)
        elif text == "save" and self.sliders:
            MUSIC_VOLUME = int(self.sliders["music volume_s"] // (int(self.width - self.gap_borders * 2) / self.slider_attrs["music volume_s"][1]))
            SFX_VOLUME = int(self.sliders["sfx volume_s"] // (int(self.width - self.gap_borders * 2) / self.slider_attrs["sfx volume_s"][1]))
            pygame.mixer.music.set_volume(MUSIC_VOLUME / 100)
            for _, sound in SOUNDS.items():
                sound.set_volume(SFX_VOLUME / 100)
            with open("data/settings.txt", "w") as file:
                file.write(f"MUSIC_VOLUME {MUSIC_VOLUME}\nSFX_VOLUME {SFX_VOLUME}\n")
            buttons = {"resume": pygame.Rect(0, 0, 0, 0), "save": pygame.Rect(0, 0, 0, 0),
                       "load": pygame.Rect(0, 0, 0, 0), "settings": pygame.Rect(0, 0, 0, 0),
                       "main menu": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Game paused", buttons)
        elif text == "save" and not self.sliders:
            self.input_text = f"save_{len(SAVES.keys()) + 1}"
            buttons = {"input_i": pygame.Rect(0, 0, 0, 0), "ok": pygame.Rect(0, 0, 0, 0),
                       "cancel": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Save game", buttons)
        elif text == "input_i":
            self.active_input = True
        elif not self.sliders and not "input_i" in self.buttons.keys():
            return True, text + ".txt"
        return False, ""


# класс главной менюшки (методы те же, но кнопки и положение другое)
class MainMenu(PauseMenu):
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.big_font = pygame.font.Font(pygame.font.get_default_font(), 60)
        self.width = WIDTH // 2
        self.height = HEIGHT // 2
        self.gap_between = 5
        self.gap_borders = 10
        self.anim_trigger = False
        attrs = MENU_ANIMATIONS_ATTRS["main_menu"]
        self.frame_index = 0
        self.stop_animation = False
        self.images = self.get_layer_array(attrs)[::-1]
        self.image = self.images[0]
        self.pos = ((WIDTH - self.width) // 2, HEIGHT - self.height - 20)
        self.anim_rect = pygame.Rect(self.pos[0], 0, self.width, self.height)
        buttons = {"new game": pygame.Rect(0, 0, 0, 0), "load": pygame.Rect(0, 0, 0, 0),
                   "settings": pygame.Rect(0, 0, 0, 0), "exit": pygame.Rect(0, 0, 0, 0)}
        self.set_ui("Main menu", buttons)

    def process_button(self, text):
        global MUSIC_VOLUME, SFX_VOLUME
        if text in ("new game", "ok"):
            return True, text
        elif text == "load":
            buttons = dict()
            for save in SAVES.keys():
                buttons[save] = pygame.Rect(0, 0, 0, 0)
            buttons["cancel"] = pygame.Rect(0, 0, 0, 0)
            self.set_ui("Load save", buttons)
        elif text == "exit":
            buttons = {"ok": pygame.Rect(0, 0, 0, 0), "cancel": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Exit", buttons, caption="Close the game?")
        elif text == "settings":
            slider_attrs = {"music volume_s": (MUSIC_VOLUME, 101), "sfx volume_s": (SFX_VOLUME, 101)}
            buttons = {"music volume_s": pygame.Rect(0, 0, 0, 0), "sfx volume_s": pygame.Rect(0, 0, 0, 0),
                       "save": pygame.Rect(0, 0, 0, 0), "cancel": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Settings", buttons, slider_attrs)
        elif text == "cancel":
            buttons = {"new game": pygame.Rect(0, 0, 0, 0), "load": pygame.Rect(0, 0, 0, 0),
                       "settings": pygame.Rect(0, 0, 0, 0), "exit": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Main menu", buttons)
        elif text == "save" and self.sliders:
            MUSIC_VOLUME = int(self.sliders["music volume_s"] // (int(self.width - self.gap_borders * 2) / self.slider_attrs["music volume_s"][1]))
            SFX_VOLUME = int(self.sliders["sfx volume_s"] // (int(self.width - self.gap_borders * 2) / self.slider_attrs["sfx volume_s"][1]))
            pygame.mixer.music.set_volume(MUSIC_VOLUME / 100)
            for _, sound in SOUNDS.items():
                sound.set_volume(SFX_VOLUME / 100)
            with open("data/settings.txt", "w") as file:
                file.write(f"MUSIC_VOLUME {MUSIC_VOLUME}\nSFX_VOLUME {SFX_VOLUME}\n")
            buttons = {"new game": pygame.Rect(0, 0, 0, 0), "load": pygame.Rect(0, 0, 0, 0),
                       "settings": pygame.Rect(0, 0, 0, 0), "exit": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Game paused", buttons)
        elif not self.sliders:
            return True, text + ".txt"
        return False, ""


# класс победной меню (методы те же, но кнопки и положение другое)
class WinMenu(PauseMenu):
    def __init__(self, screen, font, app=None):
        self.app = app
        self.screen = screen
        self.font = font
        self.big_font = pygame.font.Font(pygame.font.get_default_font(), 60)
        self.width = WIDTH // 2
        self.height = HEIGHT // 2
        self.gap_between = 5
        self.gap_borders = 10
        self.anim_trigger = False
        self.frame_index = 0
        self.stop_animation = False
        attrs = MENU_ANIMATIONS_ATTRS["win_menu"]
        self.images = self.get_layer_array(attrs)[::-1]
        self.image = self.images[0]
        self.pos = ((WIDTH - self.width) // 2, HEIGHT - self.height - 20)
        self.anim_rect = pygame.Rect(self.pos[0], 0, self.width, self.pos[1])
        buttons = {"stats": pygame.Rect(0, 0, 0, 0), "main menu": pygame.Rect(0, 0, 0, 0)}
        self.set_ui("You won :)", buttons)

    def process_button(self, text):
        if text == "main menu":
            return True, ""
        elif text == "stats":
            caption = "\n".join((f"Coins collected: {self.app.coins_collected}", f"Enemies killed: {self.app.enemies_killed}", # type: ignore
                                 f"Bullets shot: {self.app.bullets_shot}", f"Boxes destroyed: {self.app.boxes_destroyed}", # type: ignore
                                 f"HP healed: {self.app.hp_healed}")) # type: ignore
            buttons = {"cancel": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("Your stats", buttons, caption=caption, multiline=True)
        elif text == "cancel":
            buttons = {"stats": pygame.Rect(0, 0, 0, 0), "main menu": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("You won :)", buttons)
        return False, ""


# класс меню поражения (методы те же, но кнопки и положение другое)
class LoseMenu(PauseMenu):
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.big_font = pygame.font.Font(pygame.font.get_default_font(), 60)
        self.width = WIDTH // 2
        self.height = HEIGHT // 2
        self.gap_between = 5
        self.gap_borders = 10
        self.anim_trigger = False
        self.frame_index = 0
        self.stop_animation = True
        attrs = MENU_ANIMATIONS_ATTRS["lose_menu"]
        self.images = self.get_layer_array(attrs)
        self.image = self.images[0]
        self.pos = ((WIDTH - self.width) // 2, HEIGHT - self.height - 20)
        self.anim_rect = pygame.Rect(self.pos[0], 0, self.width, self.pos[1])
        buttons = {"load": pygame.Rect(0, 0, 0, 0), "main menu": pygame.Rect(0, 0, 0, 0)}
        self.set_ui("You lost :(", buttons)

    def process_button(self, text):
        if text == "main menu":
            return True, ""
        elif text == "load":
            buttons = dict()
            for save in SAVES.keys():
                buttons[save] = pygame.Rect(0, 0, 0, 0)
            buttons["cancel"] = pygame.Rect(0, 0, 0, 0)
            self.set_ui("Load save", buttons)
        elif text == "cancel":
            buttons = {"load": pygame.Rect(0, 0, 0, 0), "main menu": pygame.Rect(0, 0, 0, 0)}
            self.set_ui("You lost :(", buttons)
        else:
            return True, text + ".txt"
        return False, ""
