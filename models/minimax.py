import copy

# 🐚 Game Setup
def initialize_board():
    return [["quan"], ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5,
            ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["quan"]]

def calculate_score(dan, quan):
    return dan + quan * 5

def is_valid_move(pos, is_player_A):
    return bool(board[pos]) and (
        (is_player_A and 1 <= pos <= 5) or
        (not is_player_A and 6 <= pos <= 10)
    )

def get_next_position(current_pos, step):
    movement_order = [0, 1, 2, 3, 4, 5, 11, 6, 7, 8, 9, 10]
    current_index = movement_order.index(current_pos)
    next_index = (current_index + (1 if step > 0 else -1)) % len(movement_order)
    return movement_order[next_index]

def move(board, pos, step):
    seeds_to_sow = board[pos][:]
    board[pos] = []
    current_pos = pos
    while seeds_to_sow:
        current_pos = get_next_position(current_pos, step)
        board[current_pos].append(seeds_to_sow.pop(0))
    return current_pos

def relay_move(board, start_pos, step):
    current_pos = start_pos
    while True:
        last_pos = move(board, current_pos, step)
        next_pos = get_next_position(last_pos, step)
        if board[next_pos] and next_pos not in [0, 11]:
            current_pos = next_pos
            continue
        return last_pos

def capture(board, start_pos, is_player_A, step):
    captured_dan = 0
    captured_quan = 0

    last_pos = relay_move(board, start_pos, step)
    next_pos = get_next_position(last_pos, step)
    after_next = get_next_position(next_pos, step)

    if not board[next_pos] and board[after_next]:
        captured = board[after_next]
        board[after_next] = []
        captured_dan = captured.count("dan")
        captured_quan = captured.count("quan")

    return captured_dan, captured_quan

def restore_player_side(board, score, is_player_A):
    side_range = range(1, 6) if is_player_A else range(6, 11)
    if all(not board[i] for i in side_range):
        if score["dan"] >= 5:
            score["dan"] -= 5
        else:
            score["dan"] = 0
        for i in side_range:
            board[i].append("dan")

def is_game_over(board, score_A, score_B):
    quan_empty = score_A["quan"] + score_B["quan"] == 2
    dan_empty = all(not board[i] for i in range(1, 11))
    return quan_empty or dan_empty

def minimax(board, score_A, score_B, depth, is_maximizing):
    if depth == 0 or is_game_over(board, score_A, score_B):
        return calculate_score(score_B["dan"], score_B["quan"]) - calculate_score(score_A["dan"], score_A["quan"])

    best_value = float('-inf') if is_maximizing else float('inf')
    best_move = None

    valid_positions = range(6, 11) if is_maximizing else range(1, 6)
    directions = [1, -1]

    for pos in valid_positions:
        if not board[pos]:
            continue
        for step in directions:
            new_board = copy.deepcopy(board)
            new_score_A = score_A.copy()
            new_score_B = score_B.copy()

            captured_dan, captured_quan = capture(new_board, pos, is_maximizing, step)
            if is_maximizing:
                new_score_B["dan"] += captured_dan
                new_score_B["quan"] += captured_quan
            else:
                new_score_A["dan"] += captured_dan
                new_score_A["quan"] += captured_quan

            value = minimax(new_board, new_score_A, new_score_B, depth - 1, not is_maximizing)

            if is_maximizing and value > best_value:
                best_value = value
                best_move = (pos, step)
            elif not is_maximizing and value < best_value:
                best_value = value
                best_move = (pos, step)

    return best_value

def get_ai_move(board, is_player_A):
    best_score = float('-inf')
    best_move = None

    valid_positions = range(6, 11)
    directions = [1, -1]

    for pos in valid_positions:
        if not board[pos]:
            continue
        for step in directions:
            test_board = copy.deepcopy(board)
            temp_score_A = {"dan": 0, "quan": 0}
            temp_score_B = {"dan": 0, "quan": 0}

            captured_dan, captured_quan = capture(test_board, pos, False, step)
            temp_score_B["dan"] += captured_dan
            temp_score_B["quan"] += captured_quan

            score = minimax(test_board, temp_score_A, temp_score_B, depth=4, is_maximizing=False)

            if score > best_score:
                best_score = score
                best_move = (pos, step)

    return best_move
