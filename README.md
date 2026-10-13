# AI Doc Quality Skills

面向 **AI 生成交付物**（PRD、概要/详细设计、测试文档）的质量评估 Skills 组合规范。

目标不是再写一个「万能提示词」，而是把评审拆成可编排、可版本化、可门禁的工程资产：

- **确定性规则**负责结构与追踪
- **语义 Skills**负责缺口、歧义、可实现性与可测试性
- **评分与报告**输出质量分 + 阻断项双轨结果
- **编排器**统一调度并给出 PASS / NEEDS_WORK / REJECT

> 公开生态里没有现成的「PRD + 详细设计 + 测试文档」完整评审包。本仓库提供**可落地的设计规范与契约**，便于企业内实现或接到 Claude Code / Codex 等 Agent Runtime。

---

## 为什么需要组合，而不是单个 Skill

| 问题 | 单 Skill 常见失败 | 本组合的对策 |
|------|-------------------|--------------|
| 平均分掩盖致命缺陷 | 总分 85 但无权限模型 | **质量分 + 阻断项**双轨 |
| 写评同一上下文 | 自评偏松 | Reviewer 与生成者身份分离；子评审并行 |
| 结构问题靠模型猜 | 章节缺失却被语义粉饰 | `structure-rules-check` 确定性优先 |
| 需求-设计-测试断链 | 各评各的 | `traceability-audit` 强制追踪矩阵 |
| 标准漂移 | 提示词随会话改 | 检查清单与 `score-config.yaml` 版本化 |

---

## 架构总览

```text
输入文档包 (MD / DOCX / 目录)
        │
        ▼
┌───────────────────┐
│ doc-ingest        │  解析章节树、需求 ID、图表引用
└─────────┬─────────┘
          │
          ├──────────────────────┐
          ▼                      ▼
 structure-rules-check    （可并行）语义评审
 （确定性 JSON）              ├ prd-quality-review
                            ├ design-quality-review
                            └ test-doc-quality-review
          │                      │
          └──────────┬───────────┘
                     ▼
            traceability-audit
                     │
                     ▼
         quality-scorecard-report
                     │
                     ▼
         doc-quality-orchestrator
         PASS | PASS_WITH_RISKS | NEEDS_WORK | REJECT
```

详细设计见 [docs/architecture.md](docs/architecture.md)。

---

## Skills 一览

| Skill ID | 职责 | 类型 |
|----------|------|------|
| `doc-quality-orchestrator` | 识别文档类型、调度子 Skill、合并 findings、门禁裁决 | 编排 |
| `doc-ingest` | 解析 Markdown/Word，抽出结构与 ID | 解析 |
| `structure-rules-check` | 必备章节、ID 格式、引用存在性 | 确定性规则 |
| `prd-quality-review` | PRD 完整性、歧义、验收可测性 | 语义评审 |
| `design-quality-review` | 架构/数据/API/权限/异常/NFR | 语义评审 |
| `test-doc-quality-review` | 覆盖矩阵、可判定断言、边界异常 | 语义评审 |
| `traceability-audit` | 需求 ↔ 设计 ↔ 测试双向追踪 | 混合 |
| `quality-scorecard-report` | 分维评分、阻断清单、HTML/JSON 报告 | 报告 |

每个 Skill 的输入输出合同、禁止项与 Definition of Done 见 [`skills/`](skills/)。

---

## 门禁规则（默认）

1. 任意 **P0 阻断项** → 不得 `PASS` / `PASS_WITH_RISKS`，至少 `NEEDS_WORK`，严重时 `REJECT`。
2. 仅有 P2/P3 → 可 `PASS_WITH_RISKS`，必须列出待决策项与 owner 建议。
3. 结构规则失败中标记为 `blocking: true` 的项，视为 P0 等价。
4. 评分维度与权重以 [`config/score-config.yaml`](config/score-config.yaml) 为准，禁止模型临场改权重。

