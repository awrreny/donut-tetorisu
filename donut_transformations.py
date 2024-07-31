import pygame.locals as pgl
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

key_to_transformation_dict = {
        pgl.K_u: "left",
        pgl.K_o: "right",
        pgl.K_k: "down",
        pgl.K_i: "up",  # transform_up(board, stack_height),
        pgl.K_j: "leftbound",
        pgl.K_l: "rightbound",
    }



def shift_board(board, transformation_key):
    leftmost_tile_index = len(board[0]) - 1
    rightmost_tile_index = 0

    # currently calculates bounding box every transformation. Maybe would be better to store it and update when it changes?
    # bounding box usually does change every transformation so this seems fine

    # find height of bounding box
    # assumes there are no empty rows with non-empty rows above it, which is true in standard gameplay and with these 6 transformations
    # if performance for larger boards becomes an issue then binary search can be implemented
    stack_height = 0
    for row in reversed(board):
        if all([tile == '0' for tile in row]): break
        stack_height += 1

    # find leftmost tile for bounding box
    for row in board:  
        for colNum, tile in enumerate(row):
            if tile != "0":
                leftmost_tile_index = min(leftmost_tile_index, colNum)
                break

    # find rightmost tile for bounding box
    for row in board:  
        for colNum, tile in reversed(list(enumerate(row))):
            if tile != "0":
                rightmost_tile_index = max(rightmost_tile_index, colNum)
                break
    
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

    else:
        raise KeyError(f"invalid key for donut transformation. expected one of {', '.join(map(str,key_to_transformation_dict.keys()))} but found {transformation_key}")

    return board


