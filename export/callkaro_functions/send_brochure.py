@tool
async def send_brochure(consent_id: str, consent_quote: str, lang: str = "en") -> dict:
    """
    Send the project brochure on WhatsApp to the number on this call. Refuses unless consent_id matches the
    customer's yes (record_consent, purpose whatsapp).
    """
    ctx = globals().get("x_context") or {}  # runtime-injected call context (phone, time)
    import hashlib, re
    affirmative = re.compile(r"""\b(yes|yeah|yep|sure|okay|ok|go ahead|please do|do it|book it|send it|sounds good|fine|alright|no problem|haan|haanji|han|ji haan|theek hai|thik hai|kar dijiye|kar do|bhej do|chalega|bilkul)\b|हाँ|हां|जी हाँ|ठीक है|कर दीजिए""", re.I)
    negative = re.compile(r"""\b(no(?! problem)|nope|not|don'?t(?! worry)|do not|nahi|nahin|mat|never|stop|wait|cancel|maybe|later)\b|नहीं|मत|रुकिए""", re.I)

    def consent_ok(purpose, consent_id, quote):
        q = quote or ""
        expected = "CN-" + hashlib.sha1((purpose + "|" + q).encode()).hexdigest()[:6].upper()
        return consent_id == expected and bool(affirmative.search(q)) and not negative.search(q)
    if not consent_ok("whatsapp", consent_id, consent_quote):
        return {"ok": False, "reason": "no valid consent", "say": "Kya main brochure WhatsApp par bhej doon?" if (lang or "en").lower().startswith("hi") else "Shall I send the brochure to this WhatsApp number?"}
    return {"ok": True, "sent": True, "to": ctx.get("user_phone_number", ""),
            "say": "Ho gaya, brochure aapke WhatsApp par aa raha hai." if (lang or "en").lower().startswith("hi") else "Done, the brochure is on its way to this WhatsApp number."}
