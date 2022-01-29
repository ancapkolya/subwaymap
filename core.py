import datetime
import os
import random
import sys
import pygame
import pygame_gui
import webbrowser

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


FPS = 10
TIME_MODE = TimeMode()


# images
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

    def on_click(self, event, *args):
        if 'on_click_func' in self.__dict__:
            self.on_click_func(self, event)


# classes
class EmptyClass: pass


def load_game_data():
    objects = list(models.GameData.select())
    if objects:
        object = objects[0]
        object.load_data()
        return object
    else:
        object = models.GameData()
        object.save()
        object.load_data()
        return object



class GameLoop:

    def __init__(self, screen, clock, gamedata):
        self.gamedata = gamedata
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
        self.gamedata.save()
        models.connection.close()
        pygame.quit()

    def set_window(self, window):
        if self.window:
            self.window.clear()
        self.window = window
        self.window.init()
        self.window.clock = self.clock
        self.window.screen = self.screen


class Window:

    def __init__(self, ui=None, init_func=None, process_events_func=None, update_func=None, groups=[], auto_text_renders=[]):
        self.screen = None
        self.clock = None
        self.ui = ui
        self.process_events_func = process_events_func
        self.update_func = update_func
        self.auto_text_renders = auto_text_renders
        self.groups = groups
        if init_func:
            self.init_func = init_func

    def init(self):
        if 'init_func' in self.__dict__:
            self.init_func()


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

    def clear(self):
        self.screen = None
        self.clock = None
        for group in self.groups:
            for sprite in group:
                sprite.kill()
        for sprite in self.ui.ui_group:
            sprite.kill()
        for text in self.auto_text_renders:
            text.clear()


class Event:

    def __init__(self, datetime, callback):
        self.datetime = datetime
        self.callback_func = callback

    run = lambda self, create_message: self.callback_func(self, create_message)


class EventCore:

    events_queue = list()

    def init(self, session):
        self.session = session
        self.events_queue = list()

    def update(self, game_delta):
        for event in self.events_queue.copy():
            if event.datetime <= self.session.clock.datetime:
                event.run(self.create_message)
                self.events_queue.remove(event)

    def create_message(self, text='', draw_func=None):
        if draw_func:
            MessageBox(self.session.warning_sprites, manager=self.session.ui_manager, draw_func=draw_func)
        else:
            MessageBox(self.session.warning_sprites, manager=self.session.ui_manager, text=text)

    add_random_event = lambda self, callback, max_days=50: self.events_queue.append(Event(self.session.clock.datetime+datetime.timedelta(days=random.choice(range(10, max_days, 1))), callback))


