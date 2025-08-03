

import random
from apis import get_llm_response
from tools import get_management_tools
from engine import PropertyTile, StreetTile, TaxTile, RailroadTile, has_monopoly_for_color_set

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


class DummyAgent(BaseAgent):
    """An agent that never buys any properties."""
    def decide_to_buy(self, observation: dict) -> dict:
        return {"type": "skip_buy"}


class LLMAgent(BaseAgent):
    """An agent that uses a large language model to make decisions."""

    def _get_buildable_properties(self, game_state, player_id):
        """Get list of properties that can be built on."""
        player_state = game_state.players[player_id]
        board_state = game_state.board
        buildable_properties = []
        
        for p_id in player_state.owned_properties:
            tile = board_state[p_id]
            if isinstance(tile, StreetTile) and tile.owner == player_id:
                # Check for monopoly
                color_set_tiles = [t for t in game_state.board if isinstance(t, StreetTile) and t.color_set == tile.color_set]
                monopoly_owned = all(t.owner == player_id for t in color_set_tiles)
                
                if monopoly_owned and tile.num_houses < 5:
                    # Check even building rule: can only build if this tile has the minimum houses in the set
                    min_houses_in_set = min(t.num_houses for t in color_set_tiles)
                    if tile.num_houses == min_houses_in_set:
                        buildable_properties.append(f"{tile.name} (Houses: {tile.num_houses}, Cost: ${tile.house_cost})")
        
        return buildable_properties

    def _get_allowed_tools(self, phase: str, buildable_properties: list) -> list:
        """Returns a list of allowed tool names for the given phase."""
        if phase == "decide_to_buy":
            return ["buy_property", "skip_buy_property"]
        elif phase == "decide_to_sell":
            return ["mortgage_property", "sell_house"]
        elif phase in ["start_management_phase", "end_management_phase"]:
            return get_management_tools(buildable_properties)
        elif phase == "decide_on_trade":
            return ["accept_trade", "reject_trade"]
        elif phase == "handle_mortgaged_trade":
            return ["resolve_mortgaged_trade"]
        elif phase == "auction_phase":
            return ["place_bid", "pass_auction"]
        elif phase == "end_turn":
            return ["end_turn"]
        return []

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
        if observation.get("logger"):
            observation.get("logger").log_custom(f"PROMPT: {prompt}")

        buildable_properties = self._get_buildable_properties(observation["game_state"], self.player_id)
        allowed_tools = self._get_allowed_tools(phase, buildable_properties)
        response = get_llm_response(prompt, observation["game_state"], allowed_tools, observation.get("logger"))
        self._update_history(response, observation)
        return response

    def _get_sellable_houses(self, game_state, player_id):
        """Get list of properties from which houses can be sold."""
        player_state = game_state.players[player_id]
        board_state = game_state.board
        sellable_houses = []

        # Group properties by color set
        color_sets = {}
        for p_id in player_state.owned_properties:
            tile = board_state[p_id]
            if isinstance(tile, StreetTile) and tile.num_houses > 0:
                if tile.color_set not in color_sets:
                    color_sets[tile.color_set] = []
                color_sets[tile.color_set].append(tile)

        # Check for even selling rule
        for color_set, properties in color_sets.items():
            max_houses_in_set = max(p.num_houses for p in properties)
            for prop in properties:
                if prop.num_houses == max_houses_in_set:
                    sellable_houses.append((prop.name, f"${prop.house_cost // 2}"))
        
        return sellable_houses

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

        prompt = f"You are Player {player_id}. You have ${player_state.cash}. It is your turn and the phase is '{phase}'."
        if game_state.history:
            prompt += "\nRecent events (in order of most recent to least recent):\n"
            for event in game_state.history[::-1]:
                prompt += f"- {event}\n"
            prompt += "\n"

        prompt += "Here is the current state of the Monopoly game:\n"
        prompt += f"- Turn: {game_state.turn_number}\n"
        prompt += f"- Current Player: {game_state.current_player_id}\n\n"

        prompt += "Players:\n"
        for p_id, p_state in game_state.players.items():
            if p_state.owned_properties:
                owned_properties = []
                for prop_id in p_state.owned_properties:
                    tile = board_state[prop_id]
                    detailed_info = format_detailed_property_info(tile, game_state)
                    owned_properties.append(f"{tile.name} {detailed_info}")
            else:
                owned_properties = 'None'
            
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
                    
                    # Add detailed status information
                    status_parts = []
                    if tile.mortgaged:
                        status_parts.append("MORTGAGED")
                    elif tile.owner is not None:
                        current_rent = calculate_current_rent(tile, game_state)
                        status_parts.append(f"Rent: ${current_rent}")
                    
                    if isinstance(tile, StreetTile):
                        if tile.num_houses > 0:
                            if tile.num_houses == 5:
                                status_parts.append("Hotel")
                            else:
                                status_parts.append(f"{tile.num_houses} Houses")
                        
                        # Check if it's part of a monopoly
                        if tile.owner is not None and has_monopoly_for_color_set(game_state, tile.owner, tile.color_set):
                            status_parts.append("MONOPOLY")
                    
                    status_info = f" [{', '.join(status_parts)}]" if status_parts else ""
                    prompt += f"- {tile.name}: ${tile.cost}{owner_info}{status_info}\n"
        
        prompt += "\nRailroads:\n"
        for tile in board_state:
            if isinstance(tile, RailroadTile):
                owner_info = f" (Owned by Player {tile.owner})" if tile.owner is not None else " (Unowned)"
                
                # Add detailed status information for railroads
                status_parts = []
                if tile.mortgaged:
                    status_parts.append("MORTGAGED")
                elif tile.owner is not None:
                    current_rent = calculate_railroad_rent(tile, game_state)
                    status_parts.append(f"Rent: ${current_rent}")
                
                status_info = f" [{', '.join(status_parts)}]" if status_parts else ""
                prompt += f"- {tile.name}: ${tile.cost}{owner_info}{status_info}\n"

        # Display non-property tiles separately
        prompt += "\nOther Tiles:\n"
        for tile in board_state:
            if not hasattr(tile, 'color_set') and not isinstance(tile, RailroadTile):
                if isinstance(tile, PropertyTile):  # For utilities
                    owner_info = f" (Owned by Player {tile.owner})" if tile.owner is not None else " (Unowned)"
                    
                    # Add detailed status information for railroads/utilities
                    status_parts = []
                    if tile.mortgaged:
                        status_parts.append("MORTGAGED")
                    elif tile.owner is not None:
                        current_rent = calculate_current_rent(tile, game_state)
                        status_parts.append(f"Rent: ${current_rent}")
                    
                    status_info = f" [{', '.join(status_parts)}]" if status_parts else ""
                    prompt += f"- {tile.name}: ${tile.cost}{owner_info}{status_info}\n"
                elif isinstance(tile, TaxTile):  # For tax tiles
                    prompt += f"- {tile.name}: Tax ${tile.rent}\n"
                else:  # For non-property tiles like GO, Chance, etc.
                    prompt += f"- {tile.name}\n"
        prompt += "\n"

        prompt += "Railroad rent is based on the number of railroads owned by the owner: 1 Railroad: $25, 2 Railroads: $50, 3 Railroads: $100, 4 Railroads: $200.\n"

        if phase == "decide_to_buy":
            tile = board_state[player_state.position]
            if hasattr(tile, 'cost'):
                prompt += f"You landed on '{tile.name}' which is unowned and costs ${tile.cost}. "
                prompt += "Would you like to buy it or skip? (YOU SHOULD SKIP)" # TODO: this is for testing, remove this line
            else:
                # This shouldn't happen - non-property tiles shouldn't trigger decide_to_buy phase
                prompt += f"You landed on '{tile.name}'. This tile is not purchasable. "
                prompt += "You should proceed to the next phase."
        
        elif phase == "decide_to_sell":
            prompt += f"You are in debt and need to raise cash. You can sell houses or mortgage properties.\n"
            prompt += "Houses must be sold evenly across a color group. You can only sell from the properties with the most houses in a color group.\n"
            prompt += "You may only mortgage a property if there are no buildings on any properties in that color group. You do not have to sell houses from other color groups in order to mortgage.\n"

            sellable_houses = self._get_sellable_houses(game_state, player_id)
            if sellable_houses:
                prompt += "You can sell the following houses (Property, Sell Value):\n"
                for prop_name, sell_value in sellable_houses:
                    prompt += f"- {prop_name}: Sell for {sell_value}\n"
            else:
                prompt += "You have no houses to sell.\n"

            mortgageable_properties = []
            for p_id in player_state.owned_properties:
                tile = board_state[p_id]
                if not tile.mortgaged:
                    # Check if the property is a street and has houses
                    if isinstance(tile, StreetTile) and tile.num_houses > 0:
                        continue
                    
                    # Check if any other property in the same color group has houses
                    if isinstance(tile, StreetTile):
                        color_set_tiles = [t for t in board_state if isinstance(t, StreetTile) and t.color_set == tile.color_set]
                        if any(t.owner == player_id and t.num_houses > 0 for t in color_set_tiles):
                            continue

                    mortgageable_properties.append((tile.name, f"${tile.cost}", f"${tile.cost // 2}"))

            if mortgageable_properties:
                prompt += "You can mortgage the following properties (Property, Cost, Mortgage Value):\n"
                for prop_name, cost, mortgage_value in mortgageable_properties:
                    prompt += f"- {prop_name}: Cost {cost}, Mortgage for {mortgage_value}\n"
            else:
                prompt += "You have no properties to mortgage.\n"
            
            prompt += "What would you like to do?"
        
        elif phase in ["start_management_phase", "end_management_phase"]:
            prompt += """\nYou are in the management phase. This is your opportunity to make strategic decisions.

Consider your current situation:
- Do you have any monopolies (complete color sets) where you could build houses?
- Are there strategic trades that would help you complete monopolies?
- Would it be better to save your cash for upcoming property purchases?

Your options:
1. PROCEED: Move to the dice roll phase if no immediate strategic actions are needed. You should generally default to this option UNLESS you have a great reason to do something else.
2. PROPOSE A TRADE: Offer a mutually beneficial deal to complete monopolies or gain strategic properties. If you propose a trade, ensure that both players have the sufficient cash and properties to complete the trade. If you have already proposed a trade and it has been rejected, you should propose a better trade deal for the trade recipient or proceed to the next phase.
3. BUILD HOUSES: If you own complete color sets, consider building to increase rent income. You MUST also have enough cash to build. Houses must be built evenly on a group of properties: e.g., a second house cannot be built on any property within a group until all of them have their first house.

Strategic guidelines:
- Completing monopolies is crucial - they allow building and charge much higher rent
- Early game: Focus on acquiring properties and completing cheaper monopolies
- Mid game: Build houses on monopolies to generate income
- Late game: Make strategic trades to gain decisive advantages
- Trading: If your trade has been rejected previously (see "Recent events"), you should either propose a better trade deal for the trade recipient or proceed to the next phase.

Choose ONE action that best fits your current strategy and game position. Think about what will help you win in the long term."""
            
            prompt += f" You have {1 - game_state.trades_proposed_this_turn} trades left in this turn.\n" # TODO: change this to 3

            # Add building information using the helper method
            buildable_properties = self._get_buildable_properties(game_state, player_id)
            
            if buildable_properties:
                prompt += "\nHere are the ONLY properties you can build on:\n"
                for prop in buildable_properties:
                    prompt += f"- {prop}\n"
                prompt += """\nIMPORTANT: You must follow the even building rule! You can ONLY build on properties that have the minimum number of houses in their color set. 

The system will reject any invalid building attempts. Look at the "Properties you can build on" list and ONLY choose from those options."""
            else:
                prompt += "\nNo properties to build on at this time.\n"

        elif phase == "decide_on_trade":
            trade = game_state.pending_trade
            from_player_id = trade['from_player']
            offer_cash = trade['offer']['cash']
            offer_properties = [board_state[p].name for p in trade['offer']['properties']]
            request_cash = trade['request']['cash']
            request_properties = [board_state[p].name for p in trade['request']['properties']]
            prompt += f"Player {from_player_id} has proposed a trade. They are offering ${offer_cash} and the properties {offer_properties} in exchange for ${request_cash} and the properties {request_properties}.\n\n"
            
            # TODO: Remove the "YOU SHOULD ACCEPT THIS TRADE." line
            prompt += (
                "Consider this trade carefully:\n\n"
                "ACCEPT if the trade:\n"
                "- Helps you complete a monopoly (full color set) - this is usually the most valuable outcome\n"
                "- Gives you properties that prevent opponents from completing monopolies\n"
                "- Provides fair value exchange (consider property costs, rent potential, and strategic position)\n"
                "- Helps you gain a strategic advantage in the game\n\n"
                "REJECT if the trade:\n"
                "- Helps your opponent complete a monopoly more than it helps you\n"
                "- Gives away properties that are key to your own monopoly potential\n"
                "- Provides unfair value (you're giving significantly more than you're receiving)\n"
                "- Weakens your strategic position without clear benefit\n\n"
                "Key considerations:\n"
                "- Monopolies are the most powerful asset in Monopoly - they allow building and charge much higher rent\n"
                "- Properties that complete color sets are worth much more than their purchase price\n"
                "- Consider the long-term impact: will this trade help you or your opponent win?\n"
                "- Think about rent potential: developed monopolies generate massive income\n"
                "- Early properties (cheaper color sets) can be more valuable than expensive individual properties\n\n"
                "Do you accept or reject this trade?"
            )
            tile_id = game_state.mortgaged_properties_to_handle[0]            
            tile = game_state.board[tile_id]            
            prompt += f"You have received the mortgaged property '{tile.name}' in a trade. You must choose how to handle the mortgage.\n"            
            prompt += f"The mortgage value is ${tile.cost // 2}.\n"            
            prompt += f"You can either unmortgage it now for ${int((tile.cost // 2) * 1.1)}, or pay the 10% interest (${int((tile.cost // 2) * 0.1)}) and keep it mortgaged."        
        elif phase == "auction_phase":            
            auction_state = game_state.auction_state            
            tile = game_state.board[auction_state["tile_id"]]            
            prompt += f"An auction is being held for the property '{tile.name}'.\n"            
            prompt += f"The current bid is ${auction_state['current_bid']}.\n"            
            prompt += f"The active bidders are: {auction_state['active_bidders']}.\n"            
            prompt += "You can either place a higher bid or pass. You should consider bidding if the property helps you complete a color set or if winning it would block another player from completing theirs. However, be cautious not to overbid—spending too much can leave you cash-poor and vulnerable, especially early in the game. If the property is not critical to your strategy or if the cost would leave you with little flexibility, it's often better to pass. Also consider whether passing would allow another player to cheaply complete a dangerous monopoly."        
        return prompt

    def _update_history(self, action: dict, observation: dict):
        """Updates the agent's history with a summary of the action."""
        game_state = observation["game_state"]
        player_id = self.player_id
        action_type = action.get("type")

        if action_type == "buy":
            tile = game_state.board[game_state.players[player_id].position]
            event = f"Player {player_id} bought {tile.name} for ${tile.cost}"
        elif action_type == "build_house":
            tile = game_state.board[action["tile_id"]]
            event = f"Player {player_id} built 1 house on {tile.name}"
        elif action_type == "mortgage_property":
            tile = game_state.board[action["tile_id"]]
            event = f"Player {player_id} mortgaged {tile.name} for ${tile.cost // 2}"
        elif action_type == "unmortgage_property":
            tile = game_state.board[action["tile_id"]]
            event = f"Player {player_id} unmortgaged {tile.name} for ${int((tile.cost // 2) * 1.1)}"
        elif action_type == "propose_trade":
            offer_cash = action["offer"]["cash"]
            offer_properties = [game_state.board[p].name for p in action["offer"]["properties"]]
            request_cash = action["request"]["cash"]
            request_properties = [game_state.board[p].name for p in action["request"]["properties"]]
            
            # Format: Player X proposes to Player Y: X gives [items] → Y gives [items]
            offer_items = []
            if offer_cash > 0:
                offer_items.append(f"${offer_cash}")
            if offer_properties:
                offer_items.extend(offer_properties)
            
            request_items = []
            if request_cash > 0:
                request_items.append(f"${request_cash}")
            if request_properties:
                request_items.extend(request_properties)
            
            offer_str = ", ".join(offer_items) if offer_items else "nothing"
            request_str = ", ".join(request_items) if request_items else "nothing"
            
            event = f"Player {player_id} proposed trade to Player {action['to_player']}: Player {player_id} gives {offer_str} → Player {action['to_player']} gives {request_str}"
            
        elif action_type == "accept_trade":
            trade = game_state.pending_trade
            from_player_id = trade['from_player']
            offer_cash = trade['offer']['cash']
            offer_properties = [game_state.board[p].name for p in trade['offer']['properties']]
            request_cash = trade['request']['cash']
            request_properties = [game_state.board[p].name for p in trade['request']['properties']]
            
            # Format what each player is giving/getting
            giver_items = []
            if offer_cash > 0:
                giver_items.append(f"${offer_cash}")
            if offer_properties:
                giver_items.extend(offer_properties)
            
            receiver_items = []
            if request_cash > 0:
                receiver_items.append(f"${request_cash}")
            if request_properties:
                receiver_items.extend(request_properties)
            
            giver_str = ", ".join(giver_items) if giver_items else "nothing"
            receiver_str = ", ".join(receiver_items) if receiver_items else "nothing"
            
            event = f"Player {player_id} ACCEPTED trade: Player {from_player_id} gives {giver_str} → Player {player_id} gives {receiver_str}"
            
        elif action_type == "reject_trade":
            trade = game_state.pending_trade
            from_player_id = trade['from_player']
            event = f"Player {player_id} REJECTED trade from Player {from_player_id}"
        elif action_type == "resolve_mortgaged_trade":
            tile = game_state.board[action["tile_id"]]
            decision = action["decision"]
            if decision == "unmortgage_now":
                event = f"Player {player_id} chose to unmortgage {tile.name} immediately."
            else:
                event = f"Player {player_id} chose to pay interest on {tile.name} and keep it mortgaged."
            
        else:
            return # Don't record other actions

        game_state.history.append(event)
        if len(game_state.history) > game_state.MAX_HISTORY:
            game_state.history.pop(0)


