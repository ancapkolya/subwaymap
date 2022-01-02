import datetime
import pygame

import core


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


# creating station
def create_station_handler(self, event):
    action_data.on_click_func = create_station
    action_data.status = 'creating_station'

    self.set_text('accept')
    self.on_click_func = accept_station_handler


def accept_station_handler(self, event):
    if len(action_data.clicks) > 0:
        create_station(action_data.clicks[-1])
    else:
        core.MessageBox(
            all_sprites,
            manager=ui_manager,
            text="Возникла какая-то ошибка")
    action_data.clear()
    self.reset_text()


def create_station(pos):
    print(pos)


# UI
ui_manager = core.Manager((width, height), 'data/styles.json')


# Groups
text_render = core.AutoTextRender()
all_sprites = pygame.sprite.Group()


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
build_line = core.Button(relative_rect=pygame.Rect((155, 145), (135, 30)), text='build line', manager=ui_manager, on_click=create_station_handler)


while running:

    time_delta, game_delta = clock.tick()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if action_data.status != 'watching':
                if 150 < event.pos[0] < 1800 and 0 < event.pos[1] < 750:
                    action_data.clicks.append(event.pos)
            action_data.on_click(event)
        ui_manager.process_events(event)

    screen.fill('white')
    all_sprites.draw(screen)
    ui_manager.draw_ui(screen)
    text_render.render()

    ui_manager.update(time_delta)

    pygame.display.flip()

pygame.quit()