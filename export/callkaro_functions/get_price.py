@tool
async def get_price(bhk: str) -> dict:
    """
    Get the exact price sheet line for a configuration (2bhk, 3bhk or 4bhk).
    Use whenever the customer asks about price, cost, rate or booking amount. Say the returned `say` text exactly.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh"}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh"}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh"}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none"}
    key = (bhk or "").lower().replace(" ", "")
    p = catalog["prices"].get(key)
    if not p:
        return {"say": "We have 2, 3 and 4 BHK homes. Which one should I check?", "found": False}
    return {"say": f"The {key.upper()} starts at {p['from']}, with a booking amount of {p['booking_amount']}.",
            "found": True, "price_from": p["from"], "booking_amount": p["booking_amount"], "source": "price_sheet"}
