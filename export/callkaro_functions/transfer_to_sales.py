@tool
async def transfer_to_sales(summary: str) -> dict:
    """
    Warm transfer to a human sales executive (maps to the platform transfer_call, warm mode) with a one-line summary.
    """
    return {"ok": True, "summary": summary, "say": "I'm connecting you to our sales manager now. Please hold."}
