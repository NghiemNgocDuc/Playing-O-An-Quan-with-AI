


Q_table = {}  # Format: {(state_repr, action): value}

TRAINING_MODE = False  # Set to False when you want to play manually






import json
try:
    with open("q_table.json", "r") as f:
        Q_table = json.load(f)
except:
    Q_table = {}



board = [["quan"], ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5,
         ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["quan"]]

score_A = {"dan": 0, "quan": 0}
score_B = {"dan": 0, "quan": 0}


def board_to_state(board):
    return tuple(tuple(square) for square in board)  # Immutable representation


def calculate_score(dan, quan):
    return dan + quan * 5

def print_board(board):
    seed_repr = {"dan": "🔸", "quan": "🌕"}
    def format_square(i):
        contents = "".join(seed_repr.get(s, "?") for s in board[i])
        return f"[{i}:{contents}]"
    top = "  ".join(format_square(i) for i in range(6, 11))
    bottom = "  ".join(format_square(i) for i in reversed(range(1, 6)))
    center = f"{format_square(11):^34}{format_square(0):>10}"
    print("\nGame Board Layout:\n")
    print("    " + top)
    print(center)
    print("    " + bottom)
    print()

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

    # Trường hợp bắt quân: ô kế tiếp trống, ô sau nữa có quân
    if not board[next_pos] and board[after_next]:
        if (is_player_A) or (not is_player_A):
            captured = board[after_next]
            board[after_next] = []
            captured_dan = captured.count("dan")
            captured_quan = captured.count("quan")
        # Bắt xong không tiếp tục kiểm tra tiếp phía sau

    # Trường hợp mất lượt: ô kế tiếp trống, ô sau nữa KHÔNG có quân
    elif not board[next_pos] and not board[after_next]:
        print("Mất lượt – không có quân để bắt.")

    return captured_dan, captured_quan


def get_player_move(board, is_player_A):
    while True:
        try:
            pos = int(input(f"{'Player A' if is_player_A else 'Player B'} – Choose a position (1–5 / 6–10): "))
            if not is_valid_move(pos, is_player_A):
                print("Invalid move. Try again.")
                continue
            direction = input("Direction (C for Clockwise / CC for Counterclockwise): ").strip().lower()
            if direction not in ["c", "cc"]:
                print("Invalid direction. Enter C or CC.")
                continue
            step = 1 if direction == "c" else -1
            return pos, step
        except ValueError:
            print("Please enter valid numbers and direction!")

def get_ai_move(board, score_B, episolon=0.1):
    import random
    state = board_to_state(board)
    valid_moves = [(pos, step) for pos in range(6, 11) if board[pos] for step in [-1, 1]]

    if not valid_moves:
        return None  # No moves available

    if random.random() < episolon:
        return random.choice(valid_moves)

    q_values = [Q_table.get((str(state), str(move)), 0) for move in valid_moves]
    return valid_moves[q_values.index(max(q_values))]


def ai_turn(board, score, is_player_A):
    prev_state = board_to_state(board)
    ai_move = get_ai_move(board, score)

    if ai_move is None:
        return False
    pos, step = ai_move
    captured_dan, captured_quan = capture(board, pos, is_player_A, step)
    score["dan"] += captured_dan
    score["quan"] += captured_quan

    reward = calculate_score(captured_dan, captured_quan)
    next_state = board_to_state(board)

    update_q_table(prev_state, ai_move, reward, next_state)


    return True




def restore_player_side(board, score, is_player_A):
    side_range = range(1, 6) if is_player_A else range(6, 11)
    if all(not board[i] for i in side_range):
        print("Re-seeding player", "A" if is_player_A else "B")
        if score["dan"] >= 5:
            score["dan"] -= 5
        else:
            print("Not enough Dân! Borrowing from opponent.")
            # Optional: implement borrowing logic here
            score["dan"] = 0
        for i in side_range:
            board[i].append("dan")


