"""
app.py — Ô Ăn Quan backend (Flask)

Endpoints:
  GET  /                   → serve game UI
  GET  /state              → full game state
  POST /move               → human move
  POST /ai_move            → request AI move (manual step-through)
  POST /switch_model       → change active AI model
  POST /reset              → restart game
  POST /undo               → undo last move
  GET  /history            → full move history
  POST /set_mode           → switch game mode (hvai, hvh, aivai)
  POST /benchmark          → run N games between two AI agents
  GET  /models             → list all available models
"""
from __future__ import annotations
import copy, importlib, time, threading, queue
from flask import Flask, render_template, request, jsonify

from models.game_logic import (
    initialize_board, execute_capture, restore_player_side,
    is_game_over, finalize_scores, determine_winner,
    calculate_score, serialize_state, GameSnapshot,
    get_valid_moves,
)

app = Flask(__name__)

# Available AI models 
MODELS = {
    "minimax":          "models.minimax",
    "monte_carlo":      "models.monte_carlo",
    "greedy":           "models.greedy_model",
    "bayesian":         "models.bayes",
    "value_iteration":  "models.value_iteration",
    "policy_iteration": "models.policy_iteration",
    "q_learning":       "models.q_learning",
}

def _load_model(name: str):
    mod = importlib.import_module(MODELS[name])
    if hasattr(mod, "init_policy"):
        threading.Thread(target=mod.init_policy, daemon=True).start()
    return mod

#  Game state 
board        = initialize_board()
score_a      = {"dan": 0, "quan": 0}
score_b      = {"dan": 0, "quan": 0}
is_player_a  = True
move_history: list[dict] = []
snapshots:   list[GameSnapshot] = []

game_mode    = "hvai"
ai_model_a   = _load_model("minimax")
ai_model_b   = _load_model("minimax")
model_name_a = "minimax"
model_name_b = "minimax"

aivai_queue: queue.Queue = queue.Queue()
aivai_running = False

#  Helpers

def _save_snapshot():
    snapshots.append(GameSnapshot(
        board=copy.deepcopy(board),
        score_a=score_a.copy(),
        score_b=score_b.copy(),
        is_player_a=is_player_a,
    ))
    if len(snapshots) > 50:
        snapshots.pop(0)

def _full_state(extra: dict = None) -> dict:
    state = serialize_state(board, score_a, score_b, is_player_a, move_history)
    state["valid_moves"] = get_valid_moves(board, is_player_a)
    state["game_mode"]   = game_mode
    state["ai_model"]    = model_name_b
    state["ai_model_a"]  = model_name_a
    if extra:
        state.update(extra)
    if is_game_over(board, score_a, score_b):
        _finalize_if_needed()
        state["winner"]  = determine_winner(score_a, score_b)
        state["total_A"] = calculate_score(score_a["dan"], score_a["quan"])
        state["total_B"] = calculate_score(score_b["dan"], score_b["quan"])
    return state

_finalized = False
def _finalize_if_needed():
    global _finalized
    if not _finalized:
        finalize_scores(board, score_a, score_b)
        _finalized = True

def _apply_move(pos: int, step: int, player_is_a: bool) -> dict:
    global is_player_a, _finalized
    _save_snapshot()
    res = execute_capture(board, pos, player_is_a, step)
    target = score_a if player_is_a else score_b
    target["dan"]  += res.captured_dan
    target["quan"] += res.captured_quan
    restore_player_side(board, score_a, True)
    restore_player_side(board, score_b, False)
    direction    = "clockwise" if step == 1 else "counterclockwise"
    player_label = "A" if player_is_a else "B (AI)"
    desc = (f"Player {player_label}: pit {pos} → {direction} | "
            f"captured {res.captured_dan} dân, {res.captured_quan} quan")
    move_history.append({"desc": desc, "pos": pos, "step": step,
                         "player": "A" if player_is_a else "B"})
    is_player_a = not player_is_a
    _finalized   = False
    return {"captured_dan": res.captured_dan, "captured_quan": res.captured_quan, "desc": desc}

#  Routes 

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/state")
def get_state():
    return jsonify(_full_state())

@app.route("/models")
def list_models():
    result = []
    for key, path in MODELS.items():
        try:
            mod = importlib.import_module(path)
            result.append({
                "id":   key,
                "name": getattr(mod, "MODEL_NAME",  key),
                "desc": getattr(mod, "DESCRIPTION", ""),
            })
        except Exception:
            pass
    return jsonify(result)

@app.route("/move", methods=["POST"])
def human_move():
    global is_player_a
    if is_game_over(board, score_a, score_b):
        return jsonify(_full_state({"error": "Game is over"}))
    if game_mode == "hvai" and not is_player_a:
        return jsonify(_full_state({"error": "Not your turn"}))

    data = request.json
    pos  = int(data["pos"])
    step = int(data["step"])

    valid = (1 <= pos <= 5) if is_player_a else (6 <= pos <= 10)
    if not valid or not board[pos]:
        return jsonify(_full_state({"error": "Invalid move"})), 400

    result = _apply_move(pos, step, is_player_a)
    extra  = {"move_result": result}

    if game_mode == "hvai" and not is_player_a and not is_game_over(board, score_a, score_b):
        ai_result = _do_ai_move(ai_model_b, False)
        extra["ai_result"] = ai_result

    return jsonify(_full_state(extra))

