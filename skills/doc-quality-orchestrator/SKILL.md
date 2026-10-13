---
name: doc-quality-orchestrator
description: >
  AI 交付物质量门禁编排器。当用户要评审 PRD、详细设计、测试文档或整包文档质量，
  需要统一评分、阻断项与 PASS/NEEDS_WORK/REJECT 时使用。触发语：审文档包、质量门禁、
  AI 交付物评审、PRD 和设计一起评。不用于写 PRD、写代码、或仅润色文案；不替代 code-review。
---

# doc-quality-orchestrator

## 职责

识别文档类型，调度子 Skill，合并 findings，应用 `config/score-config.yaml` 门禁，输出最终 verdict。

## 输入

- 文档路径列表或目录
- 可选：仅 `prd` / `design` / `test` / `bundle`
- 可选：score-config 路径（默认仓库 `config/score-config.yaml`）

## 流程

1. **Establish scope**  
   记录来源、本轮目标、是否全量。输入不足则询问，不强行当 PRD 评。

2. **Ingest**  
   调用 `doc-ingest`，得到章节树、需求 ID、图表引用。

3. **Deterministic rules**  
   调用 `structure-rules-check`，收集规则 findings。

4. **Semantic reviews（可并行）**  
   - 有 PRD → `prd-quality-review`  
   - 有设计 → `design-quality-review`（需尽量附带 PRD 做一致性）  
   - 有测试文档 → `test-doc-quality-review`

5. **Traceability**  
   多文档或 bundle 时调用 `traceability-audit`。

6. **Scorecard**  
   调用 `quality-scorecard-report` 生成分维分、阻断清单、报告。

7. **Gate**  
   按 score-config：  
   - 存在 `blocking: true` 或 P0 → 不得 PASS  
   - 结合总分阈值给出 `PASS` | `PASS_WITH_RISKS` | `NEEDS_WORK` | `REJECT`

## 输出（给人）

1. **Verdict**（单独一行）
2. **阻断项 P0 列表**（先于分数）
3. **各文档质量分与分维**
4. **优先修复 Top N**
5. **Open questions**
6. **下一步建议**（回改哪类文档 / 是否可进开发）

## 输出（机器）

合并后的 findings 数组 + `verdict` + `score_config_version`。

## 禁止

- 自己重写长文替代评审
- 在无 score-config 时临场发明权重
- 用平均分掩盖 P0
- 将代码实现质量混入文档门禁

## Definition of Done

- 每个输入文档都有明确处理路径或跳过原因
- findings 已去重并带 severity
- verdict 可追溯到 gate 规则与 P0 列表
- 声明本轮 score_config_version 与 checklist 版本
