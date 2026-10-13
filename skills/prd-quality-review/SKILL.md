---
name: prd-quality-review
description: >
  PRD / 需求文档语义评审。从产品、研发、测试视角检查完整性、歧义、验收可测性、
  范围与依赖。触发：审 PRD、需求能不能开发、验收是否可测。不用于从零写 PRD、
  详细设计专项、代码审查；方案可行性压测用独立 grill 类 Skill。
---

# prd-quality-review

## 职责

对已有 PRD 做交付就绪评审，输出 findings + 可回填修订建议，**不**宣布最终门禁 verdict。

## 透镜（至少）

| 透镜 | 关注 |
|------|------|
| PM | 问题价值、成功指标可衡量、范围 In/Out、优先级 |
| 研发 | 可实现性、依赖与约束、状态/数据是否可落地 |
| 测试 | 验收可判定、边界与异常、可构造数据 |

可选：企业 B 端场景加载 check-prd 类 14 维 references（需单独放入 `references/`）。

## 评分维度（由 scorecard 计分，本 Skill 按维打 findings）

权重见 score-config `dimensions.prd`：

- clarity_precision 25
- completeness 25
- acceptance_quality 20
- consistency 15
- scope_dependencies 15

## 流程

1. 读 PRD 与 ingest 大纲；区分「文档已写事实」与「评审推断」。
2. 按透镜收集问题，合并重复项。
3. 关键验收不可测、范围矛盾 → 倾向 P0/P1 + blocking。
4. 给出最小可替换修订块（段落或清单），不默认重写全文。
5. 列出 open questions。

## 输出

- findings bundle（schema 1.0.0）
- 可选：`readiness_hint`: `ready` | `ready_with_assumptions` | `not_ready`（**提示**编排器，不替代 gate）

## 禁止

- 编造业务规则冒充已确认需求
- 无 location 的空泛批评
- 输出最终 PASS/REJECT（交给 orchestrator）

## Definition of Done

- 三透镜覆盖且 findings 已合并
- 每条含 severity、location、recommendation、evidence_type
- 阻断项与非阻断项可区分