class EconomicsCore:

    ticket_cost = 3

    daily_expenses = 0
    second_expenses = 0
    daily_revenue = 0
    second_revenues = 0
    cash_delta = 0
    session = None

    stations_data = dict()
    routes_data = dict()

    def init(self, session):
        self.session = session
        self.stations_data = dict()
        self.routes_data = dict()

    def init(self, session):

        def give_subsidy(event, create_message):

            def draw_func(screen):
                create_text(screen, 10, 50, 15, 'город выдал вам', bold=True)
                create_text(screen, 10, 70, 15, f'субсидию в размере {subsidy}', bold=True)

            subsidy = random.choice(range(500, 2001, 100))
            self.session.session.cash_amount += subsidy
            create_message(draw_func=draw_func)
            self.session.events_core.add_random_event(give_subsidy, 50*self.session.session.level)

        self.session = session
        self.session.events_core.add_random_event(give_subsidy, 50*self.session.session.level)

    def update(self, game_delta):
        if self.session:
            if self.session.session.cash_amount >= 0:
                self.cash_delta += (self.second_revenues - self.second_expenses) * game_delta.seconds
                if abs(self.cash_delta) >= 1:
                    self.session.session.cash_amount += self.cash_delta
                    self.cash_delta = 0
                self.session.session.score += self.daily_flow / 86400 * game_delta.seconds
            else:
                self.session.end_game('у вас закончились деньги')

    def update_economics_properties(self, recount=True):
        self.count_people_flow(recount)
        self.update_expenses()
        self.update_revenues()
        self.daily_flow = sum([i[2] if i[2] < i[0] else i[0] for i in self.routes_data.values()])

    def update_expenses(self):
        if self.session:
            self.second_expenses = self.session.session.meta_data['lines_len'] * 0.00000015 + sum(
                [models.Route.get_by_id(route).train_n * 0.0000005 for route in self.session.routes])
            self.daily_expenses = self.second_expenses * 3600 * 24
            self.daily_expenses = round(self.daily_expenses, 2)

    def update_revenues(self):
        if self.session:
            self.daily_revenue = sum([i[2] for i in self.routes_data.values()]) * self.ticket_cost / 250 / self.session.session.level
            self.second_revenues = self.daily_revenue / 86400
            self.daily_revenue = round(self.daily_revenue, 2)

    def count_people_flow(self, recount=True):

        if len([i for i in ['station_data', 'routes_data', 'station_flow'] if i in self.session.session.meta_data]) == 3 and not recount:

            self.stations_data = self.session.session.meta_data['station_data']
            self.routes_data = self.session.session.meta_data['routes_data']
            self.station_flow = self.session.session.meta_data['station_flow']

        else:

            map = self.session.get_map().map

            if 'station_flow' not in self.__dict__:
                self.station_flow = dict()
            self.stations_data = dict()
            for station in self.session.session.stations:
                s_routes = list()
                for i in station.get_lines():
                    for j in i.routes:
                        s_routes.append(j.id)
                self.stations_data[str(station.id)] = [0, list(set(s_routes))]
                column_n, row_n = [i - 3 if i > 3 else 0 for i in self.get_cell(station.x-300, station.y)]
                for row in range(row_n, row_n + 7, 1):
                    for column in range(column_n, column_n + 7, 1):
                        self.stations_data[str(station.id)][0] += int(map[column, row])
                if self.stations_data[str(station.id)][1] != 0:
                    self.stations_data[str(station.id)][0] //= 20
                if str(station.id) not in self.station_flow:
                    self.station_flow[str(station.id)] = 0

            # routes flow cycle
            self.routes_data = dict()
            for route in self.session.session.routes:
                self.routes_data[str(route.id)] = [0, set(), 0, 0]
                for i in self.session.routes[route.id]:
                    self.routes_data[str(route.id)][0] += self.stations_data[str(i)][0] // len(self.stations_data[str(i)][1])
                    if len(self.stations_data[str(i)][1]) > 1:
                        self.routes_data[str(route.id)][1].add(i)
                self.routes_data[str(route.id)][1] = list(self.routes_data[str(route.id)][1])
                transfer_volume = self.routes_data[str(route.id)][0] * 0.5
                station_flow_volume = sum([self.stations_data[str(i)][0] for i in self.routes_data[str(route.id)][1]])
                for i in self.routes_data[str(route.id)][1]:
                    self.stations_data[str(i)][0] += int(self.stations_data[str(i)][0] / station_flow_volume * transfer_volume * random.randrange(7, 13, 1) / 10)
                trains_max, line_max = route.train_n * 30, self.routes_data[str(route.id)][0]
                self.routes_data[str(route.id)][2] = line_max if trains_max >= line_max else trains_max
                self.routes_data[str(route.id)][3] = trains_max / line_max

            self.session.session.meta_data['station_data'] = self.stations_data
            self.session.session.meta_data['routes_data'] = self.routes_data
            self.session.session.meta_data['station_flow'] = self.station_flow

    get_cell = lambda self, *pos: [i // 10 for i in pos]


class SessionSprites:

    stations = list()
    lines = list()
    routes = list()
    trains = dict()
    breakpoints = dict()


class Session:

    routes = dict()

    build_cost = 0
    new_distance = 0

    is_ended = False

    def __init__(self, exit_callback, pk=-1, clock=None):
        if pk > -1:
            session = models.GameSession.get_by_id(pk)
            if session:
                self.session = session
            else:
                self.create_session()
        else:
            self.create_session()

        self.clock = clock
        self.clock.datetime = self.session.datetime

        self.session.load_data()
        self.session.check_meta()

        self.sprites = SessionSprites()
        self.economics_core = EconomicsCore()
        self.events_core = EventCore()

        self.events_core.init(self)
        self.economics_core.init(self)

        self.exit_callback = exit_callback

    def save(self):
        self.session.datetime = self.clock.datetime
        self.session.save()
        self.session.load_data()

    def end_game(self, text='вы проиграли'):

        self.is_ended = True

        self.save()
        self.clock.set_mode(0)

        def draw_func(screen):
            create_text(screen, 10, 10, 15, text, True)
            Button(relative_rect=pygame.Rect((760, 330), (80, 30)), text='quit', manager=self.ui_manager, on_click=self.exit_callback)

        MessageBox(self.warning_sprites, manager=self.ui_manager, draw_func=draw_func, permanent=True)

    def load_sprites(self, stations_group, lines_group, routes_group, trains_group, break_points_group, warning_sprites, ui_manager, routes_list_update_callback, draw_objects_array):
        self.break_points_group = break_points_group
        self.stations_group = stations_group
        self.lines_group = lines_group
        self.routes_group = routes_group
        self.trains_group = trains_group
        self.warning_sprites = warning_sprites
        self.ui_manager = ui_manager
        self.routes_list_update_callback = routes_list_update_callback
        self.draw_objects_array = draw_objects_array

        self.update_map()


    def create_session(self):
        game_map = map_core.Map()
        self.session = models.GameSession(map=game_map.map.tolist(), centers=game_map.centers.tolist())
        self.session.save()

    def get_map(self):
        return Map(matrix=self.session.map.copy(), centers=self.session.centers.copy())

    def update_map(self):
        self.update_lines_map()
        self.update_stations_map()
        self.update_routes_map()
        self.create_trains()
        self.economics_core.update_economics_properties(recount=False)

    def update_lines_map(self):
        self.kill_array(self.sprites.breakpoints.values())
        self.sprites.lines, self.sprites.breakpoints = self.kill_array(self.sprites.lines), dict()
        for line in self.session.lines:
            sprite = Line(self.lines_group, self.break_points_group, line)
            self.sprites.lines.append(sprite)
            self.sprites.breakpoints[line.id] = sprite.breakpoint
            sprite.create_line()

    def update_routes_map(self):
        self.sprites.routes, self.routes = self.kill_array(self.sprites.routes), dict()
        for route in self.session.routes:
            self.routes[route.id] = list()
            stations = list()
            route.load_data()
            for line_id in route.lines_queue:
                line = models.Line.get_by_id(line_id)
                sprite = Route(self.routes_group, line, route)
                self.sprites.routes.append(sprite)
                sprite.create_route()
                stations.append([line.start.id, line.end.id])
            if len(stations) > 1:
                for i, s in enumerate(stations[:-1]):
                    for j in range(2):
                        if stations[i][j] in stations[i + 1]:
                            if i == 0:
                                res = stations[i].pop(j)
                                self.routes[route.id].extend([stations[i][0], res])
                            else:
                                self.routes[route.id].append(stations[i].pop(j))
                            break
                for j in range(2):
                    if stations[-1][j] == self.routes[route.id][-1]:
                        stations[-1].pop(j)
                        self.routes[route.id].append(stations[-1][0])
                        break
            else:
                self.routes[route.id] = stations[0]
        self.routes_list_update_callback()

    def update_stations_map(self):
        self.sprites.stations = self.kill_array(self.sprites.stations)
        for station in self.session.stations:
            sprite = Station(self.stations_group, self.ui_manager, self.warning_sprites, self, station)
            self.sprites.stations.append(sprite)
            sprite.update_routes()

    def create_trains(self):
        [self.kill_array(array) for array in self.sprites.trains.values()]
        self.sprites.trains = dict()
        for route in self.session.routes:
            route.load_data()
            self.sprites.trains[route.id] = list()
            first_direction = route.train_n // 2
            for i in range(first_direction):
                self.sprites.trains[route.id].append(Train(self.trains_group, route, models.Station.get_by_id(self.routes[route.id][i]), self.clock, self, direction=1))
            for i in range(route.train_n - first_direction):
                self.sprites.trains[route.id].append(Train(self.trains_group, route, models.Station.get_by_id(self.routes[route.id][-1 + -1 * i]), self.clock, self, direction=-1))

    add_new_train = lambda self, route: self.sprites.trains[route.id].append(Train(self.trains_group, route, models.Station.get_by_id(self.routes[route.id][0]), self.clock, self, direction=1))

    def get_next_station(self, route, station, direction):
        if station.id in self.routes[route.id]:
            ind = self.routes[route.id].index(station.id)
            direction = direction if 0 <= ind + direction < len(self.routes[route.id]) else -1 * direction
            return models.Station.get_by_id(self.routes[route.id][direction + ind]), direction
        else:
            return False

    def build_obj(self, action_data):
        if self.build_cost <= self.session.cash_amount:
            self.session.cash_amount -= self.build_cost
            self.build_cost = 0
            self.session.meta_data['lines_len'] += self.new_distance
            self.new_distance = 0
            self.session.save()
            self.session.load_data()
            return True
        else:
            action_data.clear(True, True)
            return False

    draw_objects = lambda self: [obj.draw() for obj in self.draw_objects_array]

    kill_array = lambda self, array: ['empty' for obj in array if obj.kill() and False]


class ActionData(OnClickMixin):

    clicks = []
    objects = []
    sprites = []
    status = 'watching'

    def clear(self, kill=False, use_callback=False, status='watching'):
        if kill:
            for i in self.sprites:
                i.kill()
        if 'on_click_func' in self.__dict__:
            del self.on_click_func
        if 'clear_func' in self.__dict__:
            if use_callback:
                self.clear_func()
            del self.clear_func
        for i in self.__dict__.copy():
            self.__setattr__(i, None)
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
    clear = lambda self: self.__setattr__('lst', list())


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
        self.objects = list()
        if 'action_data' in kwargs:
            self.action_data = kwargs['action_data']
            del kwargs['action_data']
        super().__init__(*args, **kwargs)

    def process_events(self, event: pygame.event.Event):
        super().process_events(event)
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                for obj in self.ui_group:
                    if event.ui_element == obj:
                        obj.on_click(event)
        elif 'action_data' in self.__dict__ and event.type == pygame.MOUSEBUTTONDOWN and self.action_data.status == 'watching':
            for obj in self.objects:
                if obj.rect.collidepoint(*event.pos):
                    obj.on_click(event)

    add_to_handle = lambda self, obj: self.objects.append(obj)



class Button(pygame_gui.elements.UIButton, OnClickMixin):

    def __init__(self, *args, **kwargs):
        self.default_name = kwargs['text']
        self.on_click_func = kwargs['on_click']
        del kwargs['on_click']
        super().__init__(*args, **kwargs)

    def reset_text(self):
        self.set_text(self.default_name)


# sprites
class MessageBox(pygame.sprite.Sprite):

    def __init__(self, *group, manager, text=None, draw_func=None, permanent=False):
        super().__init__(*group)
        self.image = pygame.Surface((300, 200), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(750, 300, 300, 200)
        pygame.draw.rect(self.image, pygame.Color("white"), pygame.Rect(0, 0, 300, 200), border_radius=10)
        if text:
            create_text(self.image, 10, 50, 15, text, True)
        else:
            draw_func(self.image)
        if not permanent:
            self.btn = Button(relative_rect=pygame.Rect((760, 310), (80, 30)), text='close', manager=manager, on_click=self.kill)

    def kill(self, *args):
        if len(args) == 2:
            args[0].kill()
        elif 'btn' in self.__dict__:
            self.btn.kill()
        super().kill()

    def update(self, way):
        pass


class ImageSprite(pygame.sprite.Sprite):

    def __init__(self, group, name, x, y, w, h, colorkey=None):
        super().__init__([group])
        self.image = pygame.transform.scale(load_image(name, colorkey), (w, h))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class MapSprite(pygame.sprite.Sprite):

    def __init__(self, *group, obj=None):
        super().__init__(*group)
        self.map = Map() if obj is None else obj
        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(300, 0, 1500, 750)
        self.map.draw_map(self.image)

    def generate_new(self):
        self.map = Map()
        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.map.draw_map(self.image)


class RoutesPaginator():

    def __init__(self, screen, ui_manager, auto_text_render, x, y, get_objects_func, draw_func):
        self.screen = screen
        self.ui_manager = ui_manager
        self.x, self.y = x, y

        self.draw_func = draw_func
        self.get_objects_func = get_objects_func

        self.auto_text_render = auto_text_render
        self.draw_array = list()
        self.ui_elements = list()

        self.page = 1
        self.max_page = 1
        self.update_max_page()

        Button(relative_rect=pygame.Rect((x+10, y+10), (120, 30)), text='вверх', manager=ui_manager,
                    on_click=lambda *args: self.change_page(-1))
        Button(relative_rect=pygame.Rect((x+170, y+10), (120, 30)), text='вниз', manager=ui_manager,
                    on_click=lambda *args: self.change_page())
        auto_text_render.add_text_stream(self.screen, x+140, y+15, 15, func=self.get_text_stream_data, bold=True)

        self.update_data()

    # data
    @property
    def objects(self):
        return self.get_objects_func()

    def update_max_page(self):
        n = len(self.objects) / 5
        self.max_page = int(n) if n == int(n) else int(n) + 1

    get_str_page = lambda self: f'{self.page}/{self.max_page}'
    get_text_stream_data = lambda self: self.get_str_page()

    # update
    def update_callback(self):
        self.update_max_page()
        self.check_page_n()
        self.update_data()

    def check_page_n(self):
        self.page = self.max_page if self.page > self.max_page else self.page

    def update_data(self):
        self.auto_text_render.lst = self.auto_text_render.lst[:1]
        self.draw_array.clear()
        self.ui_elements = Session.kill_array(0, self.ui_elements)
        for i, obj in enumerate(self.objects[5*(self.page-1):5*self.page]):
            self.draw_func(self, obj, i)

    def add_draw_func(self, func, *args, **kwargs):
        self.draw_array.append(lambda: func(*args, **kwargs))

    def change_page(self, change=1):
        self.update_max_page()
        self.check_page_n()
        if 0 < self.page + change <= self.max_page:
            self.page += change
            self.update_data()

    add_ui = lambda self, obj: self.ui_elements.append(obj)
    draw = lambda self: [func() for func in self.draw_array]

TRAIN_SPEED_MS = 20
ANGLE_TRAIN_SPEED_MS = 10

bigger_0 = lambda x: 1 if x >= 0 else -1


def count_speed(x, y, x1, y1):
    d_x, d_y = x1 - x, y1 - y

    if d_x == 0:
        return (0, TRAIN_SPEED_MS * bigger_0(d_y))
    elif d_y == 0:
        return (TRAIN_SPEED_MS * bigger_0(d_x), 0)
    else:
        return (ANGLE_TRAIN_SPEED_MS * bigger_0(d_x), ANGLE_TRAIN_SPEED_MS * bigger_0(d_y))


class BreakPoint(pygame.sprite.Sprite):

    def __init__(self, group, pos, s1, s2):
        super().__init__(group)
        self.image = pygame.Surface((2, 2), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(pos[0] - 1, pos[1] - 1, 2, 2)
        self.directions = {s.id:count_speed(self.rect.x + 1, self.rect.y + 1, s.x, s.y) for s in [s1, s2]}


class Station(pygame.sprite.Sprite):

    def __init__(self, group, manager, message_group, session, obj):
        super().__init__(group)
        self.obj = obj
        self.session = session

        self.high_traffic_k = 0
        self.is_built = True

        self.image = pygame.Surface((20, 20), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(self.obj.x - 10, self.obj.y - 10, 20, 20)
        pygame.draw.circle(self.image, pygame.Color("white"), (10, 10), 8)
        pygame.draw.circle(self.image, pygame.Color("black"), (10, 10), 8, 2)

        self.update_routes()

        manager.add_to_handle(self)

        self.manager = manager
        self.message_group = message_group

    def update_routes(self):
        self.directions = dict()
        for i, group in enumerate([[l for l in self.obj.lines_1], [l for l in self.obj.lines_2]]):
            for line in group:
                bp = self.session.sprites.breakpoints[line.id]
                self.directions[line.end.id if i == 0 else line.start.id] = count_speed(self.rect.x + 10, self.rect.y + 10, bp.rect.x + 1, bp.rect.y + 1)

    def count_traffic(self):
        x0, y0 = self.rect.x if self.rect.x else 1

    def update(self, time_delta, game_delta):
        if not self.session.is_ended and self.is_built:
            current_k = self.session.session.meta_data['station_flow'][str(self.obj.id)]
            if current_k > 20:
                self.session.end_game()
            else:
                pygame.draw.circle(self.image, pygame.Color('red' if current_k > 10 else 'yellow' if current_k > 5 else 'white'), (10, 10), 6)
            delta_k = 0
            routes = []
            for r in self.obj.get_lines():
                routes.extend(r.routes)
            if routes:
                for r in [i.id for i in routes]:
                    if str(r) in self.session.session.meta_data['routes_data']:
                        r_k = self.session.session.meta_data['routes_data'][str(r)][3]
                        if r_k < 1:
                            delta_k += 1 - r_k
                        else:
                            delta_k -= 0.25
            else:
                delta_k = 1
            if delta_k > 0:
                self.session.session.meta_data['station_flow'][str(self.obj.id)] += self.session.session.meta_data['station_data'][str(self.obj.id)][0] * 0.000000058 * game_delta.seconds * delta_k
            elif current_k > 0:
                self.session.session.meta_data['station_flow'][str(self.obj.id)] -= 0.000005787 * game_delta.seconds

    def on_click(self, event):

        def draw_func(screen):
            create_text(screen, 10, 50, 15, f'пассажиропоток станции: {self.session.session.meta_data["station_data"][str(self.obj.id)][0]}')

        MessageBox(self.message_group, manager=self.manager, draw_func=draw_func)


class Line(pygame.sprite.Sprite):

    def __init__(self, group, break_points_group, obj):
        super().__init__(group)

        self.obj = obj
        self.break_points_group = break_points_group

        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(300, 0, 1500, 750)

        self.create_line()

    def create_line(self):
        x, y, x1, y1 = self.obj.start.x, self.obj.start.y, self.obj.end.x, self.obj.end.y

        d_x, d_y = abs(x - x1), abs(y - y1)
        if d_y >= d_x:
            b_y = y1 + d_x * (y - y1) // d_y
            pygame.draw.line(self.image, 'white', (x - 300, y), (x - 300, b_y), 8)
            pygame.draw.line(self.image, 'white', (x - 300, b_y), (x1 - 300, y1), 10)
            self.breakpoint = BreakPoint(self.break_points_group, (x, b_y), self.obj.start, self.obj.end)
        else:
            b_x = x + (d_y + 5) * (x1 - x) // d_x - 300
            pygame.draw.line(self.image, 'white', (x - 300, y), (b_x, y1), 10)
            pygame.draw.line(self.image, 'white', (b_x, y1), (x1 - 300, y1), 8)
            self.breakpoint = BreakPoint(self.break_points_group, (b_x + 300, y1), self.obj.start, self.obj.end)
        self.breakpoint.routes = self.obj.routes


class Route(pygame.sprite.Sprite):

    def __init__(self, group, obj, route):
        super().__init__(group)

        self.obj = obj
        self.route = route

        self.color = models.ROUTES_COLORS[self.route.color]
        self.image = pygame.Surface((1500, 750), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(300, 0, 1500, 750)

        self.create_route()

    def create_route(self):
        delta = 0
        x, y, x1, y1 = self.obj.start.x, self.obj.start.y, self.obj.end.x, self.obj.end.y

        line_routes = list(self.obj.routes)
        line_routes_len = len(line_routes)

        if len(line_routes) > 1:
            route_ind = line_routes.index(self.route)
            delta = -2 * (line_routes_len - 1) + 4 * route_ind

        d_x, d_y = abs(x - x1), abs(y - y1)
        if d_y >= d_x:
            x += delta
            x1 += delta
            b_y = y1 + d_x * (y - y1) // d_y
            pygame.draw.line(self.image, self.color, (x - 300, y), (x - 300, b_y), 4)
            pygame.draw.line(self.image, self.color, (x - 300, b_y), (x1 - 300, y1), 5)
        else:
            y += delta
            y1 += delta
            b_x = x + (d_y + 5) * (x1 - x) // d_x - 300
            pygame.draw.line(self.image, self.color, (x - 300, y), (b_x, y1), 5)
            pygame.draw.line(self.image, self.color, (b_x, y1), (x1 - 300, y1), 4)


class Train(pygame.sprite.Sprite):

    def __init__(self, group, route, station, clock, session, direction=1):
        super().__init__(group)

        self.session = session
        self.route = route
        self.clock = clock

        self.next_station, self.direction = session.get_next_station(route, station, direction)
        self.station = station
        self.pos = (station.x, station.y)
        self.vx, self.vy = 0, 0
        self.collided = None
        self.collided_station = None

        self.attempt = 1

        self.draw()

    def draw(self):
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(self.pos[0] - 6, self.pos[1] - 6, 12, 12)

        pygame.draw.circle(self.image, pygame.Color("white"), (6, 6), 5)
        pygame.draw.circle(self.image, pygame.Color("black"), (6, 6), 5, 1)

    def update(self, time_delta, game_time):

        if self.clock.mode == TIME_MODE.SLOW:

            self.rect.x += int(self.vx * time_delta)
            self.rect.y += int(self.vy * time_delta)

            bp = pygame.sprite.spritecollideany(self, self.session.break_points_group)
            s = pygame.sprite.spritecollideany(self, self.session.stations_group)

            if bp or s:
                if s and s != self.collided and self.collided_station != s:
                    self.rect.x, self.rect.y = s.rect.x + 4, s.rect.y + 4
                    next_lst = self.session.get_next_station(self.route, s.obj, self.direction)
                    if next_lst:
                        self.next_station, self.direction = self.session.get_next_station(self.route, s.obj, self.direction)
                        if self.next_station.id in s.directions:
                            self.vx, self.vy = s.directions[self.next_station.id]
                        else:
                            lst = [abs(i - self.next_station.id) for i in s.directions.keys()]
                            self.vx, self.vy = s.directions[list(s.directions.keys())[lst.index(min(lst))]]
                        self.collided_station = s
                        self.collided = s
                    else:
                        self.suicide()
                elif bp and bp != self.collided and self.route in bp.routes:
                    self.rect.x, self.rect.y = bp.rect.x - 4, bp.rect.y - 4
                    if self.next_station.id in bp.directions:
                        self.vx, self.vy = bp.directions[self.next_station.id]
                    else:
                        lst = [abs(i - self.next_station.id) for i in bp.directions.keys()]
                        self.vx, self.vy = bp.directions[list(bp.directions.keys())[lst.index(min(lst))]]
                    self.collided = bp

    def suicide(self):
        self.session.add_new_train(self.route)
        self.session.sprites.trains[self.route.id].remove(self)
        self.kill()