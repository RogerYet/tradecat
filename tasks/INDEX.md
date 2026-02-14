# Tasks Index

| ID | Slug | Status | Priority | Objective | Link |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 0001 | binance-vision-um-trades-maturity | In Progress | P0 | 将 Binance Vision UM trades 采集链路补齐到“业内成熟”级别：CHECKSUM 审计、缺口修复闭环、维度字典化（v2） | tasks/0001-binance-vision-um-trades-maturity/ |
| 0002 | migrate-um-trades-ids-swap | Done | P0 | 将现有 `crypto.raw_futures_um_trades` 从旧结构（exchange/symbol + NUMERIC）安全迁移到新结构（venue_id/instrument_id + DOUBLE），并通过 rename-swap 与采集写库对齐 | tasks/0002-migrate-um-trades-ids-swap/ |
