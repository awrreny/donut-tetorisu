import pygame
# this file contains info for the display e.g colours and dictionaries for colours


def greyscale(brightness):
    return pygame.Color(brightness, brightness, brightness)


color_black = greyscale(0)
color_white = greyscale(255)
color_darkish_grey = greyscale(48)
color_darkishish_grey = greyscale(96)
color_grey = greyscale(128)
color_lightish_grey = greyscale(160)
color_light_grey = greyscale(192)
color_cyan = pygame.Color(0, 255, 255)
color_yellow = pygame.Color(255, 255, 0)
color_purple = pygame.Color(128, 0, 128)
color_green = pygame.Color(0, 255, 0)
color_red = pygame.Color(255, 0, 0)
color_blue = pygame.Color(0, 0, 255)
color_orange = pygame.Color(255, 127, 0)
color_dark_cyan = pygame.Color(0, 127, 127)
color_dark_yellow = pygame.Color(127, 127, 0)
color_dark_purple = pygame.Color(64, 0, 64)
color_dark_green = pygame.Color(0, 127, 0)
color_dark_red = pygame.Color(127, 0, 0)
color_dark_blue = pygame.Color(0, 0, 127)
color_dark_orange = pygame.Color(127, 64, 0)
color_light_cyan = pygame.Color(128, 255, 255)
color_light_yellow = pygame.Color(255, 255, 128)
color_light_purple = pygame.Color(192, 0, 192)
color_light_green = pygame.Color(128, 255, 128)
color_light_red = pygame.Color(255, 128, 128)
color_light_blue = pygame.Color(0, 64, 255)
color_light_orange = pygame.Color(255, 192, 128)

# colou?rs

tile_border_color = color_darkish_grey  # color_black
# form: [main colour, shadow/dark color, light colour]
empty_tile_color = [color_darkishish_grey, color_darkishish_grey, color_darkishish_grey]  # [color_grey, color_grey, color_light_grey]
background_color = color_darkish_grey
ghost_block_color = color_darkish_grey
main_text_color = color_lightish_grey
ui_border_color = color_darkishish_grey
ui_dark_color = color_grey  # for next/hold queue text

char_to_color = {
    "0": empty_tile_color[0],
    "i": color_cyan,
    "o": color_yellow,
    "t": color_purple,
    "s": color_green,
    "z": color_red,
    "j": color_blue,
    "l": color_orange,
    "g": color_black
}
char_to_dark_color = {
    "0": empty_tile_color[1],
    "i": color_dark_cyan,
    "o": color_dark_yellow,
    "t": color_dark_purple,
    "s": color_dark_green,
    "z": color_dark_red,
    "j": color_dark_blue,
    "l": color_dark_orange,
    "g": color_black
}
char_to_light_color = {
    "0": empty_tile_color[2],
    "i": color_light_cyan,
    "o": color_light_yellow,
    "t": color_light_purple,
    "s": color_light_green,
    "z": color_light_red,
    "j": color_light_blue,
    "l": color_light_orange,
    "g": color_black
}
