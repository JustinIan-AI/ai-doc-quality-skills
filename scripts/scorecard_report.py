#!/usr/bin/env python3
"""Merge findings bundles → scores + Markdown/JSON/HTML report."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

from common import decide_verdict, load_config, write_json


def merge_findings(bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for b in bundles:
        for f in b.get("findings", []):
            key = f"{f.get('location','')}|{f.get('problem','')}|{f.get('severity')}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(f)
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    merged.sort(key=lambda x: (order.get(x.get("severity", "P3"), 9), x.get("id", "")))
    return merged


def score_dimensions(
    doc_type: str, findings: list[dict[str, Any]], cfg: dict[str, Any]
) -> tuple[dict[str, float], float]:
    dims = dict(cfg.get("dimensions", {}).get(doc_type, {}))
    if not dims:
        # fallback flat score
        deductions = cfg.get("deductions", {"P0": 40, "P1": 15, "P2": 8, "P3": 3})
        score = 100.0
        for f in findings:
            score -= float(deductions.get(f.get("severity", "P3"), 3))
        return {"overall_only": max(0.0, score)}, max(0.0, min(100.0, score))

    # Start each dimension at 100, deduct, then weighted average
    dim_scores = {k: 100.0 for k in dims}
    deductions = cfg.get("deductions", {"P0": 40, "P1": 15, "P2": 8, "P3": 3})
    cat_to_dim = _category_map(doc_type)

    for f in findings:
        sev = f.get("severity", "P3")
        ded = float(deductions.get(sev, 3))
        cat = f.get("category", "")
        target = cat_to_dim.get(cat)
        if target and target in dim_scores:
            dim_scores[target] = max(0.0, dim_scores[target] - ded)
        else:
            # spread across all dims lightly
            share = ded / max(len(dim_scores), 1)
            for k in dim_scores:
                dim_scores[k] = max(0.0, dim_scores[k] - share)

    overall = 0.0
    weight_sum = sum(dims.values()) or 1.0
    for k, w in dims.items():
        overall += dim_scores[k] * (w / weight_sum)
    return dim_scores, round(overall, 1)


def _category_map(doc_type: str) -> dict[str, str]:
    if doc_type == "prd":
        return {
            "structure": "completeness",
            "completeness": "completeness",
            "ambiguity": "clarity_precision",
            "clarity": "clarity_precision",
            "acceptance": "acceptance_quality",
            "consistency": "consistency",
            "scope": "scope_dependencies",
            "traceability": "scope_dependencies",
        }
    if doc_type == "design":
        return {
            "structure": "architecture_boundaries",
            "architecture": "architecture_boundaries",
            "data": "data_design",
            "api": "api_contract",
            "security": "security_authz",
            "reliability": "reliability_concurrency",
            "traceability": "req_alignment",
            "observability": "observability",
        }
    if doc_type == "test":
        return {
            "structure": "coverage_mapping",
            "coverage": "coverage_mapping",
            "traceability": "coverage_mapping",
            "assertion": "assertion_decidability",
            "edge": "edge_and_negative",
        }
    return {"structure": "completeness", "traceability": "scope_dependencies"}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Doc Quality Report",
        "",
        f"- **Verdict**: `{report['verdict']}`",
        f"- **Overall**: {report['overall_score']}",
        f"- **score_config_version**: {report['score_config_version']}",
        f"- **Blocking**: {report['blocking_count']}",
        "",
        "## Dimensions",
        "",
    ]
    for k, v in report.get("dimensions", {}).items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Blocking / High findings", ""]
    for f in report.get("findings_merged", []):
        if f.get("severity") in {"P0", "P1"} or f.get("blocking"):
            lines.append(
                f"- **[{f.get('severity')}]** {f.get('problem')} (@ {f.get('location')}) — {f.get('recommendation')}"
            )
    lines += ["", "## Top fixes", ""]
    for t in report.get("top_fixes", []):
        lines.append(f"- {t}")
    return "\n".join(lines) + "\n"

def render_html(report: dict[str, Any]) -> str:
    dims = report.get("dimensions", {})
    # Simple bar + CSS conic-ish radar substitute using polygon via inline SVG
    dim_items = list(dims.items())
    svg = _radar_svg(dim_items)

    rows = []
    for f in report.get("findings_merged", []):
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(f.get('severity','')))}</td>"
            f"<td>{html.escape(str(f.get('category','')))}</td>"
            f"<td>{html.escape(str(f.get('location','')))}</td>"
            f"<td>{html.escape(str(f.get('problem','')))}</td>"
            f"<td>{html.escape(str(f.get('recommendation','')))}</td>"
            f"<td>{'Y' if f.get('blocking') else ''}</td>"
            "</tr>"
        )

    bars = []
    for k, v in dim_items:
        bars.append(
            f'<div class="bar-row"><span class="label">{html.escape(k)}</span>'
            f'<div class="bar"><i style="width:{float(v):.1f}%"></i></div>'
            f'<span class="val">{float(v):.1f}</span></div>'
        )

    top = "".join(f"<li>{html.escape(t)}</li>" for t in report.get("top_fixes", []))
    oq = "".join(f"<li>{html.escape(t)}</li>" for t in report.get("open_questions", []))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>Doc Quality Report</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; color: #111; }}
h1 {{ margin-bottom: .25rem; }}
.meta {{ color: #555; margin-bottom: 1.5rem; }}
.verdict {{ display:inline-block; padding:.25rem .6rem; border-radius:6px; background:#111; color:#fff; font-weight:600; }}
.grid {{ display:grid; grid-template-columns: 1fr 280px; gap: 2rem; }}
.bar-row {{ display:grid; grid-template-columns: 160px 1fr 48px; align-items:center; gap:.5rem; margin:.35rem 0; }}
.bar {{ background:#eee; height:10px; border-radius:5px; overflow:hidden; }}
.bar i {{ display:block; height:100%; background:#2563eb; }}
.val {{ text-align:right; font-variant-numeric: tabular-nums; }}
table {{ width:100%; border-collapse: collapse; margin-top:1rem; font-size:14px; }}
th, td {{ border-bottom:1px solid #e5e5e5; padding:.5rem; text-align:left; vertical-align:top; }}
th {{ background:#fafafa; }}
@media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<h1>Doc Quality Report</h1>
<p class="meta">
  <span class="verdict">{html.escape(report['verdict'])}</span>
  &nbsp; Overall <strong>{report['overall_score']}</strong>
  · config {html.escape(str(report['score_config_version']))}
  · blocking {report['blocking_count']}
</p>
<div class="grid">
  <div>
    <h2>Dimensions</h2>
    {''.join(bars)}
    <h2>Findings</h2>
    <table>
      <thead><tr><th>Sev</th><th>Cat</th><th>Location</th><th>Problem</th><th>Recommendation</th><th>Block</th></tr></thead>
      <tbody>
      {''.join(rows) if rows else '<tr><td colspan="6">No findings</td></tr>'}
      </tbody>
    </table>
  </div>
  <div>
    <h2>Radar</h2>
    {svg}
    <h2>Top fixes</h2>
    <ol>{top or '<li>None</li>'}</ol>
    <h2>Open questions</h2>
    <ul>{oq or '<li>None</li>'}</ul>
  </div>
</div>
</body>
</html>
"""


