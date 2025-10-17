# Playing-O-An-Quan-with-AI
A modern recreation of Ô Ăn Quan, a traditional Vietnamese board game, powered by artificial intelligence. This project combines cultural heritage and computer science by allowing users to play against AI agents that use different decision-making algorithms

# Overview
Ô Ăn Quan is a classic Vietnamese strategy game involving logical thinking and resource management. Players take turns distributing stones across pits, capturing opponents’ pieces, and collecting points based on the game’s unique rules.

This project digitizes the game and integrates various AI models that can analyze the current board state, evaluate potential moves, and make strategic decisions. Players can compete Human vs. AI or even Human vs. Human to compare algorithmic performance.

# AI Algorithms
The project features several AI agents, each representing different problem-solving strategies:
- Greedy Algorithm: Chooses the move with the highest immediate reward.
- Monte Carlo Simulation: Runs simulated playouts to predict long-term outcomes.
- Minimax Algorithm: Models adversarial play and optimizes decision trees.
- Q-Learning Agent: Learns optimal strategies through trial and reward.
- Heuristic Evaluation: Uses weighted scoring to balance offense and defense.
Each agent can be swapped or tuned independently for comparison and experimentation.

# Features
Full implementation of Ô Ăn Quan game rules.
- Playable Human vs. AI and Human vs. Human modes.
- Modular and extensible codebase for adding new algorithms.
- Visual board representation and move tracking.
- Adjustable difficulty and simulation speed.

# Tech Stack
Python 3.10+
HTML, CSS, Javascript
Flask (optional UI)
NumPy, Pandas for data representation

# Getting Started
- Clone the repository
+ git clone https://github.com/NghiemNgocDuc/Playing-O-An-Quan-with-AI.git
+ cd Playing-O-An-Quan-with-AI
- Run the game
  python app.py

# Future Improvements
- Reinforcement learning with neural networks.
- Improved GUI with dynamic animations.
- Enhanced evaluation metrics for AI agents.

# Author
Ngoc Duc Nghiem
- Email: nghiemngocduc7@gmail.com
- GitHub: NghiemNgocDuc

