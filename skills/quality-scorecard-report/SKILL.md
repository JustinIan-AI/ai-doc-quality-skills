---
name: quality-scorecard-report
description: >
  根据 findings 与 score-config 计算分维质量分、汇总阻断项，生成 Markdown/JSON/HTML 报告骨架。
  在子评审完成后、编排器给出门禁前使用。不重新发明检查项，不修改原始 findings 语义。
---

# quality-scorecard-report

## 职责

聚合各 Skill 的 findings，按权重计分，产出可读报告与机器 JSON。

## 输入

- 一个或多个 findings bundle
- `config/score-config.yaml`
- 文档类型

## 计分规则（默认）

1. 从 100 分起，按 finding 严重度与所属 dimension 扣分（具体扣分表可在 config 扩展；未扩展时使用内置：P0 维内清零倾向、P1 重扣、P2/P3 轻扣）。
2. **阻断项列表独立输出**，即使某维仍有剩余分。
3. 不把「未检查的维」标为满分；未覆盖维标记 `not_scored`。

## 报告内容

1. score_config_version / checklist 版本
2. 总体与分维分
3. P0/P1 清单（先于叙事）
4. Top N 优先修复
5. 修订示例（来自 findings.recommendation）
6. Open questions
7. 可选：HTML 骨架（表格 + 分维条；雷达图可后续脚本化）

## 输出 JSON 形状（建议）

```json
{
  "score_config_version": "1.0.0",
  "doc_type": "prd",
  "overall_score": 72,
  "dimensions": { "clarity_precision": 80, "completeness": 60 },
  "blocking_count": 2,
  "findings_merged": [],
  "top_fixes": []
}
```

## 禁止

- 丢弃 P0 只报总分
- 擅自改权重
- 代替 orchestrator 做最终 gate（可提供 score 供 gate 使用）

## Definition of Done

- 分数可复现（同 findings + 同 config → 同结果）
- 阻断项完整
- 报告可单独发给人类阅读
