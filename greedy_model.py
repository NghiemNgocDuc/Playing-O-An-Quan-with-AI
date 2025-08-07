# 🐚 Ô Ăn Quan – Traditional Vietnamese Board Game

board = [["quan"], ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5,
         ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["dan"] * 5, ["quan"]]

score_A = {"dan": 0, "quan": 0}
score_B = {"dan": 0, "quan": 0}

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
    print("\n Game Board Layout:\n")
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
        print(" Mất lượt – không có quân để bắt.")

    return captured_dan, captured_quan


def get_player_move(board, is_player_A):
    while True:
        try:
            pos = int(input(f"{'Player A' if is_player_A else ' Player B'} – Choose a position (1–5 / 6–10): "))
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

def get_ai_move(board, is_player_A):
    import copy
    best_score = -1
    best_move = None

    valid_positions = [i for i in range(6, 11) if board[i]]
    directions = [1, -1]  # Clockwise and Counterclockwise

    for pos in valid_positions:
        for step in directions:
            test_board = copy.deepcopy(board)
            temp_score_B = {"dan": 0, "quan": 0}
            captured_dan, captured_quan = capture(test_board, pos, False, step)
            temp_score_B["dan"] += captured_dan
            temp_score_B["quan"] += captured_quan
            score = calculate_score(temp_score_B["dan"], temp_score_B["quan"])
            if score > best_score:
                best_score = score
                best_move = (pos, step)

    return best_move or (valid_positions[0], 1)

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
        print("\nGAME OVER — Final Results:")
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

# Main Game Loop
while not game_over(board, score_A, score_B):
    restore_player_side(board, score_A, is_player_A=True)
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


    ai_move = get_ai_move(board, False)
    if ai_move is None:
        print("AI has no valid moves!")
        game_over(board, score_A, score_B)
        break
    ai_pos, ai_step = ai_move
    print(f"AI chooses position {ai_pos} ({'Clockwise' if ai_step == 1 else 'Counterclockwise'})")
    captured_dan, captured_quan = capture(board, ai_pos, False, ai_step)
    score_B["dan"] += captured_dan
    score_B["quan"] += captured_quan
