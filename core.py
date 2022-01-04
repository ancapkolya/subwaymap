import datetime
import os
import sys
import pygame

import map_core
import models
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
    text = get_font(size, bold).render(str(text), False, (0, 0, 0))
    screen.blit(text, (x, y))


# mixins
class OnClickMixin:

    def on_click(self, event):
        if 'on_click_func' in self.__dict__:
            self.on_click_func(self, event)


# classes
class EmptyClass: pass


class GameLoop:

    def __init__(self, screen, clock):
        self.screen = screen
        self.window = None
        self.clock = clock

    def loop(self):
        running = True
        while running and self.window:
            time_delta, game_delta = self.clock.tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.window.process_events(event)
            self.screen.fill('white')
            self.window.draw()
            self.window.update(time_delta, game_delta)
            pygame.display.flip()
        models.connection.close()
        pygame.quit()

    def set_window(self, window):
        if self.window:
            self.window.screen = None
        self.window = window
        self.window.screen = self.screen


class Window:

    def __init__(self, ui=None, process_events_func=None, update_func=None, groups=[], auto_text_renders=[]):
        self.screen = None
        self.ui = ui
        self.process_events_func = process_events_func
        self.update_func = update_func
        self.auto_text_renders = auto_text_renders
        self.groups = groups

    def draw(self):
        if self.screen:
            [group.draw(self.screen) for group in self.groups]
            [text.render() for text in self.auto_text_renders]
            self.ui.draw_ui(self.screen)

    def process_events(self, event):
        if self.screen and self.process_events_func:
            self.process_events_func(self, event)
            self.ui.process_events(event)

    def update(self, time_delta, game_time):
        if self.screen:
            self.ui.update(time_delta)
            if self.update_func:
                self.update_func(self, time_delta, game_time)


class SessionSprites:
    stations = list()
    lines = list()


class Session:

    def __init__(self, pk=-1):
        self.sprites = SessionSprites()
        if pk > -1:
            session = models.GameSession.get_or_none(id=pk)
            if session:
                self.session = session
            else:
                self.create_session()
        else:
            self.create_session()
        self.session.load_data()

    def load_sprites(self, stations_sprites, lines_sprites):
        for station in self.session.stations:
            self.sprites.stations.append(Station(stations_sprites, station))
        for line in self.session.lines:
            self.sprites.lines.append(Line(lines_sprites, line))

    def create_session(self):
        game_map = map_core.Map()
        self.session = models.GameSession(map=game_map.map.tolist(), centers=game_map.centers.tolist())
        self.session.save()

    def get_map(self):
        return Map(matrix=self.session.map.copy(), centers=self.session.centers.copy())


class ActionData(OnClickMixin):

    clicks = []
    objects = []
    sprites = []
    status = 'watching'

    def clear(self, kill=False, status='watching'):
        if 'on_click_func' in self.__dict__:
            del self.on_click_func
        for i in self.__dict__.copy():
            self.__setattr__(i, None)
        if kill:
            for i in self.sprites:
                i.kill()
        self.clicks = []
        self.objects = []
        self.sprites = []
        self.status = status


class AutoTextRender:

    __init__ = lambda self: self.__setattr__('lst', list())
    add_text = lambda self, *args, **kwargs: self.lst.append(lambda: create_text(*args, **kwargs))
    add_text_stream = lambda self, *args, func, **kwargs: self.lst.append(
        lambda: create_text(*args, text=func(), **kwargs))
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
                        print(0)
                        print(event)
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
            create_text(self.image, 10, 50, 15, text, True)
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
        self.map = Map() if obj is None else obj
        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(300, 0, 1500, 750)
        self.map.draw_map(self.image)


class Station(pygame.sprite.Sprite):

    def __init__(self, group, obj):
        super().__init__(group)
        self.obj = obj
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(self.obj.x - 10, self.obj.y - 10, 20, 20)
        pygame.draw.circle(self.image, pygame.Color("white"), (10, 10), 8)
        pygame.draw.circle(self.image, pygame.Color("black"), (10, 10), 8, 2)


class Line(pygame.sprite.Sprite):

    def __init__(self, group, obj):
        super().__init__(group)
        self.obj = obj
        self.obj.load_data()
        self.stations = [models.Station.get_by_id(id) for id in self.obj.stations]
        self.points_lst = [self.stations[0].x, self.stations[0].y, self.stations[1].x, self.stations[1].y]
        x, y, x1, y1 = self.points_lst
        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(300, 0, 1500, 750)

        d_x, d_y = abs(x - x1), abs(y - y1)
        if d_y >= d_x:
            b_y = y1 + d_x * (y - y1) // d_y
            pygame.draw.line(self.image, 'white', (x - 300, y), (x - 300, b_y), 8)
            pygame.draw.line(self.image, 'white', (x - 300, b_y), (x1 - 300, y1), 10)
        else:
            b_x = x + (d_y + 5) * (x1 - x) // d_x - 300
            pygame.draw.line(self.image, 'white', (x - 300, y), (b_x, y1), 10)
            pygame.draw.line(self.image, 'white', (b_x, y1), (x1 - 300, y1), 8)
