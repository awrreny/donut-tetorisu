from pygame.locals import *
import copy
#  this file stores the donut transformations, and you can also create your own
#  the board is stored as a 2d list - a list of rows, for example
# [
#     ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
#     ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
#     ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
#     ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
#     ['0', '0', '0', '0', 'l', 'l', 'l', 'j', 'j', 'j'],
#     ['0', '0', '0', '0', 'l', 'z', 'o', 'o', 's', 'j'],
#     ['0', '0', '0', '0', 'z', 'z', 'o', 'o', 's', 's'],
#     ['0', '0', '0', '0', 'z', 'i', 'i', 'i', 'i', 's']
# ]
# in this format, the 2d list looks like the tetris board (this is grace system)
# add a transformation by adding it to the function below (i will edit later with explanation)


def shift_board(board, transformation_key, board_columns=10):
    stack_height = 0
    leftmost_tile_index = board_columns - 1
    rightmost_tile_index = 0
    for row in enumerate(board):  # find height of bounding box
        if row[1].count("0") != board_columns:
            stack_height = 23 - row[0]
            break
    for row in board:  # find leftmost tile for bounding box
        for tile in enumerate(row):
            if tile[1] != "0":
                if tile[0] < leftmost_tile_index:
                    leftmost_tile_index = tile[0]
                break
    for row in board:  # find rightmost tile for bounding box
        for tile in enumerate(reversed(row)):
            if tile[1] != "0":
                if (board_columns - 1) - tile[0] > rightmost_tile_index:
                    rightmost_tile_index = (board_columns - 1) - tile[0]
                break
    key_to_transformation_dict = {
        K_u: "left",
        K_o: "right",
        K_k: "down",
        K_i: "up",  # transform_up(board, stack_height),
        K_j: "leftbound",
        K_l: "rightbound",
    }
    transformation = key_to_transformation_dict.get(transformation_key)
    if transformation == "left":
        for row in board:
            row.append(row[0])  # copies the leftmost column and puts it at the end
            row.pop(0)  # deletes the leftmost column
    elif transformation == "right":
        for row in board:
            row.insert(0, row[-1])
            row.pop(-1)
    elif transformation == "up":
        board.append(board[0 - stack_height])
        board.pop(-1 - stack_height)
    elif transformation == "down":
        board.insert(0 - stack_height, board[-1])
        board.pop()
    elif transformation == "leftbound":
        for row in board:
            row.insert(rightmost_tile_index + 1, row[leftmost_tile_index])
            row.pop(leftmost_tile_index)
    elif transformation == "rightbound":
        for row in board:
            row.insert(leftmost_tile_index, row[rightmost_tile_index])
            row.pop(rightmost_tile_index + 1)
    return board

# unfinished! but i need to sleep
