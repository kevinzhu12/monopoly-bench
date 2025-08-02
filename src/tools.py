import copy

MASTER_TOOLS = {
    "propose_trade": {
        "type": "function",
        "name": "propose_trade",
        "description": "Propose a trade with another player. Use this to complete monopolies, gain strategic properties, or improve your cash position. Consider what the other player needs to make the trade attractive to them.",
        "strict": True,
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
            "additionalProperties": False,
        },
    },
    "proceed": {
        "type": "function",
        "name": "proceed",
        "description": "Proceed to the next phase of the turn.",
        "parameters": {},
    },
    "build_house": {
        "type": "function",
        "name": "build_house",
        "description": "Build a house or hotel on a property. You must own all properties of a color set to build. You must build houses evenly across the color set. A hotel is 5 houses.",
        "parameters": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "The name of the property to build on."}
            },
            "required": ["property_name"],
        },
    },
    "mortgage_property": {
        "type": "function",
        "name": "mortgage_property",
        "description": "Mortgage a property to get cash from the bank (50% of property cost). Use when you need quick cash for debt, purchases, or trades. Mortgaged properties don't collect rent.",
        "parameters": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "The name of the property to mortgage."}
            },
            "required": ["property_name"],
        },
    },
    "unmortgage_property": {
        "type": "function",
        "name": "unmortgage_property",
        "description": "Unmortgage a property by paying back the mortgage with 10% interest (110% of mortgage value). This allows the property to collect rent again.",
        "parameters": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "The name of the property to unmortgage."}
            },
            "required": ["property_name"],
        },
    },
    "accept_trade": {
        "type": "function",
        "name": "accept_trade",
        "description": "Accept the pending trade offer. Use when the trade helps you complete monopolies, improves your strategic position, or provides fair value.",
        "parameters": {},
    },
    "reject_trade": {
        "type": "function",
        "name": "reject_trade",
        "description": "Reject the pending trade offer. Use when the trade doesn't benefit you sufficiently or helps your opponent too much.",
        "parameters": {},
    },
    "buy_property": {
        "type": "function",
        "name": "buy_property",
        "description": "Buy the property that the player is currently on.",
        "parameters": {},
    },
    "skip_buy_property": {
        "type": "function",
        "name": "skip_buy_property",
        "description": "Skip buying the property that the player is currently on.",
        "parameters": {},
    },
    "resolve_mortgaged_trade": {
        "type": "function",
        "name": "resolve_mortgaged_trade",
        "description": "Resolve a trade involving a mortgaged property. Choose 'unmortgage_now' to pay full cost and collect rent immediately, or 'pay_interest_only' to pay 10% interest and keep it mortgaged.",
        "parameters": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "The name of the mortgaged property."},
                "decision": {"type": "string", "enum": ["unmortgage_now", "pay_interest_only"], "description": "Your decision on how to handle the mortgaged property."}
            },
            "required": ["property_name", "decision"],
        },
    },
    "sell_house": {
        "type": "function",
        "name": "sell_house",
        "description": "Sell a house or hotel on a property for half the building cost. Houses must be sold evenly across a color group. Use when you need cash for debt or strategic purchases.",
        "parameters": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "The name of the property to sell a house from."}
            },
            "required": ["property_name"],
        },
    },
}

def get_management_tools(buildable_properties=None):
    """Generate management tools dynamically based on current game state."""
    tool_names = [
        "propose_trade",
        "proceed",
        "mortgage_property",
        "unmortgage_property",
    ]

    if buildable_properties:
        tool_names.append("build_house")

    return tool_names