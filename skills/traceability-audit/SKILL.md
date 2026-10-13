---
name: traceability-audit
description: >
  需求-设计-测试双向追踪审计。当存在多份文档或文档包，需要找出孤儿需求、无需求的设计/测试、
  断链时使用。集合运算优先确定性；合理解释一对多由模型标注。
---

# traceability-audit

## 职责

建立并校验追踪矩阵，输出断链与孤儿项 findings。

## 输入

- 各文档 ingest 的 req_ids
- 设计锚点 ID（若有）
- 测试用例 ID（若有）
- 显式映射表（若文档已提供）

## 流程

1. 归一化 ID（大小写、前缀规则按企业配置）。
2. 计算：
   - 需求无设计
   - 需求无测试
   - 设计无需求
   - 测试无需求
3. 一对多：默认允许，但需在 finding 或 summary 中说明是否合理。
4. 无法从文本解析的映射 → open_questions，不假装已链接。

## 输出

findings（category: `traceability`）+ 可选矩阵 Markdown。

核心需求断链 → P0/blocking 按 score-config。

## 禁止

- 自动「脑补」业务上不存在的 ID 映射
- 替代语义评审

## Definition of Done

- 三类文档 ID 集合关系清楚
- 断链列表可执行（知道补哪边）
