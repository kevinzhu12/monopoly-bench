from agents import RandomAgent, GreedyBuyer, LLMAgent

# Complete official US Monopoly board with all property details
tile_data = [
    # {"name": "GO", "type": "corner"},
    {"name": "Mediterranean Avenue", "type": "street", "cost": 60, "rent": 2, "rent_one_house": 10, "rent_two_houses": 30, "rent_three_houses": 90, "rent_four_houses": 160, "rent_hotel": 250, "house_cost": 50, "mortgage": 30, "color_set": "brown"},
    # {"name": "Community Chest", "type": "action"},
    {"name": "Baltic Avenue", "type": "street", "cost": 60, "rent": 4, "rent_one_house": 20, "rent_two_houses": 60, "rent_three_houses": 180, "rent_four_houses": 320, "rent_hotel": 450, "house_cost": 50, "mortgage": 30, "color_set": "brown"},
    # {"name": "Income Tax", "type": "tax", "rent": 200},
    # {"name": "Reading Railroad", "type": "railroad", "cost": 200, "rent": 25},
    {"name": "Oriental Avenue", "type": "street", "cost": 100, "rent": 6, "rent_one_house": 30, "rent_two_houses": 90, "rent_three_houses": 270, "rent_four_houses": 400, "rent_hotel": 550, "house_cost": 50, "mortgage": 50, "color_set": "light_blue"},
    # {"name": "Chance", "type": "action"},
    {"name": "Vermont Avenue", "type": "street", "cost": 100, "rent": 6, "rent_one_house": 30, "rent_two_houses": 90, "rent_three_houses": 270, "rent_four_houses": 400, "rent_hotel": 550, "house_cost": 50, "mortgage": 50, "color_set": "light_blue"},
    {"name": "Connecticut Avenue", "type": "street", "cost": 120, "rent": 8, "rent_one_house": 40, "rent_two_houses": 100, "rent_three_houses": 300, "rent_four_houses": 450, "rent_hotel": 600, "house_cost": 50, "mortgage": 60, "color_set": "light_blue"},
    # {"name": "Jail", "type": "corner"},
    {"name": "St. Charles Place", "type": "street", "cost": 140, "rent": 10, "rent_one_house": 50, "rent_two_houses": 150, "rent_three_houses": 450, "rent_four_houses": 625, "rent_hotel": 750, "house_cost": 100, "mortgage": 70, "color_set": "pink"},
    # {"name": "Electric Company", "type": "utility", "cost": 150, "rent": 4},
    {"name": "States Avenue", "type": "street", "cost": 140, "rent": 10, "rent_one_house": 50, "rent_two_houses": 150, "rent_three_houses": 450, "rent_four_houses": 625, "rent_hotel": 750, "house_cost": 100, "mortgage": 70, "color_set": "pink"},
    {"name": "Virginia Avenue", "type": "street", "cost": 160, "rent": 12, "rent_one_house": 60, "rent_two_houses": 180, "rent_three_houses": 500, "rent_four_houses": 700, "rent_hotel": 900, "house_cost": 100, "mortgage": 80, "color_set": "pink"},
    # {"name": "Pennsylvania Railroad", "type": "railroad", "cost": 200, "rent": 25},
    {"name": "St. James Place", "type": "street", "cost": 180, "rent": 14, "rent_one_house": 70, "rent_two_houses": 200, "rent_three_houses": 550, "rent_four_houses": 750, "rent_hotel": 950, "house_cost": 100, "mortgage": 90, "color_set": "orange"},
    # {"name": "Community Chest", "type": "action"},
    {"name": "Tennessee Avenue", "type": "street", "cost": 180, "rent": 14, "rent_one_house": 70, "rent_two_houses": 200, "rent_three_houses": 550, "rent_four_houses": 750, "rent_hotel": 950, "house_cost": 100, "mortgage": 90, "color_set": "orange"},
    {"name": "New York Avenue", "type": "street", "cost": 200, "rent": 16, "rent_one_house": 80, "rent_two_houses": 220, "rent_three_houses": 600, "rent_four_houses": 800, "rent_hotel": 1000, "house_cost": 100, "mortgage": 100, "color_set": "orange"},
    # {"name": "Free Parking", "type": "corner"},
    {"name": "Kentucky Avenue", "type": "street", "cost": 220, "rent": 18, "rent_one_house": 90, "rent_two_houses": 250, "rent_three_houses": 700, "rent_four_houses": 875, "rent_hotel": 1050, "house_cost": 150, "mortgage": 110, "color_set": "red"},
    # {"name": "Chance", "type": "action"},
    {"name": "Indiana Avenue", "type": "street", "cost": 220, "rent": 18, "rent_one_house": 90, "rent_two_houses": 250, "rent_three_houses": 700, "rent_four_houses": 875, "rent_hotel": 1050, "house_cost": 150, "mortgage": 110, "color_set": "red"},
    {"name": "Illinois Avenue", "type": "street", "cost": 240, "rent": 20, "rent_one_house": 100, "rent_two_houses": 300, "rent_three_houses": 750, "rent_four_houses": 925, "rent_hotel": 1100, "house_cost": 150, "mortgage": 120, "color_set": "red"},
    # {"name": "B&O Railroad", "type": "railroad", "cost": 200, "rent": 25},
    {"name": "Atlantic Avenue", "type": "street", "cost": 260, "rent": 22, "rent_one_house": 110, "rent_two_houses": 330, "rent_three_houses": 800, "rent_four_houses": 975, "rent_hotel": 1150, "house_cost": 150, "mortgage": 130, "color_set": "yellow"},
    {"name": "Ventnor Avenue", "type": "street", "cost": 260, "rent": 22, "rent_one_house": 110, "rent_two_houses": 330, "rent_three_houses": 800, "rent_four_houses": 975, "rent_hotel": 1150, "house_cost": 150, "mortgage": 130, "color_set": "yellow"},
    # {"name": "Water Works", "type": "utility", "cost": 150, "rent": 4},
    {"name": "Marvin Gardens", "type": "street", "cost": 280, "rent": 24, "rent_one_house": 120, "rent_two_houses": 360, "rent_three_houses": 850, "rent_four_houses": 1025, "rent_hotel": 1200, "house_cost": 150, "mortgage": 140, "color_set": "yellow"},
    # {"name": "Go To Jail", "type": "corner"},
    {"name": "Pacific Avenue", "type": "street", "cost": 300, "rent": 26, "rent_one_house": 130, "rent_two_houses": 390, "rent_three_houses": 900, "rent_four_houses": 1100, "rent_hotel": 1275, "house_cost": 200, "mortgage": 150, "color_set": "green"},
    {"name": "North Carolina Avenue", "type": "street", "cost": 300, "rent": 26, "rent_one_house": 130, "rent_two_houses": 390, "rent_three_houses": 900, "rent_four_houses": 1100, "rent_hotel": 1275, "house_cost": 200, "mortgage": 150, "color_set": "green"},
    # {"name": "Community Chest", "type": "action"},
    {"name": "Pennsylvania Avenue", "type": "street", "cost": 320, "rent": 28, "rent_one_house": 150, "rent_two_houses": 450, "rent_three_houses": 1000, "rent_four_houses": 1200, "rent_hotel": 1400, "house_cost": 200, "mortgage": 160, "color_set": "green"},
    # {"name": "Short Line Railroad", "type": "railroad", "cost": 200, "rent": 25},
    # {"name": "Chance", "type": "action"},
    {"name": "Park Place", "type": "street", "cost": 350, "rent": 35, "rent_one_house": 175, "rent_two_houses": 500, "rent_three_houses": 1100, "rent_four_houses": 1300, "rent_hotel": 1500, "house_cost": 200, "mortgage": 175, "color_set": "dark_blue"},
    # {"name": "Luxury Tax", "type": "tax", "rent": 100},
    {"name": "Boardwalk", "type": "street", "cost": 400, "rent": 50, "rent_one_house": 200, "rent_two_houses": 600, "rent_three_houses": 1400, "rent_four_houses": 1700, "rent_hotel": 2000, "house_cost": 200, "mortgage": 200, "color_set": "dark_blue"}
]
# Agent configuration - LLM vs Random to test LLM advantage
agents = [
    GreedyBuyer(player_id=0),
    LLMAgent(player_id=1)
]

# Game settings
num_players = len(agents)
starting_cash = 1500
max_turns = 30