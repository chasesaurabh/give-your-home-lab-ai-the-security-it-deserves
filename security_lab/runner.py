"""Deterministic evidence with separate quality and security denominators."""

from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import platform

from .policy import RequestContext, audit_event, hardened, unsafe

ROOT = Path(__file__).resolve().parent.parent
LIMITATIONS = [
    "No real model, model quality measurement, or injection-success rate.",
    "Synthetic in-process authorization only; no real authentication or sandbox.",
    "No HTTP, LAN, firewall, container, credential-store, or OS isolation test.",
    "Logical steps are test inputs, not metered compute or cumulative quotas.",
    "Finite checks do not establish security outside the tested cases.",
    "Byte digests identify inputs; they are not a trusted provenance signature.",
]


def load_fixture(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def build_report():
    # Hash exactly the fixture bytes consumed below, not a later reread.
    fixture_bytes = {p.name: p.read_bytes() for p in sorted((ROOT / "fixtures").glob("*.json"))}
    fixtures = {name: json.loads(raw) for name, raw in fixture_bytes.items()}
    documents = fixtures["documents.json"]
    cases = fixtures["security.json"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Security cases must be nonempty and uniquely identified")
    if not any(c["expected_allowed"] is True for c in cases):
        raise ValueError("Missing legitimate allow control")
    rows, events = [], []
    for case in cases:
        context = RequestContext(authenticated=case["authenticated"])
        for name, adapter in (("unsafe", unsafe), ("hardened", hardened)):
            outcome = adapter(case["proposal"], context, case["steps"], documents)
            decision_match = outcome.allowed is case["expected_allowed"]
            # The deliberately unsafe adapter has a different reason vocabulary.
            reason_match = name == "unsafe" or outcome.reason == case["expected_reason"]
            rows.append({"id": case["id"], "label": case["label"], "adapter": name,
                         "expected_allowed": case["expected_allowed"],
                         "observed_allowed": outcome.allowed, "reason": outcome.reason,
                         "matches_contract": decision_match and reason_match})
            events.append(audit_event(case["id"], name, outcome))
    quality = []
    for case in fixtures["quality.json"]:
        passed = (case["stub_answer"] == case["expected_answer"]
                  and case["stub_citation"] == case["expected_citation"])
        quality.append({"id": case["id"], "task": case["task"], "passed": passed,
                        "matches_known_demonstration": passed is case["expected_pass"]})
    if not quality or all(row["passed"] for row in quality):
        raise ValueError("Quality fixtures must retain a deliberate failure control")
    summary = {}
    for adapter in ("unsafe", "hardened"):
        subset = [r for r in rows if r["adapter"] == adapter]
        summary[adapter] = {"matched": sum(r["matches_contract"] for r in subset),
                            "total": len(subset)}
    quality_summary = {"passed": sum(r["passed"] for r in quality), "total": len(quality),
                       "backend": "fixed stub fixtures, not a model"}
    intact = (summary["hardened"]["matched"] == len(cases)
              and summary["unsafe"]["matched"] < len(cases)
              and all(q["matches_known_demonstration"] for q in quality))
    sources = sorted((ROOT / "security_lab").glob("*.py"))
    return {
        "schema_version": 1, "state": "planning prototype; no edition release",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "os": platform.system(),
                        "os_version": platform.version(), "machine": platform.machine()},
        "fixture_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in fixture_bytes.items()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "quality_summary": quality_summary, "quality_cases": quality,
        "security_summary": summary, "security_cases": rows,
        "audit_events": events, "demonstration_intact": intact,
        "limitations": LIMITATIONS,
    }


def render_html(report):
    # Use inert escaped text for arbitrary case labels; no scripts or remote assets.
    data = html.escape(json.dumps(report, indent=2, ensure_ascii=False))
    q = report["quality_summary"]
    h = report["security_summary"]["hardened"]
    u = report["security_summary"]["unsafe"]
    return ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Local AI Security Lab evidence</title>"
            "<style>body{font:17px system-ui;max-width:70rem;margin:2rem auto;padding:0 1rem}"
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f3f4;padding:1rem}"
            "h1{line-height:1.2}</style><h1>Local AI Security Lab evidence</h1>"
            "<p>Planning prototype: synthetic in-process controls and fixed stub answers.</p>"
            f"<h2>Quality: {q['passed']}/{q['total']} fixed examples satisfy the rubric</h2>"
            "<p>One wrong citation deliberately fails. These are not model results.</p>"
            f"<h2>Security contracts: hardened {h['matched']}/{h['total']}; "
            f"unsafe {u['matched']}/{u['total']}</h2>"
            "<p>Contracts include legitimate allows. The unsafe baseline deliberately fails denies. "
            "A finite pass does not establish secure deployment.</p>"
            f"<h2>Evidence and limitations</h2><pre>{data}</pre></html>")


def write_report(report, destination):
    path = Path(destination)
    path.mkdir(parents=True, exist_ok=False)
    (path / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (path / "report.html").write_text(render_html(report), encoding="utf-8")
