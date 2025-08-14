# Input:
#     - States S
#     - Actions A
#     - Transition probabilities P(s' | s, a)
#     - Rewards R(s, a, s')
#     - Discount factor γ (0 < γ ≤ 1)
#     - Threshold θ for convergence
#
# Initialize:
#     - Policy π[s] ← random action for each state s
#     - Value V[s] ← 0 for all states
#
# Repeat:
#     # --- Policy Evaluation ---
#     Loop until value function converges:
#         For each state s in S:
#             a ← π[s]  # current policy's action
#             V[s] ← sum over s':
#                 P(s' | s, a) × [R(s, a, s') + γ × V[s']]
#
#     # --- Policy Improvement ---
#     policy_stable ← true
#     For each state s in S:
#         old_action ← π[s]
#         For each action a in A:
#             Q[a] ← sum over s':
#                 P(s' | s, a) × [R(s, a, s') + γ × V[s']]
#         π[s] ← action a with highest Q[a]
#         If π[s] ≠ old_action:
#             policy_stable ← false
#
# Until policy_stable is true
#
# Output:
#     - Optimal policy π
#     - Value function V
from models.bayes import score_A
from models.value_iteration import is_terminal, step
import random
from game_logic import (
    initialize_board,
    capture,
    restore_player_side,
    game_over,
    calculate_score
)
def policy_evaluation(pi, all_states, gamma = 1.0, theta = 1e-4):
    V = {s:0 for s in all_states}
    while True:
        delta = 0
        for s in all_states:
            if is_terminal(s):
                continue
            a = pi[s]
            s2, r = step(s, a)
            v_new = r + gamma * V[s2]
            delta = max(delta, abs(v_new- V[s]))
            V[s] = v_new

        if delta < theta:
            break
    return V

def policy_iteration(all_states, all_actions, gamma= 1.0):
    pi = {s: random.choice(all_actions(s)) for s in all_states if not is_terminal(s) }
    while True:
        V = policy_evaluation(pi, all_states, gamma)
        policy_stable = True
        for s in all_states:
            if is_terminal(s):
                continue
            old_a = pi[s]
            pi[s] = max(
                all_actions(s),
                key =lambda  a: step(s,a)[1] + gamma * V[step(s, a)[0]]
            )
            if pi[s] != old_a:
                policy_stable = False
        if policy_stable:
            break
    return pi
policy_iteration_agent_pi = policy_iteration(all_states, all_actions)
from value_iteration import state_to_key
def get_ai_move(board, is_player_A):
    state = (board, score_A, score_B, is_player_A)
    key = state_to_key(state)
    return policy_iteration_agent_pi(key)