def _radar_svg(dim_items: list[tuple[str, Any]]) -> str:
    if not dim_items:
        return "<p>No dimensions</p>"
    n = len(dim_items)
    cx, cy, r = 130, 130, 100
    pts = []
    labels = []
    for i, (name, val) in enumerate(dim_items):
        ang = -3.14159265 / 2 + (2 * 3.14159265 * i / n)
        rr = r * (float(val) / 100.0)
        x = cx + rr * __import__("math").cos(ang)
        y = cy + rr * __import__("math").sin(ang)
        pts.append(f"{x:.1f},{y:.1f}")
        lx = cx + (r + 18) * __import__("math").cos(ang)
        ly = cy + (r + 18) * __import__("math").sin(ang)
        short = name if len(name) <= 14 else name[:12] + "…"
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" text-anchor="middle">{html.escape(short)}</text>'
        )
    # axis polygon
    axis_pts = []
    for i in range(n):
        ang = -3.14159265 / 2 + (2 * 3.14159265 * i / n)
        x = cx + r * __import__("math").cos(ang)
        y = cy + r * __import__("math").sin(ang)
        axis_pts.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg width="260" height="260" viewBox="0 0 260 260">'
        f'<polygon points="{" ".join(axis_pts)}" fill="#f3f4f6" stroke="#d1d5db"/>'
        f'<polygon points="{" ".join(pts)}" fill="rgba(37,99,235,0.35)" stroke="#2563eb"/>'
        + "".join(labels)
        + "</svg>"
    )


def build_report(
    bundles: list[dict[str, Any]], cfg: dict[str, Any], doc_type: str
) -> dict[str, Any]:
    findings = merge_findings(bundles)
    dim_scores, overall = score_dimensions(doc_type, findings, cfg)
    blocking = [f for f in findings if f.get("blocking") or f.get("severity") == "P0"]
    p1 = [f for f in findings if f.get("severity") == "P1"]
    verdict = decide_verdict(cfg, overall, len(blocking), len(p1))
    top_n = int(cfg.get("report", {}).get("include_top_fixes", 10))
    top_fixes = [
        f"{f.get('severity')}: {f.get('recommendation')}" for f in findings[:top_n]
    ]
    open_q: list[str] = []
    for b in bundles:
        open_q.extend(b.get("open_questions") or [])

    return {
        "score_config_version": str(cfg.get("version", "1.0.0")),
        "doc_type": doc_type,
        "overall_score": overall,
        "dimensions": {k: round(v, 1) for k, v in dim_scores.items()},
        "blocking_count": len(blocking),
        "verdict": verdict,
        "findings_merged": findings,
        "top_fixes": top_fixes,
        "open_questions": open_q,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scorecard + HTML report")
    p.add_argument("bundles", nargs="+", type=Path, help="findings bundle JSON files")
    p.add_argument("--type", default="prd", choices=["prd", "design", "test", "bundle"])
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--out-json", type=Path, default=None)
    p.add_argument("--out-md", type=Path, default=None)
    p.add_argument("--out-html", type=Path, default=None)
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    bundles = [json.loads(path.read_text(encoding="utf-8")) for path in args.bundles]
    report = build_report(bundles, cfg, args.type if args.type != "bundle" else "prd")

    if args.out_json:
        write_json(args.out_json, report)
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(report), encoding="utf-8")
    if args.out_html:
        args.out_html.parent.mkdir(parents=True, exist_ok=True)
        args.out_html.write_text(render_html(report), encoding="utf-8")

    if not any([args.out_json, args.out_md, args.out_html]):
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report["verdict"] in {"PASS", "PASS_WITH_RISKS"} else 2


if __name__ == "__main__":
    sys.exit(main())
