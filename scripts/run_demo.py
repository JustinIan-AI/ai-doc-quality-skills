#!/usr/bin/env python3
"""End-to-end demo on fixtures/ → out/report.html"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_config, write_json  # noqa: E402
from ingest_markdown import ingest  # noqa: E402
from scorecard_report import build_report, render_html, render_markdown  # noqa: E402
from structure_rules_check import check_structure  # noqa: E402
from traceability_audit import audit  # noqa: E402


def main() -> int:
    cfg = load_config()
    fixtures = ROOT / "fixtures"
    out = ROOT / "out"
    out.mkdir(exist_ok=True)

    prd = fixtures / "sample_prd.md"
    design = fixtures / "sample_design.md"
    test = fixtures / "sample_test.md"

    prd_ingest = ingest(prd, cfg)
    write_json(out / "ingest_prd.json", prd_ingest)

    struct = check_structure(prd_ingest, "prd", cfg)
    write_json(out / "structure_prd.json", struct)

    pattern = cfg.get("req_id_pattern", r"(?:REQ|US|AC)[-_]?\d+(?:\.\d+)*")
    from common import extract_req_ids

    req_ids = extract_req_ids(prd.read_text(encoding="utf-8"), pattern)
    design_ids = extract_req_ids(design.read_text(encoding="utf-8"), pattern)
    test_ids = extract_req_ids(test.read_text(encoding="utf-8"), pattern)
    trace = audit(req_ids, design_ids, test_ids, cfg)
    write_json(out / "traceability.json", trace)

    # Optional semantic mock findings (simulating LLM skill output)
    semantic_path = fixtures / "sample_semantic_findings.json"
    bundles = [struct, trace]
    if semantic_path.exists():
        bundles.append(json.loads(semantic_path.read_text(encoding="utf-8")))

    report = build_report(bundles, cfg, "prd")
    write_json(out / "report.json", report)
    (out / "report.md").write_text(render_markdown(report), encoding="utf-8")
    (out / "report.html").write_text(render_html(report), encoding="utf-8")

    print(f"Verdict: {report['verdict']}  Overall: {report['overall_score']}")
    print(f"Wrote {out / 'report.html'}")
    return 0 if report["verdict"] in {"PASS", "PASS_WITH_RISKS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