Verdict 枚举：

```text
PASS | PASS_WITH_RISKS | NEEDS_WORK | REJECT
```

---

## 契约与配置

| 路径 | 说明 |
|------|------|
| [`contracts/findings.schema.json`](contracts/findings.schema.json) | 统一 findings JSON Schema |
| [`config/score-config.yaml`](config/score-config.yaml) | 分维权重、严重度规则、门禁阈值 |
| [`docs/design-review-checklist.md`](docs/design-review-checklist.md) | 企业用详细设计审查清单（A–H） |

实现时建议：

1. 所有语义 Skill **只输出符合 schema 的 findings**，不直接写最终总分。
2. 总分与 verdict **仅由** `quality-scorecard-report` + `doc-quality-orchestrator` 计算。
3. 检查清单与权重变更走版本号（`score_config_version`），便于复盘与审计。

---

## 与开源生态的关系

可**嫁接**的外部资产（方法/检查维，不是整包替换）：

| 资产 | 建议用法 |
|------|----------|
| [check-prd](https://github.com/pmyangkun/check-prd-skill) | B 端 PRD 14 维 → `prd-quality-review` 的 references |
| [ai-product-manager-skills prd-review](https://github.com/PANGKAIFENG/ai-product-manager-skills) | PM/研发/测试三视角与 readiness verdict |
| Requirements Reviewer 类 100 分制 | 清晰/完整/验收/一致/范围 权重参考 |
| Matt Pocock `code-review` | **仅**实现阶段：代码相对 Spec；**不**用于文档质量评估 |

明确**不覆盖**本仓库目标的：以生成 PRD 为主的 Skill、以代码 diff 为主的 review Skill。

---

## 落地顺序（推荐）

1. **竖切 PRD**：`structure-rules-check` + `prd-quality-review` + 简易 scorecard  
2. **补设计**：落地 `design-quality-review` + [设计清单](docs/design-review-checklist.md)  
3. **补测试与追踪**：`test-doc-quality-review` + `traceability-audit`  
4. **编排与 CI**：`doc-quality-orchestrator` + HTML 报告；P0 > 0 则 pipeline fail  

每增加一个 Skill，必须同时具备：

- 检查清单版本号  
- 输出 JSON 符合 `findings.schema.json`  
- 至少 3 个误报/漏报复盘样例（建议放 `evals/`）  

---

## 目录结构

```text
.
├── README.md
├── LICENSE
├── config/
│   └── score-config.yaml
├── contracts/
│   └── findings.schema.json
├── docs/
│   ├── architecture.md
│   └── design-review-checklist.md
└── skills/
    ├── README.md
    ├── doc-quality-orchestrator/SKILL.md
    ├── doc-ingest/SKILL.md
    ├── structure-rules-check/SKILL.md
    ├── prd-quality-review/SKILL.md
    ├── design-quality-review/SKILL.md
    ├── test-doc-quality-review/SKILL.md
    ├── traceability-audit/SKILL.md
    └── quality-scorecard-report/SKILL.md
```

---

## 安装到 Agent Runtime（约定）

本仓库当前交付的是 **设计规范与 SKILL.md 合同**，不是绑定某一家模型的私有插件格式。接入时：

1. 将 `skills/<id>/` 拷贝到运行时的 skills 目录（如 `.claude/skills/` 或 Codex skills 路径）。  
2. 保证 Agent 能读到同仓库的 `config/score-config.yaml` 与 `contracts/`。  
3. 由 `doc-quality-orchestrator` 作为用户入口；禁止用户直接「让模型随便评一下」绕过契约。  

确定性检查（结构、ID、追踪集合运算）建议用脚本实现，Skill 只声明规则与调用方式。

---

## 许可

MIT。欢迎在企业内 fork 后替换 `score-config.yaml` 与检查清单，形成自己的 AI Native 文档质量基线。
