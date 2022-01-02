import datetime
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

game_map = map_core.Map()
SESSION = models.GameSession.create(map=game_map.map, centers=game_map.centers)


# creating station
def create_station_handler(self, event):
    action_data.on_click_func = create_station
    action_data.status = 'creating_station'

    self.set_text('accept')
    self.on_click_func = accept_station_handler


def accept_station_handler(self, event):
    if len(action_data.clicks) > 0:
        create_station(self, commit=True)
        self.on_click_func = create_station_handler
    else:
        core.MessageBox(
            all_sprites,
            manager=ui_manager,
            text="Возникла какая-то ошибка")
    action_data.clear()
    self.reset_text()


def create_station(btn, event=None, commit=False):
    x, y = event.pos

    cond = True
    for l in SESSION.lines:
        if not cond:
            break
        for s in l.stations:
            if ((s.x - x) ** 2 + (s.y - y) ** 2) ** 0.5 < 30:
                cond = False
                break

    if cond:
        if commit:
            models.Station.create()
        elif len(action_data.clicks) > 0:
            core.Station(subway_sprites, *action_data.clicks[-1])

    return cond


# creating lines
def create_line_handler(self, event):
    action_data.on_click_func = create_line_fr
    action_data.status = 'creating_line'

    self.set_text('accept')
    self.on_click_func = accept_line_handler


def accept_line_handler(self, event):
    '''if len(action_data.clicks) > 0:
        create_station(self, commit=True)
        self.on_click_func = create_station_handler
    else:
        core.MessageBox(
            all_sprites,
            manager=ui_manager,
            text="Возникла какая-то ошибка")
    action_data.clear()
    self.reset_text()'''
    pass


def create_line_fr(btn, event=None, commit=False):
    if commit:
        pass
    else:
        if len(action_data.clicks) > 1:
            core.Line(subway_sprites, *action_data.clicks[-2], *action_data.clicks[-1])


# UI
ui_manager = core.Manager((width, height), 'data/styles.json')


# Groups
text_render = core.AutoTextRender()
all_sprites = pygame.sprite.Group()
subway_sprites = pygame.sprite.Group()


# Sprites
core.MapSprite(all_sprites)


# Clock
text_render.add_text(screen, 10, 10, 15, 'clocks', True)

pause = core.Button(relative_rect=pygame.Rect((10, 40), (135, 30)), text='pause', manager=ui_manager, on_click=lambda self, event: change_time_mode(self, event))
text_render.add_text_stream(screen, 155, 45, 15, func=clock.get_str_datetime, bold=True)

def change_time_mode(self, event, mode=0):
    [obj.reset_text() for obj in [pause, speed_1, speed_2, speed_3]]
    clock.set_mode(mode)
    self.set_text('chosen')

speed_1 = core.Button(relative_rect=pygame.Rect((10, 80), (85, 30)), text='6min/day', manager=ui_manager, on_click=lambda self, event: change_time_mode(self, event, 1))
speed_2 = core.Button(relative_rect=pygame.Rect((105, 80), (85, 30)), text='24sec/day', manager=ui_manager, on_click=lambda self, event: change_time_mode(self, event, 2))
speed_3 = core.Button(relative_rect=pygame.Rect((200, 80), (85, 30)), text='1sec/day', manager=ui_manager, on_click=lambda self, event: change_time_mode(self, event, 3))


# Building
text_render.add_text(screen, 10, 125, 15, 'building', True)

build_station = core.Button(relative_rect=pygame.Rect((10, 145), (135, 30)), text='build station', manager=ui_manager, on_click=create_station_handler)
build_line = core.Button(relative_rect=pygame.Rect((155, 145), (135, 30)), text='build line', manager=ui_manager, on_click=create_line_handler)


while running:

    time_delta, game_delta = clock.tick()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if action_data.status != 'watching':
                if 300 < event.pos[0] < 1800 and 0 < event.pos[1] < 750:
                    action_data.clicks.append(event.pos)
            action_data.on_click(event)
        ui_manager.process_events(event)

    screen.fill('white')
    all_sprites.draw(screen)
    subway_sprites.draw(screen)
    ui_manager.draw_ui(screen)
    text_render.render()

    ui_manager.update(time_delta)

    pygame.display.flip()

pygame.quit()