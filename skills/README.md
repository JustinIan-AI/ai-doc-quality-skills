# Skills 设计规范索引

本目录每个子目录对应一个可独立安装的 Skill。`SKILL.md` 是 Agent Runtime 的合同入口。

## 约定

1. **Frontmatter** 必须包含 `name` 与 `description`（含触发语与明确「不用于」边界）。
2. **输出** 语义类 Skill 默认产出符合 `../contracts/findings.schema.json` 的 JSON（可同时给人读 Markdown）。
3. **禁止** 在子 Skill 内擅自改权重或宣布最终门禁 verdict（除 orchestrator 外）。
4. **证据** 每条 finding 必须有 `location` 与 `evidence_type`。
5. **版本** 引用的 checklist / score-config 版本写入输出。

## 推荐调用关系

```text
doc-quality-orchestrator
  ├── doc-ingest
  ├── structure-rules-check
  ├── prd-quality-review
  ├── design-quality-review
  ├── test-doc-quality-review
  ├── traceability-audit
  └── quality-scorecard-report
```

用户入口应优先 `doc-quality-orchestrator`，避免跳过追踪与门禁。
