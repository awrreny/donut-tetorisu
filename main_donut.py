import sys
import copy
import tkinter
import logging
from tetris_info import *
from display_info import *
from presets import *
from settings import *
from pygame.locals import *


logging.basicConfig(filename='error.log', level=logging.INFO)
pygame.init()

if tekoFontVisible:
    fonts = [pygame.font.SysFont("default", 25), pygame.font.SysFont("teko", 20), pygame.font.SysFont("teko", 25),
             pygame.font.SysFont("teko", 35)]
else:
    fonts = [pygame.font.SysFont("default", 30), pygame.font.SysFont("default", 25), pygame.font.SysFont("default", 30),
             pygame.font.SysFont("default", 40)]

softDropTime = 0
gravityTime = 0
DASLeftDelayTime = 0
DASLeftIntervalTime = 0
DASRightIntervalTime = 0
DASRightDelayTime = 0
lockDelayCancels = 0
totalLockDelayCancelTime = 0
timeOfLastPiecePlacement = 0
timeOfLastNaturalPiecePlacement = 0
timeOnGround = 0  # used for lock delay
gameOverTime = 0
current_time_ms = 0


piece_to_orientation_index_dict_global = piece_to_orientation_index_dict

leftKeyHeld = False
rightKeyHeld = False
hold_key_pressed = False  # used so the user can't hold twice without placing


