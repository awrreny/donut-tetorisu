def pc_num_to_extra_pieces(pc_num):
    if pc_num % 2 == 0:
        pc_num += 7
    return pc_num // 2


def extra_pieces_to_pc_num(extra_pieces, placed_pieces=0):
    extra_pieces += placed_pieces
    extra_pieces %= 7
    pc_num = extra_pieces*2 + 1
    if pc_num != 7:
        pc_num %= 7
    return pc_num
