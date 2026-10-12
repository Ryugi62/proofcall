@tool
async def schedule_callback(when: str, reason: str) -> dict:
    """
    Note a callback when the customer asks to be called later or wants to hear when a sold-out unit opens up.
    """
    return {"ok": True, "when": when, "reason": reason, "say": "Noted, we will call you back " + (when or "soon") + "."}
