---
type: runbook
component: knowledge-base
scenario: draft-review
priority: P2
tags:
- 知识库
- 待审核
- 管理员介入
- 多组件
- 00-README
- runbook
status: active
---

# 待审核知识草稿

管理员介入后生成的知识库草稿会先进入本目录。

审核流程：

1. 补齐组件、场景、判断依据、处理步骤和验证方式。
2. 执行知识库治理检查。
3. 确认没有敏感信息。
4. 将 `status` 从 `draft` 改为 `active`。
5. 移动到合适目录，例如 `07-故障卡片` 或 `06-FAQ`。
