---
name: design-quality-review
description: >
  详细设计 / 架构设计文档语义评审。按企业 Design Review 清单检查需求对齐、架构边界、
  数据与状态机、API 契约、权限安全、异常并发、可观测与可测试性。触发：审详细设计、
  架构评审、设计能不能开发。不用于写设计、PRD 文案润色、代码 diff 审查。
---

# design-quality-review

## 职责

对 AI 生成的设计文档做专项评审。清单权威来源：`docs/design-review-checklist.md`（版本写入输出）。

## 输入

- 设计文档（必选）
- 对应 PRD 或需求列表（强烈建议；缺失则一致性结论降级为 needs_confirmation）
- ingest 结果

## 检查块（A–H）

完整条文见清单。摘要：

| 块 | 主题 | 默认权重维 |
|----|------|------------|
| A | 与需求一致性 | req_alignment |
| B | 架构与边界 | architecture_boundaries |
| C | 数据设计 | data_design |
| D | API/契约 | api_contract |
| E | 权限与安全 | security_authz |
| F | 异常/并发/可靠性 | reliability_concurrency |
| G | 可观测与运维 | observability |
| H | 可实现与可测试 | implementability_testability |

## 默认 P0

- 核心需求无设计映射
- 状态机不闭合
- 多角色无授权模型
- 核心写路径无幂等

## 流程

1. 加载 checklist 版本与 score-config design 维。
2. 逐块审查；每条 finding 绑定 location。
3. 区分 fact_defect / inference / needs_confirmation。
4. 给出可补写的章节模板片段（最小集）。
5. 输出 `design_verdict_hint`: APPROVE | APPROVE_WITH_RISKS | NEEDS_WORK | REJECT（提示值）。

## 输出

findings bundle；`checklist_version` 必填。

## 禁止

- 假设 PRD Skill 已覆盖设计问题而跳过本 Skill
- 无 PRD 时假装完成需求对齐审查
- 宣布编排级最终 PASS（交给 orchestrator）

## Definition of Done

- A–H 均有显式通过说明或 findings
- P0 规则已检查
- 修订建议可回填
