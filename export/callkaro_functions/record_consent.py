@tool
async def record_consent(purpose: str, customer_words: str, question_asked: str) -> dict:
    """
    Record explicit consent right after the customer answers a yes/no question that named the action
    (purpose = site_visit or whatsapp). Pass the question you asked and the customer's exact words.
    Returns consent_id only for a clear yes; pass consent_id and customer_words to the action function.
    """
    ctx = globals().get("x_context") or {}  # runtime-injected call context (phone, time)
    import hashlib, re
    affirmative = re.compile(r"""\b(yes|yeah|yep|sure|okay|ok|go ahead|please do|do it|book it|send it|sounds good|fine|alright|no problem|haan|haanji|han|ji haan|theek hai|thik hai|kar dijiye|kar do|bhej do|chalega|bilkul)\b|हाँ|हां|जी हाँ|ठीक है|कर दीजिए""", re.I)
    negative = re.compile(r"""\b(no(?! problem)|nope|not|don'?t(?! worry)|do not|nahi|nahin|mat|never|stop|wait|cancel|maybe|later)\b|नहीं|मत|रुकिए""", re.I)

    def consent_ok(purpose, consent_id, quote):
        q = quote or ""
        expected = "CN-" + hashlib.sha1((purpose + "|" + q).encode()).hexdigest()[:6].upper()
        return consent_id == expected and bool(affirmative.search(q)) and not negative.search(q)
    if not affirmative.search(customer_words or "") or negative.search(customer_words or ""):
        return {"ok": True, "accepted": False, "reason": "not a clear yes", "say": "No problem, I won't do that."}
    cid = "CN-" + hashlib.sha1((purpose + "|" + customer_words).encode()).hexdigest()[:6].upper()
    return {"ok": True, "accepted": True, "consent_id": cid, "purpose": purpose, "quote": customer_words,
            "question": question_asked, "recorded_at": ctx.get("current_time", "")}
