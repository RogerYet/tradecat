# 0005 - refactor-ingestion-from-data-service

把旧的 `services/data-service` **“按功能分层重构”**到新结构中：最终采集逻辑不再以“一个服务目录”为中心，而是变成 `tradecat/ingestion` 下的可组合模块（providers/jobs/storage），并具备可验证、可回滚的迁移路径。

一句话：**旧代码只当参考/基线；新结构里重写模块边界与契约，然后用对齐验证证明迁移正确。**

## In Scope

- 源参考（只读，不改）：`/home/lenovo/.projects/tradecat/services/data-service/src/`
- 新实现目标（写在新结构）：`/home/lenovo/tradecat/tradecat/ingestion/`
- 迁移范围（只覆盖旧 data-service 的三条链路）：
  - WS 1m K线采集（buffer flush + 批量写入）
  - 缺口巡检与补齐（ZIP + REST/CCXT 兜底）
  - 期货指标采集（5m REST 并发 + 批量写入）
- 必须交付：
  - 新的 CLI 入口（替代旧 `python collectors/*.py` 的散装运行方式）
  - 与旧实现的“对齐验证脚本/用例”（单币种、固定时间窗、字段对齐）
  - 绝不污染源仓库 `.env` 与 SQLite/DB 文件（全程可证伪）

## Out of Scope

- 不在此任务里迁移 `services-preview/markets-service`（另立任务）
- 不在此任务里做数据库 schema 大改（只要能写 raw/derived 对应表即可）
- 不在此任务里做“跨源统一”（只做 Binance 这条链路的分层重构）

## 阅读与执行顺序

1. `CONTEXT.md`
2. `PLAN.md`
3. `ACCEPTANCE.md`
4. `TODO.md`
5. `STATUS.md`