class GameState:
    def __init__(self):
        self.state = "main_game"

    def manage_game_state(self):
        if self.state == "intro":
            self.intro()
        elif self.state == "main_game":
            self.main_game()
        elif self.state == "settings":
            self.settings_window()
        elif self.state == "game_over":
            self.game_over()
        else:
            raise Exception("Invalid game state")

    @staticmethod
    def intro():
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

    @staticmethod
    def game_over():
        global current_time_ms, boardLeftXValue, boardRect
        current_time_ms = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        pygame.draw.rect(screen, background_color,
                         Rect(0, 0, windowWidth, (current_time_ms - gameOverTime)*7/30))
        if current_time_ms - gameOverTime < 3000:
            boardLeftXValue = int(260 - scaled_sigmoid(current_time_ms - gameOverTime))
            game_over_text.texts[1][0] = f"You cleared {lines_cleared} lines in {format_time(gameOverTime)}"
        else:
            game_over_text.render_info_texts()
        pygame.draw.rect(screen, background_color,
                         Rect(boardLeftXValue + boardWidth, boardTopYValue, 10, boardHeight + 1))
        draw_board()
        # draw lines between squares
        for j in range(board_columns + 1):  # draw vertical lines
            pygame.draw.line(screen, tile_border_color,
                             (boardLeftXValue + j * pixelsPerTile, boardTopYValue + pixelsPerTile * 3),
                             (boardLeftXValue + j * pixelsPerTile, boardTopYValue + boardHeight))
        for j in range(board_rows - 2):  # draw horizontal lines
            pygame.draw.line(screen, tile_border_color,
                             (boardLeftXValue, boardTopYValue + pixelsPerTile * 3 + j * pixelsPerTile),
                             (boardLeftXValue + boardWidth, boardTopYValue + pixelsPerTile * 3 + j * pixelsPerTile))
        pygame.display.update()
        FPS.tick(setFPS)

    def main_game(self):
        global tetrominoState, oldTetrominoState, current_time_ms, timeOnGround, gravityTime, DASLeftDelayTime,\
            DASRightDelayTime, lockDelayCancels, hold_key_pressed, timeOfLastNaturalPiecePlacement, gameOverTime, \
            settingsButton, settingsButtonSize, presetMap, customBag, board
        oldTetrominoState = tetrominoState  # used to detect a change in piece state.
        # complementing code is at the end of the loop. may be used for t-spin checks or finesse counting
        current_time_ms = pygame.time.get_ticks()
        gameOverTime = current_time_ms
        keys_pressed = pygame.key.get_pressed()
        # lock delay
        place_tetromino(tetrominoState, True)
        if move_is_valid(change_piece_state(tetrominoState, y_change=-1)):
            timeOnGround = current_time_ms
        place_tetromino(tetrominoState)
        # place block if on ground
        if current_time_ms - timeOnGround > lockDelay:
            tetrominoState = new_tetromino()
            timeOfLastNaturalPiecePlacement = current_time_ms
        # gravity
        if current_time_ms - gravityTime > gravityInterval:
            move_and_check(tetrominoState, y_change=-1)
            gravityTime = current_time_ms
        # soft drop
        if tuple(keys_pressed)[81] and (current_time_ms - softDropTime > softDropInterval or softDropInterval == -1):
            soft_drop()
        # DAS Left
        if current_time_ms - DASLeftDelayTime > DAS and tuple(keys_pressed)[80] and\
                current_time_ms - timeOfLastPiecePlacement > newPieceDASDelay:
            if ARR == -1:
                tetrominoState = move_das(tetrominoState, -1, False)
            else:
                move_and_check(tetrominoState, -1)
        if not tuple(keys_pressed)[80]:
            DASLeftDelayTime = current_time_ms
        # DAS Right
        if current_time_ms - DASRightDelayTime > DAS and tuple(keys_pressed)[79] and\
                current_time_ms - timeOfLastPiecePlacement > newPieceDASDelay:
            if ARR == -1:
                tetrominoState = move_das(tetrominoState, 1, False)
            else:
                move_and_check(tetrominoState, 1)
        if not tuple(keys_pressed)[79]:
            DASRightDelayTime = current_time_ms
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if settingsButton.rect.collidepoint(pygame.mouse.get_pos()):
                    # settingsButton.state = "open"
                    self.state = "settings"
            if event.type == KEYDOWN:
                if event.key == K_h:
                    place_tetromino(create_ghost_piece(tetrominoState), vfx=True)
                if event.key != key_hard_drop:
                    place_tetromino(tetrominoState, True)  # destroy o.g. piece b4 placing unless hard drop
                if event.key == key_move_right or event.key == key_move_left or event.key == key_90_anticlockwise or \
                        event.key == key_90_clockwise or event.key == key_180:
                    # reset lock delay (with limit)
                    if lockDelayCancels < lockDelayCancelLimit and current_time_ms - timeOnGround > 20:
                        lockDelayCancels += 1
                        timeOnGround = current_time_ms
                if event.key == key_soft_drop:
                    soft_drop()
                elif event.key == key_move_left:
                    move_and_check(tetrominoState, -1)
                elif event.key == key_move_right:
                    move_and_check(tetrominoState, 1)
                elif event.key == key_hard_drop and \
                        current_time_ms - timeOfLastNaturalPiecePlacement > newPieceHardDropDelay:
                    tetrominoState = hard_drop(tetrominoState)
                elif event.key == key_90_clockwise:
                    tetrominoState = rotate_piece(tetrominoState, 1)
                elif event.key == key_90_anticlockwise:
                    tetrominoState = rotate_piece(tetrominoState, -1)
                elif event.key == key_180:
                    tetrominoState = rotate_piece(tetrominoState, 2)
                elif event.key == key_hold or event.key == key_hold2:  # hold piece
                    if not hold_key_pressed or allowInfiniteHolds:
                        tetrominoState = hold_piece(tetrominoState)
                        hold_key_pressed = True
                elif event.key == key_resetboard:
                    initiate_board()  # for drilling pc setups/openers
                elif event.key == key_retryqueue:
                    initiate_board(repeat_queue=True)
                elif event.key == key_printboard:
                    print(board)  # for creating presets for presets.py
                elif event.key == key_changeCustomBag:
                    line_clear_effect("check the console!!!!", 80, 300)
                    pygame.display.update()
                    print(f"current custom bag: {customBag}")
                    customBag = list(input("Please enter new custom bag: (e.g iosz) "))
                    print(f"New custom bag is now {customBag}")
                    print("Reset board to see custom bag (default: F4)")
                    line_clear_effect("", 80, 300, width=160)
                elif event.key == key_changePreset:
                    line_clear_effect("check the console!!!!", 80, 300)
                    pygame.display.update()
                    validPreset = False
                    print("possible presets: ")
                    print(presets.keys())
                    while not validPreset:
                        inputtedPreset = input("Please enter which preset to use: ")
                        if inputtedPreset in presets.keys():
                            validPreset = True
                            presetMap = inputtedPreset
                            print("Reset board to see preset (default: F4)")
                        else:
                            print("invalid preset D:<")
                    line_clear_effect("", 80, 300, width=160)
                elif event.key == key_shiftleft:
                    board = shift_board(board, "left")
                elif event.key == key_shiftright:
                    board = shift_board(board, "right")
                elif event.key == key_shiftup:
                    board = shift_board(board, "up")
                elif event.key == key_shiftdown:
                    board = shift_board(board, "down")
                elif event.key == key_shiftleftbound:
                    board = shift_board(board, "leftbound")
                elif event.key == key_shiftrightbound:
                    board = shift_board(board, "rightbound")
                place_tetromino(tetrominoState)
                render_ghost_piece()
                draw_board()
        if oldTetrominoState != tetrominoState:
            render_ghost_piece()
            draw_board()
        draw_ui_text(draw_hold_queue=True, draw_next_queue=True, print_time=True)
        pygame.display.update()

    def settings_window(self):
        global settingsButton, settingsButtonSize
        # pygame.draw.rect(screen, background_color, Rect(windowWidth*0.2, windowHeight*0.2,
        #                                                 windowWidth*0.6, windowHeight*0.6))
        # pygame.draw.rect(screen, ui_border_color, Rect(windowWidth*0.2, windowHeight*0.2,
        #                                                windowWidth*0.6, windowHeight*0.6), width=1)
        draw_box_with_title((windowWidth*0.2, windowHeight*0.2, windowWidth*0.6, windowHeight*0.6, 30),
                            (background_color, ui_border_color, ui_dark_color),
                            ("Settings", (windowWidth/2 - 30, windowHeight/5 + 3),
                             (windowWidth/2 - 35, windowHeight/5 + 7)))
        # draw_box_with_title((windowWidth * 0.2, windowHeight * 0.2, windowWidth * 0.6, windowHeight * 0.6, 30),
        #                     (background_color, ui_border_color, ui_dark_color),
        #                     ("preset", (windowWidth / 2 - 30, windowHeight / 5 + 3),
        #                      (windowWidth / 2 - 35, windowHeight / 5 + 7)))
        # if settingsButton.pressed:
        #     print("a")
        #     settingsButton.pressed = False
        #     self.state = "main_game"
        #     settingsButton.rect.topleft = (20, windowHeight - (20 + settingsButtonSize))
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if settingsButton.rect.collidepoint(pygame.mouse.get_pos()):
                    initiate_board_graphics()
                    self.state = "main_game"
        pygame.display.flip()

