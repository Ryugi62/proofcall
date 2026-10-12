@tool
async def check_slots(day: str) -> dict:
    """
    Open site-visit slots for a day (today, tomorrow, saturday, sunday, weekday).
    Use before offering or confirming any visit time. Offer one slot at a time by its exact text.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none", "price_note": "excluding GST and stamp duty"}
    d = (day or "").lower()
    slots = catalog["slots"].get(d)
    if slots is None:
        return {"ok": False, "slots": [], "say": "Which day suits you, tomorrow or the weekend?"}
    if not slots:
        return {"ok": True, "slots": [], "first_slot": "", "say": f"There are no open slots {d}. Shall I check tomorrow?"}
    return {"ok": True, "slots": slots, "first_slot": slots[0], "say": f"The earliest open slot is {slots[0]}."}
