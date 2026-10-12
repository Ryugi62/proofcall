@tool
async def check_units(bhk: str) -> dict:
    """
    Units left for a configuration. Use before saying anything is available or sold out. Say the returned `say` text.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none", "price_note": "excluding GST and stamp duty"}
    key = (bhk or "").lower().replace(" ", "")
    if key not in catalog["units"]:
        return {"ok": False, "say": "Which configuration should I check?"}
    n = catalog["units"][key]
    say = (f"Yes, {key.upper()} homes are available right now." if n > 0
           else f"The {key.upper()} homes are fully sold out right now. I can note your interest and call you if one opens up.")
    return {"ok": True, "bhk": key, "units_left": n, "available": n > 0, "say": say}
