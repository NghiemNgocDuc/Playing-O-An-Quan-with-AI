"""
models/monte_carlo.py — Monte Carlo Tree Search (MCTS).

Enhancements over original:
  - UCB1-guided tree policy (Upper Confidence Bound)
  - Proper tree nodes with visit counts and win rates
  - Configurable simulation budget
  - Rollout policy with lightweight heuristic
"""
from __future__ import annotations
import copy, math, random
from models.game_logic import (
    execute_capture, restore_player_side, is_game_over,
    finalize_scores, calculate_score, get_valid_moves,
)

C_PARAM = 1.414        # UCB1 exploration constant
SIMULATIONS = 300      # Number of MCTS rollouts per move

#  Tree node 

class Node:
    __slots__ = ("board", "score_a", "score_b", "is_player_a",
                 "move", "parent", "children", "visits", "wins",
                 "untried_moves")

    def __init__(self, board, score_a, score_b, is_player_a, move=None, parent=None):
        self.board = copy.deepcopy(board)
        self.score_a = score_a.copy()
        self.score_b = score_b.copy()
        self.is_player_a = is_player_a
        self.move = move            # (pos, step) that led here
        self.parent = parent
        self.children: list[Node] = []
        self.visits = 0
        self.wins = 0.0
        self.untried_moves = get_valid_moves(board, is_player_a)
        random.shuffle(self.untried_moves)

    def ucb1(self) -> float:
        if self.visits == 0:
            return float('inf')
        exploit = self.wins / self.visits
        explore = C_PARAM * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploit + explore

    def best_child(self) -> "Node":
        return max(self.children, key=lambda n: n.ucb1())

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def is_terminal(self) -> bool:
        return is_game_over(self.board, self.score_a, self.score_b)

#  MCTS phases 
def _expand(node: Node) -> Node:
    pos, step = node.untried_moves.pop()
    nb = copy.deepcopy(node.board)
    na, ns_b = node.score_a.copy(), node.score_b.copy()
    res = execute_capture(nb, pos, node.is_player_a, step)
    if node.is_player_a:
        na["dan"] += res.captured_dan; na["quan"] += res.captured_quan
    else:
        ns_b["dan"] += res.captured_dan; ns_b["quan"] += res.captured_quan
    restore_player_side(nb, na, True)
    restore_player_side(nb, ns_b, False)
    child = Node(nb, na, ns_b, not node.is_player_a, move=(pos, step), parent=node)
    node.children.append(child)
    return child

def _rollout(node: Node) -> float:
    """
    Random + heuristic rollout. Returns 1.0 if AI (B) wins, 0.0 otherwise.
    """
    board = copy.deepcopy(node.board)
    sa = node.score_a.copy()
    sb = node.score_b.copy()
    player = node.is_player_a

    for _ in range(40):  # depth cap to avoid infinite loops
        if is_game_over(board, sa, sb):
            break
        moves = get_valid_moves(board, player)
        if not moves:
            break
        # Heuristic: bias toward moves that capture the most
        scored = []
        for pos, step in moves:
            tb = copy.deepcopy(board)
            r = execute_capture(tb, pos, player, step)
            scored.append((r.captured_dan + r.captured_quan * 5, pos, step))
        scored.sort(reverse=True)
        # Softmax-style: pick top move 60% of the time, random otherwise
        if random.random() < 0.6 and scored:
            pos, step = scored[0][1], scored[0][2]
        else:
            pos, step = random.choice(moves)
        res = execute_capture(board, pos, player, step)
        if player:
            sa["dan"] += res.captured_dan; sa["quan"] += res.captured_quan
        else:
            sb["dan"] += res.captured_dan; sb["quan"] += res.captured_quan
        restore_player_side(board, sa, True)
        restore_player_side(board, sb, False)
        player = not player

    # Score from AI (B) perspective
    ta = calculate_score(sa["dan"], sa["quan"])
    tb = calculate_score(sb["dan"], sb["quan"])
    if tb > ta:   return 1.0
    if ta > tb:   return 0.0
    return 0.5

def _backprop(node: Node, result: float) -> None:
    while node is not None:
        node.visits += 1
        node.wins += result
        result = 1.0 - result  # flip for alternating players
        node = node.parent

#  Public API 

def get_ai_move(board, score_a, score_b, is_player_a, simulations=SIMULATIONS):
    """Return (pos, step) via MCTS."""
    root = Node(board, score_a, score_b, is_player_a)

    for _ in range(simulations):
        node = root
        # Selection
        while not node.is_terminal() and node.is_fully_expanded() and node.children:
            node = node.best_child()
        # Expansion
        if not node.is_terminal() and not node.is_fully_expanded():
            node = _expand(node)
        # Rollout
        result = _rollout(node)
        # Backpropagation
        _backprop(node, result)

    if not root.children:
        moves = get_valid_moves(board, is_player_a)
        return moves[0] if moves else (None, None)

    best = max(root.children, key=lambda n: n.visits)
    return best.move

MODEL_NAME = "Monte Carlo Tree Search"
DESCRIPTION = "UCB1-guided MCTS with heuristic rollouts. Balances exploration and exploitation to find strong moves without full game-tree enumeration."