@app.route("/ai_move", methods=["POST"])
def trigger_ai_move():
    global is_player_a
    if is_game_over(board, score_a, score_b):
        return jsonify(_full_state({"error": "Game is over"}))
    model  = ai_model_b if not is_player_a else ai_model_a
    result = _do_ai_move(model, is_player_a)
    return jsonify(_full_state({"ai_result": result}))

def _do_ai_move(model, player_is_a: bool) -> dict:
    start     = time.time()
    pos, step = model.get_ai_move(board, score_a, score_b, player_is_a)
    elapsed   = round((time.time() - start) * 1000)
    if pos is None:
        return {"error": "No moves available"}
    result = _apply_move(pos, step, player_is_a)
    result["think_ms"] = elapsed
    return result

@app.route("/switch_model", methods=["POST"])
def switch_model():
    global ai_model_b, model_name_b, ai_model_a, model_name_a
    data   = request.json
    target = data.get("target", "b")
    name   = data.get("model", "minimax")
    if name not in MODELS:
        return jsonify({"error": "Unknown model"}), 400
    mod = _load_model(name)
    if target == "a":
        ai_model_a, model_name_a = mod, name
    else:
        ai_model_b, model_name_b = mod, name
    return jsonify({"status": f"Model {target} → {name}"})

@app.route("/set_mode", methods=["POST"])
def set_mode():
    global game_mode
    mode = request.json.get("mode", "hvai")
    if mode not in ("hvai", "hvh", "aivai"):
        return jsonify({"error": "Invalid mode"}), 400
    game_mode = mode
    return jsonify({"status": f"Mode set to {mode}"})

@app.route("/reset", methods=["POST"])
def reset_game():
    global board, score_a, score_b, is_player_a, move_history, snapshots, _finalized
    board        = initialize_board()
    score_a      = {"dan": 0, "quan": 0}
    score_b      = {"dan": 0, "quan": 0}
    is_player_a  = True
    move_history = []
    snapshots    = []
    _finalized   = False
    return jsonify(_full_state())

@app.route("/undo", methods=["POST"])
def undo():
    global board, score_a, score_b, is_player_a, _finalized
    if not snapshots:
        return jsonify(_full_state({"error": "Nothing to undo"}))
    snap        = snapshots.pop()
    board       = copy.deepcopy(snap.board)
    score_a     = snap.score_a.copy()
    score_b     = snap.score_b.copy()
    is_player_a = snap.is_player_a
    if move_history:
        move_history.pop()
    _finalized = False
    return jsonify(_full_state({"undone": True}))

@app.route("/history")
def history():
    return jsonify({"history": move_history})

@app.route("/benchmark", methods=["POST"])
def benchmark():
    data    = request.json
    name_a  = data.get("model_a", "greedy")
    name_b  = data.get("model_b", "minimax")
    n_games = min(int(data.get("games", 10)), 50)

    if name_a not in MODELS or name_b not in MODELS:
        return jsonify({"error": "Unknown model(s)"}), 400

    mod_a = importlib.import_module(MODELS[name_a])
    mod_b = importlib.import_module(MODELS[name_b])

    wins_a, wins_b, draws, total_moves = 0, 0, 0, 0

    for _ in range(n_games):
        b  = initialize_board()
        sa = {"dan": 0, "quan": 0}
        sb = {"dan": 0, "quan": 0}
        turn_a = True
        moves  = 0
        for __ in range(200):
            if is_game_over(b, sa, sb):
                break
            model     = mod_a if turn_a else mod_b
            pos, step = model.get_ai_move(b, sa, sb, turn_a)
            if pos is None:
                break
            res = execute_capture(b, pos, turn_a, step)
            if turn_a:
                sa["dan"] += res.captured_dan; sa["quan"] += res.captured_quan
            else:
                sb["dan"] += res.captured_dan; sb["quan"] += res.captured_quan
            restore_player_side(b, sa, True)
            restore_player_side(b, sb, False)
            turn_a = not turn_a
            moves  += 1
        finalize_scores(b, sa, sb)
        ta = calculate_score(sa["dan"], sa["quan"])
        tb = calculate_score(sb["dan"], sb["quan"])
        if ta > tb:   wins_a += 1
        elif tb > ta: wins_b += 1
        else:         draws  += 1
        total_moves += moves

    return jsonify({
        "model_a": name_a, "model_b": name_b,
        "games":   n_games,
        "wins_a":  wins_a, "wins_b": wins_b, "draws": draws,
        "win_rate_a": round(wins_a / n_games * 100, 1),
        "win_rate_b": round(wins_b / n_games * 100, 1),
        "avg_moves":  round(total_moves / n_games, 1),
    })

import webbrowser

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
