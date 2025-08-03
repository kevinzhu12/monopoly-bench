
import random

# Game phase constants
class GamePhase:
    START_MANAGEMENT = "start_management_phase"
    END_MANAGEMENT = "end_management_phase"
    ROLL_PHASE = "roll_phase"
    DECIDE_TO_BUY = "decide_to_buy"
    DECIDE_TO_SELL = "decide_to_sell"
    DECIDE_ON_TRADE = "decide_on_trade"
    HANDLE_MORTGAGED_TRADE = "handle_mortgaged_trade"
    AUCTION_PHASE = "auction_phase"
    END_TURN = "end_turn"
    GAME_OVER = "game_over"

class BaseTile:
    """Base class for all tiles on the board."""
    def __init__(self, tile_id, name, type):
        self.tile_id = tile_id
        self.name = name
        self.type = type

class PropertyTile(BaseTile):
    """Represents an ownable property tile."""
    def __init__(self, tile_id, name, type, cost, rent):
        super().__init__(tile_id, name, type)
        self.cost = cost
        self.rent = rent
        self.owner = None
        self.mortgaged = False

class StreetTile(PropertyTile):
    """Represents a street property."""
    def __init__(self, tile_id, name, type, cost, rent, color_set, rent_one_house, rent_two_houses, rent_three_houses, rent_four_houses, rent_hotel, house_cost, mortgage):
        super().__init__(tile_id, name, type, cost, rent)
        self.color_set = color_set
        self.rent_monopoly = rent * 2
        self.rent_one_house = rent_one_house
        self.rent_two_houses = rent_two_houses
        self.rent_three_houses = rent_three_houses
        self.rent_four_houses = rent_four_houses
        self.rent_hotel = rent_hotel
        self.house_cost = house_cost
        self.mortgage = mortgage
        self.num_houses = 0

class RailroadTile(PropertyTile):
    """Represents a railroad property."""
    pass

class UtilityTile(PropertyTile):
    """Represents a utility property."""
    pass

class TaxTile(BaseTile):
    """Represents a tax space."""
    def __init__(self, tile_id, name, type, rent):
        super().__init__(tile_id, name, type)
        self.rent = rent

class OtherTile(BaseTile):
    """Represents a free parking space."""
    pass

class ActionTile(BaseTile):
    """Represents a Chance or Community Chest space."""
    pass

class Player:
    def __init__(self, player_id, cash):
        self.player_id = player_id
        self.cash = cash
        self.position = 0
        self.owned_properties = []
        self.debt = 0
        self.creditor_id = None

class GameState:
    """Represents the state of the Monopoly game."""
    def __init__(self, num_players, tile_data, max_turns=1000, starting_cash=1500):
        """Initializes the game state."""
        self.turn_number = 0
        self.players = {i: Player(i, starting_cash) for i in range(num_players)}
        self.board = self._create_board(tile_data)
        self.current_player_id = 0
        self.game_over = False
        self.max_turns = max_turns
        self.player_order = list(range(num_players))
        self.current_player_index = 0
        self.phase = GamePhase.START_MANAGEMENT
        self.pending_trade = None
        self.decision_player_id = None
        self.pre_trade_phase = None
        self.pre_mortgage_phase = None
        self.mortgaged_properties_to_handle = []
        self.auction_state = None
        self.history = []
        self.MAX_HISTORY = 10
        self.trades_proposed_this_turn = 0

    def _create_board(self, tile_data):
        """Creates the game board from tile data."""
        board = []
        for i, data in enumerate(tile_data):
            tile_type = data["type"]
            if tile_type == "street":
                board.append(StreetTile(i, **data))
            elif tile_type == "railroad":
                board.append(RailroadTile(i, **data))
            elif tile_type == "utility":
                board.append(UtilityTile(i, **data))
            elif tile_type == "tax":
                board.append(TaxTile(i, **data))
            elif tile_type == "other":
                board.append(OtherTile(i, **data))
            elif tile_type == "action":
                board.append(ActionTile(i, **data))
        return board

