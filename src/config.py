from agents import RandomAgent, GreedyBuyer, LLMAgent, DummyAgent

# Complete official US Monopoly board with all property details
tile_data = [
    # Start
    {"name": "GO", "type": "other"},
    
    # Brown Set (Cheapest - 2 properties)
    # {"name": "Mediterranean Avenue", "type": "street", "cost": 60, "rent": 2, "rent_one_house": 10, "rent_two_houses": 30, "rent_three_houses": 90, "rent_four_houses": 160, "rent_hotel": 250, "house_cost": 50, "mortgage": 30, "color_set": "brown"},
    # {"name": "Baltic Avenue", "type": "street", "cost": 60, "rent": 4, "rent_one_house": 20, "rent_two_houses": 60, "rent_three_houses": 180, "rent_four_houses": 320, "rent_hotel": 450, "house_cost": 50, "mortgage": 30, "color_set": "brown"},
    {"name": "Income Tax", "type": "tax", "rent": 200},
    
    # First Railroad + Light Blue Set (2 properties)  
    {"name": "Reading Railroad", "type": "railroad", "cost": 200, "rent": 25},
    # {"name": "Oriental Avenue", "type": "street", "cost": 100, "rent": 6, "rent_one_house": 30, "rent_two_houses": 90, "rent_three_houses": 270, "rent_four_houses": 400, "rent_hotel": 550, "house_cost": 50, "mortgage": 50, "color_set": "light_blue"},
    # {"name": "Connecticut Avenue", "type": "street", "cost": 120, "rent": 8, "rent_one_house": 40, "rent_two_houses": 100, "rent_three_houses": 300, "rent_four_houses": 450, "rent_hotel": 600, "house_cost": 50, "mortgage": 60, "color_set": "light_blue"},
    
    # Spacing + Orange Set (2 properties)
    {"name": "Free Parking", "type": "other"}, 
    {"name": "St. James Place", "type": "street", "cost": 180, "rent": 14, "rent_one_house": 70, "rent_two_houses": 200, "rent_three_houses": 550, "rent_four_houses": 750, "rent_hotel": 950, "house_cost": 100, "mortgage": 90, "color_set": "orange"},
    {"name": "Pennsylvania Railroad", "type": "railroad", "cost": 200, "rent": 25},
    {"name": "Tennessee Avenue", "type": "street", "cost": 180, "rent": 14, "rent_one_house": 70, "rent_two_houses": 200, "rent_three_houses": 550, "rent_four_houses": 750, "rent_hotel": 950, "house_cost": 100, "mortgage": 90, "color_set": "orange"},
    
    # Red Set (2 properties)
    {"name": "B&O Railroad", "type": "railroad", "cost": 200, "rent": 25},
    {"name": "Kentucky Avenue", "type": "street", "cost": 220, "rent": 18, "rent_one_house": 90, "rent_two_houses": 250, "rent_three_houses": 700, "rent_four_houses": 875, "rent_hotel": 1050, "house_cost": 150, "mortgage": 110, "color_set": "red"},
    {"name": "Indiana Avenue", "type": "street", "cost": 220, "rent": 18, "rent_one_house": 90, "rent_two_houses": 250, "rent_three_houses": 700, "rent_four_houses": 875, "rent_hotel": 1050, "house_cost": 150, "mortgage": 110, "color_set": "red"},
    
    # Green Set (2 properties) + Final Railroad
    {"name": "Short Line Railroad", "type": "railroad", "cost": 200, "rent": 25},
    {"name": "Pacific Avenue", "type": "street", "cost": 300, "rent": 26, "rent_one_house": 130, "rent_two_houses": 390, "rent_three_houses": 900, "rent_four_houses": 1100, "rent_hotel": 1275, "house_cost": 200, "mortgage": 150, "color_set": "green"},
    {"name": "Luxury Tax", "type": "tax", "rent": 100},
    {"name": "North Carolina Avenue", "type": "street", "cost": 300, "rent": 26, "rent_one_house": 130, "rent_two_houses": 390, "rent_three_houses": 900, "rent_four_houses": 1100, "rent_hotel": 1275, "house_cost": 200, "mortgage": 150, "color_set": "green"},
    
    # Dark Blue Set (Most Expensive - 2 properties)
    {"name": "Park Place", "type": "street", "cost": 350, "rent": 35, "rent_one_house": 175, "rent_two_houses": 500, "rent_three_houses": 1100, "rent_four_houses": 1300, "rent_hotel": 1500, "house_cost": 200, "mortgage": 175, "color_set": "dark_blue"},
    {"name": "Boardwalk", "type": "street", "cost": 400, "rent": 50, "rent_one_house": 200, "rent_two_houses": 600, "rent_three_houses": 1400, "rent_four_houses": 1700, "rent_hotel": 2000, "house_cost": 200, "mortgage": 200, "color_set": "dark_blue"}
]

# Agent configuration - LLM vs Random to test LLM advantage
agents = [
    LLMAgent(player_id=0),
    LLMAgent(player_id=1),
    # LLMAgent(player_id=2),
]

# Game settings
num_players = len(agents)
starting_cash = 750 # TODO: change this to 1500
max_turns = 30