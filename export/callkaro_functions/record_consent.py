@tool
async def record_consent(purpose: str, customer_words: str) -> dict:
    """
    Record explicit consent before booking a site visit (purpose=site_visit) or sending WhatsApp (purpose=whatsapp).
    Pass the customer's exact words. Proceed with the action only if accepted is true.
    """
    ctx = globals().get("x_context") or {}
    import re
    affirmative = re.compile(r"""\b(yes|yeah|yep|sure|okay|ok|go ahead|please do|do it|book it|send it|sounds good|fine|alright|no problem|haan|haanji|han|ji haan|theek hai|thik hai|kar dijiye|kar do|bhej do|chalega|bilkul)\b|हाँ|हां|जी हाँ|ठीक है|कर दीजिए""", re.I)
    negative = re.compile(r"""\b(no(?! problem)|nope|not|don'?t(?! worry)|do not|nahi|nahin|mat|never|stop|wait|cancel|maybe|later)\b|नहीं|मत|रुकिए""", re.I)
    words = customer_words or ""
    if not affirmative.search(words) or negative.search(words):
        return {"ok": True, "accepted": False, "reason": "not a clear yes",
                "say": "No problem, I won't do that."}
    return {"ok": True, "accepted": True, "purpose": purpose, "quote": words, "recorded_at": ctx.get("current_time", "")}
