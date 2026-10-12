"""LanguageModel adapter for the Gemini REST API (free tier). Key from env GEMINI_API_KEY; paced for RPM limits."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Dict, List


class GeminiModel:
    _shared_last = 0.0      # one pacer for every instance: the free-tier RPM limit is per key
    def __init__(self, model: str = "gemini-3.5-flash-lite", temperature: float = 0.4, min_interval_s: float = 4.2,
                 max_retries: int = 6):
        self.model, self.temperature = model, temperature
        self.min_interval_s, self.max_retries = min_interval_s, max_retries
        self.key = os.environ.get("GEMINI_API_KEY", "")
        self.calls = 0
        self.last_ms = None

    def complete(self, system: str, messages: List[Dict[str, str]]) -> str:
        if not self.key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": m["content"]}]} for m in messages],
                "generationConfig": {"temperature": self.temperature, "responseMimeType": "application/json"}}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        delay = 5.0
        for attempt in range(self.max_retries):
            wait = self.min_interval_s - (time.monotonic() - GeminiModel._shared_last)
            if wait > 0:
                time.sleep(wait)
            GeminiModel._shared_last = time.monotonic()
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "x-goog-api-key": self.key})
            try:
                t0 = time.monotonic()
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.loads(r.read())
                self.last_ms = (time.monotonic() - t0) * 1000
                self.calls += 1
                parts = data["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts)
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < self.max_retries - 1:
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    continue
                raise RuntimeError(f"Gemini HTTP {e.code}: {e.read()[:200]!r}")
            except (KeyError, IndexError):
                return ""
        raise RuntimeError("Gemini retries exhausted")
