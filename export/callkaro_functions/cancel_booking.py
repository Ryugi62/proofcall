@tool
async def cancel_booking(booking_id: str, reason: str, lang: str = "en") -> dict:
    """
    Cancel a site visit booked earlier in this call when the customer withdraws.
    """
    if not (booking_id or "").startswith("GL-"):
        return {"ok": False, "say": "There is no booking to cancel."}
    return {"ok": True, "cancelled": booking_id, "reason": reason,
            "say": "Theek hai, visit cancel kar diya." if (lang or "en").lower().startswith("hi") else "Okay, I have cancelled that visit."}