def calculate_current_rent(tile, game_state):
    """Calculate the current rent for a property based on its state.
    
    Args:
        tile: Property tile to calculate rent for
        game_state: Current game state
        
    Returns:
        int: Current rent amount
    """
    if tile.mortgaged or tile.owner is None:
        return 0
    
    rent = tile.rent
    if isinstance(tile, StreetTile):
        monopoly = has_monopoly_for_color_set(game_state, tile.owner, tile.color_set)
        if monopoly:
            if tile.num_houses == 0:
                rent = tile.rent_monopoly
            elif tile.num_houses == 1:
                rent = tile.rent_one_house
            elif tile.num_houses == 2:
                rent = tile.rent_two_houses
            elif tile.num_houses == 3:
                rent = tile.rent_three_houses
            elif tile.num_houses == 4:
                rent = tile.rent_four_houses
            elif tile.num_houses == 5:  # Hotel
                rent = tile.rent_hotel
    
    return rent

def format_detailed_property_info(tile, game_state):
    """Format detailed information about a property for display.
    
    Args:
        tile: Property tile to format
        game_state: Current game state
        
    Returns:
        str: Formatted property information
    """
    info_parts = [f"${tile.cost}"]
    
    if tile.mortgaged:
        info_parts.append("MORTGAGED")
    else:
        if isinstance(tile, RailroadTile):
            current_rent = calculate_railroad_rent(tile, game_state)
        else:
            current_rent = calculate_current_rent(tile, game_state)
        info_parts.append(f"Rent: ${current_rent}")
    
    if isinstance(tile, StreetTile):
        if tile.num_houses > 0:
            if tile.num_houses == 5:
                info_parts.append("Hotel")
            else:
                info_parts.append(f"{tile.num_houses} Houses")
        
        # Check if it's part of a monopoly
        if has_monopoly_for_color_set(game_state, tile.owner, tile.color_set):
            info_parts.append("MONOPOLY")
    
    elif isinstance(tile, RailroadTile):
        # Check if player owns all 4 railroads
        owned_railroads = sum(1 for t in game_state.board 
                             if isinstance(t, RailroadTile) and t.owner == tile.owner)
        if owned_railroads == 4:
            info_parts.append("ALL RAILROADS")
    
    return f"({', '.join(info_parts)})"

def calculate_railroad_rent(tile, game_state):
    """Calculate the current rent for a railroad based on how many railroads the owner has.
    
    Args:
        tile: Railroad tile to calculate rent for
        game_state: Current game state
        
    Returns:
        int: Current rent amount
    """
    if tile.mortgaged or tile.owner is None:
        return 0
    
    # Count how many railroads this player owns
    owned_railroads = sum(1 for t in game_state.board 
                         if isinstance(t, RailroadTile) and t.owner == tile.owner)
    
    # Railroad rent based on number owned: 1=$25, 2=$50, 3=$100, 4=$200
    rent_schedule = {1: 25, 2: 50, 3: 100, 4: 200}
    return rent_schedule.get(owned_railroads, 0)
