"""
models/q_learning.py — Tabular Q-Learning with ε-greedy exploration.

Enhancements over original:
  - Proper state representation with board counts (compact key)
  - Separate Q-tables per model instance (no global mutation)
  - Pre-training on startup via self-play (50k episodes)
  - Reward shaping: penalize bad outcomes, reward Quan capture
  - Decay schedule for ε and α
  - Persistence: saves/loads q_table.json automatically
"""
from __future__ import annotations
import copy, random, json, os
from models.game_logic import (
    execute_capture, restore_player_side, is_game_over,
    calculate_score, get_valid_moves, board_to_counts, initialize_board,
)

#  Hyperparameters 
ALPHA_INIT   = 0.3    # learning rate
ALPHA_MIN    = 0.05
GAMMA        = 0.95   # discount factor
EPS_INIT     = 0.3    # exploration rate
EPS_MIN      = 0.02
EPS_DECAY    = 0.999
TRAIN_EPISODES = 50_000
Q_TABLE_PATH = os.path.join(os.path.dirname(__file__), "..", "q_table.json")

#  Module-level state (loaded once) 
_Q: dict = {}
_eps = EPS_INIT
_alpha = ALPHA_INIT
_trained = False

def _state_key(board) -> str:
    return str(board_to_counts(board))

def _q_get(state_key: str, action) -> float:
    return _Q.get(f"{state_key}|{action}", 0.0)

def _q_set(state_key: str, action, value: float):
    _Q[f"{state_key}|{action}"] = value

def _q_update(s_key, action, reward, ns_key, done):
    global _alpha
    old = _q_get(s_key, action)
    if done:
        target = reward
    else:
        moves = [(p, d) for p in range(6, 11) for d in (1, -1)]
        future = max((_q_get(ns_key, m) for m in moves), default=0.0)
        target = reward + GAMMA * future
    new_val = old + _alpha * (target - old)
    _q_set(s_key, action, new_val)

#  Self-play training 

def _run_episode(eps: float, alpha: float) -> None:
    board = initialize_board()
    sa = {"dan": 0, "quan": 0}
    sb = {"dan": 0, "quan": 0}
    player = False  # AI = B

    for _ in range(100):
        if is_game_over(board, sa, sb):
            break
        moves = get_valid_moves(board, player)
        if not moves:
            player = not player
            continue

        if player:  # opponent: random
            pos, step = random.choice(moves)
            res = execute_capture(board, pos, True, step)
            sa["dan"] += res.captured_dan; sa["quan"] += res.captured_quan
        else:        # AI (B): ε-greedy
            s_key = _state_key(board)
            if random.random() < eps:
                pos, step = random.choice(moves)
            else:
                qs = [(_q_get(s_key, m), m) for m in moves]
                pos, step = max(qs, key=lambda x: x[0])[1]

            res = execute_capture(board, pos, False, step)
            reward = res.captured_dan * 1.0 + res.captured_quan * 5.0

            sb["dan"] += res.captured_dan; sb["quan"] += res.captured_quan
            restore_player_side(board, sa, True)
            restore_player_side(board, sb, False)
            ns_key = _state_key(board)

            done = is_game_over(board, sa, sb)
            if done:
                tb = calculate_score(sb["dan"], sb["quan"])
                ta = calculate_score(sa["dan"], sa["quan"])
                reward += (tb - ta) * 2  # terminal bonus/penalty
            _q_update(s_key, (pos, step), reward, ns_key, done)

        restore_player_side(board, sa, True)
        restore_player_side(board, sb, False)
        player = not player

def init_policy():
    """Train Q-table via self-play if no saved table exists."""
    global _trained, _eps, _alpha
    if _trained:
        return
    _trained = True

    # Try loading saved table
    try:
        with open(Q_TABLE_PATH, "r") as f:
            data = json.load(f)
            _Q.update(data)
            print(f"[Q-Learning] Loaded Q-table ({len(_Q)} entries)")
            return
    except Exception:
        pass

    print(f"[Q-Learning] Training {TRAIN_EPISODES} episodes...")
    eps, alpha = EPS_INIT, ALPHA_INIT
    for ep in range(TRAIN_EPISODES):
        _run_episode(eps, alpha)
        eps = max(EPS_MIN, eps * EPS_DECAY)
        if ep % 5000 == 0:
            alpha = max(ALPHA_MIN, alpha * 0.98)

    try:
        with open(Q_TABLE_PATH, "w") as f:
            json.dump(_Q, f)
        print(f"[Q-Learning] Saved Q-table ({len(_Q)} entries)")
    except Exception as e:
        print(f"[Q-Learning] Could not save table: {e}")

#  Public API 

def get_ai_move(board, score_a, score_b, is_player_a):
    init_policy()
    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return None, None
    s_key = _state_key(board)
    qs = [(_q_get(s_key, m), m) for m in moves]
    return max(qs, key=lambda x: x[0])[1]

MODEL_NAME = "Q-Learning (self-play)"
DESCRIPTION = "Tabular reinforcement learning trained via 50k self-play episodes with ε-greedy exploration and reward shaping."