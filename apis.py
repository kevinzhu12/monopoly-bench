from openai import OpenAI
import json
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini-2024-07-18"

tools = [
    {
        "type": "function",
        "name": "buy_property",
        "description": "Buy the property that the player is currently on.",
        "parameters": {},
    },
    {
        "type": "function",
        "name": "skip_buy_property",
        "description": "Skip buying the property that the player is currently on.",
        "parameters": {},
    },
    {
        "type": "function",
        "name": "sell_property",
        "description": "Sell a property to the bank for half of its original cost.",
        "parameters": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "The name of the property to sell."}
            },
            "required": ["property_name"],
        },
    },
]

def get_llm_response(prompt: str, game_state) -> dict:
    """Gets a response from the language model.

    Args:
        prompt: The prompt to send to the language model.
        game_state: The current state of the game.

    Returns:
        The response from the language model.
    """
    response = client.responses.create(
        model=model,
        instructions="You are a Monopoly player. Your goal is to win the game by making smart decisions.",
        input=prompt,
        tools=tools,
        tool_choice="required", 
    )
    print("RESPONSE", response.output[0].name)
    tool_call = response.output[0]

    if tool_call.name == "buy_property":
        return buy_property()
    elif tool_call.name == "skip_buy_property":
        return skip_buy_property()
    elif tool_call.name == "sell_property":
        args = json.loads(tool_call.arguments)
        property_name = args["property_name"]
        tile_id = -1
        for tile in game_state.board:
            if tile.name == property_name:
                tile_id = tile.tile_id
                break
        return sell_property(tile_id)

def buy_property() -> dict:
    return {"type": "buy"}

def skip_buy_property() -> dict:
    return {"type": "skip_buy"}

def sell_property(tile_id: int) -> dict:
    return {"type": "sell", "tile_id": tile_id}