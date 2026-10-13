#!/usr/bin/env python3
"""Shared helpers for doc-quality deterministic scripts (stdlib-first)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_JSON = ROOT / "config" / "score-config.json"
DEFAULT_CONFIG_YAML = ROOT / "config" / "score-config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load score config. Prefer JSON; try YAML if PyYAML is installed."""
    if path is not None:
        p = Path(path)
        if p.suffix.lower() in {".yaml", ".yml"}:
            return _load_yaml(p)
        return json.loads(p.read_text(encoding="utf-8"))

    if DEFAULT_CONFIG_JSON.exists():
        return json.loads(DEFAULT_CONFIG_JSON.read_text(encoding="utf-8"))
    if DEFAULT_CONFIG_YAML.exists():
        return _load_yaml(DEFAULT_CONFIG_YAML)
    raise FileNotFoundError("No score-config.json or score-config.yaml found under config/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise SystemExit(
            f"PyYAML required to load {path}. Install PyYAML or use config/score-config.json"
        ) from e
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finding(
    *,
    fid: str,
    severity: str,
    category: str,
    location: str,
    problem: str,
    impact: str,
    recommendation: str,
    blocking: bool,
    evidence_type: str = "fact_defect",
    lenses: list[str] | None = None,
    related_req_ids: list[str] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": fid,
        "severity": severity,
        "category": category,
        "location": location,
        "problem": problem,
        "impact": impact,
        "recommendation": recommendation,
        "blocking": blocking,
        "evidence_type": evidence_type,
    }
    if lenses:
        item["lenses"] = lenses
    if related_req_ids:
        item["related_req_ids"] = related_req_ids
    return item


def bundle(
    *,
    skill_id: str,
    doc_type: str,
    findings: list[dict[str, Any]],
    doc_path: str = "",
    score_config_version: str = "1.0.0",
    checklist_version: str = "",
    open_questions: list[str] | None = None,
    summary: str = "",
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema_version": "1.0.0",
        "skill_id": skill_id,
        "doc_type": doc_type,
        "doc_path": doc_path,
        "score_config_version": score_config_version,
        "findings": findings,
    }
    if checklist_version:
        out["checklist_version"] = checklist_version
    if open_questions:
        out["open_questions"] = open_questions
    if summary:
        out["summary"] = summary
    return out


def extract_headings(text: str) -> list[dict[str, Any]]:
    outline: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            outline.append(
                {
                    "level": len(m.group(1)),
                    "title": m.group(2).strip(),
                    "line": i,
                }
            )
    return outline


def extract_req_ids(text: str, pattern: str) -> list[str]:
    ids = re.findall(pattern, text, flags=re.IGNORECASE)
    # normalize
    normed = []
    seen = set()
    for x in ids:
        key = x.upper().replace("_", "-")
        if key not in seen:
            seen.add(key)
            normed.append(key)
    return normed


def extract_asset_labels(text: str) -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    # Markdown images ![alt](...)
    for m in re.finditer(r"!\[([^\]]*)\]\([^)]+\)", text):
        assets.append({"kind": "figure", "label": m.group(1) or "(unnamed)", "location": m.group(0)[:80]})
    # Explicit figure/table captions
    for m in re.finditer(r"^(?:表|图|Table|Figure)\s*([\d.]+)\s*[:：]?\s*(.*)$", text, re.M | re.I):
        assets.append({"kind": "figure", "label": f"{m.group(1)} {m.group(2)}".strip(), "location": m.group(0)[:80]})
    # Mermaid blocks
    if "```mermaid" in text.lower():
        assets.append({"kind": "mermaid", "label": "mermaid", "location": "```mermaid"})
    return assets


def section_present(outline_titles: list[str], required: str, aliases: dict[str, list[str]]) -> bool:
    candidates = [required] + aliases.get(required, [])
    lowered = [t.lower() for t in outline_titles]

    def match(cand: str) -> bool:
        c = cand.lower()
        return any(c in t or t in c for t in lowered)

    return any(match(c) for c in candidates)


def decide_verdict(cfg: dict[str, Any], overall: float, blocking_count: int, p1_count: int) -> str:
    gate = cfg.get("gate", {})
    if gate.get("reject_on_p0", True) and blocking_count > 0:
        if overall < gate.get("min_overall_score_for_pass_with_risks", 65):
            return "REJECT"
        return "NEEDS_WORK"
    if overall >= gate.get("min_overall_score_for_pass", 80) and p1_count <= gate.get(
        "max_p1_for_pass_with_risks", 5
    ):
        return "PASS"
    if overall >= gate.get("min_overall_score_for_pass_with_risks", 65):
        return "PASS_WITH_RISKS"
    return "NEEDS_WORK"
