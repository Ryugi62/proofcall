@tool
async def transfer_to_sales(summary: str, lang: str = "en") -> dict:
    """
    Warm transfer to a human sales executive (maps to the platform transfer_call, warm mode) with a one-line summary.
    """
    return {"ok": True, "summary": summary,
            "say": "Main aapko abhi sales manager se connect karti hoon, ek moment." if (lang or "en").lower().startswith("hi") else "I'm connecting you to our sales manager now, one moment."}