# class Board:
#     @staticmethod
#     def initiate_board():
#         global
#         seven_bag = ['i', 'o', 't', 's', 'z', 'j', 'l']
#         random.shuffle(seven_bag)
#         piece_queue = ["i"]
#         piece_queue.extend(seven_bag.copy())
#         for i in range(7 - piecesToStartWith):
#             piece_queue.pop(0)
#         held_piece = ""
#         held_piece_box_drawn = False
#         gravityInterval = defaultGravityInterval
#
#         lines_cleared = 0
#         board_columns = 10
#         board_rows = 23
#         board = [["0"] * board_columns for i in range(board_rows)]  # create board as 2d list
#         vfx_board = [["0"] * board_columns for j in range(board_rows)]  # for ghost block and other effects
#         defaultTetrominoState = [4, board_rows - 2, get_next_piece(), 0]
#         tetrominoState = defaultTetrominoState  # stores piece state in form [x, y, piece type, orientation]
#         game_state = GameState()


class Button:
    def __init__(self, surface, leftx, topy, image):
        self.surface = surface
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (leftx, topy)
        self.surface.blit(self.image, (self.rect.x, self.rect.y))


class UIText:
    def __init__(self, coords, xy_gaps, *args):  # args is the text, in list [text, font number]
        self.coords = coords
        self.xy_gaps = xy_gaps  # pixels between each text as a tuple (x, y)
        self.texts = args
        self.rect = Rect(self.coords, (250, 60))

    def render_info_texts(self):  # for texts beside the board e.g time, gravity, lines cleared, piece speed
        coords = self.coords
        rendered_text_object = fonts[self.texts[0][1]].render(self.texts[0][0], True, main_text_color)
        screen.blit(rendered_text_object, coords)
        coords = (coords[0], coords[1] + rendered_text_object.get_height() + self.xy_gaps[1])
        last_text_height = 0
        for text in self.texts[1:]:
            try:
                rendered_text_object = fonts[text[1]].render(text[0], True, main_text_color)
            except IndexError:
                print(f"fonts[text[1]]: , text[0]: {text[0]}")
            if last_text_height != 0:
                coords = (coords[0], coords[1] + last_text_height - rendered_text_object.get_height())
            if tekoFontVisible and text[1] >= 1:  # if rendering the teko font
                coords = (coords[0], coords[1] - 3)
            screen.blit(rendered_text_object, coords)
            coords = (coords[0] + rendered_text_object.get_width() + self.xy_gaps[0], coords[1])
            last_text_height = rendered_text_object.get_height()

        # coords = self.coords
        # last_text_height = 0
        # for text in self.texts:
        #     rendered_text_object = fonts[text[1]].render(text[0], True, main_text_color)
        #     if text[2]:  # if newline
        #         coords = (coords[0], coords[1] + rendered_text_object.get_height() + self.xy_gaps[1])
        #         screen.blit(rendered_text_object, coords)
        #     else:
        #         coords = (coords[0] + rendered_text_object.get_width() + self.xy_gaps[0], coords[1])
        #         screen.blit(rendered_text_object, coords)
        #         if last_text_height != 0:
        #             coords = (coords[0], coords[1] + last_text_height - rendered_text_object.get_height() - 3)
        #     last_text_height = rendered_text_object.get_height()


def sigmoid(x):
    return 2.7**x/(1+2.7**x)


def scaled_sigmoid(x):
    return 200 * sigmoid((x-1500)/250)


def format_time(time, show_milliseconds=False):
    current_minutes = time // 60000
    current_seconds = time // 1000 % 60
    current_milliseconds = time % 1000
    formatted_time = str(current_minutes) + ":" + f"{current_seconds:02}"
    if show_milliseconds:
        formatted_time += "." + f"{current_milliseconds:03}"
    return formatted_time


def shift_board(board_, direction):
    global board_columns
    stack_height = 0
    leftmost_tile_index = board_columns - 1
    rightmost_tile_index = 0
    temp_board = copy.deepcopy(board_)
    for row in enumerate(temp_board):  # find height of bounding box
        if row[1].count("0") != board_columns:
            stack_height = 23 - row[0]
            break
    for row in temp_board:  # find leftmost tile for bounding box
        for tile in enumerate(row):
            if tile[1] != "0":
                if tile[0] < leftmost_tile_index:
                    leftmost_tile_index = tile[0]
                break
    for row in temp_board:  # find rightmost tile for bounding box
        for tile in enumerate(reversed(row)):
            if tile[1] != "0":
                if (board_columns - 1) - tile[0] > rightmost_tile_index:
                    rightmost_tile_index = (board_columns - 1) - tile[0]
                break
    print(rightmost_tile_index)
    if direction == "left":
        for row in temp_board:
            row.append(row[0])
            row.pop(0)
    elif direction == "right":
        for row in temp_board:
            row.insert(0, row[-1])
            row.pop(-1)
    elif direction == "up":
        temp_board.append(temp_board[0 - stack_height])
        temp_board.pop(-1 - stack_height)
    elif direction == "down":
        temp_board.insert(0 - stack_height, temp_board[-1])
        temp_board.pop()
    elif direction == "rightbound":
        for row in temp_board:
            row.insert(leftmost_tile_index, row[rightmost_tile_index])
            row.pop(rightmost_tile_index+1)
    elif direction == "leftbound":
        for row in temp_board:
            row.insert(rightmost_tile_index+1, row[leftmost_tile_index])
            row.pop(leftmost_tile_index)
    return temp_board


