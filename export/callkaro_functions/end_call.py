@tool
async def end_call(reason: str) -> dict:
    """
    End the call (maps to the platform end_call) once the outcome is clear or the customer wants to stop.
    """
    return {"ok": True, "reason": reason}
