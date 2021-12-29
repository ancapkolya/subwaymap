import pygame

from map_core import Map
import core


# init
pygame.init()
pygame.font.init()
size = width, height = 1800, 750
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
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
    core.MessageBox(
        all_sprites,
        manager=ui_manager,
        text=action_data.clicks)


def create_station(self, event):
    pass
    #core.MessageBox()



# UI
ui_manager = core.Manager((width, height), 'data/styles.json')

# Building
core.create_text(screen, 10, 10, 'building', 15, True)

build_station = core.Button(relative_rect=pygame.Rect((10, 35), (135, 30)), text='build station', manager=ui_manager, on_click=create_station_handler)
build_line = core.Button(relative_rect=pygame.Rect((155, 35), (135, 30)), text='build line', manager=ui_manager, on_click=create_station_handler)


# Groups
all_sprites = pygame.sprite.Group()
#mb_sprites = pygame.sprite.Group()


# Sprites
core.MapSprite(all_sprites)


while running:

    time_delta = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if action_data.status != 'watching':
                if 150 < event.pos[0] < 1800 and 0 < event.pos[1] < 750:
                    action_data.clicks.append(event.pos)
            action_data.on_click(event)

        '''elif event.type == pygame.KEYDOWN:
            if STATUS == 'building_map':
                print(pygame.key.get_pressed())
        elif event.type == pygame.USEREVENT:
             if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                 if event.ui_element == build_station:
                     STATUS = 'building_map'
                     build_station.set_text('active')'''
        ui_manager.process_events(event)

    screen.fill('white')
    all_sprites.draw(screen)
    ui_manager.draw_ui(screen)

    ui_manager.update(time_delta)

    pygame.display.flip()

pygame.quit()