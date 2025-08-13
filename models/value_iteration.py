# // Initialization
# for s in all_states:
#     V[s] ← 0
#
# // Value Iteration Loop
# repeat:
#     Δ ← 0
#     for s in all_states:
#         if s is terminal: continue
#         v_old ← V[s]
#         V[s] ← max_{a ∈ A(s)} [ R(s,a) + γ * V[next_state(s,a)] ]
#         Δ ← max(Δ, |v_old - V[s]|)
# until Δ < θ
#
# // Policy Extraction
# for s in all_states:
#     if s is terminal:
#         π[s] ← None
#     else:
#         π[s] ← argmax_{a ∈ A(s)} [ R(s,a) + γ * V[next_state(s,a)] ]
#
# return π







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

import json
import copy
from game_logic import capture, game_over, restore_player_side, initialize_board

gamma = 1.0 # gamma as close to 0 mean to it care less about the future
theta = 1e-4 # threshold to know when to stop gradient descent

def state_to_key(board, is_player_A):
    key = {
        "board": board,
        "is_player_A": is_player_A

    }
    return json.dumps(key, sort_keys=True)

def get_actions(board, is_player_A):

    actions = []
    start, end = (1,5) if is_player_A else (6, 10)
    for pos in range(start, end+1):
        if board[pos]:
            for step in (-1, 1):
                actions.append((pos, step))

    return actions

def step(board, score_A, score_B, is_player_A, action):
    board_copy = copy.deepcopy(board)
    score_A_copy = score_A.copy()
    score_B_copy = score_B.copy()

    pos, step_dir = action
    if is_player_A:
        dan, quan = capture(board_copy, pos, True, step_dir)
        score_A_copy["dan"] += dan
        score_A_copy["quan"] += quan

    else:
        dan, quan = capture(board_copy, pos, False, step_dir)
        score_B_copy["dan"] += dan
        score_B_copy["quan"] += quan


    restore_player_side(
        board_copy,
        score_A_copy if is_player_A else score_B_copy,
        is_player_A

    )

    reward = dan + quan * 5
    next_state = (board_copy, score_A_copy, score_B_copy, not is_player_A)
    return next_state, reward


def is_terminal(board, score_A, score_B):
    return game_over(board, score_A, score_B)

def generate_all_states():

    initial = (initialize_board(),
               {"dan": 0, "quan": 0},
               {"dan": 0, "quan": 0},
               True)
    states = [initial]
    seen = {state_to_key(initial[0], initial[3])}
    idx = 0

    while idx < len(states):
        board, sA, sB, is_A = states[idx]
        idx += 1

        if is_terminal(board, sA, sB):
            continue
        for action in get_actions(board, is_A):
            next_s, _ = step(board, sA, sB, is_A, action)
            key = state_to_key(next_s[0], next_s[3])
            if key not in seen:
                seen.add(key)
                states.append(next_s)

    return states

def value_iteration():
    all_states = generate_all_states()

    V = {
        state_to_key(b, is_A) : 0.0
        for (b, _, _, is_A) in all_states}
    while True:
        delta = 0
        for board, sA, sB, is_A in all_states:
            key = state_to_key(board, is_A)
            if is_terminal(board, sA, sB):
                continue

        best_value = float("-inf")
        for action in get_actions(board, is_A):
            ns, r = step(board, sA, sB, is_A, action)
            ns_key = state_to_key(ns[0], ns[3])
            value = r + gamma * V[ns_key]
            best_value = max(best_value, value)

        delta = max(delta, abs(V[key]- best_value))
        V[key] = best_value

        if delta < theta:
            break

    policy = {}
    for board, sA, sB, is_A in all_states:
        key = state_to_key(board, is_A)
        if is_terminal(board, sA, sB):
            policy[key] = None
            continue

        best_action = None
        best_value = float("-inf")
        for action in get_actions(board, is_A):
            ns, r = step(board, sA, sB, is_A, action)
            ns_key = state_to_key(ns[0], ns[3])
            value = r + gamma * V[ns_key]
            if value > best_value:
                best_value = value
                best_action = action

        policy[key] = best_action

    return policy

policy = value_iteration()

def get_ai_move(board, score_A, score_B, is_player_A):
    key    = state_to_key(board, is_player_A)
    action = policy.get(key)
    return action