import pygame

import core
import map_core
import models


# init
pygame.init()
pygame.font.init()
size = width, height = 1800, 750
screen = pygame.display.set_mode(size)
clock = core.WrappedClock()
running = True
screen.fill('white')


# actions
action_data = core.ActionData()

SESSION = None


# GAME WINDOW
# creating station
def create_station_handler(self, event):
    action_data.clear(True, True)

    action_data.on_click_func = create_station
    action_data.status = 'creating_station'

    self.set_text('accept')
    self.on_click_func = accept_station_handler

    def clear_func():
        self.reset_text()
        self.on_click_func = create_station_handler

    action_data.clear_func = clear_func


def accept_station_handler(self, event):
    if len(action_data.clicks) > 0:
        create_station(self, commit=True)
    else:
        core.MessageBox(
            warning_sprites,
            manager=game_ui_manager,
            text="Возникла какая-то ошибка")
    self.on_click_func = create_station_handler
    action_data.clear()
    self.reset_text()


def create_station(btn, event=None, commit=False):
    cond = True
    if commit and len(action_data.objects) > 0 and len(action_data.sprites) > 0:
        action_data.objects[-1].save()
        SESSION.sprites.stations.append(action_data.sprites[-1])
    else:
        x, y = event.pos

        for s in SESSION.session.stations:
            if ((s.x - x) ** 2 + (s.y - y) ** 2) ** 0.5 < 30:
                cond = False
                break

        if cond and len(action_data.clicks) > 0 and action_data.status == 'creating_station':
            action_data.status = 'accepting_station'
            station = models.Station(
                game=SESSION.session.id,
                x=action_data.clicks[-1][0],
                y=action_data.clicks[-1][1]
            )
            action_data.sprites.append(core.Station(stations_sprites, SESSION, station))
            action_data.objects.append(station)

    return cond


# creating lines
def create_line_handler(self, event):
    action_data.clear(True, True)

    action_data.on_click_func = create_line_fr
    action_data.status = 'creating_line'

    self.set_text('accept')
    self.on_click_func = accept_line_handler

    def clear_func():
        self.reset_text()
        self.on_click_func = create_line_handler

    action_data.clear_func = clear_func


def accept_line_handler(self, event):
    if len(action_data.objects) > 0 and len(action_data.sprites) > 0:
        create_line_fr(self, commit=True)
    else:
        core.MessageBox(
            warning_sprites,
            manager=game_ui_manager,
            text="Возникла какая-то ошибка")
    self.on_click_func = create_line_handler
    action_data.clear()
    self.reset_text()


def create_line_fr(btn, event=None, commit=False):
    if commit:
        [obj.save() for obj in action_data.objects]
        SESSION.sprites.lines.extend(action_data.sprites)
        SESSION.update_map()
    else:
        cond = False
        if len(action_data.clicks) > 0:
            for s in SESSION.sprites.stations:
                if not cond:
                    print(s)
                    cond = s.rect.collidepoint(*action_data.clicks[-1])
                else:
                    break
            if not cond:
                action_data.clicks = action_data.clicks[:-1]
            if len(action_data.clicks) > 1:
                start, end = False, False
                for s in SESSION.sprites.stations:
                    if not start or not end:
                        if not start and s.rect.collidepoint(*action_data.clicks[-1]):
                            start = s.obj.id
                        if not end and s.rect.collidepoint(*action_data.clicks[-2]):
                            end = s.obj.id
                    else:
                        break
                if start and end:
                    for l in SESSION.session.lines:
                        if {l.start.id, l.end.id} == {start, end}:
                            action_data.clicks = action_data.clicks[:-1]
                            return
                    action_data.objects.append(models.Line(
                        game=SESSION.session.id,
                        start=start,
                        end=end
                    ))
                    action_data.sprites.append(core.Line(lines_sprites, break_points_group, action_data.objects[-1]))
                    action_data.clicks = action_data.clicks[-1:]


# creating lines
def create_route_handler(self, event):
    action_data.clear(True, True)

    action_data.on_click_func = create_route_fr
    action_data.status = 'creating_route'

    self.set_text('accept')
    self.on_click_func = accept_route_handler

    def clear_func():
        if len(action_data.objects) > 0:
            for obj in action_data.objects:
                obj.delete()
        self.reset_text()
        self.on_click_func = create_route_handler

    action_data.clear_func = clear_func