def step(game_state, action, logger=None):
    """Processes a single action and updates the game state."""
    current_player_id = game_state.current_player_id
    player = game_state.players[current_player_id]
    action_type = action["type"]

    if action_type == "proceed":
        return handle_proceed_action(game_state)
    elif action_type == "roll":
        return handle_roll_action(game_state, player)
    elif action_type == "buy":
        return handle_buy_action(game_state, player)
    elif action_type == "skip_buy":
        return handle_skip_buy_action(game_state)
    elif action_type == "mortgage_property":
        return handle_mortgage_property_action(game_state, action, player)
    elif action_type == "unmortgage_property":
        return handle_unmortgage_property_action(game_state, action, player)
    elif action_type == "sell_house":
        return handle_sell_house_action(game_state, action, player)
    elif action_type == "propose_trade":
        return handle_propose_trade_action(game_state, action)
    elif action_type == "accept_trade":
        return handle_accept_trade_action(game_state, logger)
    elif action_type == "reject_trade":
        return handle_reject_trade_action(game_state)
    elif action_type == "resolve_mortgaged_trade":
        return handle_resolve_mortgaged_trade_action(game_state, action)
    elif action_type == "build_house":
        return handle_build_house_action(game_state, action, logger)
    elif action_type == "place_bid":
        return handle_auction_action(game_state, action, player)
    elif action_type == "pass_auction":
        return handle_auction_action(game_state, action, player)
    elif action_type == "end_turn":
        return handle_end_turn_action(game_state, player)

def handle_landing_on_property(player, tile, game_state):
    """Handle when a player lands on a property tile."""
    if tile.owner is None and tile.cost > 0:
        return GamePhase.DECIDE_TO_BUY
    elif tile.owner is not None and tile.owner != player.player_id and not tile.mortgaged:
        rent = tile.rent
        if isinstance(tile, StreetTile):
            color_set = tile.color_set
            monopoly = has_monopoly_for_color_set(game_state, tile.owner, color_set)
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
                elif tile.num_houses == 5: # 5 houses means a hotel
                    rent = tile.rent_hotel
        elif isinstance(tile, RailroadTile):
            # Calculate railroad rent based on number owned: 1=$25, 2=$50, 3=$100, 4=$200
            owned_railroads = sum(1 for t in game_state.board 
                                 if isinstance(t, RailroadTile) and t.owner == tile.owner)
            rent_schedule = {1: 25, 2: 50, 3: 100, 4: 200}
            rent = rent_schedule.get(owned_railroads, 0)

        if player.cash >= rent:
            player.cash -= rent
            game_state.players[tile.owner].cash += rent
            return GamePhase.END_MANAGEMENT
        else:
            amount_paid = player.cash
            player.cash = 0
            game_state.players[tile.owner].cash += amount_paid
            player.debt = rent - amount_paid
            player.creditor_id = tile.owner

            if not get_mortgageable_properties(player, game_state):
                return GamePhase.END_TURN

            return GamePhase.DECIDE_TO_SELL
    return GamePhase.END_MANAGEMENT

def get_mortgageable_properties(player, game_state):
    """Returns a list of mortgageable properties for a player."""
    return [p for p in player.owned_properties if not game_state.board[p].mortgaged and not (isinstance(game_state.board[p], StreetTile) and game_state.board[p].num_houses > 0)]

def is_trade_valid(trade, from_player, to_player):
    """Validate if a trade can be executed between two players.
    
    Args:
        trade: Dictionary containing trade details with 'offer' and 'request'
        from_player: Player object making the offer
        to_player: Player object receiving the offer
        
    Returns:
        bool: True if trade is valid, False otherwise
    """
    # Check if offering player has enough cash
    if from_player.cash < trade["offer"]["cash"]:
        return False
    
    # Check if offering player owns all properties they're offering
    for tile_id in trade["offer"]["properties"]:
        if tile_id not in from_player.owned_properties:
            return False
    
    # Check if receiving player has enough cash
    if to_player.cash < trade["request"]["cash"]:
        return False
    
    # Check if receiving player owns all properties they're trading away
    for tile_id in trade["request"]["properties"]:
        if tile_id not in to_player.owned_properties:
            return False
    
    return True

def add_to_history(game_state, event):
    """Add an event to the game history with automatic length management."""
    game_state.history.append(event)
    if len(game_state.history) > game_state.MAX_HISTORY:
        game_state.history.pop(0)

