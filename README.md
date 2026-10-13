# AI Doc Quality Skills

面向 **AI 生成交付物**（PRD、概要/详细设计、测试文档）的质量评估 Skills 组合规范，并附带**可运行确定性骨架**（结构检查、追踪审计、HTML 评分报告）。

目标不是再写一个「万能提示词」，而是把评审拆成可编排、可版本化、可门禁的工程资产：

- **确定性规则**负责结构与追踪（`scripts/`）
- **语义 Skills**负责缺口、歧义、可实现性与可测试性（`skills/`）
- **评分与报告**输出质量分 + 阻断项双轨结果
- **编排器**统一调度并给出 PASS / NEEDS_WORK / REJECT

仓库：https://github.com/JustinIan-AI/ai-doc-quality-skills

---

## 5 分钟跑通 demo

```bash
git clone https://github.com/JustinIan-AI/ai-doc-quality-skills.git
cd ai-doc-quality-skills
python3 scripts/run_demo.py
# 打开 out/report.html
```

示例夹具故意制造 **REQ-3 设计/测试断链**，用于演示追踪审计与门禁。详见 [scripts/README.md](scripts/README.md)。

---

## 架构总览

```text
输入文档包 (MD / DOCX / 目录)
        │
        ▼
┌───────────────────┐
│ doc-ingest        │  scripts/ingest_markdown.py
└─────────┬─────────┘
          │
          ├──────────────────────┐
          ▼                      ▼
 structure-rules-check    （可并行）语义评审 Skill
 scripts/…                ├ prd-quality-review
                          ├ design-quality-review
                          └ test-doc-quality-review
          │                      │
          └──────────┬───────────┘
                     ▼
            traceability-audit  (scripts/traceability_audit.py)
                     │
                     ▼
         quality-scorecard-report (scripts/scorecard_report.py → HTML)
                     │
                     ▼
         doc-quality-orchestrator
         PASS | PASS_WITH_RISKS | NEEDS_WORK | REJECT
```

详细设计见 [docs/architecture.md](docs/architecture.md)。设计审查清单见 [docs/design-review-checklist.md](docs/design-review-checklist.md)。

---

## 图中能力覆盖（相对「输入→解析→评审引擎→评分→HTML 报告」）

| 能力 | 状态 |
|------|------|
| Markdown 解析与上下文 | **可运行** `ingest_markdown.py` |
| Word/DOCX | 规范要求保留；**未**内置解析器，需自接 |
| 规则检查 | **可运行** `structure_rules_check.py` |
| PRD / 设计 / 测试语义评审 | **Skill 合同**（需 Agent/LLM） |
| 交叉文档校验 | **可运行** `traceability_audit.py` |
| 分项评分 / 严重度 / 证据位置 | **可运行** scorecard |
| 误报复核 | 字段 `evidence_type`；**无**独立第二评审员流程 |
| 独立 HTML 报告（分维条 + 雷达 SVG） | **可运行** `scorecard_report.py --out-html` |

---

## Skills 一览

| Skill ID | 职责 | 类型 |
|----------|------|------|
| `doc-quality-orchestrator` | 调度、合并、门禁 | 编排 |
| `doc-ingest` | 解析章节与 ID | 解析 + 脚本 |
| `structure-rules-check` | 必备章节等 | 确定性 + 脚本 |
| `prd-quality-review` | PRD 语义 | 语义 |
| `design-quality-review` | 设计语义 | 语义 |
| `test-doc-quality-review` | 测试文档语义 | 语义 |
| `traceability-audit` | 需求↔设计↔测试 | 混合 + 脚本 |
| `quality-scorecard-report` | 评分与 HTML | 报告 + 脚本 |

---

## 门禁规则（默认）

1. 任意 **P0 / blocking** → 不得 `PASS`，通常为 `NEEDS_WORK` 或 `REJECT`。
2. 仅有 P2/P3 且分数达标 → 可 `PASS` / `PASS_WITH_RISKS`。
3. 权重与阈值以 [`config/score-config.json`](config/score-config.json)（及 YAML 同源说明）为准。

---

## 目录结构

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── config/
│   ├── score-config.yaml
│   └── score-config.json      # 脚本默认读取
├── contracts/
│   └── findings.schema.json
├── docs/
│   ├── architecture.md
│   └── design-review-checklist.md
├── fixtures/                  # demo 文档与 mock 语义 findings
├── scripts/                   # 可运行骨架
└── skills/                    # SKILL.md 合同
```

---

## 安装到 Agent Runtime

1. 拷贝 `skills/<id>/` 到运行时 skills 目录。  
2. 保证能访问本仓库 `config/`、`contracts/`、`scripts/`。  
3. 编排器对确定性步骤调用 `scripts/*.py`，语义步骤走 Skill。  

---

## 许可

MIT。
