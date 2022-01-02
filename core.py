import datetime
import os
import sys
import pygame

from map_core import Map


# CONSTANTS
class TimeMode:
    START_DATE = datetime.datetime(year=2000, month=1, day=1, hour=1, minute=1, second=1, microsecond=1)

    PAUSE = datetime.timedelta(minutes=0)
    SLOW = datetime.timedelta(minutes=4)
    MEDIUM = datetime.timedelta(hours=1)
    FAST = datetime.timedelta(hours=24)

    LIST = [PAUSE, SLOW, MEDIUM, FAST]


FPS = 5
TIME_MODE = TimeMode()


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


def create_text(screen, x, y, size, text='', bold=False):
    print(1)
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


class AutoTextRender:

    __init__ = lambda self: self.__setattr__('lst', list())
    add_text = lambda self, *args, **kwargs: self.lst.append(lambda: create_text(*args, **kwargs))
    add_text_stream = lambda self, *args, func, **kwargs: self.lst.append(lambda: create_text(*args, text=func(), **kwargs))
    render = lambda self: [func() for func in self.lst]

    '''def add_text_stream(self, *args, func, **kwargs):
        def wrapped_func():
            text = func()'''



class WrappedClock:

    mode = TIME_MODE.SLOW
    datetime = TIME_MODE.START_DATE

    __init__ = lambda self: self.__setattr__('clock', pygame.time.Clock())
    set_mode = lambda self, mode: self.__setattr__('mode', TIME_MODE.LIST[mode] if mode in range(0, 4) else self.mode)
    get_str_datetime = lambda self, format='%H:%M %d.%m.%Y': self.datetime.strftime(format)

    def tick(self):
        ms = self.clock.tick(FPS) / 1000.0
        game_delta = ms * self.mode
        self.datetime += game_delta
        return (ms, game_delta)


# ui
class Manager(pygame_gui.UIManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.objects, self.update_objects = list(), list()

    def process_events(self, event: pygame.event.Event):
        super().process_events(event)
        for i, obj in enumerate(self.objects):
            '''if i in self.update_objects:
                obj.update()'''
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == obj:
                        obj.on_click(event)

    def add_to_handle(self, object, update=False):
        '''if update:
            self.update_objects.append(len(self.objects))'''
        self.objects.append(object)


class Button(pygame_gui.elements.UIButton, OnClickMixin):

    def __init__(self, *args, **kwargs):
        self.default_name = kwargs['text']
        self.on_click_func = kwargs['on_click']
        kwargs['manager'].add_to_handle(self)
        del kwargs['on_click']
        '''if 'update_func' in kwargs:
            self.update_func = kwargs['update_func']
            del kwargs['update_func']'''
        super().__init__(*args, **kwargs)

    def reset_text(self):
        self.set_text(self.default_name)

    '''def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        if 'update_func' in self.__dict__:
            self.update_func()'''


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


class Station(pygame.sprite.Sprite):
    def __init__(self, *group, x, y):
        super().__init__(*group)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        pygame.draw.circle(self.image, pygame.Color("white"), (x, y), 10)