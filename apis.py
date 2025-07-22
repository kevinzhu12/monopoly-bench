from openai import OpenAI
import json
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini-2024-07-18"

management_tools = [
    {
        "type": "function",
        "name": "propose_trade",
        "description": "Propose a trade with another player.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_player": {"type": "integer", "description": "The player ID to trade with."},
                "offer_cash": {"type": "integer", "description": "The amount of cash to offer."},
                "offer_properties": {"type": "array", "items": {"type": "string"}, "description": "The names of properties to offer."},
                "request_cash": {"type": "integer", "description": "The amount of cash to request."},
                "request_properties": {"type": "array", "items": {"type": "string"}, "description": "The names of properties to request."},
            },
            "required": ["to_player", "offer_cash", "offer_properties", "request_cash", "request_properties"],
        },
    },
    {
        "type": "function",
        "name": "proceed",
        "description": "Proceed to the next phase of the turn.",
        "parameters": {},
    },
]

trade_recipient_tools = [
    {
        "type": "function",
        "name": "accept_trade",
        "description": "Accept the pending trade offer.",
        "parameters": {},
    },
    {
        "type": "function",
        "name": "reject_trade",
        "description": "Reject the pending trade offer.",
        "parameters": {},
    },
]

decide_to_buy_tools = [
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
    }
]

decide_to_sell_tools = [
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

def get_llm_response(prompt: str, game_state, tools) -> dict:
    """Gets a response from the language model.

    Args:
        prompt: The prompt to send to the language model.
        game_state: The current state of the game.
        tools: The tools to use for the given prompt

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
    print("RESPONSE", response.output[0])
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
    elif tool_call.name == "propose_trade":
        args = json.loads(tool_call.arguments)
        return propose_trade(game_state, **args)
    elif tool_call.name == "accept_trade":
        return accept_trade()
    elif tool_call.name == "reject_trade":
        return reject_trade()
    elif tool_call.name == "proceed":
        return proceed()

def buy_property() -> dict:
    return {"type": "buy"}

def skip_buy_property() -> dict:
    return {"type": "skip_buy"}

def sell_property(tile_id: int) -> dict:
    return {"type": "sell", "tile_id": tile_id}

def propose_trade(game_state, to_player, offer_cash, offer_properties, request_cash, request_properties) -> dict:
    offer_property_ids = [tile.tile_id for tile in game_state.board if tile.name in offer_properties]
    request_property_ids = [tile.tile_id for tile in game_state.board if tile.name in request_properties]
    return {
        "type": "propose_trade",
        "to_player": to_player,
        "offer": {"cash": offer_cash, "properties": offer_property_ids},
        "request": {"cash": request_cash, "properties": request_property_ids},
    }

def accept_trade() -> dict:
    return {"type": "accept_trade"}

def reject_trade() -> dict:
    return {"type": "reject_trade"}

def proceed() -> dict:
    return {"type": "proceed"}