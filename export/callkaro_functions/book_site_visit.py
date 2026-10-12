@tool
async def book_site_visit(slot: str, consent_id: str, consent_quote: str, lang: str = "en") -> dict:
    """
    Book a site visit for an exact open slot label. Refuses unless consent_id matches the customer's yes
    (from record_consent, purpose site_visit).
    """
    ctx = globals().get("x_context") or {}  # runtime-injected call context (phone, time)
    import hashlib, re
    affirmative = re.compile(r"""\b(yes|yeah|yep|sure|okay|ok|go ahead|please do|do it|book it|send it|sounds good|fine|alright|no problem|haan|haanji|han|ji haan|theek hai|thik hai|kar dijiye|kar do|bhej do|chalega|bilkul)\b|हाँ|हां|जी हाँ|ठीक है|कर दीजिए""", re.I)
    negative = re.compile(r"""\b(no(?! problem)|nope|not|don'?t(?! worry)|do not|nahi|nahin|mat|never|stop|wait|cancel|maybe|later)\b|नहीं|मत|रुकिए""", re.I)

    def consent_ok(purpose, consent_id, quote):
        q = quote or ""
        expected = "CN-" + hashlib.sha1((purpose + "|" + q).encode()).hexdigest()[:6].upper()
        return consent_id == expected and bool(affirmative.search(q)) and not negative.search(q)
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": [{"label": "tomorrow 11:00 AM", "iso": "2026-10-14T11:00:00+05:30"}, {"label": "tomorrow 4:30 PM", "iso": "2026-10-14T16:30:00+05:30"}], "saturday": [{"label": "Saturday 10:30 AM", "iso": "2026-10-17T10:30:00+05:30"}, {"label": "Saturday 3:00 PM", "iso": "2026-10-17T15:00:00+05:30"}], "sunday": [{"label": "Sunday 12:00 PM", "iso": "2026-10-18T12:00:00+05:30"}], "weekday": [{"label": "Wednesday 5:00 PM", "iso": "2026-10-21T17:00:00+05:30"}]}, "offer": "none", "price_note": "excluding GST and stamp duty", "as_of": "2026-10-13 (rehearsal clock)"}
    if not consent_ok("site_visit", consent_id, consent_quote):
        return {"ok": False, "reason": "no valid consent", "say": "Pehle confirm kar loon, visit book karoon?" if (lang or "en").lower().startswith("hi") else "Before I book, may I confirm you want the visit?"}
    match = [s for v in catalog["slots"].values() for s in v if s["label"] == slot]
    if not match:
        return {"ok": False, "reason": "slot not open", "say": "Yeh time khali nahi hai, main dobara check karti hoon." if (lang or "en").lower().startswith("hi") else "That time is not open. Let me check the open slots again."}
    seed = slot + ctx.get("user_phone_number", "") + ctx.get("current_time", "")
    ref = "GL-" + str(int(hashlib.sha1(seed.encode()).hexdigest(), 16) % 9000 + 1000)
    say = (f"Ho gaya, aapka site visit {slot} ke liye book hai. Reference {ref} WhatsApp par bhi aa jayega." if (lang or "en").lower().startswith("hi")
           else f"Done. Your site visit is booked for {slot}. Your reference {ref} will also come on WhatsApp.")
    return {"ok": True, "booking_id": ref, "slot": slot, "slot_iso": match[0]["iso"], "say": say}
