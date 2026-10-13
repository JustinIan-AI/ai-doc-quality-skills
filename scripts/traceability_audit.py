#!/usr/bin/env python3
"""Requirement ↔ design ↔ test ID set-diff traceability audit."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import bundle, extract_req_ids, finding, load_config, write_json


def load_ids_from_file(path: Path, pattern: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return extract_req_ids(text, pattern)


def load_ids_from_json_list(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(x).upper().replace("_", "-") for x in data]
    if isinstance(data, dict) and "req_ids" in data:
        return [str(x).upper().replace("_", "-") for x in data["req_ids"]]
    raise ValueError(f"Unsupported ID file shape: {path}")


def audit(
    req_ids: list[str],
    design_ids: list[str],
    test_ids: list[str],
    cfg: dict,
    core_prefix: str = "REQ-",
) -> dict:
    req_set, design_set, test_set = set(req_ids), set(design_ids), set(test_ids)
    findings = []
    n = 0

    def add(**kwargs):
        nonlocal n
        n += 1
        kwargs.setdefault("fid", f"TRACE-{n:03d}")
        findings.append(finding(**kwargs))

    missing_design = sorted(req_set - design_set)
    missing_test = sorted(req_set - test_set)
    orphan_design = sorted(design_set - req_set)
    orphan_test = sorted(test_set - req_set)

    for rid in missing_design:
        is_core = rid.startswith(core_prefix.upper()) or rid.startswith("REQ")
        add(
            severity="P0" if is_core else "P1",
            category="traceability",
            location=f"req:{rid}",
            problem=f"需求 {rid} 在设计侧无对应 ID/锚点",
            impact="实现可能遗漏该需求",
            recommendation=f"在设计文档中显式引用 {rid} 并描述实现路径",
            blocking=is_core,
            evidence_type="fact_defect",
            lenses=["traceability"],
            related_req_ids=[rid],
        )

    for rid in missing_test:
        is_core = rid.startswith(core_prefix.upper()) or rid.startswith("REQ")
        add(
            severity="P0" if is_core else "P1",
            category="traceability",
            location=f"req:{rid}",
            problem=f"需求 {rid} 无测试覆盖引用",
            impact="无法验证该需求是否交付",
            recommendation=f"补充覆盖 {rid} 的用例并在用例中写明 ID",
            blocking=is_core,
            evidence_type="fact_defect",
            lenses=["traceability"],
            related_req_ids=[rid],
        )

    for rid in orphan_design:
        add(
            severity="P2",
            category="traceability",
            location=f"design:{rid}",
            problem=f"设计引用 {rid} 但需求列表中不存在",
            impact="可能是范围蔓延或 ID 不一致",
            recommendation="核对是否应补需求，或修正设计中的 ID",
            blocking=False,
            evidence_type="needs_confirmation",
            lenses=["traceability"],
            related_req_ids=[rid],
        )

    for rid in orphan_test:
        add(
            severity="P2",
            category="traceability",
            location=f"test:{rid}",
            problem=f"测试引用 {rid} 但需求列表中不存在",
            impact="无效覆盖或 ID 漂移",
            recommendation="对齐需求 ID 或删除无效用例引用",
            blocking=False,
            evidence_type="needs_confirmation",
            lenses=["traceability"],
            related_req_ids=[rid],
        )

    matrix = {
        "req_ids": sorted(req_set),
        "design_ids": sorted(design_set),
        "test_ids": sorted(test_set),
        "missing_design": missing_design,
        "missing_test": missing_test,
        "orphan_design": orphan_design,
        "orphan_test": orphan_test,
    }

    result = bundle(
        skill_id="traceability-audit",
        doc_type="bundle",
        score_config_version=str(cfg.get("version", "1.0.0")),
        findings=findings,
        summary=(
            f"req={len(req_set)} design={len(design_set)} test={len(test_set)}; "
            f"findings={len(findings)}"
        ),
    )
    result["matrix"] = matrix
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Traceability set-diff audit")
    p.add_argument("--req", type=Path, help="PRD markdown or JSON with req_ids")
    p.add_argument("--design", type=Path, help="Design markdown or JSON")
    p.add_argument("--test", type=Path, help="Test markdown or JSON")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    pattern = cfg.get("req_id_pattern", r"(?:REQ|US|AC)[-_]?\d+(?:\.\d+)*")

    def load_side(path: Path | None) -> list[str]:
        if path is None:
            return []
        if path.suffix.lower() == ".json":
            return load_ids_from_json_list(path)
        return load_ids_from_file(path, pattern)

    result = audit(load_side(args.req), load_side(args.design), load_side(args.test), cfg)
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not any(f.get("blocking") for f in result["findings"]) else 2


if __name__ == "__main__":
    sys.exit(main())
