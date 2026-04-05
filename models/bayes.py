"""
models/bayes.py — Bayesian-inspired probabilistic AI.

Scores each legal move by its *expected value* under a sampled distribution
of opponent responses.  No external libraries required.
"""
from __future__ import annotations
import copy, random
from models.game_logic import (
    execute_capture, restore_player_side, is_game_over,
    calculate_score, get_valid_moves,
)

MODEL_NAME  = "Bayesian"
DESCRIPTION = ("Scores moves by expected value under a sampled distribution "
               "of opponent responses. Lightweight probabilistic lookahead.")

def _board_value(board, score_a, score_b) -> float:
    ta = calculate_score(score_a["dan"], score_a["quan"])
    tb = calculate_score(score_b["dan"], score_b["quan"])
    return (tb - ta) * 2.0

def _simulate_one(board, score_a, score_b, pos, step, is_player_a, opp_samples=6):
    nb = copy.deepcopy(board)
    na, nbs = score_a.copy(), score_b.copy()
    res = execute_capture(nb, pos, is_player_a, step)
    if is_player_a:
        na["dan"]  += res.captured_dan;  na["quan"]  += res.captured_quan
    else:
        nbs["dan"] += res.captured_dan;  nbs["quan"] += res.captured_quan
    restore_player_side(nb, na,  True)
    restore_player_side(nb, nbs, False)

    immediate = (res.captured_dan + res.captured_quan * 5.0) * (1 if not is_player_a else -1)

    if is_game_over(nb, na, nbs):
        return immediate + _board_value(nb, na, nbs)

    opp_is_a  = not is_player_a
    opp_moves = get_valid_moves(nb, opp_is_a)
    if not opp_moves:
        return immediate + _board_value(nb, na, nbs)

    sample   = random.sample(opp_moves, min(opp_samples, len(opp_moves)))
    opp_vals = []
    for opos, ostep in sample:
        tnb = copy.deepcopy(nb)
        tna, tnbs = na.copy(), nbs.copy()
        ores = execute_capture(tnb, opos, opp_is_a, ostep)
        if opp_is_a:
            tna["dan"]  += ores.captured_dan;  tna["quan"]  += ores.captured_quan
        else:
            tnbs["dan"] += ores.captured_dan;  tnbs["quan"] += ores.captured_quan
        restore_player_side(tnb, tna,  True)
        restore_player_side(tnb, tnbs, False)
        opp_gain = ores.captured_dan + ores.captured_quan * 5.0
        opp_vals.append(-opp_gain + _board_value(tnb, tna, tnbs))

    avg_opp = sum(opp_vals) / len(opp_vals)
    return immediate + 0.7 * avg_opp

def get_ai_move(board, score_a, score_b, is_player_a, mc_draws=10):
    moves = get_valid_moves(board, is_player_a)
    if not moves:
        return None, None
    best_score = float("-inf")
    best_move  = moves[0]
    for pos, step in moves:
        total = sum(_simulate_one(board, score_a, score_b, pos, step, is_player_a) for _ in range(mc_draws))
        avg = total / mc_draws
        if avg > best_score:
            best_score = avg
            best_move  = (pos, step)
    return best_move