def show_text_25(text, color, x, y):
    global screen
    text_rendered = fonts[1].render(text, True, color)
    screen.blit(text_rendered, (x, y))


def draw_board():
    for row in enumerate(board):
        for tile in enumerate(row[1]):
            if tile[1] == "g":  # ghost block
                raise Exception("ghost tile appeared in main board")
            else:
                if row[0] <= 2:  # above board
                    if tile[1] != "0":
                        pygame.draw.rect(screen, char_to_light_color[tile[1]],
                                         Rect((boardLeftXValue + 1 + tile[0] * pixelsPerTile,
                                               boardTopYValue + 1 + row[0] * pixelsPerTile),
                                              (pixelsPerTile - 1, pixelsPerTile - 1)))
                        pygame.draw.rect(screen, char_to_dark_color[tile[1]],
                                         Rect((boardLeftXValue + 2 + tile[0] * pixelsPerTile,
                                               boardTopYValue + 2 + row[0] * pixelsPerTile),
                                              (pixelsPerTile - 2, pixelsPerTile - 2)))
                        pygame.draw.rect(screen, char_to_color[tile[1]],
                                         Rect((boardLeftXValue + 2 + tile[0] * pixelsPerTile,
                                               boardTopYValue + 2 + row[0] * pixelsPerTile),
                                              (pixelsPerTile - 3, pixelsPerTile - 3)))
                    else:
                        pygame.draw.rect(screen, background_color,
                                         Rect((boardLeftXValue + 1 + tile[0] * pixelsPerTile,
                                               boardTopYValue + 1 + row[0] * pixelsPerTile),
                                              (pixelsPerTile - 1, pixelsPerTile - 1)))
                else:  # in board
                    pygame.draw.rect(screen, char_to_light_color[tile[1]],
                                     Rect((boardLeftXValue + 1 + tile[0] * pixelsPerTile,
                                           boardTopYValue + 1 + row[0] * pixelsPerTile),
                                          (pixelsPerTile - 1, pixelsPerTile - 1)))
                    pygame.draw.rect(screen, char_to_dark_color[tile[1]],
                                     Rect((boardLeftXValue + 2 + tile[0] * pixelsPerTile,
                                           boardTopYValue + 2 + row[0] * pixelsPerTile),
                                          (pixelsPerTile - 2, pixelsPerTile - 2)))
                    pygame.draw.rect(screen, char_to_color[tile[1]],
                                     Rect((boardLeftXValue + 2 + tile[0] * pixelsPerTile,
                                           boardTopYValue + 2 + row[0] * pixelsPerTile),
                                          (pixelsPerTile - 3, pixelsPerTile - 3)))
    for row in enumerate(vfx_board):
        for tile in enumerate(row[1]):
            if tile[1] == "g" and board[row[0]][tile[0]] == "0":  # ghost block -
                # 2nd condition is so it doesn't overwrite physical blocks
                pygame.draw.rect(screen, ghost_block_color,
                                 Rect((boardLeftXValue + 3 + tile[0] * pixelsPerTile,
                                       boardTopYValue + 3 + row[0] * pixelsPerTile),
                                      (pixelsPerTile - 5, pixelsPerTile - 5)), 1)


