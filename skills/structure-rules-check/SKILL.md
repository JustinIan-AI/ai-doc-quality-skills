---
name: structure-rules-check
description: >
  文档结构确定性检查。当需要验证必备章节、需求 ID 格式、引用是否存在时使用。
  优先规则/脚本，不依赖主观语义。不用于深度业务评审或打总分。
---

# structure-rules-check

## 职责

执行 `config/score-config.yaml` 中的结构规则，产出可机器消费的 pass/fail findings。

## 输入

- `doc-ingest` 结果
- 文档类型
- score-config（结构段）

## 检查项（默认）

1. 类型对应的必备章节是否存在（允许企业配置别名映射）。
2. 需求 ID 是否符合约定模式（可配置正则）。
3. 文内引用的图/表标签是否能在 assets 中找到。
4. 是否存在空的「待补充」占位且位于关键章节（可标 P1/P0）。

## 输出

符合 `contracts/findings.schema.json` 的 bundle：

- `skill_id`: `structure-rules-check`
- `category`: 多为 `structure`
- 规则失败且配置为 blocking → `severity: P0`, `blocking: true`

## 实现建议

- 章节存在性、正则、集合差用脚本；Skill 描述规则与如何调用脚本。
- 模型仅在「章节标题同义」映射时做有限判断，并在 finding 中标明 `evidence_type: inference`。

## 禁止

- 用长篇语义评论代替 pass/fail
- 修改 score-config 权重

## Definition of Done

- 每条失败规则有 rule 含义与 location
- JSON 可被 scorecard 直接合并
