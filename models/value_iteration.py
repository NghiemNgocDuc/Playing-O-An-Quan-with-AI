"""
models/value_iteration.py — Online Value Iteration (limited-depth lookahead).

Applies iterative Bellman updates over a bounded search tree.
Uses memoization to avoid redundant evaluations.
"""
from __future__ import annotations
import copy
from models.game_logic import (
    execute_capture, restore_player_side, is_game_over,
    calculate_score, get_valid_moves,
)

MODEL_NAME  = "Value Iteration"
DESCRIPTION = ("Online value iteration via iterative Bellman updates "
               "over a depth-4 lookahead tree.")

GAMMA = 0.95
DEPTH = 4

def _value(board, score_a, score_b, is_player_a, depth, memo):
    if depth == 0 or is_game_over(board, score_a, score_b):
        ta = calculate_score(score_a["dan"], score_a["quan"])
        tb = calculate_score(score_b["dan"], score_b["quan"])
        return float(tb - ta) * 10.0   # from AI (B) perspective

    key = (str([[len(p) for p in board]]), is_player_a, depth)
    if key in memo:
        return memo[key]

    moves = get_valid_moves(board, is_player_a)
    if not moves:
        val = _value(board, score_a, score_b, not is_player_a, depth - 1, memo)
        memo[key] = val
        return val

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

        reward = res.captured_dan + res.captured_quan * 5.0
        reward = reward if not is_player_a else -reward   # from B's view

        future = _value(nb, na, nbs, not is_player_a, depth - 1, memo)
        v = reward + GAMMA * future

        if not is_player_a:   # AI maximises
            best = max(best, v)
        else:                 # human minimises (from AI view)
            best = min(best, v)

    memo[key] = best
    return best

def get_ai_move(board, score_a, score_b, is_player_a, depth=DEPTH):
    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return None, None
    memo = {}
    best_val  = float("-inf")
    best_move = moves[0]
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
        reward = res.captured_dan + res.captured_quan * 5.0
        future = _value(nb, na, nbs, not is_player_a, depth - 1, memo)
        val = reward + GAMMA * future
        if val > best_val:
            best_val  = val
            best_move = (pos, step)
    return best_move
