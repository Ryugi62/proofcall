@tool
async def get_offer() -> dict:
    """
    Get the live offer, if any. Use whenever the customer asks for a discount, offer, waiver or cashback.
    Say the returned `say` text exactly. Never promise anything that is not returned here.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh"}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh"}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh"}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": ["tomorrow 11:00 AM", "tomorrow 4:30 PM"], "saturday": ["Saturday 10:30 AM", "Saturday 3:00 PM"], "sunday": ["Sunday 12:00 PM"], "weekday": ["Wednesday 5:00 PM"]}, "offer": "none"}
    offer = catalog.get("offer", "none")
    if not offer or offer == "none":
        return {"say": "There is no offer running right now; the price sheet price applies.", "offer": "none"}
    return {"say": f"The current offer is: {offer}.", "offer": offer}