def draw_ui_text(init=False, draw_hold_queue=False, draw_next_queue=False, print_lines_cleared=False,
                 print_gravity=False, print_time=False):
    if init:
        # draw lines between squares
        for j in range(board_columns + 1):  # draw vertical lines
            pygame.draw.line(screen, tile_border_color,
                             (boardLeftXValue + j * pixelsPerTile, boardTopYValue + pixelsPerTile * 3),
                             (boardLeftXValue + j * pixelsPerTile, boardTopYValue + boardHeight))
        for j in range(board_rows - 2):  # draw horizontal lines
            pygame.draw.line(screen, tile_border_color,
                             (boardLeftXValue, boardTopYValue + pixelsPerTile * 3 + j * pixelsPerTile),
                             (boardLeftXValue + boardWidth, boardTopYValue + pixelsPerTile * 3 + j * pixelsPerTile))
        show_text_25("controls in console/terminal", color_black, 560, 600)
        # show_text_25("made by warren", color_black, 335, 665)
        # next queue
        # next_queue_topleft_x = boardLeftXValue + boardWidth + 1
        # next_queue_topleft_y = boardTopYValue + pixelsPerTile*3
        # pygame.draw.rect(screen, ui_border_color, Rect(next_queue_topleft_x, next_queue_topleft_y, 152, 332), 1)
        # pygame.draw.line(screen, ui_border_color, (next_queue_topleft_x, next_queue_topleft_y + 22),
        #                  (next_queue_topleft_x + 151, next_queue_topleft_y + 22), 1)
        # pygame.draw.rect(screen, ui_dark_color, Rect(next_queue_topleft_x + 1, next_queue_topleft_y + 1, 150, 21))
        # if tekoFontVisible:
        #     show_text_25("next pieces", main_text_color, 575, 87)
        # else:
        #     show_text_25("next pieces", main_text_color, 572, 92)
        draw_box_with_title((boardLeftXValue + boardWidth + 1, boardTopYValue + pixelsPerTile*3 + 1, 151, 331, 21),
                            (background_color, ui_border_color, ui_dark_color),
                            ("next pieces", (575, 87), (572, 92)))
        draw_box_with_title((boardLeftXValue - 153, boardTopYValue + pixelsPerTile * 3 + 1, 152, 131, 21),
                            (background_color, ui_border_color, ui_dark_color),
                            ("held piece", (144, 87), (137, 92)))

    if draw_hold_queue:
        pygame.draw.rect(screen, background_color, Rect(boardLeftXValue - 152,
                                                        boardTopYValue + pixelsPerTile * 3 + 27, 150, 105))
        if held_piece != "":
            draw_tetromino(held_piece, 134, 190, 25)
    if draw_next_queue:
        pygame.draw.rect(screen, background_color, Rect(boardLeftXValue + boardWidth + 2,
                                                        boardTopYValue + pixelsPerTile*3 + 27, 150, 305))
        for j in enumerate(piece_queue[1:6]):
            draw_tetromino(j[1], 567, 170 + 60*j[0], 25)
    if print_lines_cleared:
        pygame.draw.rect(screen, background_color, lines_cleared_text.rect)
        lines_cleared_text.texts[1][0] = str(lines_cleared)
        lines_cleared_text.render_info_texts()
    if print_gravity:
        pygame.draw.rect(screen, background_color, gravity_text.rect)
        gravity_text.texts[1][0] = str(round(min(((lines_cleared / 10) + 1.5)*670/defaultGravityInterval, 17)))
        gravity_text.render_info_texts()
    if print_time:
        pygame.draw.rect(screen, background_color, time_text.rect)
        # when the game is not gameover, gameOverTime is the same as current time, but when gameover, it stops updating.
        time_text.texts[1][0] = format_time(gameOverTime)
        time_text.render_info_texts()


def draw_tetromino(piece_type, x, y, piece_size):
    piece_orientation_index = piece_to_orientation_index_dict[piece_type]
    for k in range(4):
        piece_x = x + piece_size * piece_orientation[piece_orientation_index][0][k][0]
        piece_y = y - piece_size * piece_orientation[piece_orientation_index][0][k][1]
        if piece_type not in "io":  # centers piece
            piece_x += piece_size//2
        if piece_type == "i":
            piece_y -= piece_size//2
        draw_tile(piece_type, piece_x, piece_y, piece_size)

    # this thing makes all the pieces show up as single tiles - i use this for peripheral vision training thing
    # piece_x = x + 35
    # piece_y = y - 35
    # draw_tile(piece_type, piece_x, piece_y, piece_size)


def draw_tile(piece_type, x, y, piece_size):  # for outside board e.g next and hold pieces
    global screen
    pygame.draw.rect(screen, char_to_light_color[piece_type], Rect(x, y, piece_size, piece_size))
    pygame.draw.rect(screen, char_to_dark_color[piece_type], Rect(x+1, y+1, piece_size-1, piece_size-1))
    pygame.draw.rect(screen, char_to_color[piece_type], Rect(x+1, y+1, piece_size-2, piece_size-2))


def place_tile(x, y, piece_type):  # function that places block on board by changing a value of the 2d list
    board[board_rows - y][x - 1] = piece_type


def place_vfx_tile(x, y, piece_type):
    vfx_board[board_rows - y][x - 1] = piece_type


def place_tetromino(piece_state, destroy_tetromino=False, vfx=False):
    global piece_to_orientation_index_dict_global
    if destroy_tetromino:
        piece_type = "0"
    else:
        piece_type = piece_state[2]
    if piece_state[2] == "g":
        piece_orientation_index = piece_to_orientation_index_dict[tetrominoState[2]]
    else:
        piece_orientation_index = piece_to_orientation_index_dict[piece_state[2]]
    if vfx:
        pass
        for j in range(4):
            place_vfx_tile(piece_state[0] + piece_orientation[piece_orientation_index][piece_state[3]][j][0],
                           piece_state[1] + piece_orientation[piece_orientation_index][piece_state[3]][j][1],
                           piece_type)
    else:
        for j in range(4):
            place_tile(piece_state[0] + piece_orientation[piece_orientation_index][piece_state[3]][j][0],
                       piece_state[1] + piece_orientation[piece_orientation_index][piece_state[3]][j][1], piece_type)


def move_is_valid(piece_state):  # only works if block to be moved is deleted beforehand
    valid = True
    global piece_to_orientation_index_dict_global
    piece_orientation_index = piece_to_orientation_index_dict[piece_state[2]]
    for j in range(4):
        test_tile_x_value = piece_state[0] + piece_orientation[piece_orientation_index][piece_state[3]][j][0]
        test_tile_y_value = piece_state[1] + piece_orientation[piece_orientation_index][piece_state[3]][j][1]
        if test_tile_x_value < 1 or test_tile_y_value > board_rows:
            valid = False
        try:
            if not board[board_rows - test_tile_y_value][test_tile_x_value - 1] == "0":
                valid = False
        except IndexError:
            valid = False
    return valid


