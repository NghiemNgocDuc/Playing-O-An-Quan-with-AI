from flask import Flask, render_template, request, jsonify

# Flask app
# render_template: Render a template
# request: Request object
# jsonify: Convert a Python object to a JSON response
import importlib # used for switching models
from game_logic import (
    initialize_board, capture, restore_player_side,
    game_over, calculate_score, check_game_end
) # import game logic
from models.minimax import get_ai_move # import ai_move by the model you choose


app = Flask(__name__) # create a Flask app
board = initialize_board()
score_A = {"dan": 0, "quan": 0}
score_B = {"dan": 0, "quan": 0}
is_player_A = True # create board, score_A, score_B, player_A

# Load default AI model
ai_module_name = "models.minimax"
ai_model = importlib.import_module(ai_module_name)

@app.route("/") # serve the game page
def index():
    return render_template("index.html") # load your html game interface

@app.route("/state")# getting the current game state
def get_state():
    return jsonify({
        "board": board,
        "score_A": score_A,
        "score_B": score_B,
        "is_player_A": is_player_A,
        "game_over": game_over(board, score_A, score_B) # return board, scores, player, and wheterh game is over or not
    })


@app.route("/move", methods=["POST"]) # Handle player or ai move
def make_move():
    global board, score_A, score_B, is_player_A # declare global variables so they can be updated

    data = request.json # get the data from the frontend
    ai_move_description = "" # prepare ai move description

    if is_player_A:
        pos = int(data["pos"]) # get player move
        step = int(data["step"]) # get player direction
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
    is_player_A = not is_player_A # switch player

    response = {
        "board": board,
        "score_A": score_A,
        "score_B": score_B,
        "is_player_A": is_player_A,
        "ai_move": ai_move_description # the response with updated game state
    }


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
            "total_A": total_A, # determin the winner
            "total_B": total_B
        })
    else:
        response["game_over"] = False

    return jsonify(response) # return the updated game state to the frontend



@app.route("/switch_model", methods=["POST"]) # change ai model
def switch_model():
    global ai_model
    model_name = request.json["model"]
    ai_module_path = f"models.{model_name}"
    ai_model = importlib.import_module(ai_module_path)
    return jsonify({"status": "Model switched to " + model_name})

@app.route("/reset", methods=["POST"])
def reset_game():
    global board, score_A, score_B, is_player_A
    board = initialize_board()
    score_A = {"dan": 0, "quan": 0}
    score_B = {"dan": 0, "quan": 0}
    is_player_A = True
    return jsonify({
        "board": board,
        "score_A": score_A,
        "score_B": score_B,
        "is_player_A": is_player_A,
        "game_over": False
    }) # reset the game


if __name__ == "__main__": # run the app
    app.run(debug=True)