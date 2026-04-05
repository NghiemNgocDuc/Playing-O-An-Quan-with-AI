"""
models/policy_iteration.py — Online Policy Iteration.

Starts with an immediate-greedy policy, then improves it iteratively
via one-step lookahead policy evaluation (depth-3 rollout).
"""
from __future__ import annotations
import copy
from models.game_logic import (
    execute_capture, restore_player_side, is_game_over,
    calculate_score, get_valid_moves,
)

MODEL_NAME  = "Policy Iteration"
DESCRIPTION = ("Iterative policy improvement: begins greedy, then "
               "refines via one-step Bellman evaluation. Depth-3 rollout.")

GAMMA = 0.9
DEPTH = 3
PI_ITERS = 3   # policy improvement rounds

def _eval_state(board, score_a, score_b, is_player_a, depth):
    if depth == 0 or is_game_over(board, score_a, score_b):
        ta = calculate_score(score_a["dan"], score_a["quan"])
        tb = calculate_score(score_b["dan"], score_b["quan"])
        return float(tb - ta) * 10.0

    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return _eval_state(board, score_a, score_b, not is_player_a, depth - 1)

    best = float("-inf") if not is_player_a else float("inf")
    for pos, step in moves:
        nb = copy.deepcopy(board)
        na, nbs = score_a.copy(), score_b.copy()
        res = execute_capture(nb, pos, is_player_a, step)
        if is_player_a:
            na["dan"]  += res.captured_dan;  na["quan"]  += res.captured_quan
        else:
            nbs["dan"] += res.captured_dan;  nbs["quan"] += res.captured_quan
        restore_player_side(nb, na,  True)
        restore_player_side(nb, nbs, False)
        r = res.captured_dan + res.captured_quan * 5.0
        r = r if not is_player_a else -r
        v = r + GAMMA * _eval_state(nb, na, nbs, not is_player_a, depth - 1)
        best = max(best, v) if not is_player_a else min(best, v)
    return best

def _score_move(board, score_a, score_b, is_player_a, pos, step, depth):
    nb = copy.deepcopy(board)
    na, nbs = score_a.copy(), score_b.copy()
    res = execute_capture(nb, pos, is_player_a, step)
    if is_player_a:
        na["dan"]  += res.captured_dan;  na["quan"]  += res.captured_quan
    else:
        nbs["dan"] += res.captured_dan;  nbs["quan"] += res.captured_quan
    restore_player_side(nb, na,  True)
    restore_player_side(nb, nbs, False)
    r = res.captured_dan + res.captured_quan * 5.0
    return r + GAMMA * _eval_state(nb, na, nbs, not is_player_a, depth - 1)

def get_ai_move(board, score_a, score_b, is_player_a):
    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return None, None

    # Policy: mapping move → score
    policy = {m: _score_move(board, score_a, score_b, is_player_a, m[0], m[1], 1)
              for m in moves}

    # Policy improvement iterations
    for _ in range(PI_ITERS):
        policy = {m: _score_move(board, score_a, score_b, is_player_a, m[0], m[1], DEPTH)
                  for m in moves}

    return max(policy, key=lambda m: policy[m])