def soft_drop():
    global tetrominoState, softDropTime
    if softDropInterval == -1:
        temp_tetromino_state = tetrominoState.copy()
        tetrominoState = hard_drop(tetrominoState, False)
        place_tetromino(temp_tetromino_state, True)  # hacky fix
        place_tetromino(tetrominoState)
    else:
        move_and_check(tetrominoState, y_change=-1)
    softDropTime = pygame.time.get_ticks()


def move_and_check(piece_state, x_change=0, y_change=0):
    global tetrominoState
    place_tetromino(piece_state, True)
    new_state = change_piece_state(piece_state, x_change, y_change)
    if move_is_valid(new_state):
        place_tetromino(new_state)
        tetrominoState = new_state
        return True  # returns whether movement was successful or not (in most cases should use move_is_valid()
    else:
        place_tetromino(piece_state)
        return False


def hard_drop(piece_state, place_block=True):
    hit_floor = False
    dropping_piece = piece_state.copy()
    place_tetromino(dropping_piece, True)
    while not hit_floor:
        can_move_down_more = move_is_valid(change_piece_state(dropping_piece, y_change=-1))
        if can_move_down_more:
            dropping_piece = change_piece_state(dropping_piece, y_change=-1)
        else:
            hit_floor = True
    if place_block:
        place_tetromino(dropping_piece)
        return new_tetromino()
    else:
        place_tetromino(piece_state)
        return dropping_piece


def move_das(piece_state, x_change, place_block=True):
    hit_edge = False
    moving_piece = piece_state.copy()
    place_tetromino(moving_piece, True)
    debug_temp_loop_counter = 0
    while not hit_edge:
        can_move_more = move_is_valid(change_piece_state(moving_piece, x_change=x_change))
        if can_move_more:
            moving_piece = change_piece_state(moving_piece, x_change=x_change)
        else:
            hit_edge = True
        debug_temp_loop_counter += 1
        if debug_temp_loop_counter > 30:
            print(hit_edge)
            raise Exception("DAS loop turned into infinite loop")
    place_tetromino(moving_piece)
    if place_block:
        return new_tetromino()
    else:
        return moving_piece


def hold_piece(piece_state):
    global held_piece, piece_queue
    if held_piece != "":
        piece_queue.insert(1, held_piece)  # because random_piece() removes first element every time it is called,
        # it is placed at the 2nd index so that the current block is removed from the piece queue
    held_piece = piece_state[2]
    return new_tetromino()


def new_tetromino():
    global timeOfLastPiecePlacement, timeOnGround, lockDelayCancels, hold_key_pressed, gravityInterval, \
        lines_cleared, totalLockDelayCancelTime, gameOverTime
    totalLockDelayCancelTime = 0
    hold_key_pressed = False
    lockDelayCancels = 0
    timeOfLastPiecePlacement = current_time_ms
    timeOnGround = current_time_ms
    line_clear_effect("empty", 80, 400)  # resets clear effect every move
    line_clear_effect("empty", 80, 500)
    lines_cleared_this_move = 0
    for row in enumerate(board):  # check if row is cleared
        if row[1].count("0") == 0:
            board.pop(row[0])
            board.insert(0, ["0"]*10)
            lines_cleared += 1
            gravityInterval = defaultGravityInterval * 1.5 / ((lines_cleared / 10) + 1.5)
            draw_ui_text(print_lines_cleared=True, print_gravity=True)
            lines_cleared_this_move += 1
    # check for all clear
    empty_rows = 0
    for row in board:
        if row.count("0") == board_columns:
            empty_rows += 1
    if empty_rows == board_rows and lines_cleared != 0:
        line_clear_effect("all clear!", 80, 400)

    if lines_cleared_this_move != 0:
        line_clear_effect(f"cleared {lines_cleared_this_move} lines!", 80, 500)
    if not move_is_valid([4, board_rows - 2, get_next_piece(), 0]):
        game_state.state = "game_over"
        gameOverTime = current_time_ms
    draw_board()
    return [4, board_rows - 2, get_next_piece(False), 0]


def line_clear_effect(text, x, y, width=130):
    pygame.draw.rect(screen, background_color, Rect(x, y, width, 100))
    if text != "empty":
        show_text_25(text, main_text_color, x, y)


def rotate_piece(piece_state, rotation):  
    place_tetromino(tetrominoState, True) 
    if piece_state[2] == "i":
        kick_table = kick_table_I
    else:
        kick_table = kick_table_normal
    kick_attempt_num = 0  # different kicks are listed 
    rotated_piece_state = change_piece_state(piece_state, orientation_change=rotation)
    successful_placement = False
    while not successful_placement:
        x_offset = kick_table[(rotation % 4) - 1][piece_state[3]][kick_attempt_num][0]
        y_offset = kick_table[(rotation % 4) - 1][piece_state[3]][kick_attempt_num][1]
        rotated_piece_state = change_piece_state(piece_state, x_offset, y_offset, orientation_change=rotation)
        if move_is_valid(rotated_piece_state):
            successful_placement = True
        else:
            kick_attempt_num += 1
            if len(kick_table[(rotation % 4) - 1][piece_state[3]]) == kick_attempt_num:
                return piece_state
    return rotated_piece_state


