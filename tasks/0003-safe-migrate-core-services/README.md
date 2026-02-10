# 0003 - safe-migrate-core-services

在**不修改原仓库任何业务代码**（只读）的前提下，将核心服务从

- 源仓库：`/home/lenovo/.projects/tradecat/services/`（忽略 `aws-service`）
- 源仓库：`/home/lenovo/.projects/tradecat/services-preview/api-service/`

安全迁移到新结构：

- 目标新结构：`/home/lenovo/tradecat/`（代码包位于 `/home/lenovo/tradecat/tradecat/`）

## In Scope

- 迁移 6 个服务到新结构（拷贝 + 重构在新目录内进行）：
  - `data-service`
  - `trading-service`
  - `signal-service`
  - `telegram-service`
  - `ai-service`
  - `services-preview/api-service`
- 为迁移定义“安全策略”：不写入/不污染原仓库的 `.env`、SQLite、备份、日志等敏感资源。
- 输出完整可执行的迁移步骤文档（面向执行 Agent），包含验证命令、回滚协议、风险量化。

## Out of Scope

- 不迁移 `services/aws-service`（明确忽略）。
- 不在此任务内重做数据库 schema（除非另起任务明确授权）。
- 不做“大规模重构/美化目录”——优先“可跑 + 可回滚 + 不污染源仓库”。

## 阅读与执行顺序（必须严格遵守）

1. `CONTEXT.md`
2. `PLAN.md`
3. `ACCEPTANCE.md`
4. `TODO.md`
5. `STATUS.md`

