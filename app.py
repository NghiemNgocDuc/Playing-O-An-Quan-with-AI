from flask import Flask, render_template, request, jsonify
import importlib
from game_logic import (
    initialize_board, capture, restore_player_side,
    game_over, calculate_score, check_game_end
)
from models.minimax import get_ai_move


app = Flask(__name__)
board = initialize_board()
score_A = {"dan": 0, "quan": 0}
score_B = {"dan": 0, "quan": 0}
is_player_A = True

# Load default AI model
ai_module_name = "models.minimax"
ai_model = importlib.import_module(ai_module_name)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/state")
def get_state():
    return jsonify({
        "board": board,
        "score_A": score_A,
        "score_B": score_B,
        "is_player_A": is_player_A,
        "game_over": game_over(board, score_A, score_B)
    })


@app.route("/move", methods=["POST"])
def make_move():
    global board, score_A, score_B, is_player_A

    data = request.json
    ai_move_description = ""

    if is_player_A:
        pos = int(data["pos"])
        step = int(data["step"])
        captured_dan, captured_quan = capture(board, pos, True, step)
        score_A["dan"] += captured_dan
        score_A["quan"] += captured_quan
    else:
        pos, step = ai_model.get_ai_move(board, False)
        captured_dan, captured_quan = capture(board, pos, False, step)
        score_B["dan"] += captured_dan
        score_B["quan"] += captured_quan
        ai_move_description = f"AI chose box [{pos}] and moved {'clockwise' if step == 1 else 'counterclockwise'}"

    restore_player_side(board, score_A if is_player_A else score_B, is_player_A)
    is_player_A = not is_player_A

    response = {
        "board": board,
        "score_A": score_A,
        "score_B": score_B,
        "is_player_A": is_player_A,
        "ai_move": ai_move_description
    }

    # ✅ Check for game over using correct logic
    if game_over(board, score_A, score_B):
        total_A = calculate_score(score_A["dan"], score_A["quan"])
        total_B = calculate_score(score_B["dan"], score_B["quan"])
        if total_A > total_B:
            winner = "Player A wins!"
        elif total_B > total_A:
            winner = "Player B wins!"
        else:
            winner = "It's a tie!"
        response.update({
            "game_over": True,
            "winner": winner,
            "total_A": total_A,
            "total_B": total_B
        })
    else:
        response["game_over"] = False

    return jsonify(response)



@app.route("/switch_model", methods=["POST"])
def switch_model():
    global ai_model
    model_name = request.json["model"]
    ai_module_path = f"models.{model_name}"
    ai_model = importlib.import_module(ai_module_path)
    return jsonify({"status": "Model switched to " + model_name})

if __name__ == "__main__":
    app.run(debug=True)