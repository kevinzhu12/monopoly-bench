
import random

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

class CornerTile(BaseTile):
    """Represents a corner space like GO or Jail."""
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
        self.phase = "start_management_phase"
        self.pending_trade = None
        self.decision_player_id = None
        self.pre_trade_phase = None

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
            elif tile_type == "corner":
                board.append(CornerTile(i, **data))
            elif tile_type == "action":
                board.append(ActionTile(i, **data))
        return board

def step(game_state, action):
    """Processes a single action and updates the game state."""
    current_player_id = game_state.current_player_id
    player = game_state.players[current_player_id]

    action_type = action["type"]

    if action_type == "proceed":
        if game_state.phase == "start_management_phase":
            game_state.phase = "roll_phase"
        elif game_state.phase == "end_management_phase":
            # End the current player's turn
            game_state.current_player_index = (game_state.current_player_index + 1) % len(game_state.player_order)
            if game_state.current_player_index == 0:
                game_state.turn_number += 1
            game_state.current_player_id = game_state.player_order[game_state.current_player_index]
            if game_state.turn_number >= game_state.max_turns:
                game_state.game_over = True
            game_state.phase = "start_management_phase"

    elif action_type == "roll":
        roll = random.randint(1, 6) + random.randint(1, 6)
        player.position = (player.position + roll) % len(game_state.board)
        tile = game_state.board[player.position]

        if isinstance(tile, PropertyTile) and tile.owner is None and tile.cost > 0:
            game_state.phase = "decide_to_buy"
        elif isinstance(tile, StreetTile) and tile.owner is not None and tile.owner != player.player_id:
            rent = tile.rent
            color_set = tile.color_set
            monopoly = all(
                t.owner == tile.owner for t in game_state.board if isinstance(t, StreetTile) and t.color_set == color_set
            )
            if monopoly:
                rent = tile.rent_monopoly

            if player.cash >= rent:
                player.cash -= rent
                game_state.players[tile.owner].cash += rent
                game_state.phase = "end_management_phase"
            else:
                amount_paid = player.cash
                player.cash = 0
                game_state.players[tile.owner].cash += amount_paid
                player.debt = rent - amount_paid
                game_state.phase = "decide_to_sell"
        elif isinstance(tile, PropertyTile) and tile.owner is not None and tile.owner != player.player_id:
            rent = tile.rent
            if player.cash >= rent:
                player.cash -= rent
                game_state.players[tile.owner].cash += rent
                game_state.phase = "end_management_phase"
            else:
                amount_paid = player.cash
                player.cash = 0
                game_state.players[tile.owner].cash += amount_paid
                player.debt = rent - amount_paid
                game_state.phase = "decide_to_sell"
        elif isinstance(tile, TaxTile):
            rent = tile.rent
            if player.cash >= rent:
                player.cash -= rent
            game_state.phase = "end_management_phase"
        else:
            game_state.phase = "end_management_phase"

    elif action_type == "buy":
        tile = game_state.board[player.position]
        if isinstance(tile, PropertyTile) and tile.owner is None and player.cash >= tile.cost:
            player.cash -= tile.cost
            tile.owner = player.player_id
            player.owned_properties.append(tile.tile_id)
        game_state.phase = "end_management_phase"

    elif action_type == "skip_buy":
        game_state.phase = "end_management_phase"

    elif action_type == "sell":
        tile_to_sell = game_state.board[action["tile_id"]]
        player.cash += tile_to_sell.cost // 2
        tile_to_sell.owner = None
        player.owned_properties.remove(action["tile_id"])

        if player.cash >= player.debt:
            player.cash -= player.debt
            owner_of_property = game_state.board[player.position].owner
            game_state.players[owner_of_property].cash += player.debt
            player.debt = 0
            game_state.phase = "end_management_phase"
        else:
            game_state.phase = "decide_to_sell"

    elif action_type == "propose_trade":
        game_state.pre_trade_phase = game_state.phase
        game_state.pending_trade = {
            "from_player": current_player_id,
            "to_player": action["to_player"],
            "offer": action["offer"],
            "request": action["request"],
        }
        game_state.phase = "decide_on_trade"
        game_state.decision_player_id = action["to_player"]

    elif action_type == "accept_trade":
        trade = game_state.pending_trade
        from_player = game_state.players[trade["from_player"]]
        to_player = game_state.players[trade["to_player"]]

        from_player.cash -= trade["offer"]["cash"]
        to_player.cash += trade["offer"]["cash"]
        from_player.cash += trade["request"]["cash"]
        to_player.cash -= trade["request"]["cash"]

        for tile_id in trade["offer"]["properties"]:
            from_player.owned_properties.remove(tile_id)
            to_player.owned_properties.append(tile_id)
            game_state.board[tile_id].owner = trade["to_player"]
        for tile_id in trade["request"]["properties"]:
            to_player.owned_properties.remove(tile_id)
            from_player.owned_properties.append(tile_id)
            game_state.board[tile_id].owner = trade["from_player"]

        game_state.pending_trade = None
        game_state.phase = game_state.pre_trade_phase
        game_state.pre_trade_phase = None
        game_state.decision_player_id = None

    elif action_type == "reject_trade":
        game_state.pending_trade = None
        game_state.phase = game_state.pre_trade_phase
        game_state.pre_trade_phase = None
        game_state.decision_player_id = None

    elif action_type == "end_turn":
        if player.debt > 0:
            player.cash = 0
            del game_state.players[current_player_id]
            game_state.player_order.remove(current_player_id)

            if len(game_state.players) <= 1:
                game_state.game_over = True
                return "game_over"

            if game_state.current_player_index >= len(game_state.player_order):
                game_state.current_player_index = 0
                game_state.turn_number += 1

            game_state.current_player_id = game_state.player_order[game_state.current_player_index]

            if game_state.turn_number >= game_state.max_turns:
                game_state.game_over = True

            game_state.phase = "start_management_phase"

    return game_state.phase
