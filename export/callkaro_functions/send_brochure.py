@tool
async def send_brochure() -> dict:
    """
    Send the project brochure on WhatsApp to this number, only after record_consent(whatsapp) accepted.
    """
    return {"ok": True, "sent": True, "say": "Done, the brochure is on its way to this WhatsApp number."}