def handle_debt_payment(game_state, player):
    if player.cash >= player.debt:
        player.cash -= player.debt
        if player.creditor_id is not None:
            game_state.players[player.creditor_id].cash += player.debt
        player.debt = 0
        player.creditor_id = None
        game_state.phase = game_state.pre_mortgage_phase
        game_state.pre_mortgage_phase = None
        return game_state.phase
    else: # player is still in debt
        if not get_mortgageable_properties(player, game_state):
            return GamePhase.END_TURN
        else:
            return GamePhase.DECIDE_TO_SELL

def has_monopoly_for_color_set(game_state, player_id, color_set):
    """Check if a player owns all properties in a specific color set.
    
    Args:
        game_state: GameState object containing the game state
        player_id: ID of the player to check monopoly for
        color_set: The color set to check (e.g., "brown", "light_blue", etc.)
        
    Returns:
        bool: True if player owns all properties in the color set, False otherwise
    """
    color_set_tiles = [t for t in game_state.board if isinstance(t, StreetTile) and t.color_set == color_set]
    return all(t.owner == player_id for t in color_set_tiles)

def log_failure_and_return_phase(game_state, message, logger=None, phase=GamePhase.END_MANAGEMENT):
    """Log a failure event and return specified phase.
    
    Args:
        game_state: GameState object containing the game state
        message: Failure message to log
        logger: Optional logger instance
        phase: Phase to return (defaults to END_MANAGEMENT)
        
    Returns:
        str: The specified game phase
    """
    add_to_history(game_state, message)
    if logger:
        logger.log_custom(message)
    game_state.phase = phase
    return phase

def handle_buy_action(game_state, player):
    """Handle the buy property action.
    
    Args:
        game_state: GameState object containing the game state
        player: Player object attempting to buy the property
        
    Returns:
        str: The next game phase ("end_management_phase")
    """
    tile = game_state.board[player.position]
    if isinstance(tile, PropertyTile) and tile.owner is None and player.cash >= tile.cost:
        player.cash -= tile.cost
        tile.owner = player.player_id
        player.owned_properties.append(tile.tile_id)
    return GamePhase.END_MANAGEMENT

def handle_proceed_action(game_state):
    """Handle the proceed action to advance game phases.
    
    Args:
        game_state: GameState object containing the game state
        
    Returns:
        str: The current game phase after proceeding
    """
    if game_state.phase == GamePhase.START_MANAGEMENT:
        game_state.phase = GamePhase.ROLL_PHASE
    elif game_state.phase == GamePhase.END_MANAGEMENT:
        game_state.phase = GamePhase.END_TURN
    return game_state.phase

def handle_skip_buy_action(game_state):
    """Handle the skip buy action.
    
    Args:
        game_state: GameState object containing the game state
        
    Returns:
        str: The next game phase ("auction_phase")
    """
    tile_to_auction = game_state.board[game_state.players[game_state.current_player_id].position]
    game_state.auction_state = {
        "tile_id": tile_to_auction.tile_id,
        "current_bid": 0,
        "high_bidder": None,
        "active_bidders": list(game_state.players.keys()),
        "last_bidder": None,
    }
    return GamePhase.AUCTION_PHASE

def handle_mortgage_property_action(game_state, action, player):
    """Handle the mortgage property action.
    
    Args:
        game_state: GameState object containing the game state
        action: Dictionary containing the action details
        player: Player object mortgaging the property
        
    Returns:
        str: The next game phase
    """
    # Don't set pre_mortgage_phase to "decide_to_sell" to avoid infinite loop
    if game_state.phase == GamePhase.DECIDE_TO_SELL:
        game_state.pre_mortgage_phase = GamePhase.END_MANAGEMENT
    else:
        game_state.pre_mortgage_phase = game_state.phase
        
    tile_to_mortgage = game_state.board[action["tile_id"]]
    if tile_to_mortgage.owner == player.player_id and not tile_to_mortgage.mortgaged:
        player.cash += tile_to_mortgage.cost // 2
        tile_to_mortgage.mortgaged = True

    next_phase = handle_debt_payment(game_state, player)
    return next_phase

