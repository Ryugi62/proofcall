@tool
async def get_offer() -> dict:
    """
    Live offer, if any. Use whenever the customer asks for a discount, offer, waiver or cashback.
    Never promise anything that is not returned here.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none", "price_note": "excluding GST and stamp duty"}
    offer = catalog.get("offer") or "none"
    if offer == "none":
        return {"ok": True, "offer": "none", "say": "There is no offer running right now; the price-sheet price applies."}
    return {"ok": True, "offer": offer, "say": f"The current offer is {offer}."}
