@tool
async def mark_dnd(reason: str) -> dict:
    """
    The customer asked not to be called again. Add this number to the do-not-call list, then end the call.
    """
    ctx = globals().get("x_context") or {}
    return {"ok": True, "dnd": True, "number": ctx.get("user_phone_number", ""), "reason": reason,
            "say": "Understood. We will not call you again. Sorry for the trouble."}
