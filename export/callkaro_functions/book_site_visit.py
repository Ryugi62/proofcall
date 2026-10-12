@tool
async def book_site_visit(slot: str) -> dict:
    """
    Book a site visit for an exact open slot, only after record_consent(site_visit) returned accepted=true
    for a question that named this slot.
    """
    import hashlib
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none", "price_note": "excluding GST and stamp duty"}
    open_slots = [s for v in catalog["slots"].values() for s in v]
    if slot not in open_slots:
        return {"ok": False, "say": "That time is not open. Let me check the open slots again."}
    ref = "GL-" + hashlib.sha1(slot.encode()).hexdigest()[:6].upper()
    return {"ok": True, "booking_id": ref, "slot": slot,
            "say": f"Done. Your site visit is booked for {slot}. Your reference is {ref}."}
