@tool
async def check_units(bhk: str) -> dict:
    """
    Check how many units are left for a configuration. Use before saying anything is available or sold out.
    Say the returned `say` text exactly.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh"}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh"}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh"}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none"}
    key = (bhk or "").lower().replace(" ", "")
    if key not in catalog["units"]:
        return {"say": "Which configuration should I check, 2, 3 or 4 BHK?", "found": False}
    n = catalog["units"][key]
    say = (f"Yes, {key.upper()} homes are available right now." if n > 0
           else f"The {key.upper()} homes are fully sold out at the moment.")
    return {"say": say, "units_left": n, "found": True}
