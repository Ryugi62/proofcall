@tool
async def check_units(bhk: str, lang: str = "en") -> dict:
    """
    Units left for a configuration. Use before saying anything is available or sold out. Speak the returned `say` text.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": [{"label": "tomorrow 11:00 AM", "iso": "2026-10-14T11:00:00+05:30"}, {"label": "tomorrow 4:30 PM", "iso": "2026-10-14T16:30:00+05:30"}], "saturday": [{"label": "Saturday 10:30 AM", "iso": "2026-10-17T10:30:00+05:30"}, {"label": "Saturday 3:00 PM", "iso": "2026-10-17T15:00:00+05:30"}], "sunday": [{"label": "Sunday 12:00 PM", "iso": "2026-10-18T12:00:00+05:30"}], "weekday": [{"label": "Wednesday 5:00 PM", "iso": "2026-10-21T17:00:00+05:30"}]}, "offer": "none", "price_note": "excluding GST and stamp duty", "as_of": "2026-10-13 (rehearsal clock)"}
    key = (bhk or "").lower().replace(" ", "")
    if key not in catalog["units"]:
        return {"ok": False, "say": "Kaunsa configuration check karoon?" if (lang or "en").lower().startswith("hi") else "Which configuration should I check?"}
    n = catalog["units"][key]
    if (lang or "en").lower().startswith("hi"):
        say = (f"Haan, {key.upper()} abhi available hai." if n > 0 else
               f"{key.upper()} abhi poora sold out hai. Koi unit khulte hi main aapko call karwa sakti hoon.")
    else:
        say = (f"Yes, {key.upper()} homes are available right now." if n > 0 else
               f"The {key.upper()} homes are fully sold out right now. I can arrange a call if one opens up.")
    return {"ok": True, "bhk": key, "units_left": n, "available": n > 0, "say": say}
