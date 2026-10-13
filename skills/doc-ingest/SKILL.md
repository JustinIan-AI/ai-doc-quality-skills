---
name: doc-ingest
description: >
  解析 PRD/设计/测试文档结构。当需要从 Markdown 或 Word 抽出章节树、需求 ID、
  表格与图表引用以便后续评审时使用。不用于评审结论、评分或改写文档。
---

# doc-ingest

## 职责

把原始文档变成后续规则检查与语义评审可用的结构化上下文。

## 输入

- 文件路径（`.md` / `.docx` 等）或粘贴正文
- 可选：已知文档类型提示

## 流程

1. 读取全文；DOCX 尽量保留表格结构，不只转扁平面纯文本。
2. 构建标题层级大纲（H1–H3 优先）。
3. 抽取疑似需求 ID（如 `REQ-1.2`、`US-03`）；记录出现位置。
4. 列出表格标题与图/Mermaid/引用标签。
5. 启发式建议 `doc_type`：`prd` | `design` | `test` | `unknown`。

## 输出

```yaml
doc_path: string
suggested_type: prd|design|test|unknown
outline:
  - level: number
    title: string
req_ids: string[]
assets:
  - kind: table|figure|mermaid|link
    label: string
    location: string
notes: string[]   # 解析限制，如「图表仅有截图无法读字」
```

## 禁止

- 输出质量分或 P0/P1 结论
- 发明文档中不存在的需求 ID
- 丢弃表格/状态机关键信息却声称解析完整

## Definition of Done

- outline 与原文标题可对应
- 解析限制写在 notes
- 可供 structure-rules-check 与语义 Skill 直接消费
