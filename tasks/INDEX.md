# Tasks Index

| ID | Slug | Status | Priority | Objective | Link |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 0001 | single-symbol-fullfield-ingestion | Not Started | P0 | 新建独立 TimescaleDB + 单币种全字段采集链路（raw 模式） | tasks/0001-single-symbol-fullfield-ingestion/ |
| 0002 | governance-constitution-and-gates | Not Started | P0 | 建立“系统宪法 + 强制门禁”，以维度模型长期治理三层架构（采集/处理/消费） | tasks/0002-governance-constitution-and-gates/ |
| 0003 | safe-migrate-core-services | Not Started | P0 | 安全迁移核心服务（不改原仓库代码），将 `services/*`（除 aws-service）与 `services-preview/api-service` 迁移到 `/home/lenovo/tradecat/` 新结构 | tasks/0003-safe-migrate-core-services/ |
| 0004 | safe-migrate-data-service | Done | P0 | 首批迁移数据采集模块：将 `services/data-service` 安全迁移到 `/home/lenovo/tradecat/services/data-service` 并验证不污染源仓库 | tasks/0004-safe-migrate-data-service/ |
| 0005 | refactor-ingestion-from-data-service | Not Started | P0 | 将 `data-service` 按新三层架构重构：把采集逻辑拆进 `/home/lenovo/tradecat/tradecat/ingestion/`（不改源仓库），并提供安全切换与对齐验证 | tasks/0005-refactor-ingestion-from-data-service/ |
