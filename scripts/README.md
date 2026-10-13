# Runnable skeleton

确定性脚本，**不依赖大模型**。语义评审（PRD/设计/测试深度判断）仍由 Agent + `skills/*/SKILL.md` 完成；脚本负责 ingest、结构规则、追踪集合差、评分与 HTML 报告。

## 依赖

- Python 3.10+
- 仅标准库即可运行（读取 `config/score-config.json`）
- 可选：`pip install -r requirements.txt` 以直接加载 YAML 版配置

## 命令

```bash
# 解析 Markdown
python3 scripts/ingest_markdown.py fixtures/sample_prd.md -o out/ingest.json

# 结构规则（exit 2 = 存在 blocking finding）
python3 scripts/structure_rules_check.py fixtures/sample_prd.md --type prd -o out/structure.json

# 追踪审计
python3 scripts/traceability_audit.py \
  --req fixtures/sample_prd.md \
  --design fixtures/sample_design.md \
  --test fixtures/sample_test.md \
  -o out/trace.json

# 评分 + HTML（可合并多个 findings bundle）
python3 scripts/scorecard_report.py out/structure.json out/trace.json \
  --type prd --out-json out/report.json --out-html out/report.html --out-md out/report.md

# 一键 demo
python3 scripts/run_demo.py
```

## 与 Skills 的关系

| 脚本 | 对应 Skill |
|------|------------|
| `ingest_markdown.py` | `doc-ingest` |
| `structure_rules_check.py` | `structure-rules-check` |
| `traceability_audit.py` | `traceability-audit` |
| `scorecard_report.py` | `quality-scorecard-report` |
| `run_demo.py` | 编排器最小演示（无 LLM） |

Agent 实现 `doc-quality-orchestrator` 时应优先调用上述脚本生成确定性 findings，再跑语义 Skill，最后再次调用 `scorecard_report.py` 出报告。