def accept_route_handler(self, event):
    if len(action_data.objects) > 0 and len(action_data.sprites) > 0:
        create_route_fr(self, commit=True)
    else:
        core.MessageBox(
            warning_sprites,
            manager=game_ui_manager,
            text="Возникла какая-то ошибка")
    self.on_click_func = create_route_handler
    action_data.clear()
    self.reset_text()


def create_route_fr(btn, event=None, commit=False):
    if commit:
        [obj.save() for obj in action_data.objects]
        SESSION.sprites.routes.extend(action_data.sprites)
        SESSION.update_routes_map()
    else:
        cond = False
        if len(action_data.clicks) > 0:
            for s in SESSION.sprites.stations:
                if not cond:
                    cond = s.rect.collidepoint(*action_data.clicks[-1])
                else:
                    break
            if not cond:
                action_data.clicks = action_data.clicks[:-1]
            if len(action_data.clicks) > 1:
                start, end = False, False
                for s in SESSION.sprites.stations:
                    if not start or not end:
                        if not start and s.rect.collidepoint(*action_data.clicks[-1]):
                            start = s.obj.id
                        if not end and s.rect.collidepoint(*action_data.clicks[-2]):
                            end = s.obj.id
                    else:
                        break
                if start and end:
                    lines = (list(models.Line.filter(start=start, end=end)) + list(models.Line.filter(start=end, end=start)))
                    if lines:
                        line = lines[0]
                        if len(action_data.objects) == 0:
                            action_data.objects.append(models.Route(
                                game=SESSION.session.id,
                                train_n=0,
                                color=models.get_route_color(SESSION.session.id)
                            ))
                        action_data.objects[-1].load_data()
                        action_data.objects[-1].lines_queue.append(line.id)
                        action_data.objects[-1].save()
                        action_data.sprites.append(
                            core.Route(
                                lines_sprites,
                                action_data.objects[-1].lines[-1],
                                action_data.objects[-1])
                        )
                        action_data.sprites[-1].create_route()
                        SESSION.update_routes_map()
                        action_data.clicks = action_data.clicks[-1:]



# UI
game_ui_manager = core.Manager((width, height), 'data/styles.json')


# Groups
text_render = core.AutoTextRender()
routes_paginator_text_render = core.AutoTextRender()

all_sprites = pygame.sprite.Group()
stations_sprites = pygame.sprite.Group()
lines_sprites = pygame.sprite.Group()
routes_group = pygame.sprite.Group()
trains_group = pygame.sprite.Group()
break_points_group = pygame.sprite.Group()
warning_sprites = pygame.sprite.Group()


