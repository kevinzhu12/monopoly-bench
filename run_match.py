from engine import GameState, step
from config import tile_data, num_players, agents, starting_cash, max_turns

def main():
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
            print("\n\n")
            print(f"--- TURN {game_state.turn_number}: PLAYER {active_player_id}'S TURN ---")
            owned_property_names = [p.name for p in game_state.board if p.owner == active_player_id]
            print(f"Player {active_player_id} | Cash: ${player.cash} | Position: {player.position} | Properties: {owned_property_names if owned_property_names else 'None'}")

        observation = {
            "game_state": game_state,
            "phase": game_state.phase
        }

        # Store state for logging
        cash_before = player.cash
        position_before = player.position
        tile_at_position_before_action = game_state.board[player.position]

        print(f"Phase before action: {game_state.phase}")

        action = agent.act(observation)
        game_state.phase = step(game_state, action)

        # Find the player object again, as it might have been removed (bankruptcy)
        player_after_action = game_state.players.get(active_player_id)
        
        print(f"Action: {action['type']}")
        print(f"Phase after action: {game_state.phase}")

        if action['type'] == 'roll':
            if player_after_action:
                new_position = player_after_action.position
                tile = game_state.board[new_position]
                print(f"  Player {active_player_id} rolled and moved from position {position_before} to {new_position} (Landed on '{tile.name}')")

                cash_after = player_after_action.cash
                if cash_after < cash_before:
                    rent_paid = cash_before - cash_after
                    print(f"  Paid ${rent_paid} in rent to Player {tile.owner}. Cash is now ${cash_after}.")
                elif tile.owner is None and tile.cost > 0:
                    print(f"  '{tile.name}' is unowned and costs ${tile.cost}.")
        
        elif action['type'] == 'buy':
            if player_after_action and player_after_action.cash < cash_before:
                cost = cash_before - player_after_action.cash
                print(f"  Bought '{tile_at_position_before_action.name}' for ${cost}. Cash is now ${player_after_action.cash}.")
            else:
                print(f"  Did not buy '{tile_at_position_before_action.name}'.")

        elif action['type'] == 'skip_buy':
            print(f"  Skipped buying '{tile_at_position_before_action.name}'.")

        elif action['type'] == 'sell':
            tile_sold = game_state.board[action["tile_id"]]
            sale_price = tile_sold.cost // 2
            print(f"  Sold '{tile_sold.name}' for ${sale_price}. Cash is now ${player.cash}.")

        elif action['type'] == 'end_turn':
            print(f"  Ending turn.")

        if not player_after_action:
             print(f"  Player {active_player_id} went bankrupt!")
        
        print("-" * 40)



    print("Game Over!")
    # Sort players by cash for final ranking
    if game_state.players:
        sorted_players = sorted(game_state.players.values(), key=lambda p: p.cash, reverse=True)
        for player in sorted_players:
            owned_property_names = [p.name for p in game_state.board if p.owner == player.player_id]
            print(f"Player {player.player_id} | Final Cash: ${player.cash} | Properties: {owned_property_names if owned_property_names else 'None'}")

if __name__ == "__main__":
    main()