def get_next_piece(remove_first_item=True):
    global piece_queue, seven_bag
    if len(piece_queue) < 7:
        random.shuffle(seven_bag)
        piece_queue.extend(seven_bag)
    if remove_first_item:
        piece_queue.pop(0)
    return piece_queue[0]


def create_ghost_piece(piece_state):
    ghost_piece_state = piece_state.copy()
    ghost_piece_state = hard_drop(ghost_piece_state, False)
    ghost_piece_state[2] = "g"
    return ghost_piece_state


def render_ghost_piece():
    for row_g in enumerate(vfx_board):
        for tile_g in enumerate(row_g[1]):
            if tile_g[1] == "g":
                vfx_board[row_g[0]][tile_g[0]] = "0"

    ghost_piece_state = create_ghost_piece(tetrominoState)
    place_tetromino(ghost_piece_state, vfx=True)


def change_piece_state(piece_state, x_change=0, y_change=0, new_piece_type="none", orientation_change=0):
    if new_piece_type == "none":
        piece_type = piece_state[2]
    else:
        piece_type = new_piece_type
    return [piece_state[0] + x_change, piece_state[1] + y_change, piece_type, (piece_state[3] + orientation_change) % 4]


# debug function
def print_board():
    for row in board:
        print(row)


def draw_box_with_title(coords, colors, text):
    # coords is (leftx, topy, width, height, headerheight)
    # colors are (bgcolor, bordercolor, header_color)
    # text coords are (text (x, y with teko), (x, y without))
    pygame.draw.rect(screen, colors[0], Rect(coords[0] + 1, coords[1] + 1, coords[2], coords[3]))
    pygame.draw.rect(screen, colors[1], Rect(coords[0], coords[1], coords[2]+1, coords[3]+1), 1)
    pygame.draw.line(screen, colors[1], (coords[0], coords[1] + coords[4]+1),
                     (coords[0] + coords[2], coords[1] + coords[4]+1), 1)
    pygame.draw.rect(screen, colors[2], Rect(coords[0] + 1, coords[1] + 1, coords[2]-1, coords[4]))
    if tekoFontVisible:
        show_text_25(text[0], main_text_color, text[1][0], text[1][1])
    else:
        show_text_25(text[0], main_text_color, text[2][0], text[2][1])


def initiate_board(repeat_queue=False):
    global seven_bag, piece_queue, held_piece, held_piece_box_drawn, gravityInterval, lines_cleared, board, vfx_board,\
        defaultTetrominoState, tetrominoState, hold_key_pressed, current_piece_queue
    # seven_bag = ['i', 'o', 't', 's', 'z', 'j', 'l']
    # random.shuffle(seven_bag)
    piece_queue = ["i"]
    # piece_queue.extend(customBag)
    # piece_queue.extend(seven_bag.copy())
    if not repeat_queue:
        if useVeryCustomBag:
            piece_queue.extend(create_very_custom_queue())
        else:
            seven_bag = ['i', 'o', 't', 's', 'z', 'j', 'l']

            piece_queue = ["i"]
            if shuffleCustomBag:
                random.shuffle(customBag)
            piece_queue.extend(customBag)
            try:
                if randomlyMirrorBag and random.randint(1, 2) == 1:
                    for i in range(len(piece_queue)):
                        piece_queue[i] = pieceMirrors[piece_queue[i]]
            except KeyError:
                print("Piece in queue must be one of \"i\", \"j\", \"l\", \"o\", \"t\", \"s\", or \"z\".")
                raise KeyError("Piece in queue must be one of \"i\", \"j\", \"l\", \"o\", \"t\", \"s\", or \"z\".")
            for i in range(2):
                random.shuffle(seven_bag)
                piece_queue.extend(seven_bag.copy())
        # for j in range(7 - piecesToStartWith):
        #     piece_queue.pop(0)
        current_piece_queue = copy.deepcopy(piece_queue)
    else:
        print(f"piece queue: {piece_queue}")
        print(f"saved piece queue: {current_piece_queue}")
        piece_queue = copy.deepcopy(current_piece_queue)
        print("queue copied")
    held_piece = ""
    hold_key_pressed = False
    gravityInterval = defaultGravityInterval
    lines_cleared = 0
    draw_ui_text(print_lines_cleared=True, print_gravity=True, print_time=True)
    board = copy.deepcopy(get_preset_list(presetMap, board_rows))
    vfx_board = [["0"] * board_columns for j in range(board_rows)]  # for ghost block and other effects
    tetrominoState = [4, board_rows - 2, get_next_piece(), 0]
    # stores piece state in form [x, y, piece type, orientation]
    queue_to_paste_in_pcfinder = ""
    for piece in piece_queue[:9]:
        queue_to_paste_in_pcfinder += piece
    # print(queue_to_paste_in_pcfinder)
    r = tkinter.Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(queue_to_paste_in_pcfinder)
    r.update()
    if putPieceInHold:
        tetrominoState = hold_piece(tetrominoState)


