"""UC-5 recording: render a simulated call to audio with two synthetic voices (Edge neural TTS, free) and ffmpeg.
Gap before each agent turn = the measured text-pipeline latency of that turn (model + audit), so silence is not hidden.
Rehearsal use only — contest recordings come from the voice platform's own test calls."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List

CUSTOMER_GAP_S = 0.6


async def _tts(text: str, voice: str, path: str) -> None:
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)


def _silence(path: str, seconds: float) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", f"{max(seconds, 0.05):.2f}", "-c:a", "libmp3lame", "-b:a", "48k", path], check=True)


def render_call(call: Dict[str, Any], voice_cfg: Dict[str, Any], out_path: str) -> str:
    agent_voice = voice_cfg.get("tts_voice_agent", "en-IN-NeerjaNeural")
    cust_voice = voice_cfg.get("tts_voice_customer", "en-IN-PrabhatNeural")
    tmp = tempfile.mkdtemp(prefix="proofcall-")
    parts: List[str] = []
    timeline: List[Dict[str, Any]] = []
    for i, t in enumerate(call["turns"]):
        text = (t.get("text") or "").strip()
        if not text:
            continue
        gap = (t.get("model_ms", 0) + t.get("audit_ms", 0)) / 1000 if t["role"] == "agent" else CUSTOMER_GAP_S
        if i > 0:
            sp = os.path.join(tmp, f"{i:03d}_gap.mp3")
            _silence(sp, gap)
            parts.append(sp)
        vp = os.path.join(tmp, f"{i:03d}_{t['role']}.mp3")
        asyncio.get_event_loop().run_until_complete(_tts(text, agent_voice if t["role"] == "agent" else cust_voice, vp))
        parts.append(vp)
        timeline.append({"turn": i, "role": t["role"], "gap_before_s": round(gap, 2) if i > 0 else 0, "text": text})
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "64k", out_path], check=True)
    with open(os.path.splitext(out_path)[0] + ".timeline.json", "w", encoding="utf-8") as f:
        json.dump({"scenario": call["scenario_id"], "mode": call["mode"], "run": call["run"],
                   "voices": {"agent": agent_voice, "customer": cust_voice, "both_synthetic": True},
                   "timeline": timeline}, f, ensure_ascii=False, indent=1)
    return out_path
