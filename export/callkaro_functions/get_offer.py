@tool
async def get_offer(lang: str = "en") -> dict:
    """
    Live offer, if any. Use whenever the customer asks for a discount, offer, waiver or cashback.
    Never promise anything that is not returned here.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": [{"label": "tomorrow 11:00 AM", "iso": "2026-10-14T11:00:00+05:30"}, {"label": "tomorrow 4:30 PM", "iso": "2026-10-14T16:30:00+05:30"}], "saturday": [{"label": "Saturday 10:30 AM", "iso": "2026-10-17T10:30:00+05:30"}, {"label": "Saturday 3:00 PM", "iso": "2026-10-17T15:00:00+05:30"}], "sunday": [{"label": "Sunday 12:00 PM", "iso": "2026-10-18T12:00:00+05:30"}], "weekday": [{"label": "Wednesday 5:00 PM", "iso": "2026-10-21T17:00:00+05:30"}]}, "offer": "none", "price_note": "excluding GST and stamp duty", "as_of": "2026-10-13 (rehearsal clock)"}
    offer = catalog.get("offer") or "none"
    if offer == "none":
        return {"ok": True, "offer": "none",
                "say": "Abhi koi offer nahi chal raha, price sheet wala rate hi lagega." if (lang or "en").lower().startswith("hi") else "There is no offer running right now; the price-sheet price applies."}
    return {"ok": True, "offer": offer, "say": f"Current offer: {offer}."}
