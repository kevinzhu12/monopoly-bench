

import random
from apis import get_llm_response
from engine import PropertyTile

class BaseAgent:
    """A base class for all agents."""
    def __init__(self, player_id, seed=0):
        """Initializes the agent.

        Args:
            player_id: The ID of the player.
            seed: The seed for the random number generator.
        """
        self.player_id = player_id
        self.random = random.Random(seed)

    def act(self, observation: dict) -> dict:
        """Returns an action based on the current observation.

        Args:
            observation: A dictionary representing the current state of the game.

        Returns:
            A dictionary representing the action to be taken.
        """
        phase = observation["phase"]
        if phase == "decide_to_buy":
            return self.decide_to_buy(observation)
        elif phase == "decide_to_sell":
            return self.decide_to_sell(observation)
        elif phase == "roll":
            return {"type": "roll"}
        else:
            return {"type": "end_turn"}

    def decide_to_buy(self, observation: dict) -> dict:
        """Decides whether to buy a property.

        Args:
            observation: A dictionary representing the current state of the game.

        Returns:
            A dictionary representing the action to be taken.
        """
        raise NotImplementedError

    def decide_to_sell(self, observation: dict) -> dict:
        """Decides which property to sell.

        Args:
            observation: A dictionary representing the current state of the game.

        Returns:
            A dictionary representing the action to be taken.
        """
        player_properties = observation["game_state"].players[self.player_id].owned_properties
        if not player_properties:
            return {"type": "end_turn"}  # No properties to sell, declare bankruptcy

        properties_with_costs = [
            (p, observation["game_state"].board[p].cost) for p in player_properties
        ]
        
        # Sell the most expensive property to raise cash quickly
        property_to_sell = max(properties_with_costs, key=lambda item: item[1])
        return {"type": "sell", "tile_id": property_to_sell[0]}


class RandomAgent(BaseAgent):
    """A baseline agent that makes random decisions."""
    def decide_to_buy(self, observation: dict) -> dict:
        if self.random.choice([True, False]):
            return {"type": "buy"}
        else:
            return {"type": "skip_buy"}


class GreedyBuyer(BaseAgent):
    """An agent that buys any unowned property it lands on."""
    def decide_to_buy(self, observation: dict) -> dict:
        return {"type": "buy"}


class LLMAgent(BaseAgent):
    """An agent that uses a large language model to make decisions."""
    def act(self, observation: dict) -> dict:
        """Returns an action based on the current observation.

        Args:
            observation: A dictionary representing the current state of the game.

        Returns:
            A dictionary representing the action to be taken.
        """
        phase = observation["phase"]
        if phase == "roll":
            return {"type": "roll"}
        elif phase == "end_turn":
            return {"type": "end_turn"}
        
        if phase == "decide_to_sell":
            if not observation["game_state"].players[self.player_id].owned_properties:
                return {"type": "end_turn"}

        prompt = self._create_prompt(observation)
        print(prompt)
        try:
            response = get_llm_response(prompt, observation["game_state"])
            return response
        except Exception as e:
            print(e)
            # Fallback to random agent if LLM fails
            return RandomAgent(self.player_id).act(observation)

    def _create_prompt(self, observation: dict) -> str:
        """Creates a prompt for the language model based on the current observation."""
        game_state = observation["game_state"]
        player_state = game_state.players[self.player_id]
        board_state = game_state.board
        phase = observation["phase"]

        prompt = f"You are Player {self.player_id}. It is your turn and the phase is '{phase}'.\n\n"
        prompt += "Here is the current state of the game:\n"
        prompt += f"- Turn: {game_state.turn_number}\n"
        prompt += f"- Current Player: {game_state.current_player_id}\n\n"

        prompt += "Players:\n"
        for p_id, p_state in game_state.players.items():
            owned_properties = (
                [(board_state[p].name, f"${board_state[p].cost}") for p in p_state.owned_properties]
                if p_state.owned_properties else 'None'
            )
            prompt += f"- Player {p_id}: Cash: ${p_state.cash}, Position: {p_state.position}, Properties: {owned_properties}\n"
        prompt += "\n"

        # Organize properties by color set
        prompt += "Board by Color Set:\n"
        color_sets = {
            "brown": "Brown",
            "light_blue": "Light Blue",
            "pink": "Pink",
            "orange": "Orange",
            "red": "Red",
            "yellow": "Yellow",
            "green": "Green",
            "dark_blue": "Dark Blue"
        }
        
        # Group properties by color set
        properties_by_color = {}
        for tile in board_state:
            if hasattr(tile, 'color_set'):
                if tile.color_set not in properties_by_color:
                    properties_by_color[tile.color_set] = []
                properties_by_color[tile.color_set].append(tile)
        
        # Display properties by color set
        for color_set, display_name in color_sets.items():
            if color_set in properties_by_color:
                prompt += f"\n{display_name}:\n"
                for tile in properties_by_color[color_set]:
                    owner_info = f" (Owned by Player {tile.owner})" if tile.owner is not None else " (Unowned)"
                    prompt += f"- {tile.name}: ${tile.cost}{owner_info}\n"
        
        # Display non-property tiles separately
        prompt += "\nOther Tiles:\n"
        for tile in board_state:
            if not hasattr(tile, 'color_set'):
                if isinstance(tile, PropertyTile):  # For railroads and utilities
                    owner_info = f" (Owned by Player {tile.owner})" if tile.owner is not None else " (Unowned)"
                    prompt += f"- {tile.name}: ${tile.cost}{owner_info}\n"
                else:  # For non-property tiles like GO, Chance, etc.
                    prompt += f"- {tile.name}\n"
        prompt += "\n"

        if phase == "decide_to_buy":
            tile = board_state[player_state.position]
            prompt += f"You landed on '{tile.name}' which is unowned and costs ${tile.cost}. "
            prompt += "Would you like to buy it or skip?"
        
        elif phase == "decide_to_sell":
            prompt += f"You are in debt and need to sell a property to continue. "
            owned_properties = [(board_state[p].name, f"${board_state[p].cost}") for p in player_state.owned_properties]
            prompt += f"You own the following properties: {owned_properties if owned_properties else 'None'}. "
            prompt += "Which property should you sell?"

        return prompt
