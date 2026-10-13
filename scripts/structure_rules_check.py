#!/usr/bin/env python3
"""Deterministic structure rules check → findings bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import bundle, finding, load_config, section_present, write_json
from ingest_markdown import ingest


def check_structure(ingest_result: dict, doc_type: str, cfg: dict) -> dict:
    rules = cfg.get("structure_rules", {})
    aliases = cfg.get("section_aliases", {})
    key = {
        "prd": "prd_required_sections",
        "design": "design_required_sections",
        "test": "test_required_sections",
    }.get(doc_type)

    findings = []
    titles = [o["title"] for o in ingest_result.get("outline", [])]

    if not key:
        findings.append(
            finding(
                fid="STRUCT-000",
                severity="P2",
                category="structure",
                location="document",
                problem=f"无法应用结构规则：doc_type={doc_type}",
                impact="可能漏检必备章节",
                recommendation="在调用时显式传入 --type prd|design|test",
                blocking=False,
                evidence_type="needs_confirmation",
                lenses=["structure"],
            )
        )
        return bundle(
            skill_id="structure-rules-check",
            doc_type=doc_type,
            doc_path=ingest_result.get("doc_path", ""),
            score_config_version=str(cfg.get("version", "1.0.0")),
            findings=findings,
            summary="doc_type unknown",
        )

    required = rules.get(key, [])
    for i, section in enumerate(required, start=1):
        if not section_present(titles, section, aliases):
            findings.append(
                finding(
                    fid=f"STRUCT-{i:03d}",
                    severity="P0",
                    category="structure",
                    location=f"missing section ≈ {section}",
                    problem=f"缺少必备章节：{section}",
                    impact="结构不完整，后续语义评审与追踪不可靠",
                    recommendation=f"补充「{section}」章节（或使用企业配置的同义标题）",
                    blocking=True,
                    evidence_type="fact_defect",
                    lenses=["structure"],
                )
            )

    if not titles:
        findings.append(
            finding(
                fid="STRUCT-HEAD",
                severity="P1",
                category="structure",
                location="document",
                problem="未检测到 Markdown 标题（# 标题）",
                impact="无法做章节级定位与必备项检查",
                recommendation="使用 AT1–H3 组织文档",
                blocking=False,
                evidence_type="fact_defect",
                lenses=["structure"],
            )
        )

    return bundle(
        skill_id="structure-rules-check",
        doc_type=doc_type,
        doc_path=ingest_result.get("doc_path", ""),
        score_config_version=str(cfg.get("version", "1.0.0")),
        findings=findings,
        summary=f"checked {len(required)} required sections; {len(findings)} findings",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Structure rules check skeleton")
    p.add_argument("markdown", type=Path, nargs="?", help="Markdown file (or use --ingest-json)")
    p.add_argument("--ingest-json", type=Path, help="Precomputed ingest JSON")
    p.add_argument("--type", choices=["prd", "design", "test", "auto"], default="auto")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args(argv)

    cfg = load_config(args.config)

    if args.ingest_json:
        ingest_result = json.loads(args.ingest_json.read_text(encoding="utf-8"))
    elif args.markdown:
        ingest_result = ingest(args.markdown, cfg)
    else:
        p.error("Provide markdown path or --ingest-json")

    doc_type = args.type
    if doc_type == "auto":
        doc_type = ingest_result.get("suggested_type") or "unknown"

    result = check_structure(ingest_result, doc_type, cfg)
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not any(f.get("blocking") for f in result["findings"]) else 2


if __name__ == "__main__":
    sys.exit(main())
