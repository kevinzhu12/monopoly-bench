import logging
import os
from datetime import datetime
from pathlib import Path

class GameLogger:
    """Handles logging of game trajectories to files."""
    
    def __init__(self, game_id=None):
        """Initialize the game logger.
        
        Args:
            game_id: Optional custom game ID. If None, generates timestamp-based ID.
        """
        # Create results directory if it doesn't exist
        self.results_dir = Path("../results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Generate game ID if not provided
        if game_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            game_id = f"game_{timestamp}"
        
        self.game_id = game_id
        self.log_file = self.results_dir / f"{game_id}.log"
        
        # Set up logger
        self.logger = logging.getLogger(f"monopoly_game_{game_id}")
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Also log to console for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"=== MONOPOLY GAME LOG: {game_id} ===")
        self.logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 50)
    
    def log_turn_start(self, turn_number, player_id, player_cash, player_position, owned_properties):
        """Log the start of a player's turn."""
        self.logger.info(f"\n--- TURN {turn_number}: PLAYER {player_id}'S TURN ---")
        properties_str = owned_properties if owned_properties != 'None' else 'None'
        self.logger.info(f"Player {player_id} | Cash: ${player_cash} | Position: {player_position} | Properties: {properties_str}")
    
    def log_phase(self, phase, prefix="Phase"):
        """Log the current game phase."""
        self.logger.info(f"{prefix}: {phase}")
    
    def log_action(self, action_type):
        """Log a player action."""
        self.logger.info(f"Action: {action_type}")
    
    def log_movement(self, player_id, old_position, new_position, tile_name):
        """Log player movement."""
        self.logger.info(f"  Player {player_id} rolled and moved from position {old_position} to {new_position} (Landed on '{tile_name}')")
    
    def log_rent_payment(self, rent_paid, owner_id, new_cash):
        """Log rent payment to another player or tax payment to the bank."""
        if owner_id is None:
            self.logger.info(f"  Paid ${rent_paid} in tax to the bank. Cash is now ${new_cash}.")
        else:
            self.logger.info(f"  Paid ${rent_paid} in rent to Player {owner_id}. Cash is now ${new_cash}.")
    
    def log_property_available(self, tile_name, cost):
        """Log when a property is available for purchase."""
        self.logger.info(f"  '{tile_name}' is unowned and costs ${cost}.")
    
    def log_property_bought(self, tile_name, cost, new_cash):
        """Log property purchase."""
        self.logger.info(f"  Bought '{tile_name}' for ${cost}. Cash is now ${new_cash}.")
    
    def log_property_not_bought(self, tile_name):
        """Log when a property purchase was attempted but failed."""
        self.logger.info(f"  Did not buy '{tile_name}'.")
    
    def log_property_skipped(self, tile_name):
        """Log when a property purchase was skipped."""
        self.logger.info(f"  Skipped buying '{tile_name}'.")
    
    def log_property_sold(self, tile_name, sale_price, new_cash):
        """Log property sale."""
        self.logger.info(f"  Sold '{tile_name}' for ${sale_price}. Cash is now ${new_cash}.")
    
    def log_turn_end(self):
        """Log turn ending."""
        self.logger.info(f"  Ending turn.")
    
    def log_bankruptcy(self, player_id):
        """Log player bankruptcy."""
        self.logger.info(f"  Player {player_id} went bankrupt!")
    
    def log_separator(self):
        """Log a separator line."""
        self.logger.info("-" * 40)
    
    def log_game_over(self):
        """Log game over."""
        self.logger.info("\nGame Over!")
    
    def log_final_results(self, player_id, final_cash, owned_properties):
        """Log final player results."""
        properties_str = owned_properties if owned_properties != 'None' else 'None'
        self.logger.info(f"Player {player_id} | Final Cash: ${final_cash} | Properties: {properties_str}")
    
    def log_api_response(self, response_data):
        """Log API responses for debugging."""
        self.logger.info(f"API RESPONSE: {response_data}")
    
    def log_model_reasoning(self, reasoning):
        """Log model reasoning."""
        self.logger.info(f"MODEL REASONING: {reasoning}")
    
    def log_tool_call(self, tool_name):
        """Log tool calls."""
        self.logger.info(f"TOOL CALL: {tool_name}")
    
    def log_custom(self, message):
        """Log a custom message."""
        self.logger.info(message)
    
    def close(self):
        """Close the logger and handlers."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler) 