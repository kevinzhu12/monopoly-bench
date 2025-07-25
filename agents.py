

import random
from apis import get_llm_response, decide_to_sell_tools, decide_to_buy_tools, management_tools, trade_recipient_tools
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
        if phase in ["start_management_phase", "end_management_phase"]:
            return self.management_phase(observation)
        elif phase == "decide_to_buy":
            return self.decide_to_buy(observation)
        elif phase == "decide_to_sell":
            return self.decide_to_sell(observation)
        elif phase == "roll_phase":
            return {"type": "roll"}
        elif phase == "decide_on_trade":
            return self.decide_on_trade(observation)
        else:
            return {"type": "end_turn"}

    def management_phase(self, observation: dict) -> dict:
        """Decides on management actions like trading, building, or mortgaging."""
        return {"type": "proceed"}

    def decide_on_trade(self, observation: dict) -> dict:
        """Decides whether to accept or reject a trade offer."""
        return {"type": "reject_trade"}

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

    def decide_on_trade(self, observation: dict) -> dict:
        # This will override BaseAgent's decide_on_trade
        return {"type": "accept_trade" if self.random.choice([True, False]) else "reject_trade"}


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
        if phase == "roll_phase":
            return {"type": "roll"}
        elif phase == "end_turn":
            return {"type": "end_turn"}
        
        prompt = self._create_prompt(observation)
        # print(prompt)
        
        if phase == "decide_to_sell":
            if not observation["game_state"].players[self.player_id].owned_properties:
                return {"type": "end_turn"}
            response = get_llm_response(prompt, observation["game_state"], decide_to_sell_tools)
            return response
        
        elif phase == "decide_to_buy":
            response = get_llm_response(prompt, observation["game_state"], decide_to_buy_tools)
            return response
        
        elif phase in ["start_management_phase", "end_management_phase"]:
            response = get_llm_response(prompt, observation["game_state"], management_tools)
            return response
        
        elif phase == "decide_on_trade":
            response = get_llm_response(prompt, observation["game_state"], trade_recipient_tools)
            return response

    def _create_prompt(self, observation: dict) -> str:
        """Creates a prompt for the language model based on the current observation."""
        game_state = observation["game_state"]
        board_state = game_state.board
        phase = observation["phase"]

        if phase == "decide_on_trade":
            player_id = game_state.decision_player_id
        else:
            player_id = self.player_id

        player_state = game_state.players[player_id]

        prompt = f"You are Player {player_id}. It is your turn and the phase is '{phase}'.\n\n"
        prompt += "Here is the current state of the Monopoly game:\n"
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
        
        # Group properties by color
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
        
        elif phase in ["start_management_phase", "end_management_phase"]:
            prompt += "You are in the management phase. You can propose a trade, build houses, mortgage properties, or proceed to the next phase."
        
        elif phase == "decide_on_trade":
            trade = game_state.pending_trade
            from_player_id = trade['from_player']
            offer_cash = trade['offer']['cash']
            offer_properties = [board_state[p].name for p in trade['offer']['properties']]
            request_cash = trade['request']['cash']
            request_properties = [board_state[p].name for p in trade['request']['properties']]
            prompt += f"Player {from_player_id} has proposed a trade. They are offering ${offer_cash} and the properties {offer_properties} in exchange for ${request_cash} and the properties {request_properties}. Do you accept or reject?"

        return prompt

