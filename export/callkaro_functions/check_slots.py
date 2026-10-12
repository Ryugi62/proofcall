@tool
async def check_slots(day: str) -> dict:
    """
    Get open site-visit slots for a day (today, tomorrow, saturday, sunday, weekday).
    Use before offering or confirming any visit time. Say the returned `say` text exactly.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh"}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh"}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh"}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none"}
    slots = catalog["slots"].get((day or "").lower())
    if slots is None:
        return {"say": "Which day suits you, tomorrow or the weekend?", "slots": []}
    if not slots:
        return {"say": f"There are no open slots {day}. Shall I check another day?", "slots": []}
    return {"say": "Open slots: " + ", ".join(slots) + ". Which one works?", "slots": slots}
