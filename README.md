# Monopoly Bench

Monopoly Bench is a lightweight, text-based simulation of the classic board game Monopoly, designed for benchmarking and analyzing agent-based strategies. This platform allows developers and researchers to implement and test various playing strategies in a controlled and repeatable environment.

## Setup

To get started with Monopoly Bench, you will need Python 3. No external libraries are required, so you can run the simulation out of the box. Follow these steps to set up the project:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/monopoly-bench.git
    cd monopoly-bench
    ```

2.  **Verify your Python version:**

    Ensure you have Python 3 installed on your system:

    ```bash
    python3 --version
    ```

    If you do not have Python 3, please install it from the official [Python website](https://www.python.org/downloads/).

## Usage

To run a Monopoly simulation, execute the `run_match.py` script from the root directory of the project:

```bash
python3 run_match.py
```

This will start a game with the default settings, which include two players with predefined agents: a `GreedyBuyer` and a `RandomAgent`. The simulation will run until one player goes bankrupt or the maximum number of turns is reached.

The output will provide a detailed log of each turn, including player actions, cash, properties, and rent payments. At the end of the game, the final results will be displayed, showing the winner and their assets.

## Project Structure

The project is organized into three main files:

-   `run_match.py`: This is the main script to run a Monopoly simulation. It initializes the game state, agents, and the game board. You can modify this file to customize the number of players, the agents used, and the board layout.

-   `engine.py`: This file contains the core game logic, including the `GameState`, `Player`, and `Tile` classes. It manages the game state, player actions, and the rules of the game, such as moving players, buying and selling properties, and paying rent.

-   `agents.py`: This file defines the different agents that can play the game. By default, it includes:
    -   `RandomAgent`: A baseline agent that makes random decisions.
    -   `GreedyBuyer`: An agent that buys any unowned property it lands on.

    You can create your own agents by extending the base `Agent` class and implementing the `act` method.

## How to Add a New Agent

To add a new agent, create a new class in `agents.py` that inherits from the base `Agent` class and implements the `act` method. The `act` method should take the current game state as input and return an action.

Once you have created your agent, you can add it to a simulation by modifying the `run_match.py` script to include your new agent in the `agents` list.

## Selling Properties

When a player owes rent and does not have enough cash to cover the cost, they will enter a `decide_to_sell` phase. In this phase, the player can choose to sell one of their properties to the bank for half of its original cost. The agent will continue to sell properties until the debt is paid or they have no more properties to sell, at which point they will go bankrupt.

## Future Updates

This README will be updated to reflect any changes to the codebase, including new features, bug fixes, and improvements to the simulation engine.