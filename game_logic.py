# game_logic.py

def initialize_board():
    return [
        ["quan"],  # 0
        ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5,  # 1–5
        ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5,  # 6–10
        ["quan"]   # 11
    ]

def calculate_score(dan, quan):
    return dan + quan * 5

def is_valid_move(board, pos, is_player_A):
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
        score["dan"] -= 5  # Always subtract 5, even if it goes negative
        for i in side_range:
            board[i].append("dan")


def game_over(board, score_A, score_B):
    # Game ends if all quan are captured
    quan_empty = score_A["quan"] + score_B["quan"] == 2

    # Or if all dan squares are empty
    dan_empty = all(not board[i] for i in range(1, 11))

    if quan_empty or dan_empty:
        # Add remaining dan to scores
        score_A["dan"] += sum(square.count("dan") for square in board[1:6])
        score_B["dan"] += sum(square.count("dan") for square in board[6:11])
        for i in range(1, 11):
            board[i] = []
        return True

    return False


def get_board_state(board):
    # Returns a simplified version of the board for frontend or testing
    return [[seed for seed in square] for square in board]

def get_scores(score_A, score_B):
    return {
        "score_A": {
            "dan": score_A["dan"],
            "quan": score_A["quan"],
            "total": calculate_score(score_A["dan"], score_A["quan"])
        },
        "score_B": {
            "dan": score_B["dan"],
            "quan": score_B["quan"],
            "total": calculate_score(score_B["dan"], score_B["quan"])
        }
    }
def check_game_end(board, score_A, score_B):
    # Check if all player squares [1] to [10] are empty
    if all(len(board[i]) == 0 for i in range(1, 11)):
        total_A = score_A["dan"] + score_A["quan"] * 5
        total_B = score_B["dan"] + score_B["quan"] * 5

        if total_A > total_B:
            winner = "Player A wins!"
        elif total_B > total_A:
            winner = "Player B wins!"
        else:
            winner = "It's a tie!"

        return {
            "game_over": True,
            "winner": winner,
            "total_A": total_A,
            "total_B": total_B
        }

    return { "game_over": False }

