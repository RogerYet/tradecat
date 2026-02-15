# Tasks Index

| ID | Slug | Status | Priority | Objective | Link |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 0001 | binance-vision-um-trades-maturity | Done | P0 | 将 Binance Vision UM trades 采集链路补齐到“业内成熟”级别：CHECKSUM 审计、缺口修复闭环、维度字典化（v2） | tasks/0001-binance-vision-um-trades-maturity/ |
| 0002 | migrate-um-trades-ids-swap | Done | P0 | 将现有 `crypto.raw_futures_um_trades` 从旧结构（exchange/symbol + NUMERIC）安全迁移到新结构（venue_id/instrument_id + DOUBLE），并通过 rename-swap 与采集写库对齐 | tasks/0002-migrate-um-trades-ids-swap/ |
| 0003 | migrate-cm-trades-ids-swap | Done | P0 | 将运行库中仍为旧结构的 `crypto.raw_futures_cm_trades` 迁移到 ids+DOUBLE 事实表形态，并补齐 CM trades（实时+回填）采集卡片与写库链路 | tasks/0003-migrate-cm-trades-ids-swap/ |
| 0004 | refactor-spot-trades-fact-table | Done | P0 | 将 `crypto.raw_spot_trades` 从 legacy(file_id+time_ts+NUMERIC) 重构为极简事实表（ids+DOUBLE+time=epoch_us），并补齐 spot trades（实时+回填）采集卡片与审计闭环 | tasks/0004-refactor-spot-trades-fact-table/ |
| 0005 | add-cm-spot-trades-repair | Not Started | P0 | 补齐 CM/Spot trades 的 repair 闭环（消费 `crypto.ingest_gaps`），并统一 spot watermark 的时间单位口径（ms）以避免治理漂移 | tasks/0005-add-cm-spot-trades-repair/ |
