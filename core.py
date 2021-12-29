import os
import sys
import pygame

from map_core import Map


# images
import pygame_gui


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# fonts
def get_font(size, bold=False):
    return pygame.font.Font(f'data/fonts/{"bold-" if bold else ""}font.ttf', size)

def create_text(screen, x, y, text, size, bold=False):
    text = get_font(size, bold).render(str(text), False, (0, 0, 0))
    screen.blit(text, (x, y))


# mixins
class OnClickMixin:

    def on_click(self, event):
        if 'on_click_func' in self.__dict__:
            self.on_click_func(self, event)


# classes
class ActionData(OnClickMixin):

    clicks = []
    status = 'watching'

    def clear(self, status='watching'):
        for i in self.__dict__:
            self.__setattr__(i, None)
            self.clicks = []
            self.status = status
            if 'on_click_func' in self.__dict__:
                del self.on_click_func


# ui
class Manager(pygame_gui.UIManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.objects = list()

    def process_events(self, event: pygame.event.Event):
        super().process_events(event)
        for obj in self.objects:
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == obj:
                        obj.on_click(event)

    def add_to_handle(self, object):
        self.objects.append(object)


class Button(pygame_gui.elements.UIButton, OnClickMixin):

    def __init__(self, *args, **kwargs):
        self.on_click_func = kwargs['on_click']
        kwargs['manager'].add_to_handle(self)
        del kwargs['on_click']
        super().__init__(*args, **kwargs)


# sprites
class MessageBox(pygame.sprite.Sprite):
    def __init__(self, *group, manager, text=None, draw_func=None):
        super().__init__(*group)
        self.image = pygame.Surface((300, 200), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(750, 300, 300, 200)
        pygame.draw.rect(self.image, pygame.Color("white"), pygame.Rect(0, 0, 300, 200), border_radius=10)
        if text:
            create_text(self.image, 10, 50, text, 15, True)
        else:
            draw_func(self.image)
        Button(relative_rect=pygame.Rect((760, 310), (80, 30)), text='close', manager=manager, on_click=self.kill)

    def kill(self, btn, event):
        btn.kill()
        super().kill()

    def update(self, way):
        pass


class MapSprite(pygame.sprite.Sprite):
    def __init__(self, *group, obj=None):
        super().__init__(*group)
        self.map = Map(obj.map, obj.centers) if obj else Map()
        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(300, 0, 1500, 750)
        self.map.draw_map(self.image)