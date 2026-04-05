"""
models/greedy.py — Greedy heuristic AI.

Picks the move that maximizes immediate capture score.
Serves as a fast, weak baseline.
"""
from __future__ import annotations
import copy
from models.game_logic import execute_capture, get_valid_moves, calculate_score

def get_ai_move(board, score_a, score_b, is_player_a):
    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return None, None

    best_score = -1
    best_move = moves[0]
    for pos, step in moves:
        test = copy.deepcopy(board)
        res = execute_capture(test, pos, is_player_a, step)
        val = res.captured_dan + res.captured_quan * 5
        if val > best_score:
            best_score = val
            best_move = (pos, step)
    return best_move

MODEL_NAME = "Greedy"
DESCRIPTION = "Chooses the move with the highest immediate capture reward. Fast but shortsighted — easy to defeat with lookahead."