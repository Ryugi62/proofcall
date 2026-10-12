"""Composition root and CLI.

  python -m proofcall run --config configs/X.json --catalog configs/Y.json --scenarios scenarios/Z.yaml \
        --modes guarded,baseline --runs 1 [--only S01,S04] --out runs/<id>
  python -m proofcall export --config configs/X.json --out export/
  python -m proofcall render --results runs/<id>/results.json --call S01:guarded:1 --out recordings/x.mp3
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import List

import yaml

from ..application.agent import AgentEngine
from ..application.simulate import report_markdown, records_to_json, run_call
from ..domain.model import AgentConfig, Scenario


class MonoClock:
    def now(self) -> float:
        return time.monotonic()


def _load_env(path: str = "~/.config/jarvis/env/gemini.env") -> None:
    p = os.path.expanduser(os.environ.get("PROOFCALL_ENV", path))
    if os.path.exists(p) and not os.environ.get("GEMINI_API_KEY"):
        for line in open(p):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.replace("export ", "").strip(), v.strip().strip("'\""))


def cmd_run(a: argparse.Namespace) -> int:
    from ..adapters.function_tools import FunctionTools
    from ..adapters.gemini import GeminiModel
    _load_env()
    raw_cfg = json.load(open(a.config, encoding="utf-8"))
    catalog = json.load(open(a.catalog, encoding="utf-8"))
    config = AgentConfig.from_dict(raw_cfg)
    scenarios = [Scenario.from_dict(d) for d in yaml.safe_load(open(a.scenarios, encoding="utf-8"))]
    if a.only:
        keep = set(a.only.split(","))
        scenarios = [s for s in scenarios if s.id in keep]
    os.makedirs(a.out, exist_ok=True)
    agent_llm = GeminiModel(model=a.agent_model, temperature=0.3)
    cust_llm = GeminiModel(model=a.customer_model, temperature=0.8)
    records = []
    for sc in scenarios:
        for mode in a.modes.split(","):
            for run in range(1, a.runs + 1):
                eng = AgentEngine(config, agent_llm, FunctionTools(raw_cfg, catalog), MonoClock(), mode=mode)
                def show(row):
                    tag = "AGENT" if row["role"] == "agent" else "CUST "
                    extra = (" BLOCKED" if row.get("blocked") else "") + (" VIOL " + ",".join(v["code"] for v in row["violations"]) if row.get("violations") else "")
                    print(f"  [{sc.id} {mode} r{run}] {tag}: {row['text']}{extra}", flush=True)
                rec = run_call(config, sc, eng, cust_llm, run=run, on_turn=show)
                print(f"== {sc.id} {mode} r{run}: outcome={rec.outcome} expected={rec.expected} "
                      f"violations={len(rec.violations)} blocked={len(rec.blocked)} error={rec.error}", flush=True)
                records.append(rec)
                with open(os.path.join(a.out, "results.json"), "w", encoding="utf-8") as f:
                    f.write(records_to_json(records))
    with open(os.path.join(a.out, "report.md"), "w", encoding="utf-8") as f:
        f.write(report_markdown(records, {s.id: s for s in scenarios}))
    print(f"LLM calls: agent={agent_llm.calls} customer={cust_llm.calls}")
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    from ..application.simulate import CallRecord
    data = json.load(open(a.results, encoding="utf-8"))
    records = [CallRecord(**c) for c in data["calls"]]
    scenarios = {d["id"]: Scenario.from_dict(d) for d in yaml.safe_load(open(a.scenarios, encoding="utf-8"))}
    out = os.path.join(os.path.dirname(a.results), "report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(report_markdown(records, scenarios))
    with open(a.results, "w", encoding="utf-8") as f:
        f.write(records_to_json(records))
    print(out)
    return 0


def cmd_reaudit(a: argparse.Namespace) -> int:
    from ..application.reaudit import reaudit
    config = AgentConfig.from_dict(json.load(open(a.config, encoding="utf-8")))
    data = json.load(open(a.transcript, encoding="utf-8"))
    result = reaudit(config, data["turns"] if isinstance(data, dict) else data)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if result["violations"] == 0 else 1


def cmd_export(a: argparse.Namespace) -> int:
    from ..adapters.export import export_all
    config = json.load(open(a.config, encoding="utf-8"))
    catalog = json.load(open(a.catalog, encoding="utf-8")) if a.catalog else None
    for p in export_all(config, a.out, catalog):
        print(p)
    return 0


def cmd_render(a: argparse.Namespace) -> int:
    from ..adapters.speech import render_call
    data = json.load(open(a.results, encoding="utf-8"))
    sid, mode, run = a.call.split(":")
    call = next(c for c in data["calls"] if c["scenario_id"] == sid and c["mode"] == mode and str(c["run"]) == run)
    config = json.load(open(a.config, encoding="utf-8"))
    print(render_call(call, config.get("voice", {}), a.out))
    return 0


def main(argv: List[str] = None) -> int:
    ap = argparse.ArgumentParser(prog="proofcall")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True)
    r.add_argument("--catalog", required=True)
    r.add_argument("--scenarios", required=True)
    r.add_argument("--modes", default="guarded,baseline")
    r.add_argument("--runs", type=int, default=1)
    r.add_argument("--only", default="")
    r.add_argument("--out", required=True)
    r.add_argument("--agent-model", default="gemini-3.5-flash-lite")
    r.add_argument("--customer-model", default="gemini-3.5-flash-lite")
    e = sub.add_parser("export")
    e.add_argument("--config", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--catalog", default="")
    d = sub.add_parser("render")
    d.add_argument("--results", required=True)
    d.add_argument("--config", required=True)
    d.add_argument("--call", required=True)
    d.add_argument("--out", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--results", required=True)
    rp.add_argument("--scenarios", required=True)
    ra = sub.add_parser("reaudit")
    ra.add_argument("--config", required=True)
    ra.add_argument("--transcript", required=True)
    a = ap.parse_args(argv)
    return {"run": cmd_run, "export": cmd_export, "render": cmd_render, "report": cmd_report,
            "reaudit": cmd_reaudit}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
