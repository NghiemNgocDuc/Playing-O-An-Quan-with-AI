"""
models/minimax.py — Minimax with Alpha-Beta pruning.

Enhancements over original:
  - Alpha-beta pruning (cuts search space dramatically)
  - Move ordering heuristic (try high-capture moves first)
  - Configurable depth (difficulty levels)
  - Proper multi-capture evaluation
"""
from __future__ import annotations
import copy
from models.game_logic import (
    execute_capture, restore_player_side, is_game_over,
    finalize_scores, calculate_score, get_valid_moves,
)

DEFAULT_DEPTH = 5  # Increase for harder difficulty

#  Heuristic evaluation 

def _evaluate(board, score_a, score_b) -> float:
    """
    Evaluate board from B's perspective (AI = B).
    Positive = better for AI.
    """
    ta = calculate_score(score_a["dan"], score_a["quan"])
    tb = calculate_score(score_b["dan"], score_b["quan"])

    # Material advantage
    score = (tb - ta) * 10

    # Mobility: AI wants more options
    ai_moves   = len(get_valid_moves(board, False))
    human_moves = len(get_valid_moves(board, True))
    score += (ai_moves - human_moves) * 2

    # Quan proximity: don't let human capture Quan
    if board[0]:   score += 3   # human's quan still alive → slight advantage for AI
    if board[11]:  score += 3   # AI's quan still alive

    # Seed density on opponent's side (harder for human)
    score += sum(len(board[i]) for i in range(6, 11)) * 0.5

    return score

#  Move ordering 

def _order_moves(board, moves, is_maximizing):
    """
    Quick greedy pre-sort: try moves that capture most seeds first.
    Improves alpha-beta pruning efficiency.
    """
    def move_score(mv):
        pos, step = mv
        test = copy.deepcopy(board)
        sa = {"dan": 0, "quan": 0}
        sb = {"dan": 0, "quan": 0}
        res = execute_capture(test, pos, not is_maximizing, step)
        return res.captured_dan + res.captured_quan * 5

    return sorted(moves, key=move_score, reverse=True)

#  Alpha-Beta search 

def _alphabeta(board, score_a, score_b, depth, alpha, beta, is_maximizing) -> float:
    if depth == 0 or is_game_over(board, score_a, score_b):
        return _evaluate(board, score_a, score_b)

    moves = get_valid_moves(board, not is_maximizing)
    if not moves:
        return _evaluate(board, score_a, score_b)

    moves = _order_moves(board, moves, is_maximizing)

    if is_maximizing:
        best = float('-inf')
        for pos, step in moves:
            nb = copy.deepcopy(board)
            na, nb_score = score_a.copy(), score_b.copy()
            res = execute_capture(nb, pos, False, step)
            nb_score["dan"] += res.captured_dan
            nb_score["quan"] += res.captured_quan
            restore_player_side(nb, na, True)
            restore_player_side(nb, nb_score, False)
            val = _alphabeta(nb, na, nb_score, depth - 1, alpha, beta, False)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break  # β-cutoff
        return best
    else:
        best = float('inf')
        for pos, step in moves:
            nb = copy.deepcopy(board)
            na, nb_score = score_a.copy(), score_b.copy()
            res = execute_capture(nb, pos, True, step)
            na["dan"] += res.captured_dan
            na["quan"] += res.captured_quan
            restore_player_side(nb, na, True)
            restore_player_side(nb, nb_score, False)
            val = _alphabeta(nb, na, nb_score, depth - 1, alpha, beta, True)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break  # α-cutoff
        return best

#  Public API 

def get_ai_move(board, score_a, score_b, is_player_a, depth=DEFAULT_DEPTH):
    """Return (pos, step) for the AI's best move using Alpha-Beta Minimax."""
    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return None, None

    moves = _order_moves(board, moves, True)
    best_val = float('-inf')
    best_move = moves[0]

    for pos, step in moves:
        nb = copy.deepcopy(board)
        na, nb_score = score_a.copy(), score_b.copy()
        res = execute_capture(nb, pos, False, step)
        nb_score["dan"] += res.captured_dan
        nb_score["quan"] += res.captured_quan
        restore_player_side(nb, na, True)
        restore_player_side(nb, nb_score, False)
        val = _alphabeta(nb, na, nb_score, depth - 1, float('-inf'), float('inf'), False)
        if val > best_val:
            best_val = val
            best_move = (pos, step)

    return best_move

MODEL_NAME = "Minimax α-β (depth 5)"
DESCRIPTION = "Adversarial search with alpha-beta pruning. Looks several turns ahead and plays optimally within its search horizon."