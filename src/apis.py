from openai import OpenAI
import json
from dotenv import load_dotenv
import os
from tools import MASTER_TOOLS, get_management_tools

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini-2024-07-18"
# model = "o3-2025-04-16"
# model = "o3-mini-2025-01-31"

def get_llm_response(prompt: str, game_state, tool_names, logger=None) -> dict:
    """Gets a response from the language model.

    Args:
        prompt: The prompt to send to the language model.
        game_state: The current state of the game.
        tool_names: The names of the tools to use for the given prompt
        logger: Optional logger instance for logging API responses

    Returns:
        The response from the language model.
    """
    tools = [MASTER_TOOLS[tool_name] for tool_name in tool_names]
    response = client.responses.create(
        model=model,
        instructions="You are a Monopoly player. Your goal is to win the game by making smart decisions. Before taking any action, briefly explain your reasoning/strategy for the action you are taking.",
        input=prompt,
        tools=tools,
        tool_choice="required", 
    )

    # Log API response if logger is provided
    if logger:
        logger.log_api_response(str(response.output))
    else:
        print("RESPONSE", response.output)

    tool_call = None
    for item in response.output:
        if hasattr(item, "name"):
            tool_call = item
            break
    
    if tool_call is None:
        raise ValueError("No tool call found in response")

    if tool_call.name == "buy_property":
        return buy_property()
    elif tool_call.name == "skip_buy_property":
        return skip_buy_property()
    elif tool_call.name == "propose_trade":
        args = json.loads(tool_call.arguments)
        return propose_trade(game_state, **args)
    elif tool_call.name == "accept_trade":
        return accept_trade()
    elif tool_call.name == "reject_trade":
        return reject_trade()
    elif tool_call.name == "proceed":
        return proceed()
    elif tool_call.name == "build_house":
        args = json.loads(tool_call.arguments)
        property_name = args["property_name"]
        tile_id = -1
        for tile in game_state.board:
            if tile.name == property_name:
                tile_id = tile.tile_id
                break
        return build_house(tile_id)
    elif tool_call.name == "mortgage_property":
        args = json.loads(tool_call.arguments)
        property_name = args["property_name"]
        tile_id = -1
        for tile in game_state.board:
            if tile.name == property_name:
                tile_id = tile.tile_id
                break
        return mortgage_property(tile_id)
    elif tool_call.name == "unmortgage_property":
        args = json.loads(tool_call.arguments)
        property_name = args["property_name"]
        tile_id = -1
        for tile in game_state.board:
            if tile.name == property_name:
                tile_id = tile.tile_id
                break
        return unmortgage_property(tile_id)
    elif tool_call.name == "resolve_mortgaged_trade":
        args = json.loads(tool_call.arguments)
        property_name = args["property_name"]
        decision = args["decision"]
        tile_id = -1
        for tile in game_state.board:
            if tile.name == property_name:
                tile_id = tile.tile_id
                break
        return resolve_mortgaged_trade(tile_id, decision)
    elif tool_call.name == "sell_house":
        args = json.loads(tool_call.arguments)
        property_name = args["property_name"]
        tile_id = -1
        for tile in game_state.board:
            if tile.name == property_name:
                tile_id = tile.tile_id
                break
        return sell_house(tile_id)
    elif tool_call.name == "place_bid":
        args = json.loads(tool_call.arguments)
        return place_bid(args["bid_amount"])
    elif tool_call.name == "pass_auction":
        return pass_auction()
    else:
        print(f"ERROR: Unknown tool call: {tool_call.name}")
        return None

def buy_property() -> dict:
    return {"type": "buy"}

def skip_buy_property() -> dict:
    return {"type": "skip_buy"}

def mortgage_property(tile_id: int) -> dict:
    return {"type": "mortgage_property", "tile_id": tile_id}

def unmortgage_property(tile_id: int) -> dict:
    return {"type": "unmortgage_property", "tile_id": tile_id}

def resolve_mortgaged_trade(tile_id: int, decision: str) -> dict:
    return {"type": "resolve_mortgaged_trade", "tile_id": tile_id, "decision": decision}

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

def build_house(tile_id: int) -> dict:
    return {"type": "build_house", "tile_id": tile_id}

def sell_house(tile_id: int) -> dict:
    return {"type": "sell_house", "tile_id": tile_id}

def place_bid(bid_amount: int) -> dict:
    return {"type": "place_bid", "bid_amount": bid_amount}

def pass_auction() -> dict:
    return {"type": "pass_auction"}