def initiate_board_graphics():
    screen.fill(background_color)
    draw_board()
    draw_ui_text(init=True, print_lines_cleared=True, print_gravity=True, print_time=True)
    settingsButton.surface.blit(settingsButton.image, (settingsButton.rect.x, settingsButton.rect.y))


seven_bag = ['i', 'o', 't', 's', 'z', 'j', 'l']
random.shuffle(seven_bag)
piece_queue = ["i"]
piece_queue.extend(seven_bag.copy())
for i in range(7 - piecesToStartWith):
    piece_queue.pop(0)
held_piece = ""
held_piece_box_drawn = False
gravityInterval = defaultGravityInterval
current_piece_queue = copy.deepcopy(piece_queue)

lines_cleared = 0
board_columns = 10
board_rows = 23
board = [["0"] * board_columns for i in range(board_rows)]  # create board as 2d list
vfx_board = [["0"] * board_columns for j in range(board_rows)]  # for ghost block and other effects
defaultTetrominoState = [4, board_rows - 2, get_next_piece(), 0]
tetrominoState = defaultTetrominoState  # stores piece state in form [x, y, piece type, orientation]
game_state = GameState()

windowWidth = 800
windowHeight = 692
screen = pygame.display.set_mode((windowWidth, windowHeight))  # window is 800*692px
# screen.fill(color_light_grey)  # make window white
pygame.display.set_caption("Tetris")  # Title of window

FPS = pygame.time.Clock()

# draw board background
boardLeftXValue = 260
boardTopYValue = 5
boardWidth = 280
boardHeight = 644
boardRect = Rect(boardLeftXValue, boardTopYValue, boardWidth, boardHeight)
pixelsPerTile = boardWidth/board_columns

# draw board squares
if tekoFontVisible:
    lines_cleared_text = UIText((555, 510), (0, -10), ["lines cleared:", 1, True], [str(lines_cleared), 2, False])
    gravity_text = UIText((555, 430), (5, -5), ["gravity:", 1, True], [str((lines_cleared / 10) + 1.5), 2, False],
                          ["tiles/second", 1, False])
    time_text = UIText((555, 580), (0, -10), ["time:", 1, True], ["0:00", 2, False])
    game_over_text = UIText((353, 340), (0, -17), ["Game Over!", 3, True],
                            [f"You cleared {lines_cleared} lines in 0:00", 2, False])
else:
    lines_cleared_text = UIText((555, 510), (0, 0), ["lines cleared:", 1, True], [str(lines_cleared), 2, False])
    gravity_text = UIText((555, 430), (5, 0), ["gravity:", 1, True], [str((lines_cleared / 10) + 1.5), 2, False],
                          ["tiles/second", 1, False])
    time_text = UIText((555, 580), (0, 0), ["time:", 1, True], ["0:00", 2, False])
    game_over_text = UIText((353, 340), (0, 0), ["Game Over!", 3, True],
                            [f"You cleared {lines_cleared} lines in 0:00", 2, False])

settingsIcon = pygame.image.load("assets/settingsButton.png")
settingsButtonSize = 30
settingsIcon = pygame.transform.scale(settingsIcon, (settingsButtonSize, settingsButtonSize))
settingsButton = Button(screen, 20, windowHeight - (20+settingsButtonSize), settingsIcon)

place_tetromino(tetrominoState)
render_ghost_piece()

initiate_board_graphics()
gameStartTime = pygame.time.get_ticks()

# print controls
print("←: move left \n →: move right \n ↓: soft drop (move down) \n space: hard drop (instantly drop and place)"
      "\n D: rotate 90° clockwise ↻ \n A: rotate 90° anticlockwise ↺ \n S: rotate 180° \n \\ or shift: hold piece \n"
      "controls can be changed in settings.py")
print("please report bugs to me")

# Game loop #
try:
    while True:
        game_state.manage_game_state()
        FPS.tick(setFPS)  # limit game loop to previously set FPS value
except Exception as e:
    logging.exception(str(e))
input("press enter to end")
# todo:  make game over screen better
#   make time stop on settings screen
#   add score/attack/clear effects, add t spin checks
#   restart board, show controls, fix up text, redo hold and next queue,
#   fix lock delay cancel when piece put in air (idea: have second lock delay where it locks regardless)
#   make the board an object
# done list (for motivation): 7-bag randomisation, kick table, hold queue, next queue, lines cleared count,
# spawn blocks at row 22/23, add 180 kick values, fail when topped out, gravity (req timer), limit hold,
# fix repeating inputs (req timer), add lock delay (with limit) make gravity levelling, timer,
# fix ghost block flickering, add new piece DAS delay setting, redo movement code
# count cleared lines
# long term todo: make gravity based on levels, not lines; make 40 lines timer, save scores to file, make puzzle e.g
#               downstack puzzles, make builtin scenario practice which saves times, e.g for openers
#               make softdrop code less hacky, maybe put placing block in vfx board instead of main board


# todo list 2: electric boogaloo:
# make SRS for solves
# make a modified queue randomizer so that all minimals of a setup are practiced an equal amount of times (solves the problem of less common minimals not being practiced enough)
#       do this with sfinder cover output csv file
# tetris bot/??
#
#
