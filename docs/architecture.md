# 架构说明

## 1. 设计原则

1. **结构确定性、语义可模型化**  
   章节是否存在、ID 是否合法、引用是否断链 → 脚本/规则。  
   需求是否歧义、设计是否可实现 → 语义 Skill。

2. **双轨输出**  
   - 文档质量分（分维度、可复现）  
   - 阻断性清单（P0，不被平均分淹没）

3. **身份分离**  
   文档生成者与 Reviewer 在流程上分离；编排器合并时去重，不让生成上下文直接「自评通过」。

4. **证据强制**  
   每条 finding 必须带 `location`（章节/段落/表格锚点）。无法定位的只能标为 `待确认`，不得假装已证实。

5. **配置外置**  
   权重、门禁阈值、必备章节列表在 `config/score-config.yaml`，版本号写入报告，禁止改提示词偷偷改标准。

## 2. 数据流

```text
DocumentBundle
  → IngestResult (outline, req_ids, assets)
  → RuleFindings[]          (structure-rules-check)
  → SemanticFindings[]      (prd | design | test)
  → TraceFindings[]         (traceability-audit)
  → Scorecard               (quality-scorecard-report)
  → GateVerdict             (doc-quality-orchestrator)
```

统一中间结构见 `contracts/findings.schema.json`。

## 3. 文档类型识别

编排器根据路径、标题、必备章节启发式判定：

| 类型 | 典型信号 |
|------|----------|
| `prd` | 用户故事、验收标准、范围 In/Out、成功指标 |
| `design` | 架构、数据模型、API、时序/状态机、NFR 机制 |
| `test` | 用例、前置条件、步骤、期望结果、覆盖矩阵 |
| `bundle` | 同目录或多文件同时含以上类型 |

无法判定时询问用户，不默认当成 PRD 硬评。

## 4. 并行与合并

- `structure-rules-check` 与各语义评审可并行。  
- 合并时按 `(doc_id, location, problem_fingerprint)` 去重。  
- 同一问题多视角命中：保留最高严重度，`lenses` 数组记录来源。  

## 5. 与实现层的边界

本组合止于**文档门禁**。代码是否实现 Spec，应使用独立的 code-review（例如 Matt Pocock 双轴 Standards + Spec），不要塞进文档评分器。

## 6. 安全与数据边界

Skills 本身是指令与规则文件，**不保证**数据不出域。企业部署需单独约束：

- 模型推理端点与网络出口  
- 文档临时文件与日志留存  
- 是否允许将客户 PRD 发到公有 API  

建议在编排器输出中增加 `data_residency_note` 字段，提示本轮是否本地推理。
