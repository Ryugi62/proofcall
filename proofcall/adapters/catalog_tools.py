"""ToolBackend over a static catalog JSON (rehearsal). The official brief replaces the catalog file."""
from __future__ import annotations

import itertools
import json
from typing import Any, Dict


class CatalogTools:
    def __init__(self, catalog: Dict[str, Any]):
        self.c = catalog
        self._ids = itertools.count(1001)

    @staticmethod
    def load(path: str) -> "CatalogTools":
        with open(path, encoding="utf-8") as f:
            return CatalogTools(json.load(f))

    def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        bhk = str(args.get("bhk", "")).lower().replace(" ", "")
        if name == "get_price":
            p = self.c["prices"].get(bhk)
            if not p:
                return {"message": f"no configuration {bhk!r}; options: {', '.join(self.c['prices'])}"}
            return {f"price.{bhk}.from": p["from"], f"price.{bhk}.booking_amount": p["booking_amount"]}
        if name == "check_units":
            if bhk not in self.c["units"]:
                return {"message": f"no configuration {bhk!r}"}
            return {f"availability.units.{bhk}": self.c["units"][bhk]}
        if name == "check_slots":
            day = str(args.get("day", "")).lower()
            slots = self.c["slots"].get(day)
            if slots is None:
                return {"message": f"unknown day {day!r}; use one of {', '.join(self.c['slots'])}"}
            return {"availability.slots": ", ".join(slots) if slots else "no slots"}
        if name == "get_offer":
            return {"offer.current": self.c.get("offer", "none")}
        if name == "book_site_visit":
            slot = str(args.get("slot", ""))
            all_slots = [s for v in self.c["slots"].values() for s in v]
            if slot not in all_slots:
                return {"message": f"slot {slot!r} is not an open slot"}
            return {"booking.id": f"GL-{next(self._ids)}", "booking.slot": slot}
        if name == "send_brochure":
            return {"brochure.sent": "yes"}
        if name in ("transfer_to_sales", "end_call"):
            return {"message": "ok"}
        return {"message": f"unknown tool {name}"}
