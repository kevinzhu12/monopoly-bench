# Monopoly Bench

Monopoly Bench is a lightweight, text-based simulation of the classic board game Monopoly, designed for benchmarking and analyzing agent-based strategies. This project allows LLMs to play Monopoly against each other, providing a controlled environment to test strategic decision-making capabilities.

## Features

- **LLM Agent Support**: Integrates with OpenAI API (GPT-4, o3, etc.) for AI players
- **Condensed Board**: Optimized 19-tile board to reduce game length and API costs
- **Multiple Agent Types**: Support for LLM agents, random agents, and custom strategies
- **Detailed Logging**: Comprehensive game logs for analysis and debugging
- **Auction System**: Full property auction mechanics when players skip purchases
- **Trading & Building**: Complete property trading and house-building mechanics

## Quick Start

1. **Setup Environment**
   ```bash
   # Install UV package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Clone and setup project
   git clone <repository-url>
   cd monopoly-bench
   uv sync
   ```

2. **Configure OpenAI API**
   ```bash
   # Create .env file with your API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

3. **Run a Game**
   ```bash
   uv run src/run_match.py
   ```

## Project Structure

```
monopoly-bench/
├── src/
│   ├── run_match.py    # Main game runner
│   ├── engine.py       # Core game logic and rules
│   ├── agents.py       # AI agent implementations
│   ├── apis.py         # OpenAI API integration
│   ├── tools.py        # LLM function definitions
│   ├── config.py       # Game configuration
│   └── logger.py       # Game logging utilities
├── results/            # Game logs and results
└── README.md
```

## Configuration

Edit `src/config.py` to customize:

- **Agents**: Choose between LLM, Random, or custom agents
- **Starting Cash**: Default $1000 (optimized for faster games)
- **Max Turns**: Default 30 turns to prevent infinite games
- **Board Layout**: Condensed 19-tile board with core Monopoly mechanics

## Game Mechanics

The simulation includes core Monopoly features:

- **Property Management**: Buy, mortgage, and trade properties
- **House Building**: Build houses on monopolies for increased rent
- **Auctions**: Properties go to auction when skipped
- **Debt Resolution**: Automatic bankruptcy handling
- **Strategic Trading**: LLM agents can propose and negotiate trades

## Example Output

```
=== MONOPOLY GAME LOG ===
--- TURN 1: PLAYER 0'S TURN ---
Player 0 | Cash: $1000 | Position: 0 | Properties: None
Phase: start_management_phase
Action: proceed
Player 0 rolled 8, moved to Baltic Avenue
Bought Baltic Avenue for $60
```

## Development

To add custom agents, extend the base `Agent` class in `agents.py`:

```python
class CustomAgent(Agent):
    def act(self, observation):
        # Implement your strategy
        return {"type": "proceed"}
```

## Requirements

- Python 3.8+
- OpenAI API key (for LLM agents)
- UV package manager for dependencies