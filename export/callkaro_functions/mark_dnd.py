@tool
async def mark_dnd(reason: str, lang: str = "en") -> dict:
    """
    The customer asked not to be called again. Add this number to the do-not-call list, then end the call.
    """
    ctx = globals().get("x_context") or {}  # runtime-injected call context (phone, time)
    return {"ok": True, "dnd": True, "number": ctx.get("user_phone_number", ""), "reason": reason,
            "say": "Samajh gayi, hum aapko dobara call nahi karenge. Maaf kijiye." if (lang or "en").lower().startswith("hi") else "Understood. We will not call you again. Sorry for the trouble."}