# Sprites
def init_game_window():

    # Main
    text_render.add_text(screen, 10, 10, 15, 'Menu', True)

    core.Button(relative_rect=pygame.Rect((10, 40), (135, 30)), text='cancel', manager=game_ui_manager,
                on_click=lambda *args: action_data.clear(True, True))
    core.Button(relative_rect=pygame.Rect((155, 40), (135, 30)), text='quit', manager=game_ui_manager,
                on_click=lambda *args: game_loop.set_window(start_window))
    core.Button(relative_rect=pygame.Rect((10, 80), (135, 30)), text='save', manager=game_ui_manager,
                on_click=lambda: print(0))
    core.Button(relative_rect=pygame.Rect((155, 80), (135, 30)), text='empty', manager=game_ui_manager,
                on_click=lambda: print(1))

    # Clocks
    def change_time_mode(self, event, mode=0):
        [obj.reset_text() for obj in [pause, speed_1, speed_2, speed_3]]
        clock.set_mode(mode)
        self.set_text('chosen')

    core.MapSprite(all_sprites, obj=SESSION.get_map())

    text_render.add_text(screen, 10, 125, 15, 'budget', True)
    text_render.add_text_stream(screen, 10, 155, 15, func=lambda: f'cash: 1000000', bold=True)
    text_render.add_text_stream(screen, 155, 155, 15, func=lambda: f'build cost: 100000', bold=True)

    speed_1 = core.Button(relative_rect=pygame.Rect((10, 195), (85, 30)), text='6min/day', manager=game_ui_manager,
                          on_click=lambda self, event: change_time_mode(self, event, 1))
    speed_2 = core.Button(relative_rect=pygame.Rect((105, 195), (85, 30)), text='24sec/day', manager=game_ui_manager,
                          on_click=lambda self, event: change_time_mode(self, event, 2))
    speed_3 = core.Button(relative_rect=pygame.Rect((200, 195), (85, 30)), text='1sec/day', manager=game_ui_manager,
                          on_click=lambda self, event: change_time_mode(self, event, 3))

    text_render.add_text(screen, 10, 240, 15, 'clocks', True)
    text_render.add_text_stream(screen, 155, 275, 15, func=clock.get_str_datetime, bold=True)

    pause = core.Button(relative_rect=pygame.Rect((10, 270), (135, 30)), text='pause', manager=game_ui_manager, on_click=lambda self, event: change_time_mode(self, event))
    speed_1 = core.Button(relative_rect=pygame.Rect((10, 310), (85, 30)), text='6min/day', manager=game_ui_manager, on_click=lambda self, event: change_time_mode(self, event, 1))
    speed_2 = core.Button(relative_rect=pygame.Rect((105, 310), (85, 30)), text='24sec/day', manager=game_ui_manager, on_click=lambda self, event: change_time_mode(self, event, 2))
    speed_3 = core.Button(relative_rect=pygame.Rect((200, 310), (85, 30)), text='1sec/day', manager=game_ui_manager, on_click=lambda self, event: change_time_mode(self, event, 3))


    # Building
    text_render.add_text(screen, 10, 355, 15, 'building', True)

    core.Button(relative_rect=pygame.Rect((10, 375), (135, 30)), text='build station', manager=game_ui_manager, on_click=create_station_handler)
    core.Button(relative_rect=pygame.Rect((155, 375), (135, 30)), text='build line', manager=game_ui_manager, on_click=create_line_handler)

    # Routes
    text_render.add_text(screen, 10, 420, 15, 'Routes', True)

    core.Button(relative_rect=pygame.Rect((10, 440), (135, 30)), text='create route', manager=game_ui_manager,
                on_click=create_route_handler)
    core.Button(relative_rect=pygame.Rect((155, 440), (135, 30)), text='empty', manager=game_ui_manager,
                on_click=create_line_handler)

    def route_draw_func(self, obj, i):
        obj.load_data()
        obj.max_n = len(obj.lines_queue) + 1
        d = i * 40
        self.auto_text_render.add_text(self.screen, self.x+45, self.y+65+d, 15, str(i + 1), True)
        self.add_draw_func(pygame.draw.rect, self.screen, models.ROUTES_COLORS[obj.color], (self.x+15, self.y+65+d, 20, 20), border_radius=3)
        self.add_ui(core.Button(relative_rect=pygame.Rect((self.x+65, self.y+65+d), (20, 20)), text='-', manager=self.ui_manager, on_click=lambda *args: change_train_n(obj, -1)))
        self.auto_text_render.add_text_stream(self.screen, self.x+90, self.y+65+d, 15, func=lambda: f'{obj.train_n}/{obj.max_n}', bold=True)
        self.add_ui(core.Button(relative_rect=pygame.Rect((self.x+125, self.y+65+d), (20, 20)), text='+', manager=self.ui_manager, on_click=lambda *args: change_train_n(obj, +1)))
        self.add_ui(core.Button(relative_rect=pygame.Rect((self.x+160, self.y+65+d), (55, 20)), text='stats', manager=self.ui_manager, on_click=lambda *args: 0))
        self.add_ui(core.Button(relative_rect=pygame.Rect((self.x+225, self.y+65+d), (55, 20)), text='del', manager=self.ui_manager, on_click=lambda *args: delete_route(obj)))

        def change_train_n(obj, c):
            if 0 <= obj.train_n + c <= obj.max_n:
                obj.train_n += c
                obj.save()
                SESSION.create_trains()

        def delete_route(obj):
            obj.delete_instance()
            SESSION.update_routes_map()
            SESSION.create_trains()

    routes_list = core.RoutesPaginator(
        screen,
        ui_manager=game_ui_manager,
        auto_text_render=routes_paginator_text_render,
        x=0, y=490,
        get_objects_func=lambda: list(models.Route.filter(game=SESSION.session.id)),
        draw_func=route_draw_func
    )

    SESSION.load_sprites(
        stations_group=stations_sprites,
        lines_group=lines_sprites,
        routes_group=routes_group,
        trains_group=trains_group,
        break_points_group=break_points_group,
        routes_list_update_callback=routes_list.update_callback,
        draw_objects_array=[routes_list],
        clock=clock
    )