def handle_unmortgage_property_action(game_state, action, player):
    """Handle the unmortgage property action.
    
    Args:
        game_state: GameState object containing the game state
        action: Dictionary containing the action details
        player: Player object unmortgaging the property
        
    Returns:
        str: The next game phase ("end_management_phase")
    """
    tile_to_unmortgage = game_state.board[action["tile_id"]]
    unmortgage_cost = int((tile_to_unmortgage.cost // 2) * 1.1)
    if tile_to_unmortgage.owner == player.player_id and tile_to_unmortgage.mortgaged and player.cash >= unmortgage_cost:
        player.cash -= unmortgage_cost
        tile_to_unmortgage.mortgaged = False
    return GamePhase.END_MANAGEMENT

def handle_sell_house_action(game_state, action, player):
    """Handle the sell house action.
    
    Args:
        game_state: GameState object containing the game state
        action: Dictionary containing the action details
        player: Player object selling the house
        
    Returns:
        str: The next game phase
    """
    # Don't set pre_mortgage_phase to "decide_to_sell" to avoid infinite loop
    if game_state.phase == GamePhase.DECIDE_TO_SELL:
        game_state.pre_mortgage_phase = GamePhase.END_MANAGEMENT
    else:
        game_state.pre_mortgage_phase = game_state.phase
        
    tile_to_sell_from = game_state.board[action["tile_id"]]
    if isinstance(tile_to_sell_from, StreetTile) and tile_to_sell_from.owner == player.player_id and tile_to_sell_from.num_houses > 0:
        # Check for even selling
        color_set_tiles = [t for t in game_state.board if isinstance(t, StreetTile) and t.color_set == tile_to_sell_from.color_set and t.owner == player.player_id]
        max_houses = max(t.num_houses for t in color_set_tiles)
        if tile_to_sell_from.num_houses == max_houses:
            player.cash += tile_to_sell_from.house_cost // 2
            tile_to_sell_from.num_houses -= 1

    next_phase = handle_debt_payment(game_state, player)
    return next_phase

def handle_propose_trade_action(game_state, action):
    """Handle the propose trade action.
    
    Args:
        game_state: GameState object containing the game state
        action: Dictionary containing the action details
        
    Returns:
        str: The next game phase
    """
    if game_state.trades_proposed_this_turn >= 1: # TODO: change this to 3
        return GamePhase.END_MANAGEMENT
    
    game_state.trades_proposed_this_turn += 1
    game_state.pre_trade_phase = game_state.phase
    game_state.pending_trade = {
        "from_player": game_state.current_player_id,
        "to_player": action["to_player"],
        "offer": action["offer"],
        "request": action["request"],
    }
    game_state.decision_player_id = action["to_player"]
    return GamePhase.DECIDE_ON_TRADE

def handle_accept_trade_action(game_state, logger):
    """Handle the accept trade action.
    
    Args:
        game_state: GameState object containing the game state
        logger: Logger object for logging events
        
    Returns:
        str: The next game phase
    """
    trade = game_state.pending_trade
    from_player = game_state.players[trade["from_player"]]
    to_player = game_state.players[trade["to_player"]]

    if not is_trade_valid(trade, from_player, to_player):
        game_state.pending_trade = None
        game_state.phase = game_state.pre_trade_phase
        game_state.pre_trade_phase = None
        game_state.decision_player_id = None
        failure_event = f"Trade failed due to insufficient assets."
        add_to_history(game_state, failure_event)
        if logger:
            logger.log_custom(failure_event)
        return game_state.phase

    from_player.cash -= trade["offer"]["cash"]
    to_player.cash += trade["offer"]["cash"]
    from_player.cash += trade["request"]["cash"]
    to_player.cash -= trade["request"]["cash"]

    for tile_id in trade["offer"]["properties"]:
        from_player.owned_properties.remove(tile_id)
        to_player.owned_properties.append(tile_id)
        game_state.board[tile_id].owner = trade["to_player"]
        if game_state.board[tile_id].mortgaged:
            game_state.mortgaged_properties_to_handle.append(tile_id)

    for tile_id in trade["request"]["properties"]:
        to_player.owned_properties.remove(tile_id)
        from_player.owned_properties.append(tile_id)
        game_state.board[tile_id].owner = trade["from_player"]

    if game_state.mortgaged_properties_to_handle:
        game_state.phase = "handle_mortgaged_trade"
        game_state.decision_player_id = to_player.player_id
    else:
        game_state.pending_trade = None
        game_state.phase = game_state.pre_trade_phase
        game_state.pre_trade_phase = None
        game_state.decision_player_id = None
    
    return game_state.phase

def handle_reject_trade_action(game_state):
    """Handle the reject trade action.
    
    Args:
        game_state: GameState object containing the game state
        
    Returns:
        str: The next game phase
    """
    game_state.pending_trade = None
    game_state.phase = game_state.pre_trade_phase
    game_state.pre_trade_phase = None
    game_state.decision_player_id = None
    return game_state.phase

def handle_resolve_mortgaged_trade_action(game_state, action):
    """Handle the resolve mortgaged trade action.
    
    Args:
        game_state: GameState object containing the game state
        action: Dictionary containing the action details
        
    Returns:
        str: The next game phase
    """
    tile_id = action["tile_id"]
    decision = action["decision"]
    tile = game_state.board[tile_id]
    player = game_state.players[game_state.decision_player_id]

    if decision == "unmortgage_now":
        unmortgage_cost = int((tile.cost // 2) * 1.1)
        if player.cash >= unmortgage_cost:
            player.cash -= unmortgage_cost
            tile.mortgaged = False
    elif decision == "pay_interest_only":
        interest_cost = int((tile.cost // 2) * 0.1)
        if player.cash >= interest_cost:
            player.cash -= interest_cost

    game_state.mortgaged_properties_to_handle.remove(tile_id)

    if not game_state.mortgaged_properties_to_handle:
        game_state.pending_trade = None
        game_state.phase = game_state.pre_trade_phase
        game_state.pre_trade_phase = None
        game_state.decision_player_id = None
    
    return game_state.phase

def handle_build_house_action(game_state, action, logger):
    """Handle the build house action.
    
    Args:
        game_state: GameState object containing the game state
        action: Dictionary containing the action details
        logger: Logger object for logging events
        
    Returns:
        str: The next game phase ("end_management_phase")
    """
    current_player_id = game_state.current_player_id
    player = game_state.players[current_player_id]
    tile_id = action["tile_id"]
    tile = game_state.board[tile_id]

    # Check if it's a street tile and owned by the current player
    if not isinstance(tile, StreetTile) or tile.owner != current_player_id:
        failure_message = f"Player {current_player_id} failed to build on {tile.name} (not owned or not a street)"
        return log_failure_and_return_phase(game_state, failure_message, logger)

    # Check for monopoly
    monopoly_owned = has_monopoly_for_color_set(game_state, current_player_id, tile.color_set)
    if not monopoly_owned:
        failure_message = f"Player {current_player_id} failed to build on {tile.name} (no monopoly on {tile.color_set})"
        return log_failure_and_return_phase(game_state, failure_message, logger)

    # Check for even build rule
    color_set_tiles = [t for t in game_state.board if isinstance(t, StreetTile) and t.color_set == tile.color_set]
    current_houses_on_set = [t.num_houses for t in color_set_tiles]
    if tile.num_houses > min(current_houses_on_set):
        failure_message = f"Player {current_player_id} failed to build on {tile.name} (violates even building rule)"
        return log_failure_and_return_phase(game_state, failure_message, logger)

    # Check for max houses (4 houses or 1 hotel)
    if tile.num_houses >= 5:
        failure_message = f"Player {current_player_id} failed to build on {tile.name} (already has hotel/max houses)"
        return log_failure_and_return_phase(game_state, failure_message, logger)

    # Check cash
    if player.cash < tile.house_cost:
        failure_message = f"Player {current_player_id} failed to build on {tile.name} (insufficient cash: need ${tile.house_cost}, have ${player.cash})"
        return log_failure_and_return_phase(game_state, failure_message, logger)

    # Build the house/hotel successfully
    player.cash -= tile.house_cost
    tile.num_houses += 1
    # Add success to history too
    success_event = f"Player {current_player_id} built house on {tile.name} (now has {tile.num_houses} houses)"
    add_to_history(game_state, success_event)
    game_state.phase = GamePhase.END_MANAGEMENT
    return game_state.phase

def handle_end_turn_action(game_state, player):
    """Handle the end turn action.
    
    Args:
        game_state: GameState object containing the game state
        player: Player object ending their turn
        
    Returns:
        str: The next game phase
    """
    current_player_id = game_state.current_player_id
    
    if player.debt > 0:
        # Player is bankrupt
        if player.creditor_id is not None:
            creditor = game_state.players[player.creditor_id]
            creditor.cash += player.cash # Transfer remaining cash
            for prop_id in player.owned_properties:
                prop = game_state.board[prop_id]
                prop.owner = creditor.player_id
                creditor.owned_properties.append(prop_id)
        else:
            # If no specific creditor, properties go to bank (unowned)
            for prop_id in player.owned_properties:
                prop = game_state.board[prop_id]
                prop.owner = None
                prop.mortgaged = False # Unmortgage properties
                prop.num_houses = 0 # Remove houses
        
        player.cash = 0
        player.owned_properties = []
        player.debt = 0
        player.creditor_id = None

        del game_state.players[current_player_id]
        game_state.player_order.remove(current_player_id)

        if len(game_state.players) <= 1:
            game_state.game_over = True
            return GamePhase.GAME_OVER

        game_state.phase = GamePhase.START_MANAGEMENT
    else:
        # end player's turn, continue to next player
        game_state.current_player_index += 1   
        if game_state.current_player_index >= len(game_state.player_order):
            game_state.current_player_index = 0
            game_state.turn_number += 1

        game_state.current_player_id = game_state.player_order[game_state.current_player_index]
        game_state.trades_proposed_this_turn = 0

        if game_state.turn_number >= game_state.max_turns:
            game_state.game_over = True
        
        game_state.phase = GamePhase.START_MANAGEMENT
    
    return game_state.phase

def handle_roll_action(game_state, player):
    """Handle the roll dice action and determine next phase based on landing tile.
    
    Args:
        game_state: GameState object containing the game state
        player: Player object rolling the dice
        
    Returns:
        str: The next game phase based on where the player lands
    """
    roll = random.randint(1, 6) + random.randint(1, 6)
    player.position = (player.position + roll) % len(game_state.board)
    tile = game_state.board[player.position]

    if isinstance(tile, PropertyTile):
        return handle_landing_on_property(player, tile, game_state)
    elif isinstance(tile, TaxTile):
        rent = tile.rent
        if player.cash >= rent:
            player.cash -= rent
            return GamePhase.END_MANAGEMENT
        else:
            amount_paid = player.cash
            player.cash = 0
            player.debt = rent - amount_paid
            player.creditor_id = None  # Bank is the creditor
            
            if not get_mortgageable_properties(player, game_state):
                return GamePhase.END_TURN
            else:
                return GamePhase.DECIDE_TO_SELL
    elif isinstance(tile, OtherTile):
        return GamePhase.END_MANAGEMENT
    else:
        return GamePhase.END_MANAGEMENT

def handle_auction_action(game_state, action, player):
    """Handle auction actions (place_bid and pass_auction)."""
    auction_state = game_state.auction_state
    action_type = action["type"]

    if action_type == "place_bid":
        bid_amount = action["bid_amount"]
        if bid_amount > auction_state["current_bid"] and player.cash >= bid_amount:
            auction_state["current_bid"] = bid_amount
            auction_state["high_bidder"] = player.player_id
            auction_state["last_bidder"] = player.player_id
        else:
            # Invalid bid, treat as a pass
            auction_state["active_bidders"].remove(player.player_id)

    elif action_type == "pass_auction":
        auction_state["active_bidders"].remove(player.player_id)

    if len(auction_state["active_bidders"]) == 1:
        # Auction ends - only one bidder left
        winner_id = auction_state.get("high_bidder")
        if winner_id is not None:
            winner = game_state.players[winner_id]
            tile = game_state.board[auction_state["tile_id"]]
            winner.cash -= auction_state["current_bid"]
            tile.owner = winner_id
            winner.owned_properties.append(tile.tile_id)
        # If winner_id is None, no one bid and property remains unowned
        game_state.auction_state = None
        return GamePhase.END_MANAGEMENT
    elif not auction_state["active_bidders"]:
        # All players passed
        game_state.auction_state = None
        return GamePhase.END_MANAGEMENT
    else:
        # Continue auction
        current_bidder_index = auction_state["active_bidders"].index(auction_state["last_bidder"])
        next_bidder_index = (current_bidder_index + 1) % len(auction_state["active_bidders"])
        game_state.decision_player_id = auction_state["active_bidders"][next_bidder_index]
        return GamePhase.AUCTION_PHASE