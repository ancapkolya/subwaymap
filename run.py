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

SESSION = core.Session(pk=4)


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
            action_data.sprites.append(core.Station(subway_sprites, *action_data.clicks[-1]))
            action_data.objects.append(models.Station(
                game=SESSION.session.id,
                x=action_data.clicks[-1][0],
                y=action_data.clicks[-1][1]
            ))

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
                            start = s.rect
                        if not end and s.rect.collidepoint(*action_data.clicks[-2]):
                            end = s.rect
                    else:
                        break
                if start and end:
                    action_data.sprites.append(core.Line(subway_sprites, *[i + 10 for i in [start.x, start.y, end.x, end.y]]))
                    action_data.objects.append(models.Line(
                        game=SESSION.session.id,
                        x=action_data.clicks[-1][0],
                        y=action_data.clicks[-1][1]
                    ))
                    core.Line(subway_sprites, *[i + 10 for i in [start.x, start.y, end.x, end.y]])


# UI
ui_manager = core.Manager((width, height), 'data/styles.json')


# Groups
text_render = core.AutoTextRender()
all_sprites = pygame.sprite.Group()
subway_sprites = pygame.sprite.Group()


# Sprites
core.MapSprite(all_sprites, obj=SESSION.get_map())


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

SESSION.load_sprites(subway_sprites)


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