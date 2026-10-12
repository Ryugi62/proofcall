@tool
async def record_consent(purpose: str, customer_words: str) -> dict:
    """
    Record explicit consent before booking a site visit (purpose=site_visit) or sending WhatsApp (purpose=whatsapp).
    Pass the customer's exact words. Only proceed with the action if accepted is true.
    """
    import re
    affirmative = re.compile(r"""\b(yes|yeah|yep|sure|okay|ok|go ahead|please do|do it|book it|sounds good|fine|alright|haan|haanji|han|ji haan|theek hai|thik hai|kar dijiye|kar do|chalega|bilkul)\b""", re.I)
    negative = re.compile(r"""\b(no|nope|not now|don'?t|do not|nahi|nahin|mat|never|stop|wait)\b""", re.I)
    words = customer_words or ""
    if not affirmative.search(words) or negative.search(words):
        return {"accepted": False, "say": "No problem, I won't do that. Is there anything else?",
                "reason": "not a clear yes"}
    return {"accepted": True, "purpose": purpose, "quote": words, "recorded_at": x_context.get("current_time", "")}
