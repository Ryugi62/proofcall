@tool
async def check_slots(day: str, lang: str = "en") -> dict:
    """
    Open site-visit slots for a day (today, tomorrow, saturday, sunday, weekday).
    Use before offering or confirming any visit time. Offer first_slot by its exact label.
    """
    catalog = {"prices": {"2bhk": {"from": "₹1.12 crore", "booking_amount": "₹5 lakh", "from_inr": 11200000, "booking_amount_inr": 500000}, "3bhk": {"from": "₹1.58 crore", "booking_amount": "₹7 lakh", "from_inr": 15800000, "booking_amount_inr": 700000}, "4bhk": {"from": "₹2.35 crore", "booking_amount": "₹10 lakh", "from_inr": 23500000, "booking_amount_inr": 1000000}}, "units": {"2bhk": 14, "3bhk": 6, "4bhk": 0}, "slots": {"today": [], "tomorrow": [{"label": "tomorrow 11:00 AM", "iso": "2026-10-14T11:00:00+05:30"}, {"label": "tomorrow 4:30 PM", "iso": "2026-10-14T16:30:00+05:30"}], "saturday": [{"label": "Saturday 10:30 AM", "iso": "2026-10-17T10:30:00+05:30"}, {"label": "Saturday 3:00 PM", "iso": "2026-10-17T15:00:00+05:30"}], "sunday": [{"label": "Sunday 12:00 PM", "iso": "2026-10-18T12:00:00+05:30"}], "weekday": [{"label": "Wednesday 5:00 PM", "iso": "2026-10-21T17:00:00+05:30"}]}, "offer": "none", "price_note": "excluding GST and stamp duty", "as_of": "2026-10-13 (rehearsal clock)"}
    d = (day or "").lower()
    slots = catalog["slots"].get(d)
    if slots is None:
        return {"ok": False, "slots": "", "first_slot": "",
                "say": "Kaunsa din theek rahega, kal ya weekend?" if (lang or "en").lower().startswith("hi") else "Which day suits you, tomorrow or the weekend?"}
    if not slots:
        return {"ok": True, "slots": "", "first_slot": "",
                "say": f"{d} koi slot khali nahi hai. Kal check karoon?" if (lang or "en").lower().startswith("hi") else f"There are no open slots {d}. Shall I check tomorrow?"}
    first = slots[0]
    return {"ok": True, "slots": ", ".join(s["label"] for s in slots), "first_slot": first["label"], "first_slot_iso": first["iso"],
            "say": f"Sabse pehla khali slot {first['label']} hai." if (lang or "en").lower().startswith("hi") else f"The earliest open slot is {first['label']}."}