def update_q_table(prev_state, action, reward, next_state, alpha =0.1, gamma = 0.9):
    prev_key = (str(prev_state), str(action))
    next_qs = [Q_table.get((str(next_state), str(a)), 0) for a in [(pos, s) for pos in range(6, 11) for s in [1, -1]]]
    max_future = max(next_qs) if next_qs else 0
    old_value = Q_table.get(prev_key, 0)
    new_value = old_value + alpha * (reward + gamma * max_future - old_value)
    Q_table[prev_key] = new_value


def game_over(board, score_A, score_B):
    quan_empty = score_A["quan"] + score_B["quan"] == 2
    dan_empty = all(not board[i] for i in range(1, 11))
    if quan_empty or dan_empty:
        score_A["dan"] += sum(square.count("dan") for square in board[1:6])
        score_B["dan"] += sum(square.count("dan") for square in board[6:11])
        for i in range(1, 11):
            board[i] = []
        total_A = calculate_score(score_A["dan"], score_A["quan"])
        total_B = calculate_score(score_B["dan"], score_B["quan"])
        print("\n GAME OVER — Final Results:")
        print(f"Player A: {score_A['dan']} Dân, {score_A['quan']} Quan → Total: {total_A}")
        print(f"Player B: {score_B['dan']} Dân, {score_B['quan']} Quan → Total: {total_B}")
        if total_A > total_B:
            print("Player A wins!")
        elif total_B > total_A:
            print("Player B wins!")
        else:
            print("It’s a tie!")
        return True
    return False

# Main Game Loop( For AI vs AI)
# while not game_over(board, score_A, score_B):
#
#     if TRAINING_MODE:
#         for _ in range(10000):  # Train for 1000 games
#             board = [["quan"], ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5,
#                      ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["quan"]]
#             score_A = {"dan": 0, "quan": 0}
#             score_B = {"dan": 0, "quan": 0}
#
#             while not game_over(board, score_A, score_B):
#                 restore_player_side(board, score_A, is_player_A=True)
#                 restore_player_side(board, score_B, is_player_A=False)
#                 ai_turn(board, score_A, is_player_A=True)
#                 if game_over(board, score_A, score_B):
#                     break
#                 ai_turn(board, score_B, is_player_A=False)
#     else:
#
#
#         restore_player_side(board, score_A, is_player_A=True)
#         restore_player_side(board, score_B, is_player_A=False)
#
#         if TRAINING_MODE:
#             ai_turn(board, score_A, is_player_A=True)
#             if game_over(board, score_A, score_B):
#                 break
#             ai_turn(board, score_B, is_player_A=False)
#         else:
#             print_board(board)
#             print("--- Your turn ---")
#             pos, step = get_player_move(board, True)
#             captured_dan, captured_quan = capture(board, pos, True, step)
#             score_A["dan"] += captured_dan
#             score_A["quan"] += captured_quan
#
#             if game_over(board, score_A, score_B):
#                 break
#
#             restore_player_side(board, score_B, is_player_A=False)
#             print_board(board)
#             print("--- AI's turn ---")
#             ai_turn(board, score_B, is_player_A=False)
# Turn on when human vs AI
while not game_over(board, score_A, score_B):
    restore_player_side(board, score_A, is_player_A=True)
    restore_player_side(board, score_B, is_player_A=False)

    print_board(board)
    print("--- Your turn ---")
    pos, step = get_player_move(board, True)
    captured_dan, captured_quan = capture(board, pos, True, step)
    score_A["dan"] += captured_dan
    score_A["quan"] += captured_quan

    if game_over(board, score_A, score_B):
        break

    restore_player_side(board, score_B, is_player_A=False)
    print_board(board)
    print("--- AI's turn ---")
    ai_turn(board, score_B, is_player_A=False)

with open("q_table.json", "w") as f:
    json.dump({str(k): v for k, v in Q_table.items()}, f)