# GAME WINDOW CREATING
def game_window_process_events(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        if action_data.status != 'watching':
            if 300 < event.pos[0] < 1800 and 0 < event.pos[1] < 750:
                action_data.clicks.append(event.pos)
        action_data.on_click(event)

def game_window_update(self, *args, **kwargs):
    SESSION.draw_objects()
    self.groups[4].update(*args)

game_window = core.Window(
    init_func=init_game_window,
    process_events_func=game_window_process_events,
    update_func=game_window_update,
    auto_text_renders=[text_render, routes_paginator_text_render],
    groups=[all_sprites, lines_sprites, routes_group, stations_sprites, trains_group, warning_sprites, break_points_group],
    ui=game_ui_manager,
)


# START WINDOW
# Groups
start_text_render = core.AutoTextRender()
start_sprites = pygame.sprite.Group()


# UI
start_ui_manager = core.Manager((width, height), 'data/styles.json')


def init_start_window():

    def load_game(pk):
        global SESSION
        SESSION = core.Session(pk)
        game_loop.set_window(game_window)

    start_text_render.add_text(screen, 732, 280, 50, 'subwaymap', True)

    core.Button(relative_rect=pygame.Rect((725, 350), (195, 50)), text='load previous', manager=start_ui_manager, on_click=lambda self, event: load_game(-1))
    core.Button(relative_rect=pygame.Rect((925, 350), (145, 50)), text='new game', manager=start_ui_manager, on_click=lambda self, event: game_loop.set_window(new_game_window))

    start_text_render.add_text(screen, 35, 410, 20, 'games', True)

    length = len(models.GameSession.select())
    rows = length // 29 + 1

    for i in range(rows):
        for j in range(29):
            n = i * 29 + j + 1
            if n <= length:
                core.Button(relative_rect=pygame.Rect((j * 60 + 35, 450 + i * 40), (60, 30)), text=str(n),
                            manager=start_ui_manager, on_click=lambda self, event, n=n: load_game(n))
            else:
                break

    core.ImageSprite(start_sprites, 'logo.png', 725, 100, 350, 167)


start_window = core.Window(
    init_func=init_start_window,
    process_events_func=lambda *args: 0,
    auto_text_renders=[start_text_render],
    groups=[start_sprites],
    ui=start_ui_manager,
)


# NEW GAME WINDOW
# Groups
new_game_text_render = core.AutoTextRender()
new_game_sprites = pygame.sprite.Group()


# UI
new_game_ui_manager = core.Manager((width, height), 'data/styles.json')


def create_and_run_game(map_obj, level):
    global SESSION
    session = models.GameSession(
        map=map_obj.map.tolist(),
        centers=map_obj.centers.tolist(),
        level=level
    )
    session.save()
    SESSION = core.Session(pk=session.id)
    game_loop.set_window(game_window)


def init_new_game_window():
    sprite = core.MapSprite(new_game_sprites)
    sprite.level = 1

    # Main
    new_game_text_render.add_text(screen, 10, 10, 15, 'Menu', True)

    core.Button(relative_rect=pygame.Rect((10, 40), (135, 30)), text='start', manager=new_game_ui_manager,
                on_click=lambda *args: create_and_run_game(sprite.map, sprite.level))
    core.Button(relative_rect=pygame.Rect((155, 40), (135, 30)), text='generate', manager=new_game_ui_manager,
                on_click=lambda *args: sprite.generate_new())
    core.Button(relative_rect=pygame.Rect((10, 80), (135, 30)), text='quit', manager=new_game_ui_manager,
                on_click=lambda *args: game_loop.set_window(start_window))
    core.Button(relative_rect=pygame.Rect((155, 80), (135, 30)), text='empty', manager=new_game_ui_manager,
                on_click=lambda: print(1))

    new_game_text_render.add_text(screen, 10, 125, 15, 'Level (1-3)', True)

    def change_level(sprite, delta=-1):
        if 1 <= sprite.level + delta <= 3:
            sprite.level += delta

    core.Button(relative_rect=pygame.Rect((10, 155), (135, 30)), text='-', manager=new_game_ui_manager,
                on_click=lambda *args: change_level(sprite))
    core.Button(relative_rect=pygame.Rect((155, 155), (135, 30)), text='+', manager=new_game_ui_manager,
                on_click=lambda *args: change_level(sprite, 1))

    new_game_text_render.add_text_stream(screen, 10, 195, 15, func=lambda: f'level: {sprite.level}', bold=True)



new_game_window = core.Window(
    init_func=init_new_game_window,
    process_events_func=lambda *args: 0,
    auto_text_renders=[new_game_text_render],
    groups=[new_game_sprites],
    ui=new_game_ui_manager,
)


# GAME LOOP
game_loop = core.GameLoop(screen, clock)
game_loop.set_window(start_window)


game_loop.loop()