@tool
async def schedule_callback(when: str, reason: str, lang: str = "en") -> dict:
    """
    Note a callback when the customer asks to be called later or wants a call when a sold-out unit opens up.
    """
    return {"ok": True, "when": when, "reason": reason,
            "say": ("Theek hai, hum aapko " + (when or "jaldi") + " call karenge.") if (lang or "en").lower().startswith("hi") else ("Noted, we will call you back " + (when or "soon") + ".")}
