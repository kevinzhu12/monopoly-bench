from engine import GameState, step
from config import tile_data, num_players, agents, starting_cash, max_turns
from logger import GameLogger

def main():
    # Initialize logger
    logger = GameLogger()
    
    game_state = GameState(num_players, tile_data, max_turns, starting_cash)

    while not game_state.game_over:
        if not game_state.players:
            game_state.game_over = True
            continue

        if game_state.decision_player_id is not None:
            active_player_id = game_state.decision_player_id
        else:
            active_player_id = game_state.current_player_id
        
        player = game_state.players[active_player_id]
        agent = next(a for a in agents if a.player_id == active_player_id)

        if game_state.phase == "start_management_phase":
            owned_property_names = [p.name for p in game_state.board if hasattr(p, 'owner') and p.owner == active_player_id]
            logger.log_turn_start(
                game_state.turn_number, 
                active_player_id, 
                player.cash, 
                player.position, 
                owned_property_names if owned_property_names else 'None'
            )

        observation = {
            "game_state": game_state,
            "phase": game_state.phase,
            "logger": logger
        }

        # Store state for logging
        cash_before = player.cash
        position_before = player.position
        tile_at_position_before_action = game_state.board[player.position]

        logger.log_phase(game_state.phase, "Phase before action")

        action = agent.act(observation)
        game_state.phase = step(game_state, action, logger)

        # Find the player object again, as it might have been removed (bankruptcy)
        player_after_action = game_state.players.get(active_player_id)
        
        logger.log_action(action['type'])
        logger.log_phase(game_state.phase, "Phase after action")

        if action['type'] == 'roll':
            if player_after_action:
                new_position = player_after_action.position
                tile = game_state.board[new_position]
                logger.log_movement(active_player_id, position_before, new_position, tile.name)

                cash_after = player_after_action.cash
                if cash_after < cash_before:
                    rent_paid = cash_before - cash_after
                    owner_id = getattr(tile, 'owner', None)  # None for tax tiles
                    logger.log_rent_payment(rent_paid, owner_id, cash_after)
                elif hasattr(tile, 'owner') and hasattr(tile, 'cost') and tile.owner is None and tile.cost > 0:
                    logger.log_property_available(tile.name, tile.cost)
        
        elif action['type'] == 'buy':
            if player_after_action and player_after_action.cash < cash_before:
                cost = cash_before - player_after_action.cash
                logger.log_property_bought(tile_at_position_before_action.name, cost, player_after_action.cash)
            else:
                logger.log_property_not_bought(tile_at_position_before_action.name)

        elif action['type'] == 'skip_buy':
            logger.log_property_skipped(tile_at_position_before_action.name)

        elif action['type'] == 'sell':
            tile_sold = game_state.board[action["tile_id"]]
            sale_price = tile_sold.cost // 2
            logger.log_property_sold(tile_sold.name, sale_price, player.cash)

        elif action['type'] == 'end_turn':
            logger.log_turn_end()

        if not player_after_action:
            logger.log_bankruptcy(active_player_id)
        
        logger.log_separator()

    logger.log_game_over()
    # Sort players by cash for final ranking
    if game_state.players:
        sorted_players = sorted(game_state.players.values(), key=lambda p: p.cash, reverse=True)
        for player in sorted_players:
            owned_property_names = [p.name for p in game_state.board if hasattr(p, 'owner') and p.owner == player.player_id]
            logger.log_final_results(
                player.player_id, 
                player.cash, 
                owned_property_names if owned_property_names else 'None'
            )
    
    # Close the logger
    logger.close()

if __name__ == "__main__":
    main()