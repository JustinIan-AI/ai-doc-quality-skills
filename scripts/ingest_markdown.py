#!/usr/bin/env python3
"""Parse Markdown into outline / req_ids / assets (doc-ingest skeleton)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    DEFAULT_CONFIG_JSON,
    extract_asset_labels,
    extract_headings,
    extract_req_ids,
    load_config,
    write_json,
)


def guess_type(text: str, outline_titles: list[str]) -> str:
    blob = " ".join(outline_titles) + "\n" + text[:2000]
    scores = {
        "prd": sum(k in blob for k in ("验收", "用户故事", "范围", "Acceptance", "User Stor")),
        "design": sum(k in blob for k in ("架构", "数据模型", "API", "状态机", "Architecture")),
        "test": sum(k in blob for k in ("测试用例", "覆盖", "前置条件", "Test Case", "期望结果")),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def ingest(path: Path, cfg: dict) -> dict:
    text = path.read_text(encoding="utf-8")
    outline = extract_headings(text)
    titles = [o["title"] for o in outline]
    pattern = cfg.get("req_id_pattern", r"(?:REQ|US|AC)[-_]?\d+(?:\.\d+)*")
    return {
        "doc_path": str(path),
        "suggested_type": guess_type(text, titles),
        "outline": outline,
        "req_ids": extract_req_ids(text, pattern),
        "assets": extract_asset_labels(text),
        "notes": [],
        "char_count": len(text),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Markdown doc-ingest skeleton")
    p.add_argument("markdown", type=Path, help="Path to .md file")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("-o", "--output", type=Path, default=None, help="Write JSON result")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    result = ingest(args.markdown, cfg)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        write_json(args.output, result)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
